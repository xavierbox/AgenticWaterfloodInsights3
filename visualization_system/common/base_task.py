from typing_extensions import Self
from typing import Any, Dict, Generic, List, Iterable, Literal, TypeVar, Union, Optional,TypedDict
from typing_extensions import Self
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

