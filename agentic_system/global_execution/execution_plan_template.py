from typing import List

from pydantic import BaseModel, Field

from agentic_system.common.base_task import BaseSystemTask

from agentic_system.common.base_task import BaseSystemTask

class deleteme_ExecutionTask(BaseSystemTask):
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
            "The specific domain-expert agent assigned to execute this task."
        )
    ) 

class delete_meExecutionPlanTemplate(BaseModel):
    
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
