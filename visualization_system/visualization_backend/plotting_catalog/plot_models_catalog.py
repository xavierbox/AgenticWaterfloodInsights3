from enum import Enum
from typing import Dict, List, Literal, Optional, Union, Any
from pydantic import BaseModel, Field
import pprint, inspect

from   visualization_backend.global_constants import CRMDATASET
import visualization_backend.plotting_catalog.plot_functions as plot_functions 


class PlotStringParameter(BaseModel):
    display_name: str
    description: str
    type: Literal["string"] = "string"
    value: str


class PlotFloatParameter(BaseModel):
    display_name: str
    description: str
    type: Literal["float"] = "float"
    value: float


class PlotBoolParameter(BaseModel):
    display_name: str
    description: str
    type: Literal["bool"] = "bool"
    value: bool


class PlotIntParameter(BaseModel):
    display_name: str
    description: str
    type: Literal["int"] = "int"
    value: int


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
    application: str = ""
    data_context: List[str] = Field(default_factory=list)
    category: str = "General"
    parameters: Dict[str, PlotParameterValue] = Field(default_factory=dict)
    data: Optional[Any] = None  # Placeholder for any additional data needed for the plot

class WORPlot(PlotCatalogItem):
    display_name: str = "WOR vs cumulative oil"
    function: str = "plot_wor_vs_cumulative_oil"
    description: str = "Plots WOR against cumulative oil production."
    application: str = "Useful for analyzing water production behavior versus cumulative oil."
    data_context: List[str] = Field(default_factory=lambda: [CRMDATASET])
    category: str = "Surveillance"
    parameters: Dict[str, PlotParameterValue] = Field(default_factory=lambda: {
        "split_by_well": PlotBoolParameter(
            display_name="Split by Well",
            description="Whether to split by well",
            value=True,
        ),
        "split_by_sector": PlotBoolParameter(
            display_name="Split by Sector",
            description="Whether to split by sector",
            value=False,
        ),
    })

class VRRPlot(PlotCatalogItem):
    display_name: str = "VRR vs cumulative water injected"
    function: str = "plot_vrr_vs_cumulative_water_injected"
    description: str = "Plots voidage replacement ratio against cumulative water injected."
    application: str = "Useful for analyzing injection efficiency and reservoir voidage replacement."
    data_context: List[str] = Field(default_factory=lambda: [CRMDATASET])
    category: str = "Surveillance"
    parameters: Dict[str, PlotParameterValue] = Field(default_factory=lambda: {
        "bo": PlotFloatParameter(
            display_name="Bo",
            description="Oil formation volume factor",
            value=1.2,
        ),
        "bw": PlotFloatParameter(
            display_name="Bw",
            description="Water formation volume factor",
            value=1.0,
        ),
        "bg": PlotFloatParameter(
            display_name="Bg",
            description="Gas formation volume factor",
            value=0.005,
        ),
        #"split_by_well": PlotBoolParameter(
        #    display_name="Split by Well",
        #    description="Whether to split by well",
        #    value=True,
        #),
        "split_by_sector": PlotBoolParameter(
            display_name="Split by Sector",
            description="Whether to split by sector",
            value=False,
        ),
    })

class HallPlot(PlotCatalogItem):
    display_name: str = "Hall Plot"
    function: str = "plot_hall"
    description: str = "Cumulative injection pressure over time vs cumulative injected fluid volume."
    application: str = "Useful for diagnosing injectivity changes, formation damage, and stimulation effects."
    data_context: List[str] = Field(default_factory=lambda: [CRMDATASET])
    category: str = "Diagnostic"

class WellCount(PlotCatalogItem):
    display_name: str = "Well count over time"
    function: str = "plot_well_count_over_time"
    description: str = "Displays the number of active injector and producer wells over time."
    application: str = "Useful for monitoring well activity over time."
    data_context: List[str] = Field(default_factory=lambda: [CRMDATASET])
    category: str = "Monitoring"

class PlotCatalog(BaseModel):
    items: List[PlotCatalogItem] = Field(default_factory=list)

class HallPlot2(PlotCatalogItem):
    display_name: str = "Hall Plot2"
    function: str = "plot_hall"
    description: str = "Cumulative injection pressure over time vs cumulative injected fluid volume."
    application: str = "Useful for diagnosing injectivity changes, formation damage, and stimulation effects."
    data_context: List[str] = Field(default_factory=lambda: [CRMDATASET])
    category: str = "Diagnostic"

class WellCount2(PlotCatalogItem):
    display_name: str = "Well count over time2"
    function: str = "plot_well_count_over_time"
    description: str = "Displays the number of active injector and producer wells over time."
    application: str = "Useful for monitoring well activity over time."
    data_context: List[str] = Field(default_factory=lambda: [CRMDATASET])
    category: str = "Monitoring"

                      
def get_historical_data_plot_catalog() -> PlotCatalog:
    return PlotCatalog(
        items=[
            WORPlot(),
            VRRPlot(),
            HallPlot(),
            WellCount()
        ]
    )

def parameter_values(parameters):
    if parameters is None:
        return {}

    result = {}

    for name, param in parameters.items():
        if hasattr(param, "value"):
            result[name] = param.value
        elif isinstance(param, dict):
            result[name] = parameter_values(param)
        else:
            result[name] = param

    return result

def get_plot_functions_by_name():
    
    plot_functions_dict = {
        name: func
        for name, func in inspect.getmembers(plot_functions, inspect.isfunction)
        if name.startswith("plot_")
    }
    return plot_functions_dict

def get_plot_function_by_name(function_name: str):
    plot_functions_dict = {
        name: func
        for name, func in inspect.getmembers(plot_functions, inspect.isfunction)
        if name.startswith("plot_")
    }

    return plot_functions_dict.get(function_name)

def generate_plots(data, items: List[PlotCatalogItem]):
    crm_dataset = data.get("crm_dataset", None)
    crm_simulation_results = data.get("crm_simulation_results", None)
    plot_functions_dict = get_plot_functions_by_name()
    
    results = []
    for item in items:
        args = [] 
        function = plot_functions_dict.get(item.function, None)
        parameters = parameter_values(item.parameters)

        if item.data_context and CRMDATASET in item.data_context:
            args.append(crm_dataset)
        if item.data_context and "crm_simulation_results" in item.data_context:
            args.append(crm_simulation_results)

        if function:
            result = function(*args, **parameters)
            results.append(result)

    return results







if __name__ == "__main__":
    catalog = get_historical_data_plot_catalog()
    pprint.pprint(catalog.model_dump())


