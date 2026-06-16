
from pydantic import BaseModel, Field
from typing import Any, List, Optional, Union, TypeVar, Generic, Literal
from typing_extensions import Self
  

class UIState(BaseModel):
    """
    We pass this from the UI to the backend.
    The backend detects changes in the UIState and updates the agents accordingly. 
    """

    project_name: str #| None = None 
    selected_wells: Optional[List[str]]  = Field(default=None)
    selected_subzone: str|None = Field(default = None, description="Selected subzone for filtering")
    selected_sectors: Optional[List[int]] | None  = Field(default=None, description="Selected sector for filtering")
    selected_study: Optional[str] | None  = Field(default=None, description="Selected simulation for filtering")
    selected_wells: Optional[List[str]] |None = Field(default=None)  
    query: str #| None = Field(default=None, description="User query typed in the chat")

    def project_changed( self, new_input: Self )->bool:
        return self.project_name != new_input.project_name 

    def data_filters_changed( self, new_input: Self )->bool:
        return (
            self.sectors_selected != new_input.sectors_selected
            or self.subzone_selected != new_input.subzone_selected
            or self.wells_selected != new_input.wells_selected
        ) 
    
    def simulation_changed( self, new_input: Self )->bool:
        return (
            self.simulation_selected != new_input.simulation_selected
        ) 
    
    def needs_data_reload( self, new_input: Self ):
        return self.project_changed(new_input) or self.data_filters_changed(new_input)
 
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


