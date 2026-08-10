from dataclasses import dataclass
import sys, pprint, pandas as pd  
sys.path.append('../../')
sys.path.append('../')
sys.path.append('./')
import warnings

from typing import Any, Dict, Generic, List, Iterable, Literal, TypeVar, Union, Optional,TypedDict
from typing_extensions import Self
from uuid import uuid4
from pydantic import BaseModel, Field 
from pathlib import Path

TPlan = TypeVar("TPlan", bound=BaseModel)

@dataclass 
class PlannerConfig:
    prompt :str # |  None  = None #planner_prompt3

 
class PlannerComponent(Generic[TPlan]):

    def __init__(self, llm: Any,  
                 config: PlannerConfig, 
                 plan_model: type[TPlan]
                 ):

    
        self.config = config #if not config is None else PlannerConfig()
        self.llm = llm
        self.plan_model = plan_model

    @property
    def prompt(self) -> str|None:
        return self.config.prompt

    def run(self, user_query: str,previous_state = None ) -> TPlan:
        return self.plan( user_query )
    
    def plan(self, user_query: str, previous_state = None ) -> TPlan:
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": user_query},
        ]

        structured_llm = self.llm.with_structured_output(self.plan_model)
        return structured_llm.invoke(messages)

 