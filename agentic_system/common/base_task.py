from typing_extensions import Self
from typing import Any, Dict, Generic, List, Iterable, Literal, TypeVar, Union, Optional,TypedDict
from typing_extensions import Self
from pydantic import BaseModel, Field


from pydantic import BaseModel, Field

class BaseSystemTask(BaseModel):
    instruction: str = Field(
        description=(
            "The comprehensive, high-level objective for this agent phase. "
            "Do NOT break down sub-steps, intermediate calculations, or plotting adjustments. "
            "Provide the complete end-goal description verbatim so the receiving agent "
            "can handle its own internal execution steps."
        )
    )
    agent: str = Field(
        description=(
            "The name of the specific domain-expert agent assigned to execute this task."
        )
    )

 
class ExecutionTask(BaseSystemTask):

    task_id: str = Field(
        description=(
            "A unique identifier for this task. "
            "Use a simple, human-readable format that can be referenced in downstream tasks. "
        )
    )

    depends_on: Optional[List[str]] = Field(
        description=(   
        "List of task_ids that this task depends on. "
            "If this task requires the output of other tasks, list their task_ids here. "
            "If there are no dependencies, leave this field empty or null."
        )
    )
    



class obsolete_ExecutionTask(BaseSystemTask):

    task_id: str = Field(
        description=(
            "A unique identifier for this task. "
            "Use a simple, human-readable format that can be referenced in downstream tasks. "
        )
    )

    depends_on: Optional[List[str]] = Field(
        description=(   
        "List of task_ids that this task depends on. "
            "If this task requires the output of other tasks, list their task_ids here. "
            "If there are no dependencies, leave this field empty or null."
        ),
        default=None
        )

   