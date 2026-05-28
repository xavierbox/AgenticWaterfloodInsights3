"""
Application-wide Pydantic models and shared data structures.

This package contains models that are shared across multiple
application modules and services, including API payloads,
responses, configuration objects, metadata structures,
and common domain entities.

Models specific to a particular feature or package
(e.g. analyst agents, charting, simulations)
should remain within their corresponding package
to avoid unnecessary coupling.

Typical contents:
    - Shared response models
    - Project metadata models
    - User/session models
    - Configuration models
    - Common utility structures

This package should contain only reusable,
cross-application models.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class UIState(BaseModel):
    """
    Captures the state of the UI including the project selected, the data filters and 
    well selections if any.


    """
    project_name:str = Field(description="The name of the waterflood project as it shows in the UI")
    
    study_name: Optional[str] = Field(default=None, description="A selected simulation(if any)")
    selected_wells : Optional[List[str]] = Field(default=[], description="A list of selected wells")

    filters : Optional[Dict[str, Any]] = Field(default={}, description="A dictionary of filters applied to the data, e.g. {'subzone': 'A', 'year': 2020}")


class StatusResponse(BaseModel):
    """
    Generic application status response.

    This model is used to communicate the outcome
    of an operation, API request, validation step,
    or internal process.

    Attributes:
        success:
            Indicates whether the operation completed successfully.

        message:
            Optional descriptive message providing additional
            details about the result, warning, or error.
    """
    success: bool
    message: str | None = None
