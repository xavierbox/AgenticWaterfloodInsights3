import sys, pprint, pandas as pd  
sys.path.append('../../')
sys.path.append('../')
sys.path.append('./')

from typing import Any, Dict, List, Iterable, Literal, Union, Optional,TypedDict
from typing_extensions import Self
   
from uuid import uuid4
 
from pydantic import BaseModel, Field 
from get_llm_model import azure_llm_if
from pathlib import Path
from langchain.agents.structured_output import ToolStrategy
from langgraph.graph import StateGraph, END

from langchain.agents import create_agent

from visualization_system.visualization_backend.analyst.analyst_system import PlannerConfig, DirectAnswerConfig
from visualization_system.visualization_backend.analyst.analyst_models import TableItemAgentResponse, SystemPlan, SystemTask 
from visualization_system.visualization_backend.analyst.smart_data import SmartData
from visualization_system.visualization_backend.analyst.smart_data_tools import SmartDataTools
from visualization_system.visualization_backend.analyst.analyst_system import SQLAnalystConfig


class PlannerComponent:
    def __init__(self, llm: Any,  config: PlannerConfig | None = None):
        self.config = config if not config is None else PlannerConfig()
        self.llm = llm

    @property
    def prompt(self) -> str:
        return self.config.prompt

    def run(self, user_query: str,previous_state = None ) -> SystemPlan:
        return self.plan( user_query )
    
    def plan(self, user_query: str, previous_state = None ) -> SystemPlan:
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": user_query},
        ]

        structured_llm = self.llm.with_structured_output(SystemPlan)
        return structured_llm.invoke(messages)
    
class RouterState(BaseModel):
    plan: SystemPlan
    task_index_to_execute: int = 0
    #waiting_for_user: bool = False

class RouterComponent:
    """
    Decide which execution route should run next for the current plan state.

    Note that task_index_to_execute = 0 is the step right after the plan. Plan can be seen as step -1 

    The router does not execute tasks. It only inspects the current `SystemPlan`,
    the current `task_index`, and whether the system is waiting for user input,
    then returns a symbolic route name such as:

    - "direct_answer"
    - "rag_retriever"
    - "data_analysis"
    - "clarification"
    - "aggregate"
    - "end"

    The returned route is later mapped by the graph to the corresponding node.
    """
 
    def route(self, state: RouterState) -> str:
        plan = state.plan

        if plan.clarification_request is not None:
            return "clarification"

        if plan.direct_answer is not None:
            return "direct_answer"

        if state.task_index_to_execute >= len(plan.tasks):
            return "aggregate"

        return plan.tasks[state.task_index_to_execute].agent

    def run(self, state: RouterState) -> str:
        return self.route(state)

class TextResult(BaseModel):
    text: str
    role: str = "answer"

class DataFrameResult(BaseModel):
    table_name: str
    description: str | None = None
    dataframe: Any

class TaskResult(BaseModel):
    """
    Output produced by one executed task.

    This object separates the task output into three layers:
    cheap prompt context, raw agent-specific outputs, and normalized
    downstream-consumable data.
    """

    agent: str = Field(
        description="Name of the agent/component that executed the task."
    )

    instruction: str = Field(
        description="Original instruction given to the agent/component."
    )

    cheap_output: str | None = Field(
        default=None,
        description=(
            "Short, cheap textual summary of the result. "
            "This is intended to be added to facts_context and reused in prompts."
        ),
    )

    raw_results: list[Any] = Field(
        default_factory=list,
        description=(
            "Original agent-specific outputs, such as structured LLM responses, "
            "Pydantic models, tool call responses, or metadata objects."
        ),
    )

    data_results: list[Any] = Field(
        default_factory=list,
        description=(
            "Materialized downstream-friendly objects, such as DataFrames, "
            "figures, arrays, or tables. Downstream components should consume "
            "these without knowing the raw output schema."
        ),
    )

class ExecutorState(TypedDict):
    """
    Shared graph execution state.

    This is the persistent state passed between graph nodes.
    """

    user_query: str
    plan: SystemPlan | None
    task_index_to_execute: int

    facts_context: str
    cheap_tool_outputs: list[str]
    task_results: list[TaskResult]

    final_answer: str | None
    clarification_request: str | None
    #waiting_for_user: bool

class ExecutionStateUpdater:
    """
    Utility responsible for applying a TaskResult to the graph execution state.

    It centralizes the state-update rules used after a worker/component finishes:
    advancing the task cursor, storing the result, collecting cheap prompt
    context, and rebuilding facts_context.
    """

    def append_result(
        self,
        state: ExecutorState,
        result: TaskResult,
    ) -> dict:
        cheap_tool_outputs = list(state.get("cheap_tool_outputs", []))

        if result.cheap_output:
            cheap_tool_outputs.append(result.cheap_output)

        return {
            "task_index_to_execute": state["task_index_to_execute"] + 1,
            "task_results": list(state.get("task_results", [])) + [result],
            "cheap_tool_outputs": cheap_tool_outputs,
            "facts_context": "\n\n".join(cheap_tool_outputs),
        }

    def set_final_answer(
        self,
        final_answer: str,
        waiting_for_user: bool = False,
    ) -> dict:
        return {
            "final_answer": final_answer,
            "waiting_for_user": waiting_for_user,
        }
    
class TaskExecutionContext(BaseModel):
    """
    Clean input passed to a worker for executing one task.

    This is built from ExecutorState immediately before calling a worker.
    Workers should not receive the full graph state.
    """

    plan: SystemPlan = Field(
        description="The full execution plan produced by the planner."
    )

    task: SystemTask = Field(
        description="The specific task to execute now."
    )

    task_index_to_execute: int = Field(
        description="Index of the task being executed in plan.tasks."
    )

    facts_context: str = Field(
        default="",
        description=(
            "Accumulated cheap textual context from previous tasks. "
            "Workers may use this as conversation/history context."
        ),
    )

class TaskExecutionContextBuilder:
    """
    Builds the clean worker input object from the graph execution state.

    Graph nodes should use this before calling a worker, instead of passing the
    full ExecutorState directly to the worker.
    """

    def from_state(self, state: ExecutorState) -> TaskExecutionContext:
        plan = state["plan"]

        if plan is None:
            raise ValueError("No plan available")

        task_index_to_execute = state["task_index_to_execute"]

        if task_index_to_execute >= len(plan.tasks):
            raise IndexError(
                f"task_index_to_execute {task_index_to_execute} out of range "
                f"for {len(plan.tasks)} tasks"
            )

        task = plan.tasks[task_index_to_execute]

        return TaskExecutionContext(
            plan=plan,
            task=task,
            task_index_to_execute=task_index_to_execute,
            facts_context=state.get("facts_context", ""),
        )
    
class DirectAnswerComponent:
    agent_name = "direct_answer"

    def __init__(self, llm: Any, config: DirectAnswerConfig | None = None):
        self.llm = llm
        self.config = config if config is not None else DirectAnswerConfig()

    @property
    def prompt(self) -> str:
        return self.config.prompt


    def run(self, query: str,  facts_context = None ) -> TaskResult:
        response = self.llm.invoke([
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": query},
        ])

        answer = response.content

        text_result = TextResult(
            text=answer,
            role="answer",
        )

        return TaskResult(
            agent=self.agent_name,
            instruction=query,
            cheap_output=answer,
            raw_results=[answer],
            data_results=[text_result],
        )



class AgentTableResponse(BaseModel):
    # Literal ensures the LLM chooses only these specific strings
    agent: Literal["analyst"] = Field(
        default="analyst", 
        description="The role of the agent. Always 'analyst'."
    )

    clarification: Optional[str] = Field(default=None, description="A follow-up question if the response_type is 'question'")

    user_query: str = Field( description='sanitized user query')
    tables: List[TableItemAgentResponse] = Field(default=[], description="Comma-separated list of table names")

class DataAnalystComponent:
    agent_name = "data_analysis"

    def __init__(
            self,
            llm: Any,
            smart_data: SmartData | None = None,
            config: SQLAnalystConfig | None = None,
        ):
        self.llm = llm
        self._smart_data = smart_data if smart_data is not None else SmartData()
        self.config = config if config is not None else SQLAnalystConfig()

        self.tools_object = SmartDataTools(self._smart_data)
        self.tools = self.tools_object.get_tools()

    @property
    def prompt(self) -> str:
        return self.config.prompt # type: ignore

    @property
    def smart_data(self) -> SmartData:
        return self._smart_data
    
    def init_semantic_models(self,semantic_catalog, idiom_rules, idiom = 'duckdb'): 
        
        
        # the tables
        #first set the semantic model, when data arrives later we set the new data. No tools or anything will need update
        #this has no data, just semantic models and we dont know the size of the tables 
        self._smart_data.init_from_semantic_models( semantic_catalog.tables )

        # the base prompt (without history, which could be added)
        constraints = "".join([f"- {i}\n" for i in semantic_catalog.semantic_constraints])
        idiom_context = "".join([f"- {i}: {v}\n" for i,v in idiom_rules.items()])
        self.config.prompt = self.config.prompt_template.format(idiom = idiom, 
                                    idiom_examples = idiom_context, 
                                    constraints = constraints)

    def set_data(self,df_dict: Dict[str,pd.DataFrame]):
         self._smart_data.set_data(df_dict) 

    def run(self, query: str, facts_context : str | None  = None) -> TaskResult:

        prompt = self.prompt
        if  facts_context:
            prompt = prompt + f"\nCONVERSATION FACTS:\n{facts_context}" 


        agent = create_agent(
            model=self.llm,
            system_prompt = prompt,
            tools=self.tools,
            response_format=ToolStrategy(AgentTableResponse),
        )

        response = agent.invoke({
            "messages": [
                {"role": "user", "content": query}
            ]
        })

        raw_result = response.get("structured_response")

        if raw_result is None:
            raw_results = []
        elif isinstance(raw_result, list):
            raw_results = raw_result
        else:
            raw_results = [raw_result]

        cheap_parts: list[str] = []
        data_results: list[DataFrameResult] = []

        for raw in raw_results:
            text = getattr(raw, "text", None)
            if text:
                cheap_parts.append(text)

            tables = getattr(raw, "tables", []) or []

            for table in tables:
                table_name = getattr(table, "table_name", None)
                description = getattr(table, "description", None)

                if not table_name:
                    continue

                cheap_parts.append(
                    f"{self.agent_name} agent created and stored the table `{table_name}`: {description or 'No description provided.'}"
                )

                df = self._smart_data.get_table_as_df(table_name)

                data_results.append(
                    DataFrameResult(
                        table_name=table_name,
                        description=description,
                        dataframe=df,
                    )
                )

                if df.shape[0] < 10 and df.shape[1] < 4:
                    cheap_parts.append(
                        f"Table `{table_name}` contents:\n{df.to_string(index=False)}"
                    )

        cheap_output = "\n\n".join(cheap_parts) if cheap_parts else (
            "Data analyst completed, but no textual summary or table metadata was returned."
        )

        return TaskResult(
            agent=self.agent_name,
            instruction=query,
            cheap_output=cheap_output,
            raw_results=raw_results,
            data_results=data_results,
        )

class AggregatorComponent:
    """
    Builds the final user-facing answer from completed task results.
    """

    def run(self, task_results: list[TaskResult]) -> str:
        parts: list[str] = []

        for task_result in task_results:
            if task_result.cheap_output:
                parts.append(task_result.cheap_output)

        if not parts:
            return "The requested tasks completed, but no textual result was produced."

        return "\n\n".join(parts)
    
class AgenticSystem:
    """
    Minimal graph orchestrator.

    Owns the components, builds the graph, and executes the planned tasks
    sequentially until the router returns aggregate/end.
    """

    def __init__(
        self,
        llm: Any,
        planner_component: PlannerComponent | None = None,
        router_component: RouterComponent | None = None,
        direct_answer_component: DirectAnswerComponent | None = None,
        data_analyst_component: DataAnalystComponent | None = None,
        aggregator_component: AggregatorComponent | None = None,
    ):
        self.llm = llm

        self.planner_component = planner_component or PlannerComponent(llm=llm)
        self.router_component = router_component or RouterComponent()
        self.direct_answer_component = direct_answer_component or DirectAnswerComponent(llm=llm)
        self.data_analyst_component = data_analyst_component or DataAnalystComponent(llm=llm)
        self.aggregator_component = aggregator_component or AggregatorComponent()

        self.state_updater = ExecutionStateUpdater()

        self.graph = StateGraph(ExecutorState)
        self.app = None

    def create_graph(self):
        graph = self.graph

        graph.add_node("planner_node", self.planner_node)
        graph.add_node("router_node", self.router_node)
        graph.add_node("direct_answer_node", self.direct_answer_node)
        graph.add_node("data_analysis_node", self.data_analysis_node)
        graph.add_node("aggregator_node", self.aggregator_node)
        graph.add_node("clarification_node", self.clarification_node)
        graph.set_entry_point("planner_node")

        graph.add_edge("planner_node", "router_node")

        graph.add_conditional_edges(
            "router_node",
            self.route_next_task,
            {
                "direct_answer": "direct_answer_node",
                "data_analysis": "data_analysis_node",
                "clarification": "clarification_node",
                "aggregate": "aggregator_node",
                "end": END,
            },
        )

        graph.add_edge("direct_answer_node", "router_node")
        graph.add_edge("data_analysis_node", "router_node")
        graph.add_edge("clarification_node", END)
        graph.add_edge("aggregator_node", END)

        return graph

    def compile_graph(self):
        self.app = self.graph.compile()
        return self.app

    def clarification_node(self, state: ExecutorState):
        plan = state["plan"]

        if plan is None:
            raise ValueError("No plan available")

        return {}

    def planner_node(self, state: ExecutorState):
        plan = self.planner_component.run(state["user_query"])

        return {
            "plan": plan,
            "task_index_to_execute": 0,
            "facts_context": "",
            "cheap_tool_outputs": [],
            "task_results": [],
            "final_answer": None,
            "clarification_request": plan.clarification_request,
        }

    def router_node(self, state: ExecutorState):
        return {}

    def route_next_task(self, state: ExecutorState) -> str:

        plan = state["plan"]

        if plan is None:
            raise ValueError("No plan available")

        router_state = RouterState(
            plan=plan,
            task_index_to_execute=state["task_index_to_execute"],
            #waiting_for_user=state.get("waiting_for_user", False),
        )

        return self.router_component.run(router_state)

    def _get_current_task(self, state: ExecutorState) -> SystemTask:
        plan = state["plan"]

        if plan is None:
            raise ValueError("No plan available")

        task_index_to_execute = state["task_index_to_execute"]

        if task_index_to_execute >= len(plan.tasks):
            raise IndexError(
                f"task_index_to_execute {task_index_to_execute} out of range "
                f"for {len(plan.tasks)} tasks"
            )

        return plan.tasks[task_index_to_execute]

    def direct_answer_node(self, state: ExecutorState):
        task = self._get_current_task(state)

        task_result = self.direct_answer_component.run(
            query=task.instruction,
            facts_context=state.get("facts_context", ""),
        )
        return self.state_updater.append_result(state, task_result)

    def data_analysis_node(self, state: ExecutorState):
        task = self._get_current_task(state)

        task_result = self.data_analyst_component.run(
                query=task.instruction,
                facts_context=state.get("facts_context", ""),
            )
        
        return self.state_updater.append_result(state, task_result)

    def aggregator_node(self, state: ExecutorState):
        final_answer = self.aggregator_component.run(
            state.get("task_results", [])
        )

        return {
            "final_answer": final_answer,
        }

    def run(self, user_query: str):
        if self.app is None:
            self.create_graph()
            self.compile_graph()

        initial_state: ExecutorState = {
            "user_query": user_query,
            "plan": None,
            "task_index_to_execute": 0,
            "facts_context": "",
            "cheap_tool_outputs": [],
            "task_results": [],
            "final_answer": None,
            "clarification_request": None,
        }


        return self.app.invoke(initial_state)
    
 
class UIItem(BaseModel):
    id: str
    type: Literal["table", "chart", "text", "markdown", "error", "question"]
    title: str | None = None
    data: dict[str, Any]
    meta: dict[str, Any] = Field(default_factory=dict)


class PresenterResponse(BaseModel):
    agent: Literal["presenter"] = "presenter"
    layout: Literal["vertical", "horizontal"] = "vertical"
    items: list[UIItem] = Field(default_factory=list)

class ChartRequest(BaseModel):
    user_query: str
    user_intent: str | None = None

    table_name: str
    table_description: str | None = None
    dataframe: Any

    facts_context: str = ""

class TableGeneratorComponent:
    """
    Converts a DataFrameResult into a UI table item.
    """

    def run(self, dataframe_result: DataFrameResult) -> UIItem:
        df = dataframe_result.dataframe

        columns = [
            {
                "header": str(col),
                "field": str(col),
            }
            for col in df.columns
        ]

        rows = df.to_dict(orient="records")

        return UIItem(
            id=f"table_{dataframe_result.table_name}_{uuid4().hex[:8]}",
            type="table",
            title=dataframe_result.table_name,
            data={
                "columns": columns,
                "rows": rows,
            },
            meta={
                "description": dataframe_result.description,
                "sortable": True,
                "shape": {
                    "rows": int(df.shape[0]),
                    "columns": int(df.shape[1]),
                },
            },
        )

class ChartGeneratorComponent:
    """
    Creates chart UI items from chart requests.

    For now this returns a dummy Plotly chart item. Later this component can use
    rules, tools, or an LLM to generate an appropriate Plotly figure.
    """

    def __init__(self, llm: Any):
        self.llm = llm

    def run(self, request: ChartRequest) -> UIItem:
        df = request.dataframe

        if df is None or not hasattr(df, "shape") or df.empty:
            return UIItem(
                id=f"chart_error_{uuid4().hex[:8]}",
                type="error",
                title=f"Could not chart {request.table_name}",
                data={
                    "message": "Cannot produce chart for empty or invalid dataframe.",
                    "details": request.table_description or "",
                },
                meta={
                    "source_table": request.table_name,
                },
            )

        return UIItem(
            id=f"chart_{request.table_name}_{uuid4().hex[:8]}",
            type="chart",
            title=request.table_name,
            data={
                "engine": "plotly",
                "plotly": {
                    "data": [],
                    "layout": {
                        "title": {
                            "text": request.table_description or request.table_name
                        },
                        "margin": {
                            "t": 40,
                            "r": 40,
                            "b": 60,
                            "l": 60,
                        },
                    },
                },
            },
            meta={
                "source_table": request.table_name,
                "description": request.table_description,
                "user_query": request.user_query,
                "user_intent": request.user_intent,
                "dummy": True,
            },
        )

class PresenterComponent:
    """
    Converts the completed ExecutorState into UI display items.

    This component decides whether each result should become text, table, chart,
    question, or error. It delegates table serialization to TableGeneratorComponent
    and chart generation to ChartGeneratorComponent.
    """

    def __init__(self, llm: Any):
        self.llm = llm

    def run(self, result_state: ExecutorState) -> PresenterResponse:

        def _make_clarification_item(clarification_request: str) -> UIItem:
            return UIItem(
                id=f"question_{uuid4().hex[:8]}",
                type="question",
                title="Additional information required",
                data={"question": clarification_request},
            )

        def _make_text_item(data_result: TextResult) -> UIItem:
            return UIItem(
                id=f"text_{uuid4().hex[:8]}",
                type="text",
                title=None,
                data={"text": data_result.text},
            )

        def _make_error_item(
            task_result: TaskResult,
            data_result: object | None = None,
        ) -> UIItem:
            return UIItem(
                id=f"error_{uuid4().hex[:8]}",
                type="error",
                title="Presentation error",
                data={
                    "message": f"No presenter for result from {task_result.agent}",
                    "details": (
                        str(type(data_result))
                        if data_result is not None
                        else task_result.instruction
                    ),
                },
            )

        ui_items: list[UIItem] = []

        clarification_request = result_state.get("clarification_request")
        if clarification_request:
            ui_items.append(_make_clarification_item(clarification_request))
            return PresenterResponse(items=ui_items)

        for task_result in result_state.get("task_results", []):
            for data_result in task_result.data_results:

                if isinstance(data_result, TextResult):
                    ui_items.append(_make_text_item(data_result))

                elif isinstance(data_result, DataFrameResult):
                    print("processing dataframe result")
                    # later:
                    # ui_items.append(table_or_chart_item)

                else:
                    ui_items.append(_make_error_item(task_result, data_result))

        return PresenterResponse(items=ui_items)











   







