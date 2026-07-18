from dataclasses import dataclass
import sys, pprint, pandas as pd  
sys.path.append('../../')
sys.path.append('../')
sys.path.append('./')
import warnings

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
from visualization_system.visualization_backend.analyst.prompts import small_table_prompt
from visualization_system.visualization_backend.analyst.prompts import split_subinstructions_prompt

 


import pandas as pd, re, json  
from langchain_core.messages import SystemMessage, HumanMessage
from visualization_system.visualization_backend.global_models import UIState
 
  

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
        self.last_query =  UIState( project_name="NoSet", query="Nothing") # type: ignore


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

class xxChartRequest(BaseModel):
    user_query: str
    user_intent: str | None = None

    table_name: str
    table_description: str | None = None
    dataframe: Any

    facts_context: str = ""

class xxPresenterChartingTools:

    ALLOWED_AGGS = {"sum", "mean", "median", "min", "max", "count", "nunique"}


    plotly_config = {
                "responsive": True,
                "displaylogo": False,
            }



    def run_preprocess(
        self,
        df: pd.DataFrame,
        preprocess_steps: list[dict] | None,
    ) -> pd.DataFrame:
        work = df.copy()

        for step in preprocess_steps or []:
            operation = step.get("operation")
            args = step.get("args") or {}

            work = self.run_preprocess_operation(
                operation=operation,
                df=work,
                args=args,
            )

        return work


    def run_preprocess_operation(
        self,
        operation: str,
        df: pd.DataFrame,
        args: dict[str, Any],
    ) -> pd.DataFrame:
        preprocess_tools = {
            "filter_rows": self.filter_rows,
            "aggregate": self.aggregate_for_chart,
            "sort_rows": self.sort_rows,
            "limit_rows": self.limit_rows,
            "select_columns": self.select_columns,
            "select_top_entities": self.select_top_entities,
            "create_combined_category": self.create_combined_category,
            "create_date_bucket": self.create_date_bucket,
        }

        if operation not in preprocess_tools:
            raise ValueError(f"Unknown preprocess operation: {operation}")

        return preprocess_tools[operation](
            df=df,
            **args,
        )


    ##########################
    #       pre-process      # 
    ##########################
    def filter_rows(self,df: pd.DataFrame,filters: list[dict]) -> pd.DataFrame:
        
        work = df.copy()
        for item in filters:
            column = item["column"]
            operator = item["operator"]
            value = item["value"]

            self._validate_columns(work, [column])

            if operator == "==":
                work = work[work[column] == value]
            elif operator == "!=":
                work = work[work[column] != value]
            elif operator == ">":
                work = work[work[column] > value]
            elif operator == ">=":
                work = work[work[column] >= value]
            elif operator == "<":
                work = work[work[column] < value]
            elif operator == "<=":
                work = work[work[column] <= value]
            elif operator == "in":
                work = work[work[column].isin(value)]
            elif operator == "not_in":
                work = work[~work[column].isin(value)]
            else:
                raise ValueError(f"Unsupported filter operator: {operator}")

        return work

    def aggregate_for_chart(
        self,
        df: pd.DataFrame,
        group_by: list[str],
        metrics: dict[str, str],
    ) -> pd.DataFrame:
            self._validate_columns(df, group_by)

            for column, aggregate in metrics.items():
                self._validate_columns(df, [column])

                if aggregate not in self.ALLOWED_AGGS:
                    raise ValueError(f"Unsupported aggregate: {aggregate}")

            return (
                df.groupby(group_by, dropna=False, as_index=False)
                .agg(metrics)
            )

    def sort_rows(
        self,
        df: pd.DataFrame,
        sort_by: str | list[str],
        ascending: bool = True,
    ) -> pd.DataFrame:
        sort_columns = self._as_list(sort_by)
        self._validate_columns(df, sort_columns)

        return df.sort_values(
            sort_columns,
            ascending=ascending,
        )

    def limit_rows(
        self,
        df: pd.DataFrame,
        n: int,
    ) -> pd.DataFrame:
        return df.head(n)

    def select_columns(
        self,
        df: pd.DataFrame,
        columns: list[str],
    ) -> pd.DataFrame:
        self._validate_columns(df, columns)
        return df[columns].copy()

    def create_combined_category(
        self,
        df: pd.DataFrame,
        col1: str,
        col2: str,
        new_col: str | None = None,
        sep: str = " / ",
    ) -> pd.DataFrame:
        out = df.copy()

        self._validate_columns(out, [col1, col2])

        new_col = new_col or f"{col1}_{col2}"

        out[new_col] = (
            out[col1].fillna("").astype(str)
            + sep
            + out[col2].fillna("").astype(str)
        )

        return out

    def create_date_bucket(
        self,
        df: pd.DataFrame,
        date_col: str,
        bucket: str,
        new_col: str | None = None,
    ) -> pd.DataFrame:
        out, generated_col = self._bucket_date(
            df,
            date_col,
            bucket,
        )

        if new_col and new_col != generated_col:
            out = out.rename(
                columns={generated_col: new_col}
            )

        return out

    def select_top_entities(
        self,
        df: pd.DataFrame,
        entity_col: str,
        metric_col: str,
        n: int,
        aggregate: str = "sum",
        ascending: bool = False,
        filters: list[dict] | None = None,
        keep_all_rows: bool = True,
    ) -> pd.DataFrame:
        self._validate_columns(
            df,
            [entity_col, metric_col],
        )

        ranking_data = df.copy()

        if filters:
            ranking_data = self.filter_rows(
                ranking_data,
                filters,
            )

        ranking = (
            ranking_data
            .groupby(entity_col, dropna=False, as_index=False)[metric_col]
            .agg(aggregate)
            .sort_values(metric_col, ascending=ascending)
            .head(n)
        )

        selected_entities = ranking[entity_col].tolist()

        if keep_all_rows:
            return df[df[entity_col].isin(selected_entities)].copy()

        return ranking









    def run_plot_tool(
        self,
        tool_name: str,
        df: pd.DataFrame,
        args: dict[str, Any],
    ) -> dict:
        plotting_tools = {
            "plot_bar_chart": self.plot_bar_chart,
            "plot_line_chart": self.plot_line_chart,
            "plot_pie_chart": self.plot_pie_chart,
            "plot_scatter_chart": self.plot_scatter_chart,
            "plot_table": self.plot_table,
        }

        if tool_name not in plotting_tools:
            raise ValueError(f"Unknown plot tool: {tool_name}")

        args = self._filter_args(tool_name, args)
        return plotting_tools[tool_name](df=df, **args)

    def old_run_preprocess(self, df: pd.DataFrame, preprocess: dict) -> pd.DataFrame:
        tool_name = preprocess.get("tool")
        args = preprocess.get("args") or {}

        if tool_name != "preprocess_for_chart":
            raise ValueError(f"Unknown preprocess tool: {tool_name}")

        args = self._filter_args(tool_name, args)
        return self.preprocess_for_chart(df, **args)

    def format_label(self, name: str) -> str:
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

    def _as_list(self, value):
        if value is None:
            return []
        return [value] if isinstance(value, str) else list(value)

    def _strip_markdown_json(self, text: str) -> str:
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
        self,
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
        self,
        tool_name: str,
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
                "group_by","series_by",
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
            "plot_list": {
                "columns",
                "sort_by",
                "sort_order",
                "limit",
                "title",
            },
        }

        if tool_name not in allowed_args:
            raise ValueError(f"Unknown tool: {tool_name}")

        return {
            k: v
            for k, v in args.items()
            if k in allowed_args[tool_name]
        }

    def _aggregate(
        self,
        df: pd.DataFrame,
        group_by: list[str],
        value_cols: list[str],
        aggregate: str,
    ) -> pd.DataFrame:
        if aggregate not in self.ALLOWED_AGGS:
            raise ValueError(f"Unsupported aggregate: {aggregate}")

        self._validate_columns(df, group_by, "group_by column")
        self._validate_columns(df, value_cols, "value column")

        return (
            df.groupby(group_by, dropna=False, as_index=False)[value_cols]
            .agg(aggregate)
        )

    def _bucket_date(
        self,
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

        self._validate_columns(out, [date_col])

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
        self,
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

            self._validate_columns(out, [col1, col2])

            out[new_col] = (
                out[col1].fillna("").astype(str)
                + sep
                + out[col2].fillna("").astype(str)
            )

        if create_date_bucket:
            date_col = create_date_bucket["date_col"]
            bucket = create_date_bucket["bucket"]
            new_col = create_date_bucket.get("new_col") or f"{date_col}_{bucket}"

            self._validate_columns(out, [date_col])

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
        self,
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
        # template: str = "plotly_white",
    ) -> dict:
        y_cols = self._as_list(y)

        required = [x, *y_cols]
        if color_by:
            required.append(color_by)

        self._validate_columns(df, required)

        work = df.copy()

        if aggregate is not None:
            group_cols = self._as_list(group_by) or [x]

            if x not in group_cols:
                group_cols.insert(0, x)

            if color_by and color_by not in group_cols:
                group_cols.append(color_by)

            work = self._aggregate(work, group_cols, y_cols, aggregate)

        data = []
        groups = work.groupby(color_by, dropna=False) if color_by else [(None, work)]

        for group_value, g in groups:
            for y_col in y_cols:
                if group_value is None:
                    name = self.format_label(y_col)
                else:
                    name = self.format_label(str(group_value))

                if group_value is not None and len(y_cols) > 1:
                    name = f"{self.format_label(str(group_value))} - {self.format_label(y_col)}"

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

        y_label = self.format_label(", ".join(y_cols))
        x_label = self.format_label(x)

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
                # "template": template,
            },
            "config": {
                "responsive": True,
                "displaylogo": False,
            },
        }

    def plot_line_chart(
        self,
        df: pd.DataFrame,
        x: str,
        y: str | list[str],
        *,
        aggregate: str | None = None,
        group_by: list[str] | str | None = None,
        series_by: str | None = None,
        color_by: str | None = None,  # backwards compatibility
        date_bucket: str | None = None,
        cumulative: bool = False,
        title: str | None = None,
        # template: str = "plotly_white",
    ) -> dict:
        y_cols = self._as_list(y)

        if series_by is None:
            series_by = color_by

        required = [x, *y_cols]
        if series_by:
            required.append(series_by)

        self._validate_columns(df, required)

        work = df.copy()
        x_plot = x

        if date_bucket is not None:
            work, x_plot = self._bucket_date(work, x, date_bucket)

        if aggregate is not None:
            group_cols = self._as_list(group_by) or [x_plot]

            if x_plot not in group_cols:
                group_cols.insert(0, x_plot)

            if series_by and series_by not in group_cols:
                group_cols.append(series_by)

            work = self._aggregate(work, group_cols, y_cols, aggregate)

        sort_cols = [series_by, x_plot] if series_by else [x_plot]
        work = work.sort_values(sort_cols)

        if cumulative:
            if series_by:
                for col in y_cols:
                    work[col] = work.groupby(series_by, dropna=False)[col].cumsum()
            else:
                for col in y_cols:
                    work[col] = work[col].cumsum()

        data = []
        groups = work.groupby(series_by, dropna=False) if series_by else [(None, work)]

        total_points = len(work) * len(y_cols)
        disable_all_markers = total_points > 2000

        for group_value, g in groups:
            for y_col in y_cols:
                if group_value is None:
                    name = self.format_label(y_col)
                elif len(y_cols) == 1:
                    name = str(group_value)
                else:
                    name = f"{group_value} - {self.format_label(y_col)}"

                data.append({
                    "type": "scatter",
                    "mode": "lines",
                    "x": g[x_plot].tolist(),
                    "y": g[y_col].tolist(),
                    "name": name,
                })

        return {
            "data": data,
            "layout": {
                "title": {
                    "text": self.format_label(title) or f"{', '.join(y_cols)} over {x}"
                },
                "xaxis": {
                    "title": {
                        "text": self.format_label(x)
                    }
                },
                "yaxis": {
                    "title": {
                        "text": self.format_label(", ".join(y_cols))
                    }
                },
            },
            "config": self.plotly_config,
        }

    def plot_pie_chart(
        self,
        df: pd.DataFrame,
        labels: str,
        values: str,
        *,
        aggregate: str | None = None,
        group_by: list[str] | str | None = None,
        title: str | None = None,
        hole: float = 0.0,
        # template: str = "plotly_white",
    ) -> dict:
        self._validate_columns(df, [labels, values])

        work = df.copy()

        if aggregate is not None:
            group_cols = self._as_list(group_by) or [labels]

            if labels not in group_cols:
                group_cols.insert(0, labels)

            work = self._aggregate(work, group_cols, [values], aggregate)

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
                "title": {
                    "text": title or f"{values} share by {labels}"
                },
                # "template": template,
            },
            "config": self.plotly_config
        }

    def plot_scatter_chart(
        self,
        df: pd.DataFrame,
        x: str,
        y: str | list[str],
        *,
        color_by: str | None = None,
        size_by: str | None = None,
        text_by: str | None = None,
        title: str | None = None,
        # template: str = "plotly_white",
    ) -> dict:
        y_cols = self._as_list(y)

        required = [x, *y_cols]
        if color_by:
            required.append(color_by)
        if size_by:
            required.append(size_by)
        if text_by:
            required.append(text_by)

        self._validate_columns(df, required)

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
                "title": {
                    "text": title or f"{', '.join(y_cols)} vs {x}"
                },
                "xaxis": {
                    "title": {
                        "text": x
                    }
                },
                "yaxis": {
                    "title": {
                        "text": ", ".join(y_cols)
                    }
                },
                # "template": template,
            },
            "config": self.plotly_config
        }

    def plot_list(
        self,
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
            columns = self._as_list(columns)
            self._validate_columns(work, columns)
            work = work[columns]

        if sort_by is not None:
            self._validate_columns(work, [sort_by])

            ascending = sort_order.lower() == "asc"
            work = work.sort_values(sort_by, ascending=ascending)

        if limit is not None:
            work = work.head(limit)

        header_values = [self.format_label(c) for c in work.columns]

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
                    "text": self.format_label(title) or "Table"
                },
            },
            "config": self.plotly_config
        }
    
    
class TableResponseProcessor:
    """
    Builds compact, chart-oriented table summaries for a Plotly presenter LLM.
    The LLM receives metadata and limited column examples, but never the full data.
    """

    def __init__(
        self,
        max_examples: int = 3,
        low_cardinality_threshold: int = 10,
        medium_cardinality_threshold: int = 50,
        categorical_numeric_threshold: int = 12,
    ):
        self.max_examples = max_examples
        self.low_cardinality_threshold = low_cardinality_threshold
        self.medium_cardinality_threshold = medium_cardinality_threshold
        self.categorical_numeric_threshold = categorical_numeric_threshold

    def extract_table_context(
        self,
        data_result: Any,
    ) -> str:
        """
        Convert one DataFrameResult into compact, LLM-friendly text.
        """
        table_name = getattr(data_result, "table_name", "unknown_table")
        table_description = getattr(data_result, "description", None)
        df = data_result.dataframe

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
            "Column summaries:",
        ])

        preferred_order = [
            "description",
            "dtype",
            "role",
            "unique_count",
            "unique_ratio",
            "cardinality",
            "null_count",
            "null_ratio",
            "min",
            "max",
            "mean",
            "median",
            "min_date",
            "max_date",
            "common_interval",
            "is_monotonic_increasing",
            "has_negative_values",
            "has_zero_values",
            "example_values",
        ]

        for col in df.columns:
            series = df[col]

            # Handle duplicate column names gracefully.
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

    def _safe_parse_datetime_candidate(self, s: pd.Series) -> pd.Series:
        values = s.dropna()

        if values.empty:
            return pd.Series(dtype="datetime64[ns]")

        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Could not infer format.*",
                category=UserWarning,
            )

            return pd.to_datetime(values, errors="coerce")

    def infer_column_role(self, s: pd.Series) -> str:
        """
        Infer a chart-oriented semantic role.
        """
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
            parsed = self._safe_parse_datetime_candidate(s)

            valid_ratio = parsed.notna().mean() if len(parsed) else 0.0

            if valid_ratio >= 0.9:
                return "temporal"

            return "categorical"

        return "unknown"

    def infer_column_summary(self, s: pd.Series) -> dict[str, Any]:
        """
        Produce compact metadata for one DataFrame column.
        """
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

        if role in {"categorical", "categorical_numeric"}:
            summary["cardinality"] = self.classify_cardinality(unique_count)

            examples = (
                non_null
                .drop_duplicates()
                .astype(str)
                .head(self.max_examples)
                .tolist()
            )

            if examples:
                summary["example_values"] = examples

        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            numeric = pd.to_numeric(non_null, errors="coerce").dropna()

            if not numeric.empty:
                summary.update({
                    "min": round(float(numeric.min()), 4),
                    "max": round(float(numeric.max()), 4),
                    "mean": round(float(numeric.mean()), 4),
                    "median": round(float(numeric.median()), 4),
                })

        if role == "temporal" or pd.api.types.is_datetime64_any_dtype(s):
            dt = pd.to_datetime(non_null, errors="coerce").dropna()

            if not dt.empty:
                summary.update({
                    "min_date": str(dt.min()),
                    "max_date": str(dt.max()),
                })

        return summary

    def classify_cardinality(self, unique_count: int) -> str:
        """
        Convert unique count into low/medium/high cardinality label.
        """
        if unique_count <= self.low_cardinality_threshold:
            return "low"

        if unique_count <= self.medium_cardinality_threshold:
            return "medium"

        return "high"


class PresenterChartingTools:

    ALLOWED_AGGS = {"sum", "mean", "median", "min", "max", "count", "nunique"}


    plotly_config = {
                "responsive": True,
                "displaylogo": False,
            }



    def run_preprocess(
        self,
        df: pd.DataFrame,
        preprocess_steps: list[dict] | None,
    ) -> pd.DataFrame:
        work = df.copy()

        for step in preprocess_steps or []:
            
            operation = step.get("operation")

            if not operation:
                raise ValueError("Preprocess step is missing 'operation'")

            args = step.get("args") or {}

            work = self.run_preprocess_operation(
                operation=operation,
                df=work,
                args=args,
            )

        return work


    def run_preprocess_operation(
        self,
        operation: str,
        df: pd.DataFrame,
        args: dict[str, Any],
    ) -> pd.DataFrame:
        preprocess_tools = {
            "filter_rows": self.filter_rows,
            "aggregate": self.aggregate_for_chart,
            "sort_rows": self.sort_rows,
            "limit_rows": self.limit_rows,
            "select_columns": self.select_columns,
            "select_top_entities": self.select_top_entities,
            "create_combined_category": self.create_combined_category,
            "create_date_bucket": self.create_date_bucket,
        }

        if operation not in preprocess_tools:
            raise ValueError(f"Unknown preprocess operation: {operation}")

        return preprocess_tools[operation](
            df=df,
            **args,
        )


    ##########################
    #       pre-process      # 
    ##########################
    def filter_rows(self,df: pd.DataFrame,filters: list[dict]) -> pd.DataFrame:
        
        work = df.copy()
        for item in filters:
            column = item["column"]
            operator = item["operator"]
            value = item["value"]

            self._validate_columns(work, [column])

            if operator == "==":
                work = work[work[column] == value]
            elif operator == "!=":
                work = work[work[column] != value]
            elif operator == ">":
                work = work[work[column] > value]
            elif operator == ">=":
                work = work[work[column] >= value]
            elif operator == "<":
                work = work[work[column] < value]
            elif operator == "<=":
                work = work[work[column] <= value]
 


            elif operator == "in":
                if not isinstance(value, (list, tuple, set)):
                    raise ValueError("'in' filter value must be a list")
                work = work[work[column].isin(value)]

            elif operator == "not_in":
                if not isinstance(value, (list, tuple, set)):
                    raise ValueError("'not_in' filter value must be a list")
                work = work[~work[column].isin(value)]




            else:
                raise ValueError(f"Unsupported filter operator: {operator}")

        return work

    def aggregate_for_chart( self, df: pd.DataFrame, group_by: list[str],
        metrics: dict[str, str],
    ) -> pd.DataFrame:
        
        self._validate_columns(df, group_by)

        for column, aggregate in metrics.items():
            self._validate_columns(df, [column])

            if aggregate not in self.ALLOWED_AGGS:
                raise ValueError(f"Unsupported aggregate: {aggregate}")

        return (df.groupby(group_by, dropna=False, as_index=False).agg(metrics))

    def sort_rows(
        self,
        df: pd.DataFrame,
        sort_by: str | list[str],
        ascending: bool = True,
    ) -> pd.DataFrame:
        sort_columns = self._as_list(sort_by)
        self._validate_columns(df, sort_columns)

        return df.sort_values(
            sort_columns,
            ascending=ascending,
        )

    def limit_rows(
        self,
        df: pd.DataFrame,
        n: int,
    ) -> pd.DataFrame:
        return df.head(n)

    def select_columns(
        self,
        df: pd.DataFrame,
        columns: list[str],
    ) -> pd.DataFrame:
        self._validate_columns(df, columns)
        return df[columns].copy()

    def create_combined_category(
        self,
        df: pd.DataFrame,
        col1: str,
        col2: str,
        new_col: str | None = None,
        sep: str = " / ",
    ) -> pd.DataFrame:
        out = df.copy()

        self._validate_columns(out, [col1, col2])

        new_col = new_col or f"{col1}_{col2}"

        out[new_col] = (
            out[col1].fillna("").astype(str)
            + sep
            + out[col2].fillna("").astype(str)
        )

        return out

    def create_date_bucket(
        self,
        df: pd.DataFrame,
        date_col: str,
        bucket: str,
        new_col: str | None = None,
    ) -> pd.DataFrame:
        out, generated_col = self._bucket_date(
            df,
            date_col,
            bucket,
        )

        if new_col and new_col != generated_col:
            out = out.rename(
                columns={generated_col: new_col}
            )

        return out

    def select_top_entities(
        self,
        df: pd.DataFrame,
        entity_col: str,
        metric_col: str,
        n: int,
        aggregate: str = "sum",
        ascending: bool = False,
        filters: list[dict] | None = None,
        keep_all_rows: bool = True,
    ) -> pd.DataFrame:
        
        self._validate_columns(df,[entity_col, metric_col])
        if aggregate not in self.ALLOWED_AGGS:
            raise ValueError(f"Unsupported aggregate: {aggregate}")

        if n <= 0:
            raise ValueError("n must be greater than zero")
        
        ranking_data = df.copy()

        if filters:
            ranking_data = self.filter_rows(
                ranking_data,
                filters,
            )

        ranking = (
            ranking_data
            .groupby(entity_col, dropna=False, as_index=False)[metric_col]
            .agg(aggregate)
            .sort_values(metric_col, ascending=ascending)
            .head(n)
        )

        selected_entities = ranking[entity_col].tolist()

        if keep_all_rows:
            return df[df[entity_col].isin(selected_entities)].copy()

        return ranking


    ##########################
    #       plot             # 
    ##########################

    def run_plot_tool(
        self,
        tool_name: str,
        df: pd.DataFrame,
        args: dict[str, Any],
    ) -> dict:
        plotting_tools = {
            "plot_bar_chart": self.plot_bar_chart,
            "plot_line_chart": self.plot_line_chart,
            "plot_pie_chart": self.plot_pie_chart,
            "plot_scatter_chart": self.plot_scatter_chart,
            "plot_table": self.plot_table,
        }

        if tool_name not in plotting_tools:
            raise ValueError(f"Unknown plot tool: {tool_name}")

        args = self._filter_args(tool_name, args)
        return plotting_tools[tool_name](df=df, **args)

    def format_label(self, name: str) -> str:
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

    def _as_list(self, value):
        if value is None:
            return []
        return [value] if isinstance(value, str) else list(value)

    def _strip_markdown_json(self, text: str) -> str:
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
        self,
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
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Remove unsupported arguments generated by the LLM.
        """

        allowed_args = {
            "plot_bar_chart": {
                "x",
                "y",
                "series_by",
                "orientation",
                "barmode",
                "title",
            },
            "plot_line_chart": {
                "x",
                "y",
                "series_by",
                "title",
            },
            "plot_pie_chart": {
                "labels",
                "values",
                "title",
                "hole",
            },        
            "plot_scatter_chart": {
                "x",
                "y",
                "series_by",
                "size_by",
                "text_by",
                "title",
            },
            "plot_table": {
                "title",
            },
        }

        if tool_name not in allowed_args:
            raise ValueError(f"Unknown tool: {tool_name}")

        return {
            k: v
            for k, v in args.items()
            if k in allowed_args[tool_name]
        }

    def _aggregate(
        self,
        df: pd.DataFrame,
        group_by: list[str],
        value_cols: list[str],
        aggregate: str,
    ) -> pd.DataFrame:
        if aggregate not in self.ALLOWED_AGGS:
            raise ValueError(f"Unsupported aggregate: {aggregate}")

        self._validate_columns(df, group_by, "group_by column")
        self._validate_columns(df, value_cols, "value column")

        return (
            df.groupby(group_by, dropna=False, as_index=False)[value_cols]
            .agg(aggregate)
        )

    def _bucket_date(
        self,
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

        self._validate_columns(out, [date_col])

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

    def plot_bar_chart(
        self,
        df: pd.DataFrame,
        x: str,
        y: str | list[str],
        *,
        series_by: str | None = None,
        orientation: str = "v",
        barmode: str = "group",
        title: str | None = None,
    ) -> dict:
        y_cols = self._as_list(y)

        required = [x, *y_cols]

        if series_by:
            required.append(series_by)

        self._validate_columns(df, required)

        if orientation not in {"v", "h"}:
            raise ValueError("orientation must be 'v' or 'h'")

        if barmode not in {"group", "stack", "relative"}:
            raise ValueError(
                "barmode must be 'group', 'stack', or 'relative'"
            )

        work = df.copy()

        groups = (
            work.groupby(series_by, dropna=False)
            if series_by
            else [(None, work)]
        )

        data = []

        for group_value, group in groups:
            for y_col in y_cols:

                if group_value is None:
                    trace_name = self.format_label(y_col)

                elif len(y_cols) == 1:
                    trace_name = str(group_value)

                else:
                    trace_name = (
                        f"{group_value} - {self.format_label(y_col)}"
                    )

                trace = {
                    "type": "bar",
                    "name": trace_name,
                    "orientation": orientation,
                }

                if orientation == "h":
                    trace["x"] = group[y_col].tolist()
                    trace["y"] = group[x].astype(str).tolist()

                else:
                    trace["x"] = group[x].astype(str).tolist()
                    trace["y"] = group[y_col].tolist()

                data.append(trace)

        x_label = self.format_label(x)
        y_label = self.format_label(", ".join(y_cols))

        return {
            "data": data,
            "layout": {
                "title": {
                    "text": (
                        self.format_label(title)
                        or f"{y_label} by {x_label}"
                    )
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
            },
            "config": self.plotly_config,
        }

    def plot_line_chart(
        self,
        df: pd.DataFrame,
        x: str,
        y: str | list[str],
        *,
        series_by: str | None = None,
        title: str | None = None,
    ) -> dict:
        y_cols = self._as_list(y)

        required = [x, *y_cols]

        if series_by:
            required.append(series_by)

        self._validate_columns(df, required)

        work = df.copy()

        sort_cols = [series_by, x] if series_by else [x]
        work = work.sort_values(sort_cols)

        groups = (
            work.groupby(series_by, dropna=False)
            if series_by
            else [(None, work)]
        )

        data = []

        for group_value, group in groups:
            for y_col in y_cols:

                if group_value is None:
                    trace_name = self.format_label(y_col)

                elif len(y_cols) == 1:
                    trace_name = str(group_value)

                else:
                    trace_name = (
                        f"{group_value} - {self.format_label(y_col)}"
                    )

                data.append({
                    "type": "scatter",
                    "mode": "lines",
                    "x": group[x].tolist(),
                    "y": group[y_col].tolist(),
                    "name": trace_name,
                })

        return {
            "data": data,
            "layout": {
                "title": {
                    "text": (
                        self.format_label(title)
                        or f"{self.format_label(', '.join(y_cols))} over "
                        f"{self.format_label(x)}"
                    )
                },
                "xaxis": {
                    "title": {
                        "text": self.format_label(x)
                    }
                },
                "yaxis": {
                    "title": {
                        "text": self.format_label(", ".join(y_cols))
                    }
                },
            },
            "config": self.plotly_config,
        }


    def plot_pie_chart(
        self,
        df: pd.DataFrame,
        labels: str,
        values: str,
        *,
        title: str | None = None,
        hole: float = 0.0,
    ) -> dict:
        self._validate_columns(df, [labels, values])

        if not 0.0 <= hole <= 1.0:
            raise ValueError("hole must be between 0 and 1")

        return {
            "data": [
                {
                    "type": "pie",
                    "labels": df[labels].astype(str).tolist(),
                    "values": df[values].tolist(),
                    "hole": hole,
                }
            ],
            "layout": {
                "title": {
                    "text": (
                        self.format_label(title)
                        or (
                            f"{self.format_label(values)} share by "
                            f"{self.format_label(labels)}"
                        )
                    )
                },
            },
            "config": self.plotly_config,
        }


    def plot_scatter_chart(
        self,
        df: pd.DataFrame,
        x: str,
        y: str | list[str],
        *,
        series_by: str | None = None,
        size_by: str | None = None,
        text_by: str | None = None,
        title: str | None = None,
    ) -> dict:
        y_cols = self._as_list(y)

        required = [x, *y_cols]

        if series_by:
            required.append(series_by)

        if size_by:
            required.append(size_by)

        if text_by:
            required.append(text_by)

        self._validate_columns(df, required)

        work = df.copy()

        groups = (
            work.groupby(series_by, dropna=False)
            if series_by
            else [(None, work)]
        )

        data = []

        for group_value, group in groups:
            for y_col in y_cols:

                if group_value is None:
                    trace_name = self.format_label(y_col)

                elif len(y_cols) == 1:
                    trace_name = str(group_value)

                else:
                    trace_name = (
                        f"{group_value} - {self.format_label(y_col)}"
                    )

                trace = {
                    "type": "scattergl",
                    "mode": "markers",
                    "x": group[x].tolist(),
                    "y": group[y_col].tolist(),
                    "name": trace_name,
                }

                if size_by:
                    size_values = (
                        pd.to_numeric(
                            group[size_by],
                            errors="coerce",
                        )
                        .fillna(0)
                    )

                    max_size = max(
                        float(size_values.max()),
                        1.0,
                    )

                    trace["marker"] = {
                        "size": size_values.tolist(),
                        "sizemode": "area",
                        "sizeref": max_size / 40,
                        "sizemin": 4,
                    }

                if text_by:
                    trace["text"] = (
                        group[text_by]
                        .fillna("")
                        .astype(str)
                        .tolist()
                    )

                    trace["hovertemplate"] = (
                        f"{self.format_label(x)}: %{{x}}<br>"
                        f"{self.format_label(y_col)}: %{{y}}<br>"
                        f"{self.format_label(text_by)}: %{{text}}"
                        "<extra></extra>"
                    )

                data.append(trace)

        return {
            "data": data,
            "layout": {
                "title": {
                    "text": (
                        self.format_label(title)
                        or (
                            f"{self.format_label(', '.join(y_cols))} vs "
                            f"{self.format_label(x)}"
                        )
                    )
                },
                "xaxis": {
                    "title": {
                        "text": self.format_label(x)
                    }
                },
                "yaxis": {
                    "title": {
                        "text": self.format_label(", ".join(y_cols))
                    }
                },
            },
            "config": self.plotly_config,
        }


    def plot_table(
        self,
        df: pd.DataFrame,
        *,
        title: str | None = None,
    ) -> dict:
        header_values = [
            self.format_label(column)
            for column in df.columns
        ]

        cell_values = []

        for column in df.columns:
            series = df[column]

            if pd.api.types.is_datetime64_any_dtype(series):
                values = (
                    series
                    .dt.strftime("%Y-%m-%d")
                    .fillna("")
                    .tolist()
                )
            else:
                values = (
                    series
                    .fillna("")
                    .astype(str)
                    .tolist()
                )

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
                    "text": self.format_label(title) or "Table"
                },
            },
            "config": self.plotly_config,
        }


class PresenterConfig:

    prompt :str = chart_agent_prompt
    split_subinstructions_prompr: str = split_subinstructions_prompt 
    small_table_prompt: str = small_table_prompt 
    
    def __init__(
        self,
        charting_tools: PresenterChartingTools | None = None,
    ):
        self.charting_tools = charting_tools or PresenterChartingTools()


class SubInstruction(BaseModel):
    """
    One presentation item to produce from one source.
    """

    sub_instruction: str = Field(
        description=(
            "The specific part of the original instruction that this source "
            "should answer."
        )
    )

    kind: Literal["table", "text"] = Field(
        description="Whether the source is a table or a text result."
    )

    source_id: str = Field(
        description=(
            "The exact SOURCE_ID provided in the available sources. "
            "For tables use the table name. "
            "For text use the text SOURCE_ID."
        )
    )


class SubInstructions(BaseModel):
    """
    Ordered presentation plan for one TaskResult.
    """

    items: list[SubInstruction] = Field(
        description=(
            "The ordered list of presentation items to generate."
        )
    )
    
    
 

class xxPresenterComponent3:
    """
    Converts the completed ExecutorState into UI display items.

    """

    def __init__(self, llm: Any, config: PresenterConfig | None = None ):
        self.llm = llm
        self.config = config or PresenterConfig()
        self.charting_tools = self.config.charting_tools


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

                    table_text_or_chart_item = self._process_dataframe(data_result,task_result.instruction)
                    # later:
                    if table_text_or_chart_item:
                        ui_items.append(table_text_or_chart_item)

                else:
                    ui_items.append(_make_error_item(task_result, data_result))

        return PresenterResponse(items=ui_items)
   









    def old_run(self, result_state: ExecutorState) -> PresenterResponse:

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

                    table_text_or_chart_item = self._process_dataframe(data_result,task_result.instruction)
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
        work = df.copy()

        preprocess = plan.get("preprocess")
        plot = plan.get("plot")

        if preprocess:
            work = self.charting_tools.run_preprocess(work, preprocess)

        if not plot:
            return None

        tool_name = plot.get("tool")
        args = plot.get("args") or {}

        print("The args for the plot are ")
        print(args)


        return self.charting_tools.run_plot_tool(
            tool_name=tool_name,
            df=work,
            args=args,
        )


    def _format_label(self, name: str) -> str:
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


    def _process_dataframe( self,data_result,instruction ):


        df = data_result.dataframe
        nrows, ncols = df.shape    

        print(100*'=') 
        print('instruction', instruction)

        #inst="""show the count of wells split by type, and the yearly cumulative liquid production since the year 2015."""
        # if the table is 1 row and 2 or less columns, just produce a textual response
        if nrows <= 2 and ncols <=2:
            print("it is a small table")
            return self._present_very_small_table( df,data_result, instruction )
        
        else:
            p = TableResponseProcessor()# self.llm )

            print("Extracting context")
            table_context = p.extract_table_context( data_result )
 
            #chart_plan = self._select_chart_plan( data_result, table_context )
            chart_plan = self._select_chart_plan( instruction, table_context )

            print(50*'=','Plan',50*'=')
            print(chart_plan)
            print(100*'=')
            
            
            chart_output = self._run_chart_plan( chart_plan, df )

            #later 
            #if chart_output["data"]["type"] == "table":
            #    format as a table.
            #    pass 

            return self._make_chart_item( self._format_label(data_result.table_name), 
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

    def _select_chart_plan(self,
        
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
        r= json.loads(text)

        

        return r 


class PresenterComponent4:
    """
    Converts an ExecutorState into UI display items.

    Each TaskResult is processed as a whole:
    - all TextResult and DataFrameResult objects are added to one context;
    - one LLM call splits the task instruction into sub-instructions;
    - each sub-instruction is associated with one source;
    - text sources become text UIItems;
    - table sources are passed to the existing dataframe presentation logic.
    """

    def __init__(
        self,
        llm: Any,
        config: PresenterConfig | None = None,
    ):
        self.llm = llm
        self.config = config or PresenterConfig()
        self.charting_tools = self.config.charting_tools

    def run(self, result_state: ExecutorState) -> PresenterResponse:
        return self.process_task_results(result_state)

    def _make_clarification_item(
        self,
        clarification_request: str,
    ) -> UIItem:
        return UIItem(
            id=f"question_{uuid4().hex[:8]}",
            type="question",
            title="Additional information required",
            data={"question": clarification_request},
        )

    def _make_text_item(
        self,
        data_result: TextResult,
    ) -> UIItem:
        return UIItem(
            id=f"text_{uuid4().hex[:8]}",
            type="text",
            title=None,
            data={"text": data_result.text},
        )

    def _make_error_item(
        self,
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

    def build_task_result_context(
        self,
        task_result: TaskResult,
    ) -> tuple[str, dict[str, TextResult | DataFrameResult]]:
        """
        Build:
        - one text context containing all TextResult and DataFrameResult objects;
        - a source map used later to recover the original result objects.
        """
        processor = TableResponseProcessor()

        context_parts: list[str] = []
        source_map: dict[str, TextResult | DataFrameResult] = {}

        for n, data_result in enumerate(task_result.data_results):

            if isinstance(data_result, TextResult):
                source_id = f"text_{n}"

                context_parts.append(
                    "\n".join([
                        f"SOURCE_ID: {source_id}",
                        "SOURCE_TYPE: text",
                        "CONTENT:",
                        data_result.text,
                    ])
                )

                source_map[source_id] = data_result

            elif isinstance(data_result, DataFrameResult):
                source_id = data_result.table_name
                table_context = processor.extract_table_context(data_result)

                context_parts.append(
                    "\n".join([
                        f"SOURCE_ID: {source_id}",
                        "SOURCE_TYPE: table",
                        table_context,
                    ])
                )

                source_map[source_id] = data_result

        context_text = "\n\n---\n\n".join(context_parts)

        return context_text, source_map

    def get_subinstructions(
        self,
        task_result: TaskResult,
        context_text: str,
    ) -> SubInstructions:
        """
        Split the task instruction and associate each sub-instruction
        with one available source.
        """
        messages = [
            SystemMessage(content=self.config.split_subinstructions_prompr),
            HumanMessage(
                content=(
                    f"INSTRUCTION\n"
                    f"{task_result.instruction}\n\n"
                    f"AVAILABLE SOURCES\n"
                    f"{context_text}"
                )
            ),
        ]

        structured_llm = self.llm.with_structured_output(SubInstructions)

        return structured_llm.invoke(messages)

    def process_single_task_result(
        self,
        task_result: TaskResult,
    ) -> list[UIItem]:
        context_text, source_map = self.build_task_result_context(
            task_result
        )

        sub_instructions = self.get_subinstructions(
            task_result=task_result,
            context_text=context_text,
        )

        ui_items: list[UIItem] = []

        for item in sub_instructions.items:
            source = source_map[item.source_id]

            if item.kind == "text":
                ui_items.append(
                    self._make_text_item(source)
                )

            elif item.kind == "table":
                ui_items.append(
                    self._process_dataframe(
                        source,
                        item.sub_instruction,
                    )
                )

        return ui_items

    def process_task_results(
        self,
        execution_state: ExecutorState,
    ) -> PresenterResponse:
        ui_items: list[UIItem] = []

        clarification_request = execution_state.get(
            "clarification_request"
        )

        if clarification_request:
            ui_items.append(
                self._make_clarification_item(
                    clarification_request
                )
            )

            return PresenterResponse(items=ui_items)

        for task_result in execution_state.get("task_results", []):
            ui_task_items = self.process_single_task_result(
                task_result
            )

            ui_items.extend(ui_task_items)

        return PresenterResponse(items=ui_items)

    def _present_very_small_table(
        self,
        df: pd.DataFrame,
        data_result: DataFrameResult,
        instruction: str,
    ) -> UIItem:
        data_string = df.to_json()

        print('processing very small table')
        prompt = (
            self.config.small_table_prompt
            + "\n\n"
            + (
                "### Context\n"
                f"- Table Name: {getattr(data_result, 'table_name', 'N/A')}\n"
                f"- Description: "
                f"{getattr(data_result, 'description', 'No description provided.')}\n\n"
                "### Data\n"
                f"{data_string}\n\n"
                "User question:\n"
                f"{instruction}\n"
            )
        )

        response = self.llm.invoke(prompt)

        text_output = (
            response.content
            if hasattr(response, "content")
            else str(response)
        )

        return UIItem(
            id=f"text_{uuid4().hex[:8]}",
            type="text",
            title=None,
            data={"text": text_output},
        )

    def _make_chart_item(
        self,
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

    def _make_table_item(
        self,
        figure_title: str,
        plotly_json_figure: dict,
        description: str | None = None,
    ) -> UIItem:
        return UIItem(
            id=f"table_{uuid4().hex[:8]}",
            type="table",
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
        work = df.copy()

        preprocess_steps = plan.get("preprocess") or []
        plot = plan.get("plot")

        if preprocess_steps:
            work = self.charting_tools.run_preprocess(
                work,
                preprocess_steps,
            )

        if not plot:
            return None

        tool_name = plot.get("tool")
        args = plot.get("args") or {}

        return self.charting_tools.run_plot_tool(
            tool_name=tool_name,
            df=work,
            args=args,
        )


    def _format_label(
        self,
        name: str,
    ) -> str:
        if name is None:
            return ""

        text = str(name).replace("_", " ").strip().lower()

        return text[:1].upper() + text[1:]

    def _process_dataframe(
        self,
        data_result: DataFrameResult,
        instruction: str,
    ) -> UIItem:
        df = data_result.dataframe
        nrows, ncols = df.shape

        if nrows <= 2 and ncols <= 2:
        #if nrows <= 5 and ncols <= 5:
            
            return self._present_very_small_table(
                df,
                data_result,
                instruction,
            )

        processor = TableResponseProcessor()

        table_context = processor.extract_table_context(
            data_result
        )

        chart_plan = self._select_chart_plan(
            instruction,
            table_context,
        )

        print('****chart plan****')
        print(instruction)
        print(chart_plan)


        chart_output = self._run_chart_plan(
            chart_plan,
            df,
        )

        plot = chart_plan.get("plot") or {}
        tool_name = plot.get("tool")


        if tool_name == "plot_table":
            return self._make_table_item(
                self._format_label(data_result.table_name),
                chart_output,
                data_result.description,
            )

        return self._make_chart_item(
            self._format_label(data_result.table_name),
            chart_output,
            data_result.description,
        )


        return self._make_chart_item(
            self._format_label(data_result.table_name),
            chart_output,
            data_result.description,
        )

    def _strip_markdown_json(
        self,
        text: str,
    ) -> str:
        text = text.strip()

        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

        return text.strip()

    def _select_chart_plan(
        self,
        user_query: str,
        table_context: str,
    ) -> dict:
        messages = [
            SystemMessage(content=self.config.prompt),
            HumanMessage(
                content=(
                    f"USER QUERY\n"
                    f"{user_query}\n\n"
                    f"TABLE\n"
                    f"{table_context}"
                )
            ),
        ]

        response = self.llm.invoke(messages)

        text = self._strip_markdown_json(
            response.content
        )

        return json.loads(text)
    






   







