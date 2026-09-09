from dataclasses import dataclass
from typing import Any, Dict, Generic, List, Iterable, Literal, TypeVar, Union, Optional,TypedDict
from typing_extensions import Self
from pydantic import BaseModel, Field 
from pathlib import Path

#TPlan = TypeVar("TPlan", bound=BaseModel)

 
class TaskResult(BaseModel):
    """
    Output produced by one executed task.

    This object separates the task output into three layers:
    cheap prompt context, raw agent-specific outputs, and normalized
    downstream-consumable data.

    agent: str the name of the agent
    instruction: str the instruction passed to the agent
    cheap_output: the agent might return a short text, or similar to be added to context.Cheap, few tokens
    raw_results: 
    data_results: downstream other modules will consume these results. The  related data is here 
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

class DataFrameResult(BaseModel):
    table_name: str
    description: str | None = None
    dataframe: Any

class TableItemAgentResponse(BaseModel):
    table_name: str = Field(description="Name of a materialized output table")
    description: str = Field(description="Brief summary of the table contents")
 
class AgentTableResponse(BaseModel):
    # Literal ensures the LLM chooses only these specific strings
    agent: Literal["analyst"] = Field(
        default="analyst", 
        description="The role of the agent. Always 'analyst'."
    )

    clarification: Optional[str] = Field(default=None, description="A follow-up question if the response_type is 'question'")

    user_query: str = Field( description='sanitized user query')
    tables: List[TableItemAgentResponse] = Field(default=[], description="Comma-separated list of table names")




