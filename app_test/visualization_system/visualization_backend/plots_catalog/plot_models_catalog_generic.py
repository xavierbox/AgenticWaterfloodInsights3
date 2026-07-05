from typing import Any, Dict, Generic, List, Literal, Optional, TypeVar, Union

from pydantic import BaseModel, Field

from app_test.visualization_system.visualization_backend.plots_catalog.global_constants import CRMDATASET


ParameterType = Literal["string", "float", "bool", "int"]
T = TypeVar("T", str, float, bool, int)


class PlotParameter(BaseModel, Generic[T]):
    display_name: str
    description: str
    type: ParameterType
    value: T


PlotStringParameter = PlotParameter[str]
PlotFloatParameter = PlotParameter[float]
PlotBoolParameter = PlotParameter[bool]
PlotIntParameter = PlotParameter[int]

PlotParameterValue = Union[
    PlotStringParameter,
    PlotFloatParameter,
    PlotBoolParameter,
    PlotIntParameter,
]



class PlotCatalogItem(BaseModel):
    display_name: str
    function: str = Field(..., description="Function name to call")
    description: str
    category: str = Field(default="General", description="Category of the plot for organizational purposes")

    parameters: Optional[Dict[str, PlotParameterValue]] = Field(default=None, description="List of parameters for the plot")
    
class WORPlot(PlotCatalogItem):
    display_name: str = "WOR vs cumulative oil"
    function: str = "plot_wor_vs_cumulative_oil"
    description: str = "Plots WOR against cumulative oil production."
    application: str = "This plot is useful for analyzing the water cut and understanding the efficiency of water injection in enhanced oil recovery processes. It helps in identifying the point at which water production starts to dominate over oil production, which can inform decisions on well management and optimization strategies."
    data_context: list[str] = Field(default_factory=lambda: [CRMDATASET], description="Data context required for this plot")
    category: str = "Surveillance"
    parameters: Optional[Dict[str, PlotParameterValue]] = {
        "split_by_well": PlotBoolParameter(
            display_name="Split by Well",
            description="Whether to split by well",
            type="bool",
            value=True,
        ),
        "split_by_sector": PlotBoolParameter(
            display_name="Split by Sector",
            description="Whether to split by sector",
            type="bool",
            value=False,
        )    
        }

class VRRPlot(PlotCatalogItem):
    display_name: str = "VRR vs cumulative water injected"
    function: str = "plot_vrr_vs_cumulative_water_injected"
    description: str = "Plots voidage replacement ratio against cumulative water injected."
    application: str = "This plot is useful for analyzing the voidage replacement ratio and understanding the efficiency of water injection in enhanced oil recovery processes."
    data_context: list[str] = Field(default_factory=lambda: [CRMDATASET], description="Data context required for this plot")
    category: str = "Surveillance"
    parameters: Optional[Dict[str, PlotParameterValue]] = {
        "bo": PlotFloatParameter(
            display_name="Bo",
            description="Formation volume factor for oil",
            type="float",
            value=1.2,
        ),
        "bw": PlotFloatParameter(
            display_name="Bw",
            description="Formation volume factor for water",
            type="float",
            value=1.0,
        ),
        "rg": PlotFloatParameter(
            display_name="Rg",
            description="Gas formation volume factor",
            type="float",
            value=0.005,
        ),

        "split_by_well": PlotBoolParameter(
            display_name="Split by Well",
            description="Whether to split by well",
            type="bool",
            value=True,
        ),
        "split_by_sector": PlotBoolParameter(
            display_name="Split by Sector",
            description="Whether to split by sector",
            type="bool",
            value=False,
        ),
    }
    
class HallPlot(PlotCatalogItem):
    display_name: str = "Hall Plot"
    function: str = "plot_hall_plot"
    application: str = "Identifying Formation Damage: It highlights near-wellbore plugging or damage. If the plot's slope steepens or moves upward, it means injectivity is declining—often indicating that poor-quality fluid or solids are blocking the reservoir pores.Diagnosing Well Stimulation: It tracks the effectiveness of acidizing or hydraulic fracturing. A drop or flattening in the slope suggests that the well has been successfully stimulated, making fluid injection much easier.Monitoring Long-Term Trends: It smoothes out day-to-day rate and pressure fluctuations, allowing engineers to spot gradual, long-term changes in reservoir pressure and fluid transmissibility over weeks or months.Evaluating Injection Strategies: It helps determine if the injected fluids are moving evenly through the reservoir and displacing oil or gas efficiently"
    description: str = "Cummulative injection pressure over time vs cummulative volume of fluid injected" 
    data_context: list[str] = Field(default= [CRMDATASET], description="Data context required for this plot")
    category: str = "Diagnostic"
    parameters: Optional[Dict[str, PlotParameterValue]] = None 

class WellCount(PlotCatalogItem):
    display_name: str = "Well count over time"
    function: str = "plot_well_count"
    application: str = "Monitoring well activity over time" 
    description: str = "Displays the number of active wells over time; injectors and producers" 
    data_context: list[str] = Field(default= [CRMDATASET], description="Data context required for this plot")
    category: str = "Monitoring"
    parameters: Optional[Dict[str, PlotParameterValue]] = None 

class PlotCatalog(BaseModel):
    items: List[PlotCatalogItem] = Field(default_factory=list)

def get_historical_data_plot_catalog() -> PlotCatalog:
    return PlotCatalog(
        items=[
            WORPlot(),
            VRRPlot(),
            HallPlot(),
            WellCount(),
        ]
    )


catalog = get_historical_data_plot_catalog()

print(catalog.model_dump())




'''
in the server

needs_data_context = Any( [item for item in catalog.items if 'crm_data' initem.data_context] )
needs_simulation_context = Any( [item for item in catalog.items if 'crm_simulation_results' initem.data_context] )

crm_dataset = None if not needs_data_context else load_crm_dataset( filters )
crm_simulation_results = None if not needs_simulation_context else load_crm_simulation_results( filters )

for item in items:

    data = {}

    if 'crm_data' in item.data_context:
        data['crm_dataset'] = crm_datase
    if 'crm_simulation_results' in item.data_context:
        data['crm_simulation_results'] = crm_simulation_results

    item.generate_plot( **data, item.parameters )

    else:

        item.generate_plot( data_context=DataContext( ui_state=ui_state ) )


'''


