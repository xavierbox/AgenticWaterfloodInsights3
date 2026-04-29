from langchain_core.tools import StructuredTool, Tool
from agentic.v4.semantic_models import * 
from typing import Iterable, Union
import duckdb
from typing import Any, Dict
import yaml
import pandas as pd, numpy as np

from agentic.v4.catalog import Catalog


class SmartData:

    def __init__(self):
        self._catalog = Catalog() 
        self.conn= duckdb.connect()

    def _normalize_sql(self, sql: str) -> str:
        lines = sql.strip().splitlines()
        print(lines)
        cleaned = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("--"):
                continue
            cleaned.append(line)
        return "\n".join(cleaned).strip()


    def execute_sql( self, sql:str, table_description:str ):
        """
        materialize a table by executing sql.  
        Args:
            sql(str): sql quiery to execute. Must start with WITH or SELECT 
            table_description: brief description of the resulting table  
        """
        #print('materializing')
        #print('sql', sql)
        #print('description', table_description)
        norm_sql = self._normalize_sql( sql )
        result = self.conn.execute(norm_sql).fetchdf()
        return result 

    def clear( self ):
        self._catalog.clear()
        self.conn.close()
        self.conn= duckdb.connect()

        
    def clear_derived( self ):
        derived_table_names = [
            name
            for name, card in self._catalog.tables.items()
            if card.kind == 'derived'
        ]

        for name in derived_table_names:
            try:
                self.conn.unregister(name)
            except duckdb.CatalogException:
                pass
            self._catalog.tables.pop(name, None)


    def sanitize_df(self, df):

        df = df.copy()
        return df 
    
        # Ensure index is not problematic
        if df.index.name is not None or not isinstance(df.index, pd.RangeIndex):
            df = df.reset_index()

        # Attempt to convert object columns
        for col in df.columns:
            if df[col].dtype == "object":
                # try datetime
                converted = pd.to_datetime(df[col], errors="ignore")
                if not pd.api.types.is_object_dtype(converted):
                    df[col] = converted
                    continue

                # try numeric
                converted = pd.to_numeric(df[col], errors="ignore")
                if not pd.api.types.is_object_dtype(converted):
                    df[col] = converted

        return df
    
    def initialize_from_named_dataframes( self, df_dict: Dict[str,pd.DataFrame], named_table_models ):
        self.clear()

        try:
            conn = self.conn
            self._catalog.initialize_from_named_dataframes( df_dict, named_table_models )
            
            for name, df in df_dict.items():
                df = self.sanitize_df(df)
                conn.register(name, df)

        except Exception as e:
            print( 'exception', str(e))
            self.clear()
            
    def catalog_snapshot(self, input_tables: None | str | Iterable[str] = None) -> str:
        """
        Returns schema and description of all tables (base and derived) in the database
        """
        if input_tables is None:
            return self._catalog.snapshot()
        if isinstance(input_tables, str):
            card = self._catalog.tables[input_tables]
            return self._catalog.snapshot(card)
        if isinstance(input_tables, Iterable):
            cards = [self._catalog.tables[name] for name in input_tables]
            return self._catalog.snapshot(cards)
        raise TypeError(f"{type(input_tables).__name__} is not supported")
    
    def register_derived_table(self, df:pd.DataFrame, name:str, table_description:str ):
        card = Catalog.dataframe_to_table_card( df, name, table_description, 'derived' )
        self._catalog.register_table( card )
        self.conn.register(name, df)



    def get_table_names( self ):
        """Returns the table names"""
        return [name for name in self._catalog.tables ] 
    
    def get_tables_creation_datetime( self )-> Dict[str,str]  :
        """Returns the creation date of each table"""
        return { t: v.creation_date  for t,v in self._catalog.tables.items() }   # pyright: ignore[reportReturnType]
    
    def get_tables_brief_description( self ):
        """Returns a brief textual description of the tables"""
        return { t: v.description  for t,v in self._catalog.tables.items() }  

    def get_table_as_df( self, table_name )->pd.DataFrame:
        return self.conn.execute(f"SELECT * FROM {table_name}").fetchdf()
