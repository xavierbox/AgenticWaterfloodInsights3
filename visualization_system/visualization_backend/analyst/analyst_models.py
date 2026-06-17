
from typing_extensions import Self
from typing import Any, Dict, List, Iterable, Literal, Union, Optional,TypedDict
from typing_extensions import Self

from pydantic import BaseModel, Field



class SystemTask(BaseModel):
    agent: Literal[
        "direct_answer",
        "rag_retriever",
        "data_analysis",
        "clarification"
    ] = Field(
        description="The specific domain expert agent assigned to execute this task phase."
   )

    instruction: str = Field(
      description=(
            "The comprehensive, high-level objective for this agent phase. "
            "Do NOT break down sub-steps, intermediate calculations, or plotting adjustments. "
            "Provide the complete end-goal description verbatim so the receiving agent "
            "can handle its own internal execution steps."
        )
    )

class SystemPlan(BaseModel):
    
    #agent: Literal["planner"] = Field(
    #    description="Fixed identifier for the planner agent."
    #)

    user_intent: str = Field(
        description="One-sentence summary of the user's ultimate goal."
    )

    tasks: List[SystemTask] = Field(
        description=(
            "The macro-level pipeline. Create an individual task entry for EACH distinct "
            "question or request found inside the user's prompt. "
            "For example, if the user asks for a conceptual explanation AND a data analysis "
            "plot, generate separate task elements in order: "
            "Task 1 (direct_answer) for the explanation, Task 2 (data_analysis) for the plot."
        )
    )

    needs_clarification: bool = Field(
        default=False,
        description="True when the user request is ambiguous and cannot be safely executed."
    )

    clarification_question: str | None = Field(
        default=None,
        description="Question to ask the user before executing any tasks."
    )

    direct_answer: str | None = None

class ToolOutput(BaseModel):
    tool_name: str
    task: SystemTask
    result: str

class ExecutorState(TypedDict):
    user_query: str
    plan: SystemPlan | None
    task_index: int

    facts_context: str
    rag_context: str
    plot_context: str

    tool_outputs: list[ToolOutput]

    final_answer: str | None
    waiting_for_user: bool
