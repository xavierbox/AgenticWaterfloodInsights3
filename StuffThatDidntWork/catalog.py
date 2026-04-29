import sys 
from datetime import datetime 
from typing import Dict, List, Tuple, Optional, Any 
from pathlib import Path 
from semantics.semantic_models import * 
from typing import Iterable, Union

from typing import Any, Dict
import yaml
import pandas as pd, numpy as np

class Catalog:

    def __init__(self):
        self.tables: Dict[str, TableCard] = {}

    def clear(self):
        self.tables = {} 

    def initialize_from_named_dataframes( self, df_dict: Dict[str,pd.DataFrame], named_table_models ):
        
        self.clear() 

        for name,df in df_dict.items():
            model = named_table_models.get(name, None)
            if model:
                model.row_count = df.shape[0]

                dt = datetime.now() if hasattr(datetime, "now") else datetime.datetime.now()  
                model.creation_date = str( dt )
                
                self.tables[name] = model
            else:
                raise ValueError(f"Table named {name} is not in the known tables catalog")
       
    def register_table(self, table_card: TableCard ):
        dt = datetime.now() if hasattr(datetime, "now") else datetime.datetime.now()  
             
        table_card.creation_date = str( dt )
        self.tables[ table_card.name ] = table_card

    @staticmethod  
    def dataframe_to_table_card( df: pd.DataFrame, name, description, kind:Literal['base','derived'], **kwargs):
        dt = datetime.now() if hasattr(datetime, "now") else datetime.datetime.now()  
             
        cols = [ ColumnCard( name = col, data_type = str(df[col].dtype), description = None) for col in df.columns] 
        table_card = TableCard(
            name=name,
            description=description,
            kind = kind, 
            creation_date=str( dt ),
            row_count=df.shape[0],
            columns = cols,
            relationships = [] if not kwargs else kwargs.get('relationships', []),
            sql_examples  = [] if not kwargs else kwargs.get('sql_exampled',  [])

        )

        return table_card

    def __repr__(self) -> str:
        return self.snapshot()

    def snapshot(self, input_tables: None | TableCard | Iterable[TableCard] = None ) -> str: # pyright: ignore[reportArgumentType]
        
        table_blocks: list[str] = []
        
        items = (
            self.tables.values()
            if input_tables is None
            else [input_tables]
            if isinstance(input_tables, TableCard)
            else input_tables if isinstance(input_tables,Iterable)
            else list(input_tables)
        )
        '''
        s = "tables:\n"
        for tc in  sorted( items,  key=lambda x: x.name):
            s1 = f" - table:{tc.name}\n{tc.description}"
            cols = ""
            s = s + s1 

        return s 
        '''
 

        for tc in  sorted( items,  key=lambda x: x.name):
            d = tc.model_dump(
                exclude_none=True,
                exclude_defaults=True,
                exclude_unset = True,
                mode = 'json',
                #exclude = {'columns'}
            )

            block = yaml.dump(
                {"table": [d]},
                sort_keys=False,
                allow_unicode=True,
                width=1000  # avoid wrapping
            ).rstrip()

            table_blocks.append(block)
            table_blocks.append("")


        return "\n".join(table_blocks) 



    

    def __getitem__(self, value):
        
        cards = None 
        if isinstance(value, slice):
            cards =  list(self.tables.values())[value] 

        if isinstance(value, str ):
            cards = self.tables[value]

        if isinstance(value, Iterable ):
            cards = [ self.tables[v] for v in value] 
 

        return cards  
