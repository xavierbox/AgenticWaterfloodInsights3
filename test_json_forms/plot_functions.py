from typing import Dict, List, Literal, Optional, Union, Any
import pprint 
from pydantic import BaseModel, Field
from test_json_forms.global_constants import CRMDATASET


def plot_wor_vs_cumulative_oil(crm_dataset: Any, split_by_well: bool = True, split_by_sector: bool = False):
    
    crm_dataset = crm_dataset
    print("Plotting WOR vs cumulative oil")
    print("Parameters:", split_by_well, split_by_sector)

    return "plot_wor_vs_cumulative_oil executed fine"

def plot_hall(crm_dataset: Any ):
    print("Plotting Hall plot", crm_dataset)
    return "plot_hall executed fine"

def plot_well_count_over_time( crm_dataset: Any):
    print("Plotting well count over time", crm_dataset)
    return "plot_hall plot_well_count_over_time fine"

