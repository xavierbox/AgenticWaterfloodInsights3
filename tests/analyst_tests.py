import inspect
import sys, pprint, pandas as pd , os, json, re, plotly.io as pio 
from pathlib import Path
sys.path.append('../../')
sys.path.append('../')
sys.path.append('./')
from agentic_system.visualization.catalog import Catalog  
from agentic_system.visualization.smart_data import SmartData
from agentic_system.common.semantic_models import SemanticCatalog 
from agentic_system.visualization.smart_data_tools import SmartDataTools

from agentic_system.common.get_llm import azure_llm_if as get_llm 
#import agentic_system as agentic_system 


import sys, pprint, pandas as pd , os, json, re, plotly.io as pio 
from pathlib import Path
sys.path.append('../../')
sys.path.append('../')
sys.path.append('./')


import re,pandas as pd
import plotly.io as pio
import json
from typing import Any, Dict, List, Iterable, Literal, Union, Optional,TypedDict
from typing_extensions import Self   
from uuid import uuid4
from pydantic import BaseModel, Field 
from get_llm_model import azure_llm_if
print('imported')

 
parent_dir = Path(__file__).parent.parent / "datasets/IX5I_4P"
print(f"Parent Path: {parent_dir.resolve()}")

def get_config():
    return None 

# mock of DATAIKU setup  
class DataDrivenStorage:
        
    def __init__( self, config_vars ):
        pass 

    def get_project_dataset(self, project_name=None, filters=None):
        #path =  "../datasets/Demo1/"
        #path =  Path("../datasets/IX5I_4P/") 
        path = parent_dir# Path(inspect.getfile(SmartDataTools)).resolve().parent
        
        print(path)


        inj, prod, locs = self.fetch_data(path) 
        return inj, prod, locs

    def fetch_data(self,path:Path):
        inj  = pd.read_csv(path / "injectors.csv")
        pinj = pd.read_csv(path / "producers.csv")
        locs = pd.read_csv(path / "locations.csv")
        inj['DATE'] = pd.to_datetime( inj['DATE'],dayfirst=True)
        inj['DAY']   = inj['DATE'].dt.day
        inj['MONTH'] = inj['DATE'].dt.month
        inj['YEAR']  = inj['DATE'].dt.year
        pinj['DATE'] = pd.to_datetime( pinj['DATE'],dayfirst=True)
        pinj['DAY']   = pinj['DATE'].dt.day
        pinj['MONTH'] = pinj['DATE'].dt.month
        pinj['YEAR']  = pinj['DATE'].dt.year


        return inj, pinj, locs

# mock of fetching CRM input data 
inj,prod,locs = DataDrivenStorage( get_config() ).get_project_dataset(123, {}) 
print( inj.head(2) )
print( prod.head(2))
print( locs.head(2))

# these tables are used by the visualization system (input data)
# lets create smart data for those tables.
# For a fully operational SmartData object we need 
# 1. the data 
# 2. the semantic models 

# but we can initialize it from the semantic models and pass data later when we have it,
# we can initialize the object with both at the same time.
# every time data is "set" all previous tables are deleted.
# the semantic model doesnt change automatically. if needed, use the provided method. 



#This is a dictionary of table-name: semantic info
from agentic_system.common.known_tables_models import inj_prod_locs_semantic_catalog 
#inj_prod_locs_semantic_catalog
semantic_catalog = SemanticCatalog.model_validate(inj_prod_locs_semantic_catalog)
#type(semantic_catalog)

known_table_models = { t.name: t for t in semantic_catalog.tables } 
df_dict = {'injectors': inj, 'producers': prod , 'locations': locs }
#models = [ TableCard(x) for x in inj_prod_locs_semantic_catalog]

#one option 
smart_data = SmartData()
smart_data.init_from_semantic_models( semantic_catalog.tables )
smart_data.set_data( df_dict )
print(smart_data.get_table_names())
print(smart_data.get_tables_brief_description())

smart_data.get_table_as_df('producers')
smart_data.get_single_table_brief_description('producers')

model = smart_data.catalog_snapshot('producers') #(), (['producers','locations'])

model.model_dump() 
print()


result = smart_data.execute_sql(
    """
        SELECT
            NAME,
            SUM(WATER_INJECTION_VOLUME) AS total_injection
        FROM injectors
        GROUP BY NAME
        ORDER BY total_injection DESC
        LIMIT 3
    """)

print(result)

print() 
