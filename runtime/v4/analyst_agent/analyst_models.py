
from  typing import List, Any, Optional, Iterable, Literal
from pydantic import BaseModel,Field



class PlanStep(BaseModel):
    step_id: int
    target_table: str
    source_tables: List[str]
    reusable_tables: List[str] = Field(default_factory=list)
    logic: str

class ExecutionPlan(BaseModel):
    #raw_query: str 
    user_query: str
    refined_query: Optional[str] = None 
    tables_needed: List[str] = Field( default=[],description="List of all the tables in the catalog that will be needed to answer the question")
    steps: List[PlanStep]

class TableItemAgentResponse(BaseModel):
    table_name: str = Field(description="Name of a materialized output table")
    description: str = Field(description="Brief summary of the table contents")
        

class AgentTableResponse(BaseModel):
    # Literal ensures the LLM chooses only these specific strings
    agent: Literal["analyst"] = Field(
        default="analyst", 
        description="The role of the agent. Always 'analyst'."
    )
    user_query: str = Field( description='sanitized user query')
    tables: List[TableItemAgentResponse] = Field(default=[], description="Comma-separated list of table names")

    #text : Optional[str]  = Field(default=None, description="textual response summarizing small tables")
    #tables: List[TableItemAgentResponse] = Field(default_factory=list, description="List of materialized output tables")
    
    