
from typing_extensions import Self
from typing import Any, Dict, List, Iterable, Literal, Union, Optional,TypedDict
from typing_extensions import Self

from pydantic import BaseModel, Field


class TableItemAgentResponse(BaseModel):
    table_name: str = Field(description="Name of a materialized output table")
    description: str = Field(description="Brief summary of the table contents")
        
class AgentTableResponse(BaseModel):
    # Literal ensures the LLM chooses only these specific strings
    agent: Literal["analyst"] = Field(
        default="analyst", 
        description="The role of the agent. Always 'analyst'."
    )
    #response_type: Literal["table","text","question","table+text"] = Field(
    #    description="The type of response: 'table' for tabular data, 'text' for textual summaries, and 'question' for follow-up questions."
    #) 

    question: Optional[str] = Field(default=None, description="A follow-up question if the response_type is 'question'")

    text: Optional[str]  = Field(default=None, description="A textual response summarizing small tables.")

    user_query: str = Field( description='sanitized user query')
    tables: List[TableItemAgentResponse] = Field(default=[], description="Comma-separated list of table names")

    #text : Optional[str]  = Field(default=None, description="textual response summarizing small tables")
    #tables: List[TableItemAgentResponse] = Field(default_factory=list, description="List of materialized output tables")



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

    #needs_clarification: bool = Field(
    #    default=False,
    #    description="True when the user request is ambiguous and cannot be safely executed."
    #)

    clarification_request: str | None = Field(
        default=None,
        description=(
            "Clarification question/request to ask the user before executing any tasks. "
            "If this is not None, execution must stop and ask the user for clarification."
        ),
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
