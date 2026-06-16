from dataclasses import dataclass
import inspect 
from functools import wraps
from typing_extensions import Self
from typing import Any, Dict, List, Iterable, Literal, Union, Optional,TypedDict
from typing_extensions import Self

from VisualizationSystem.visualization_backend.global_models import UIState
from VisualizationSystem.visualization_backend.analyst.prompts import planner_prompt3
from VisualizationSystem.visualization_backend.analyst.analyst_models import * 

from langgraph.graph import END, StateGraph
from langchain_core.tools import StructuredTool, Tool
from langchain.agents import create_agent
 

from VisualizationSystem.visualization_backend.analyst.analyst_models import ExecutorState


@dataclass 
class PlannerConfig:
    prompt :str = planner_prompt3

@dataclass 
class DirectAnswerConfig:
    prompt :str =  ("Answer using stable general knowledge. "
                    "Be concise. Return reusable factual context."
                    "The user is a reservoir engineer")

def make_llm_calling_node(node, llm):
    @wraps(node)
    def wrapped_node(state):
        return node(state, llm=llm)

    return wrapped_node



@dataclass 
class SQLAnalystConfig:
    
    prompt :str = "You are an analyst that reponds to quantitative questions about the data"

    reference_density: float = 1.0 

    def updateDensity( self, value:float ):
        self.reference_density = value 



class SQLAnalystTools:

    def __init__( self ):
        self.data = None 

    def compute_injection_mass( self ):
        """
        Returns the total mass volume injected.
        """

        print("TOOL: compute_injection_mass " )

        return self.data.reference_density # type: ignore

    def get_tools(self):#, include_planning_tools: bool = False):
        tools = []
        
        for name in dir(self):
            if name.startswith("_") or name == "get_tools":
                continue
            #if not include_planning_tools and name in planning_tools:
            #    continue
                
            attr = getattr(self, name)
            if not attr.__doc__:
                continue


            if callable(attr) and attr.__doc__:
                tools.append(
                    StructuredTool.from_function(
                        func=attr,
                        name=name,
                        description=inspect.getdoc(attr),
                    )
                )
        return tools
  


class AgenticSystem:

    def __init__(self):
        self.planner_config: PlannerConfig = PlannerConfig()
        self.direct_answer_config = DirectAnswerConfig() 

        self.graph = StateGraph(ExecutorState)
        self._llm: Any | None = None
        self.app: Any | None = None

        self.sql_analyst_config: SQLAnalystConfig = SQLAnalystConfig()
        self.sql_tools = None 

        self.last_query: UIState | None = None#UIState( project_name="NoSet", query="Nothing")
 


    @property
    def llm(self):
        if self._llm is None:
            raise ValueError("llm has not been set")
        return self._llm

    @llm.setter
    def llm(self, value):
        if value is None:
            raise ValueError("llm cannot be None")
        self._llm = value

    @property
    def planner_prompt(self):
        if self.planner_config is None:
            raise ValueError("planner_config has not been set")
        return self.planner_config.prompt

    @property
    def sql_analyst_prompt(self):
        return self.sql_analyst_config.prompt

    def create_graph(self):
        graph = self.graph

        graph.add_node("planner_node", self.planner_node)
        graph.add_node("router_node", self.router_node)

        graph.add_node("direct_answer_node", self.direct_answer_node)
        graph.add_node("rag_retriever_node", self.rag_retriever_node)
        graph.add_node("data_analysis_node", self.data_analysis_node)
        graph.add_node("clarification_node", self.clarification_node)

        graph.add_node("aggregator_node", self.aggregator_node)

        graph.set_entry_point("planner_node")

        route_map = {
            "direct_answer": "direct_answer_node",
            "rag_retriever": "rag_retriever_node",
            "data_analysis": "data_analysis_node",
            "clarification": "clarification_node",
            "aggregate": "aggregator_node",
            "end": END,
        }

        graph.add_edge("planner_node", "router_node")

        graph.add_conditional_edges(
            "router_node",
            self.route_next_task,
            route_map,
        )

        graph.add_edge("direct_answer_node", "router_node")
        graph.add_edge("rag_retriever_node", "router_node")
        graph.add_edge("data_analysis_node", "router_node")

        graph.add_edge("clarification_node", END)
        graph.add_edge("aggregator_node", END)

    def compile_graph(self):
        self.app = self.graph.compile()
        return self.app

    def planner_node(self, state: ExecutorState):
        user_query = state["user_query"]

        messages = [
            {"role": "system", "content": self.planner_prompt},
            {"role": "user", "content": user_query},
        ]

        structured_llm = self.llm.with_structured_output(SystemPlan)
        plan = structured_llm.invoke(messages)

        #print(plan)

        return {
            "plan": plan,
            "task_index": 0,
            "facts_context": "",
            "rag_context": "",
            "plot_context": "",
            "tool_outputs": [],
            "final_answer": None,
            "waiting_for_user": False,
        }


    def route_next_task(self, state: ExecutorState):

        plan = state["plan"]
        if plan is None:
            raise ValueError("No plan available")

        if state.get("waiting_for_user"):
            return "end"

        if plan.needs_clarification or plan.direct_answer:
            return "end"
    
 
    
        
        task_index = state["task_index"]



        print("Router ", task_index,len(plan.tasks) )
        if task_index >= len(plan.tasks):
            print("Router returning aggregate")
            return "aggregate"

        print("Router returening ",plan.tasks[task_index].tool )
        return plan.tasks[task_index].tool

    def xxxanalyst_agent_node(self, state: ExecutorState):

        plan, task, task_index = self._dummy_worker_node(state)
        result = f"[analyst node executed : {task.instruction}]"
        previous_context = state.get("aggregated_context") or ""

        print(100*'=')
        print("Analyst")
        

        agent = create_agent(
        model=self.llm,
        tools=self.sql_tools,             
        system_prompt= self.sql_analyst_prompt, 
        checkpointer=None,     # stateless
        #response_format=SystemPlan
        )

    
        analyst_response = agent.invoke({"messages": [{"role": "user", "content": task.instruction}]})
        print(analyst_response['messages'][-1].content)
        print(100*'=')
        
        return {
            "aggregated_context": previous_context + 'Analyst',
            "task_index": task_index + 1,
            "analyst_response": analyst_response
        }

    def explanation_rag_node(self, state: ExecutorState):
        
        plan, task, task_index = self._dummy_worker_node(state)
        result = f"[explanation_rag_node] : {task.instruction}"
        previous_context = state.get("aggregated_context") or ""
        return {
            "aggregated_context": previous_context + result,
            "task_index": task_index + 1,
        }

    def xxxproject_structure_agent_node(self, state: ExecutorState):
        
        plan, task, task_index = self._dummy_worker_node(state)
        result = f"[project_structure_agent_node]: {task.instruction}"
        previous_context = state.get("aggregated_context") or ""
        return {
            "aggregated_context": previous_context + result,
            "task_index": task_index + 1,
        }

    def _dummy_worker_node(self, state: ExecutorState):
        plan = state["plan"]
        task_index = state["task_index"]

        #if plan is None:
        #    raise ValueError("No plan available")

        task = plan.tasks[task_index] # type: ignore

        return plan, task, task_index 

        #result = (
        #    f"Dummy result from {agent_name}. "
        #    f"Received instruction: {task.instruction}"
        #)

        #previous_context = state.get("aggregated_context") or ""

        #new_context = (
        #    previous_context
        #    + f"\n\n## Task {task_index + 1}: {agent_name}\n"
        #    + f"Instruction: {task.instruction}\n"
        #    + f"Result: {result}\n"
        #)

        #return {
        #    "aggregated_context": new_context,
        #    "task_index": task_index + 1,
        #}

    def _get_current_task(self, state: ExecutorState):
        plan = state["plan"]
        task_index = state["task_index"]

        if plan is None:
            raise ValueError("No plan available")

        if task_index >= len(plan.tasks):
            raise IndexError(
                f"task_index {task_index} out of range for {len(plan.tasks)} tasks"
            )

        return plan, plan.tasks[task_index], task_index

    def router_node(self, state: ExecutorState):
        return {}


    def direct_answer_node(self, state: ExecutorState):
        _, task, _ = self._get_current_task(state)

        response = self.llm.invoke([
            {
                "role": "system",
                "content": self.direct_answer_config.prompt
            },
            {
                "role": "user",
                "content": task.instruction,
            },
        ])

        result = response.content

        return self._append_output(
            state=state,
            tool_name="direct_answer",
            task=task,
            result=result,
            context_key="facts_context",
        )


    def clarification_node(self, state: ExecutorState):
        _, task, task_index = self._get_current_task(state)

        return {
            "final_answer": task.instruction,
            "waiting_for_user": True,
            "task_index": task_index + 1,
        }

    def _append_output(
        self,
        state: ExecutorState,
        tool_name: str,
        task: SystemTask,
        result: str,
        context_key: str | None = None,
    ):
        previous_outputs = state.get("tool_outputs") or []

        update = {
            "task_index": state["task_index"] + 1,
            "tool_outputs": previous_outputs + [
                {
                    "tool_name": tool_name,
                    "task": task,
                    "result": result,
                }
            ],
        }

        if context_key is not None:
            previous_context = state.get(context_key) or ""
            update[context_key] = previous_context + "\n\n" + result

        return update

    def aggregator_node(self, state: ExecutorState):
        facts = state.get("facts_context") or ""
        rag = state.get("rag_context") or ""
        plots = state.get("plot_context") or ""

        final_answer = f"""
    Final answer:

    Facts:
    {facts}

    Domain/RAG context:
    {rag}

    Quantitative output:
    {plots}
    """.strip()

        return {
            "final_answer": final_answer,
        }

    def rag_retriever_node(self, state: ExecutorState):
        _, task, _ = self._get_current_task(state)

        result = f"[RAG retrieved context for]: {task.instruction}"

        return self._append_output(
            state=state,
            tool_name="rag_retriever",
            task=task,
            result=result,
            context_key="rag_context",
        )
    
    def data_analysis_node(self, state: ExecutorState):
        _, task, _ = self._get_current_task(state)

        prompt = f"""
    Task:
    {task.instruction}

    Known facts:
    {state.get("facts_context") or ""}

    RAG context:
    {state.get("rag_context") or ""}

    Use the available historical production/injection data tools to generate the requested quantitative result or plot.
    """

        agent = create_agent(
            model=self.llm,
            tools=self.sql_tools,
            system_prompt=self.sql_analyst_prompt,
            checkpointer=None,
        )

        analyst_response = agent.invoke({
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })

        result = analyst_response["messages"][-1].content

        return self._append_output(
            state=state,
            tool_name="data_plotter",
            task=task,
            result=result,
            context_key="plot_context",
        )

    def run_planner(self, user_query: str):


        messages = [
            {"role": "system", "content": self.planner_prompt},
            {"role": "user", "content": user_query},
        ]

        structured_llm = self.llm.with_structured_output(SystemPlan)
        plan = structured_llm.invoke(messages)
        return plan 
            
        state: ExecutorState = {
            "user_query": user_query,
            "plan": None,
            "task_index": 0,
            "facts_context": "",
            "rag_context": "",
            "plot_context": "",
            "tool_outputs": [],
            "final_answer": None,
            "waiting_for_user": False,
        }

        return self.planner_node(state)



if __name__ == "__main__":

    print("analyst models as main module")
    system = AgenticSystem()

