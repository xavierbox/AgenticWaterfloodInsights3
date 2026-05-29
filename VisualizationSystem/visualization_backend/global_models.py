
from pydantic import BaseModel, Field
from typing import Any, List, Optional, Union, TypeVar, Generic, Literal

class UIState(BaseModel):
    """
    We pass this from the UI to the backend.
    The backend detects changes in the UIState and updates the agents accordingly. 
    """
    project_name: str
    selected_wells: Optional[List[str]] = Field(default_factory=list)
    subzone_selected: List[str] = Field(default_factory=list, description="Selected subzone for filtering")
    sector_selected: List[int] = Field(default_factory=list, description="Selected sector for filtering")
    simulation_selected: Optional[str] = Field(default="", description="Selected simulation for filtering")

class DataContext(BaseModel):
    """
    This is the context that the backend have access to when generating plots.
    It includes the UI state and any other relevant information about the data.
    """
    ui_state: UIState
    simulation_results: Any
    crm_dataset: Any
    project_name: str
    # Add any other relevant context information here, such as available datasets, metadata, etc.


