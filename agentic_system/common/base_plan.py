from dataclasses import dataclass
import sys, pprint, pandas as pd

from agentic_system.common.base_task import ExecutionTask  


sys.path.append('../../')
sys.path.append('../')
sys.path.append('./')
import warnings

from typing import Any, Dict, Generic, List, Iterable, Literal, TypeVar, Union, Optional,TypedDict
from typing_extensions import Self
from uuid import uuid4
from pydantic import BaseModel, Field, model_validator 
from pathlib import Path
from graphlib import TopologicalSorter, CycleError
from pydantic import BaseModel, Field, model_validator
from typing import List

from langchain_core.exceptions import OutputParserException
from pydantic import ValidationError
TPlan = TypeVar("TPlan", bound=BaseModel)

@dataclass 
class PlannerConfig:
    prompt :str # |  None  = None #planner_prompt3
    max_retries: int = 3 

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

    def plan(self, user_query: str, previous_state = None) -> TPlan:
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": user_query},
        ]
        structured_llm = self.llm.with_structured_output(self.plan_model)
        max_retries = getattr(self.config, "max_retries", 3)

        for attempt in range(max_retries):
            try:
                # 1. Try to invoke the LLM (Runs Pydantic validators automatically)
                generated_plan = structured_llm.invoke(messages)                   
                
                # 2. SUCCESS: Reorder tasks chronologically using your property
                generated_plan.tasks = generated_plan.execution_order
                return generated_plan

            except (ValidationError, OutputParserException) as e:
                print(f"⚠️ Validation failed on attempt {attempt + 1}/{max_retries}.")
                
                # Handle the absolute final failure safely to avoid crashing down the line
                if attempt == max_retries - 1:
                    print(f"❌ Max retries reached. Validation failed permanently. Returning fallback plan.")
                    fallback_plan = self.plan_model(
                        user_intent=f"FAILED_GENERATION: Could not build a stable graph for: {user_query}  ",
                        tasks=[]
                    )
                    return fallback_plan
                
                # --- Safe extraction using getattr to satisfy Pylance ---
                bad_generation = "Unavailable"
                if isinstance(e, ValidationError):
                    bad_generation = str(getattr(e, "input_value", "Unavailable"))
                elif isinstance(e, OutputParserException):
                    bad_generation = str(getattr(e, "llm_output", "Unavailable"))
                
                # 3. Format BOTH the bad generation and the validator error
                error_feedback = (
                    f"Your previous generation failed validation.\n\n"
                    f"--- YOUR PREVIOUS OUTPUT ---\n"
                    f"{bad_generation}\n\n"
                    f"--- VALIDATION ERROR ---\n"
                    f"{str(e)}\n\n"
                    f"Please inspect your previous output, fix any missing task IDs, "
                    f"and rewrite the plan ensuring there are NO circular dependencies/deadlocks."
                )
                
                # 4. Append history transitions for the next retry loop iteration
                messages.append({"role": "assistant", "content": "Analyzing dependency graph error..."})
                messages.append({"role": "user", "content": error_feedback})

        # --- CRITICAL FIX FOR PYLANCE ---
        # Safeguard fallback if max_retries is configured <= 0, ensuring a TPlan is always returned.
        return self.plan_model(
            user_intent=f"FAILED_GENERATION: Retries configured to zero or negative. Could not plan: {user_query} ",
            tasks=[]
        )


    def v2_plan(self, user_query: str, previous_state = None) -> TPlan:
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": user_query},
        ]
        structured_llm = self.llm.with_structured_output(self.plan_model)
        max_retries = self.config.max_retries #or 3

        for attempt in range(max_retries):
            try:
                # 1. Invoke LLM (Triggers your @model_validator instantly)
                generated_plan = structured_llm.invoke(messages)                   
                # 2. SUCCESS: Reorder tasks chronologically using your property
                generated_plan.tasks = generated_plan.execution_order
                return generated_plan

          
            except (ValidationError, OutputParserException) as e:
                # 2. Check if we have exhausted our retries
                if attempt == max_retries - 1:
                    print(f"❌ Max retries reached. Execution plan validation failed permanently.")
                    fallback_plan = self.plan_model(
                        user_intent=f"FAILED_GENERATION: {user_query[:50]}...",
                        tasks=[] # Empty task list is perfectly safe and won't crash loops
                    )
                    return fallback_plan
                    #raise e
                
                print(f"⚠️ Validation failed on attempt {attempt + 1}. Feed-forwarding error to LLM...")
                
                # 3. Format the error details so the LLM understands exactly what failed
                error_feedback = (
                    f"Your previous generation failed schema or constraint validation.\n"
                    f"Error Details:\n{str(e)}\n\n"
                    f"Please fix any missing task IDs and ensure there are NO circular dependencies/deadlocks."
                )
                
                # 4. Append a mock assistant transition and the error feedback to the message history
                messages.append({"role": "assistant", "content": "Analyzing dependency graph error..."})
                messages.append({"role": "user", "content": error_feedback})

       
    
        
    def old_plan(self, user_query: str, previous_state = None ) -> TPlan:
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": user_query},
        ]

        max_retries = self.config.max_retries

        structured_llm = self.llm.with_structured_output(self.plan_model)
        return structured_llm.invoke(messages)

class ExecutionPlanTemplate(BaseModel):
    user_intent: str = Field(
        description="One-sentence summary of the user's ultimate goal."
    )
    tasks: List[ExecutionTask] = Field(
        description="The macro-level pipeline. List of Task entries assigned to agents."
    )

    @model_validator(mode="after")
    def validate_execution_plan(self) -> "ExecutionPlanTemplate":
        """
        Comprehensive validator that ensures:
        1. All referenced dependency IDs exist.
        2. There are no circular dependencies (deadlocks).
        """
        # --- 1. Validate Dependency IDs Exist ---
        existing_ids = {task.task_id for task in self.tasks}
        
        for task in self.tasks:
            if task.depends_on:
                for dependency in task.depends_on:
                    if dependency not in existing_ids:
                        raise ValueError(
                            f"LLM Generation Error: Task '{task.task_id}' depends on '{dependency}', "
                            f"but '{dependency}' was never defined in the tasks list."
                        )
        
        # --- 2. Validate No Circular Dependencies ---
        try:
            ts = TopologicalSorter()
            for task in self.tasks:
                dependencies = task.depends_on if task.depends_on else []
                # graphlib expects: ts.add(node, *predecessors)
                ts.add(task.task_id, *dependencies)
            
            # This triggers a CycleError if an infinite loop exists
            ts.prepare()
        except CycleError as e:
            raise ValueError(
                f"Circular Dependency Error: The LLM generated a plan with an infinite loop deadlock: {e}"
            )
                        
        return self

    @property
    def execution_order(self) -> List[ExecutionTask]:
        """Returns the tasks sorted chronologically by their execution order."""
        task_lookup = {task.task_id: task for task in self.tasks}
        
        ts = TopologicalSorter()
        for task in self.tasks:
            dependencies = task.depends_on if task.depends_on else []
            ts.add(task.task_id, *dependencies)
        
        return [task_lookup[task_id] for task_id in ts.static_order()]

class oldExecutionPlanTemplate(BaseModel):
    
    user_intent: str = Field(
        description="One-sentence summary of the user's ultimate goal."
    )

    tasks: List[ExecutionTask] = Field(
        description=(
            "The macro-level pipeline. List of Task entries assigned to agents "
            "For example, if the user asks for a conceptual explanation AND an input data analysis "
            "plot, generate separate task elements in order: "
            "Task 1 (direct_answer) for the explanation, Task 2 (input_data_analysis) for the plot."
        )
    )


    @model_validator(mode="after")
    def validate_dependency_ids(self) -> "ExecutionPlanTemplate":
        """Ensures all task_ids referenced in 'depends_on' actually exist in the plan."""
        # 1. Map out all existing task IDs generated by the LLM
        existing_ids = {task.task_id for task in self.tasks}
        
        # 2. Verify every dependency references a valid ID
        for task in self.tasks:
            if task.depends_on:
                for dependency in task.depends_on:
                    if dependency not in existing_ids:
                        raise ValueError(
                            f"LLM Generation Error: Task '{task.task_id}' depends on '{dependency}', "
                            f"but '{dependency}' was never defined in the tasks list."
                        )
                        
        return self
