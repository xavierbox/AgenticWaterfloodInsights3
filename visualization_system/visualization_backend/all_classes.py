from dataclasses import dataclass
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

#from visualization_system.visualization_backend.analyst.analyst_system import PlannerConfig, DirectAnswerConfig
from visualization_system.visualization_backend.analyst.analyst_models import TableItemAgentResponse, SystemPlan, SystemTask 
from visualization_system.visualization_backend.analyst.smart_data import SmartData
from visualization_system.visualization_backend.analyst.smart_data_tools import SmartDataTools
from visualization_system.visualization_backend.analyst.analyst_system import SQLAnalystConfig

from visualization_system.visualization_backend.analyst.prompts import planner_prompt3 
from visualization_system.visualization_backend.analyst.prompts import anayst_prompt_template 
from visualization_system.visualization_backend.analyst.prompts import chart_agent_prompt


@dataclass 
class DirectAnswerConfig:
    prompt :str =  ("Answer using stable general knowledge. "
                    "Be concise. Return reusable factual context."
                    "The user is a reservoir engineer")

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


class TextResult(BaseModel):
    text: str
    role: str = "answer"


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

class DataFrameResult(BaseModel):
    table_name: str
    description: str | None = None
    dataframe: Any

@dataclass 
class PlannerConfig:
    prompt :str = planner_prompt3

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

class xxTableGeneratorComponent:
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

class old_ChartGeneratorComponent:
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

class old_PresenterComponent:
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

                #Note: when the analyst returns 2+ tables, we still use the same code 
                # as the dataresults are just added to the list 
                elif isinstance(data_result, DataFrameResult):
                    print("processing dataframe result")
                    # later:
                    # ui_items.append(table_or_chart_item)

                else:
                    ui_items.append(_make_error_item(task_result, data_result))

        return PresenterResponse(items=ui_items)














from typing import Any
import pandas as pd, re, json  
from langchain_core.messages import SystemMessage, HumanMessage

 



def format_label(name: str) -> str:
    """
    Convert column-like names to display labels.

    Examples:
    - year_quarter -> Year quarter
    - percentage_contribution -> Percentage contribution
    - TOTAL_WATER_INJECTION_VOLUME -> Total water injection volume
    """
    if name is None:
        return ""

    text = str(name).replace("_", " ").strip().lower()
    return text[:1].upper() + text[1:]
def _as_list(value):
    if value is None:
        return []
    return [value] if isinstance(value, str) else list(value)

def _strip_markdown_json(text: str) -> str:
    """
    Remove markdown code fences from LLM JSON responses.

    Examples:
    ```json
    {...}
    ```

    ->
    {...}
    """

    text = text.strip()

    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    return text.strip()


def _validate_columns(
    df: pd.DataFrame,
    columns: list[str],
    label: str = "column",
):
    """
    Validate that all requested columns exist in the dataframe.
    """

    missing = [c for c in columns if c not in df.columns]

    if missing:
        raise ValueError(f"Missing {label}(s): {missing}")

def _filter_args(
    tool: str,
    args: dict[str, Any],
) -> dict[str, Any]:
    """
    Remove unsupported arguments generated by the LLM.
    """

    allowed_args = {
        "preprocess_for_chart": {
            "create_combined_category",
            "create_date_bucket",
        },

        "plot_bar_chart": {
            "x",
            "y",
            "aggregate",
            "group_by",
            "color_by",
            "orientation",
            "barmode",
            "title",
            "template",
        },

        "plot_line_chart": {
            "x",
            "y",
            "aggregate",
            "group_by",
            "color_by",
            "date_bucket",
            "cumulative",
            "title",
            "template",
        },

        "plot_pie_chart": {
            "labels",
            "values",
            "aggregate",
            "group_by",
            "title",
            "hole",
            "template",
        },

        "plot_scatter_chart": {
            "x",
            "y",
            "color_by",
            "size_by",
            "text_by",
            "title",
            "template",
        },
    }

    if tool not in allowed_args:
        raise ValueError(f"Unknown tool: {tool}")

    return {
        k: v
        for k, v in args.items()
        if k in allowed_args[tool]
    }

ALLOWED_AGGS = {"sum", "mean", "median", "min", "max", "count", "nunique"}


def _aggregate(
    df: pd.DataFrame,
    group_by: list[str],
    value_cols: list[str],
    aggregate: str,
) -> pd.DataFrame:
    if aggregate not in ALLOWED_AGGS:
        raise ValueError(f"Unsupported aggregate: {aggregate}")

    _validate_columns(df, group_by, "group_by column")
    _validate_columns(df, value_cols, "value column")

    return (
        df.groupby(group_by, dropna=False, as_index=False)[value_cols]
        .agg(aggregate)
    )


def _bucket_date(
    df: pd.DataFrame,
    date_col: str,
    bucket: str,
) -> tuple[pd.DataFrame, str]:
    """
    Create a date bucket column.

    bucket:
    - "D": day
    - "W": week
    - "M": month
    - "Q": quarter
    - "Y": year
    """

    out = df.copy()
    bucket_col = f"{date_col}_{bucket}"

    _validate_columns(out, [date_col])

    out[date_col] = pd.to_datetime(out[date_col], errors="coerce")

    if bucket == "D":
        out[bucket_col] = out[date_col].dt.to_period("D").dt.to_timestamp()
    elif bucket == "W":
        out[bucket_col] = out[date_col].dt.to_period("W").dt.start_time
    elif bucket == "M":
        out[bucket_col] = out[date_col].dt.to_period("M").dt.to_timestamp()
    elif bucket == "Q":
        out[bucket_col] = out[date_col].dt.to_period("Q").dt.to_timestamp()
    elif bucket == "Y":
        out[bucket_col] = out[date_col].dt.to_period("Y").dt.to_timestamp()
    else:
        raise ValueError("date_bucket must be one of: D, W, M, Q, Y")

    return out, bucket_col

def preprocess_for_chart(
    df: pd.DataFrame,
    *,
    create_combined_category: dict | None = None,
    create_date_bucket: dict | None = None,
) -> pd.DataFrame:
    """
    Prepare a dataframe for charting by creating optional derived columns.
    """

    out = df.copy()

    if create_combined_category:
        col1 = create_combined_category["col1"]
        col2 = create_combined_category["col2"]
        new_col = create_combined_category.get("new_col") or f"{col1}_{col2}"
        sep = create_combined_category.get("sep", " / ")

        _validate_columns(out, [col1, col2])

        out[new_col] = (
            out[col1].fillna("").astype(str)
            + sep
            + out[col2].fillna("").astype(str)
        )

    if create_date_bucket:
        date_col = create_date_bucket["date_col"]
        bucket = create_date_bucket["bucket"]
        new_col = create_date_bucket.get("new_col") or f"{date_col}_{bucket}"

        _validate_columns(out, [date_col])

        dt = pd.to_datetime(out[date_col], errors="coerce")

        if bucket == "D":
            out[new_col] = dt.dt.to_period("D").dt.to_timestamp()
        elif bucket == "W":
            out[new_col] = dt.dt.to_period("W").dt.start_time
        elif bucket == "M":
            out[new_col] = dt.dt.to_period("M").dt.to_timestamp()
        elif bucket == "Q":
            out[new_col] = dt.dt.to_period("Q").dt.to_timestamp()
        elif bucket == "Y":
            out[new_col] = dt.dt.to_period("Y").dt.to_timestamp()
        else:
            raise ValueError("bucket must be one of: D, W, M, Q, Y")

    return out


def plot_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str | list[str],
    *,
    aggregate: str | None = None,
    group_by: list[str] | str | None = None,
    color_by: str | None = None,
    orientation: str = "v",
    barmode: str = "group",
    title: str | None = None,
    template: str = "plotly_white",
) -> dict:
    y_cols = _as_list(y)

    required = [x, *y_cols]
    if color_by:
        required.append(color_by)

    _validate_columns(df, required)

    work = df.copy()

    if aggregate is not None:
        group_cols = _as_list(group_by) or [x]

        if x not in group_cols:
            group_cols.insert(0, x)

        if color_by and color_by not in group_cols:
            group_cols.append(color_by)

        work = _aggregate(work, group_cols, y_cols, aggregate)

    data = []
    groups = work.groupby(color_by, dropna=False) if color_by else [(None, work)]

    for group_value, g in groups:
        for y_col in y_cols:
            if group_value is None:
                name = format_label(y_col)
            else:
                name = format_label(str(group_value))

            if group_value is not None and len(y_cols) > 1:
                name = f"{format_label(str(group_value))} - {format_label(y_col)}"

            trace = {
                "type": "bar",
                "name": name,
                "orientation": orientation,
            }

            if orientation == "h":
                trace["x"] = g[y_col].tolist()
                trace["y"] = g[x].astype(str).tolist()
            else:
                trace["x"] = g[x].astype(str).tolist()
                trace["y"] = g[y_col].tolist()

            data.append(trace)

    y_label = format_label(", ".join(y_cols))
    x_label = format_label(x)

    return {
        "data": data,
        "layout": {
            "title": {
                "text": title or f"{y_label} by {x_label}"
            },
            "xaxis": {
                "title": {
                    "text": y_label if orientation == "h" else x_label
                }
            },
            "yaxis": {
                "title": {
                    "text": x_label if orientation == "h" else y_label
                }
            },
            "barmode": barmode,
            #"template": template,
        },
        "config": {
            "responsive": True,
            "displaylogo": False,
        },
    }

def plot_line_chart(
    df: pd.DataFrame,
    x: str,
    y: str | list[str],
    *,
    aggregate: str | None = None,
    group_by: list[str] | str | None = None,
    color_by: str | None = None,
    date_bucket: str | None = None,
    cumulative: bool = False,
    title: str | None = None,
    template: str = "plotly_white",
) -> dict:
    y_cols = _as_list(y)

    required = [x, *y_cols]
    if color_by:
        required.append(color_by)

    _validate_columns(df, required)

    work = df.copy()
    x_plot = x

    if date_bucket is not None:
        work, x_plot = _bucket_date(work, x, date_bucket)

    if aggregate is not None:
        group_cols = _as_list(group_by) or [x_plot]

        if x_plot not in group_cols:
            group_cols.insert(0, x_plot)

        if color_by and color_by not in group_cols:
            group_cols.append(color_by)

        work = _aggregate(work, group_cols, y_cols, aggregate)

    sort_cols = [color_by, x_plot] if color_by else [x_plot]
    work = work.sort_values(sort_cols)

    if cumulative:
        if color_by:
            for col in y_cols:
                work[col] = work.groupby(color_by, dropna=False)[col].cumsum()
        else:
            for col in y_cols:
                work[col] = work[col].cumsum()

    data = []
    groups = work.groupby(color_by, dropna=False) if color_by else [(None, work)]

    
    total_points = len(work) * len(y_cols)
    disable_all_markers = total_points > 2000


    for group_value, g in groups:
        for y_col in y_cols:
            name = y_col if group_value is None else str(group_value)

            if group_value is not None and len(y_cols) > 1:
                name = f"{group_value} - {y_col}"

            name = format_label(y_col)


            n_points = len(g)

            use_markers = (
                not disable_all_markers
                and n_points <= 100
            )

            mode = "lines"##"lines+markers" if use_markers else "lines"


            data.append({
                "type": "scatter",
                "mode": mode,#"lines+markers",
                "x": g[x_plot].tolist(),
                "y": g[y_col].tolist(),
                "name": name,
            })


 
    return {
        "data": data,
        "layout": {
            "title": {"text": format_label(title) or f"{', '.join(y_cols)} over {x}"},
            "xaxis": {"title": {"text": format_label(x)}},
            "yaxis": {"title": {"text":  format_label(", ".join(y_cols))   }},
            #"template": template,
        },
        "config": {
            "responsive": True,
            "displaylogo": False,
        },
    }

def plot_pie_chart(
    df: pd.DataFrame,
    labels: str,
    values: str,
    *,
    aggregate: str | None = None,
    group_by: list[str] | str | None = None,
    title: str | None = None,
    hole: float = 0.0,
    template: str = "plotly_white",
) -> dict:
    _validate_columns(df, [labels, values])

    work = df.copy()

    if aggregate is not None:
        group_cols = _as_list(group_by) or [labels]

        if labels not in group_cols:
            group_cols.insert(0, labels)

        work = _aggregate(work, group_cols, [values], aggregate)

    return {
        "data": [
            {
                "type": "pie",
                "labels": work[labels].astype(str).tolist(),
                "values": work[values].tolist(),
                "hole": hole,
            }
        ],
        "layout": {
            "title": {"text": title or f"{values} share by {labels}"},
            #"template": template,
        },
        "config": {
            "responsive": True,
            "displaylogo": False,
        },
    }

def plot_scatter_chart(
    df: pd.DataFrame,
    x: str,
    y: str | list[str],
    *,
    color_by: str | None = None,
    size_by: str | None = None,
    text_by: str | None = None,
    title: str | None = None,
    template: str = "plotly_white",
) -> dict:
    y_cols = _as_list(y)

    required = [x, *y_cols]
    if color_by:
        required.append(color_by)
    if size_by:
        required.append(size_by)
    if text_by:
        required.append(text_by)

    _validate_columns(df, required)

    work = df.copy()
    data = []
    groups = work.groupby(color_by, dropna=False) if color_by else [(None, work)]


    total_points = len(work) * len(y_cols)
    disable_all_markers = total_points > 2000


    for group_value, g in groups:
        for y_col in y_cols:
            name = y_col if group_value is None else str(group_value)

            if group_value is not None and len(y_cols) > 1:
                name = f"{group_value} - {y_col}"




            n_points = len(g)

            use_markers = (
                not disable_all_markers
                and n_points <= 100
            )

            mode = "markers" if use_markers else "lines"


            trace = {
                "type": "scattergl",
                "mode": mode,
                "x": g[x].tolist(),
                "y": g[y_col].tolist(),
                "name": name,
            }

            if size_by:
                size_values = pd.to_numeric(g[size_by], errors="coerce").fillna(0)
                max_size = max(float(size_values.max()), 1.0)

                trace["marker"] = {
                    "size": size_values.tolist(),
                    "sizemode": "area",
                    "sizeref": max_size / 40,
                    "sizemin": 4,
                }

            if text_by:
                trace["text"] = g[text_by].astype(str).tolist()
                trace["hovertemplate"] = (
                    f"{x}: %{{x}}<br>"
                    f"{y_col}: %{{y}}<br>"
                    f"{text_by}: %{{text}}"
                    "<extra></extra>"
                )

            data.append(trace)

    return {
        "data": data,
        "layout": {
            "title": {"text": title or f"{', '.join(y_cols)} vs {x}"},
            "xaxis": {"title": {"text": x}},
            "yaxis": {"title": {"text": ", ".join(y_cols)}},
            #"template": template,
        },
        "config": {
            "responsive": True,
            "displaylogo": False,
        },
    }

def plot_list(
    df: pd.DataFrame,
    columns: list[str] | str | None = None,
    *,
    sort_by: str | None = None,
    sort_order: str = "desc",
    limit: int | None = None,
    title: str | None = None,
) -> dict:
    work = df.copy()

    if columns is not None:
        columns = _as_list(columns)
        _validate_columns(work, columns)
        work = work[columns]

    if sort_by is not None:
        _validate_columns(work, [sort_by])

        ascending = sort_order.lower() == "asc"
        work = work.sort_values(sort_by, ascending=ascending)

    if limit is not None:
        work = work.head(limit)

    header_values = [format_label(c) for c in work.columns]

    cell_values = []
    for col in work.columns:
        s = work[col]

        if pd.api.types.is_datetime64_any_dtype(s):
            values = s.dt.strftime("%Y-%m-%d").fillna("").tolist()
        else:
            values = s.fillna("").astype(str).tolist()

        cell_values.append(values)

    return {
        "data": [
            {
                "type": "table",
                "header": {
                    "values": header_values,
                    "align": "left",
                },
                "cells": {
                    "values": cell_values,
                    "align": "left",
                },
            }
        ],
        "layout": {
            "title": {
                "text": format_label(title) or "Table"
            },
        },
        "config": {
            "responsive": True,
            "displaylogo": False,
        },
    }




class TableResponseProcessor:
    """
    Builds compact, chart-oriented table summaries for a Plotly presenter LLM.
    The LLM receives metadata and limited column examples, but never the full data.
    """

    def __init__(
        self,
        #llm,
        max_examples: int = 3,
        low_cardinality_threshold: int = 10,
        medium_cardinality_threshold: int = 50,
        categorical_numeric_threshold: int = 12,
    ):
        #self.llm = llm 
        self.max_examples = max_examples
        self.low_cardinality_threshold = low_cardinality_threshold
        self.medium_cardinality_threshold = medium_cardinality_threshold
        self.categorical_numeric_threshold = categorical_numeric_threshold

    def extract_table_context(
        self,
        data_result: Any, # Replaced with generic Any for snippet execution
    ) -> str:
        """
        Convert one DataFrameResult into compact, LLM-friendly text.
        """
        table_name = getattr(data_result, "table_name", "unknown_table")
        table_description = getattr(data_result, "description", None)
        df = data_result.dataframe
        
        # Guard rail for empty DataFrames
        if df is None or df.empty:
            return f"Table: {table_name}\nRows: 0\nColumns: 0\nColumn summaries: []"

        nrows, ncols = df.shape 
        lines: list[str] = [f"Table: {table_name}"]
        
        if table_description:
            lines.append(f"Description: {table_description}")

        lines.extend([
            f"Rows: {nrows}",
            f"Columns: {ncols}",
            "",
            "Column summaries:"
        ])

        # Optimization: Move out of the loop so it isn't recreated for every column
        preferred_order = [
            "description", "dtype", "role", "unique_count", "unique_ratio",
            "cardinality", "null_count", "null_ratio", "min", "max", "mean",
            "median", "min_date", "max_date", "common_interval",
            "is_monotonic_increasing", "has_negative_values", "has_zero_values",
            "example_values",
        ]

        for col in df.columns:
            series = df[col]
            # Handle duplicate column names gracefully
            if isinstance(series, pd.DataFrame):
                series = series.iloc[:, 0]

            summary = self.infer_column_summary(series)
            lines.append(f"- Column: {col}")

            for key in preferred_order:
                if key in summary and summary[key] is not None:
                    val = summary[key]
                    if isinstance(val, float):
                        lines.append(f"  {key}: {val:.4f}")
                    else:
                        lines.append(f"  {key}: {val}")

        return "\n".join(lines)

    def infer_column_role(self, s: pd.Series) -> str:
        """Infer a chart-oriented semantic role."""
        if pd.api.types.is_datetime64_any_dtype(s):
            return "temporal"

        if pd.api.types.is_bool_dtype(s):
            return "categorical"

        if pd.api.types.is_numeric_dtype(s):
            nunique = s.nunique(dropna=True)
            if nunique <= self.categorical_numeric_threshold:
                return "categorical_numeric"
            return "quantitative"

        if pd.api.types.is_string_dtype(s) or pd.api.types.is_object_dtype(s):
            parsed = pd.to_datetime(s.dropna(), errors="coerce")
            valid_ratio = parsed.notna().mean() if len(parsed) else 0.0
            if valid_ratio >= 0.9:
                return "temporal"
            return "categorical"

        return "unknown"

    def infer_column_summary(self, s: pd.Series) -> dict[str, Any]:
        """Produce compact metadata for one DataFrame column."""
        non_null = s.dropna()
        row_count = len(s)
        non_null_count = len(non_null)
        null_count = row_count - non_null_count
        null_ratio = null_count / row_count if row_count else 0.0

        unique_count = non_null.nunique(dropna=True)
        unique_ratio = unique_count / row_count if row_count else 0.0

        role = self.infer_column_role(s)

        summary: dict[str, Any] = {
            "dtype": str(s.dtype),
            "role": role,
            "non_null_count": int(non_null_count),
            "null_count": int(null_count),
            "null_ratio": round(null_ratio, 4),
            "unique_count": int(unique_count),
            "unique_ratio": round(unique_ratio, 4),
        }

        # --- FIX 1: Overlap logic. Check structural traits instead of strictly 'elif' roles ---
        
        # 1. If it acts as a Category (including categorical_numeric), get categories & examples
        if role in {"categorical", "categorical_numeric"}:
            summary["cardinality"] = self.classify_cardinality(unique_count)
            examples = non_null.drop_duplicates().astype(str).head(self.max_examples).tolist()
            if examples:
                summary["example_values"] = examples

        # 2. If it is mathematically numeric, calculate bounds (fixes categorical_numeric exclusion)
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            numeric = pd.to_numeric(non_null, errors="coerce").dropna()
            if not numeric.empty:
                summary.update({
                    "min": round(float(numeric.min()), 4),
                    "max": round(float(numeric.max()), 4),
                    "mean": round(float(numeric.mean()), 4),
                    "median": round(float(numeric.median()), 4),
                    #"has_negative_values": bool((numeric < 0).any()),
                    #"has_zero_values": bool((numeric == 0).any()),
                })

        # 3. If it is temporal (or string-parsed temporal), extract temporal properties
        if role == "temporal" or pd.api.types.is_datetime64_any_dtype(s):
            dt = pd.to_datetime(non_null, errors="coerce").dropna()
            if not dt.empty:
                summary.update({
                    "min_date": str(dt.min()),
                    "max_date": str(dt.max()),
                    #"is_monotonic_increasing": bool(dt.is_monotonic_increasing),
                })
                #if len(dt) > 1:
                #    diffs = dt.sort_values().diff().dropna()
                #    if not diffs.empty:
                #        mode_diff = diffs.mode()
                #        if not mode_diff.empty:
                #            summary["common_interval"] = str(mode_diff.iloc[0])

        return summary

    def classify_cardinality(self, unique_count: int) -> str:
        """Convert unique count into low/medium/high cardinality label."""
        if unique_count <= self.low_cardinality_threshold:
            return "low"
        if unique_count <= self.medium_cardinality_threshold:
            return "medium"
        return "high"


class PresenterConfig:

    prompt :str = chart_agent_prompt


class PresenterComponent2:
    """
    Converts the completed ExecutorState into UI display items.

    """

    def __init__(self, llm: Any, config: PresenterConfig | None = None ):
        self.llm = llm
        self.config = config or PresenterConfig()



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

                #Note: when the analyst returns 2+ tables, we still use the same code 
                # as the dataresults are just added to the list 
                elif isinstance(data_result, DataFrameResult):
                    print("processing dataframe result")

                    table_text_or_chart_item = self.process_dataframe(data_result,task_result.instruction)
                    # later:
                    if table_text_or_chart_item:
                        ui_items.append(table_text_or_chart_item)

                else:
                    ui_items.append(_make_error_item(task_result, data_result))

        return PresenterResponse(items=ui_items)
    

    def _present_very_small_table(self, df, data_result,instruction):
    
        data_string = df.to_json() #@  ", ".join([f"{col}: {df.iloc[0][col]}" for col in df.columns])
        #print(data_string)

        prompt = (
                f"You are an expert data analyst. Analyze the following table \n",
                f"and present the facts that can be derived from it to address the user question.\n\n"
                f"Be brief (3 sentences maximum) in your response and use a neutral tone\n",
                f"Do not mention the table, table name, table description. Focus in the facts. \n",
                f"Address only the parts of the user question for which the table is related\n",
                f"Ignore the parts of the question that the information in the table cannot address\n",
                f"Only present the facts derived. Do not explain, do not produce a heading line\n"
                f"### Context\n"
                f"- **Table Name**: {getattr(data_result, 'table_name', 'N/A')}\n"
                f"- **Description**: {getattr(data_result, 'description', 'No description provided.')}\n\n"
                f"### Data\n"
                f"- {data_string}\n\n"
                f"User question:\n{instruction}\n"
        )
            
        response = self.llm.invoke(prompt)
        text_output = response.content if hasattr(response, 'content') else str(response)
        #print(' response ', response )
        #print(' ******as text ', text_output, '*******')

        return UIItem(
                id=f"text_{uuid4().hex[:8]}",
                type="text",
                title='None',
                data={"text": text_output},
            )
    
    def _make_chart_item(self,
        figure_title: str,
        plotly_json_figure: dict,
        description: str | None = None,
    ) -> UIItem:

        return UIItem(
            id=f"chart_{uuid4().hex[:8]}",
            type="chart",
            title=figure_title,
            data={
                "engine": "plotly",
                "plotly": plotly_json_figure,
            },
            meta={
                "description": description,
            },
        )


    def _run_chart_plan(
            self, 
        plan: dict,
        df: pd.DataFrame,
    ) -> dict | None:
        """
        Executes a chart plan shaped like:

        {
        "reason": "...",
        "preprocess": null | {
            "tool": "preprocess_for_chart",
            "args": {}
        },
        "plot": null | {
            "tool": "plot_bar_chart",
            "args": {}
        }
        }
        """

        print("****")
        print("The plan is")
        print(plan)


        work = df.copy()

        preprocess = plan.get("preprocess")
        plot = plan.get("plot")

        print("preprocess", preprocess)
        print("plot", plot)
        

        if preprocess:
            tool = preprocess.get("tool")
            args = preprocess.get("args") or {}

            if tool != "preprocess_for_chart":
                raise ValueError(f"Unknown preprocess tool: {tool}")

            args = _filter_args("preprocess_for_chart", args)
            work = preprocess_for_chart(work, **args)

        if not plot:
            print("Returing none")
            return None

        tool = plot.get("tool")
        args = plot.get("args") or {}

        plotting_tools = {
            "plot_bar_chart": plot_bar_chart,
            "plot_line_chart": plot_line_chart,
            "plot_pie_chart": plot_pie_chart,
            "plot_scatter_chart": plot_scatter_chart,
            "plot_list": plot_list,
        }

        if tool not in plotting_tools:
            raise ValueError(f"Unknown plot tool: {tool}")

        args = _filter_args(tool, args)

        print("The final tool is", tool )
        return plotting_tools[tool](df=work, **args)


    def process_dataframe( self,data_result,instruction ):


        df = data_result.dataframe
        nrows, ncols = df.shape     
        print(df.shape)
        print('instruction', instruction)

        #inst="""show the count of wells split by type, and the yearly cumulative liquid production since the year 2015."""
        # if the table is 1 row and 2 or less columns, just produce a textual response
        if nrows <= 2 and ncols <=2:
            print("it is a small table")
            return self._present_very_small_table( df,data_result, instruction )
        
        else:
            p = TableResponseProcessor()# self.llm )
            table_context = p.extract_table_context( data_result )
            chart_plan = self.select_chart_plan( data_result, table_context )
            
            print(100*'=')
            print(chart_plan)
            print(100*'=')
            
            
            chart_output = self._run_chart_plan( chart_plan, df )


            print("Type", type(chart_output) )

            return self._make_chart_item( format_label(data_result.table_name), 
                                          chart_output,  # type: ignore
                                          data_result.description )



    def _strip_markdown_json(self,text: str) -> str:
        """
        Remove markdown code fences from LLM JSON responses.

        Examples:
        ```json
        {...}
        ```

        ->
        {...}
        """

        text = text.strip()

        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        return text.strip()

    def select_chart_plan(self,
        
        user_query: str,
        table_context: str,
    ) -> dict:
        
        messages = [
            SystemMessage(content=self.config.prompt),
            HumanMessage(content=f"""
    USER QUERY
    {user_query}

    TABLES
    {table_context}
    """),
        ]

        response = self.llm.invoke(messages)
        text = self._strip_markdown_json(response.content)
        return json.loads(text)










   







