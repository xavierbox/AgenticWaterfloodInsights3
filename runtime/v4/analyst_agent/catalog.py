import sys 
from datetime import datetime 
from typing import Dict, List, Tuple, Optional, Any 
from pathlib import Path 
from runtime.v4.semantics.semantic_models import * 
from typing import Iterable, Union

from typing import Any, Dict
import yaml
import pandas as pd, numpy as np

class Catalog:

    def __init__(self):
        self.tables: Dict[str, TableCard] = {}

    def snapshot(
        self,
        input_tables=None
    ) -> CatalogTablesSnapshot:
        """
        Return structured catalog snapshot.

        Output:
        CatalogTablesSnapshot(
            base_tables=[...],
            derived_tables=[...]
        )
        """

        # =====================================================
        # SELECT TABLES
        # =====================================================

        if input_tables is None:
            items = self.tables.values()

        elif isinstance(input_tables, TableCard):
            items = [input_tables]

        else:
            items = input_tables

        # =====================================================
        # OUTPUT CONTAINERS
        # =====================================================

        base_tables = []
        derived_tables = []

        # =====================================================
        # BUILD TABLE CARDS
        # =====================================================

        for tc in items:

            columns = []

            for c in tc.columns:

                #column_card = ColumnCard(
                #    name=c.name,
                #    data_type=c.data_type or "",
                #    semantic_type=getattr(c, "semantic_type", None),
                #    description=c.description if c.description else None,
                #    allowed_values=getattr(c, "allowed_values", None),
                #)

                columns.append( c )#column_card)

            # -----------------------------------------
            # Preserve created SQL if available
            # -----------------------------------------
            created_by_sql = None

            #if hasattr(tc, "created_by_sql"):
            #    created_by_sql = tc.created_by_sql

            #elif getattr(tc, "sql_examples", None):
            #    if tc.sql_examples:
            #        created_by_sql = tc.sql_examples[0].sql

            # -----------------------------------------
            # Build structured table card
            # -----------------------------------------
            table_card = TableCard(
                name=tc.name,
                description=tc.description,
                kind=tc.kind or "base",
                row_count=tc.row_count,
                columns=columns,
                #created_by_sql=created_by_sql,
            )

            # -----------------------------------------
            # Route by type
            # -----------------------------------------
            if table_card.kind == "derived":
                derived_tables.append(table_card)

            else:
                base_tables.append(table_card)

        # =====================================================
        # RETURN STRUCTURED SNAPSHOT
        # =====================================================

        return CatalogTablesSnapshot(
            base_tables=base_tables if base_tables else None,
            derived_tables=derived_tables if derived_tables else None,
        )
            
    def textual_snapshot(self, input_tables=None) -> dict:

        if input_tables is None:
            items = self.tables.values()
        elif isinstance(input_tables, TableCard):
            items = [input_tables]
        else:
            items = input_tables

        out = {
            "base_tables": {},
            "derived_tables": {}
        }

        for tc in items:
            cols = {}

            for c in tc.columns:
                dtype = c.data_type if c.data_type else ""

                col_entry = {"type": dtype}

                if c.description:
                    col_entry["description"] = c.description

                cols[c.name] = col_entry

            #created_by_sql = None
            #if hasattr(tc, "created_by_sql"):
            #    created_by_sql = tc.created_by_sql
            #elif tc.sql_examples:
            #    created_by_sql = tc.sql_examples[0].sql

            table_entry = {
                "description": tc.description,
                "kind": tc.kind or "base",
                "row_count": tc.row_count,
                "columns": cols,
                #"created_by_sql": created_by_sql,

            }

            if tc.kind == "derived":
                out["derived_tables"][tc.name] = table_entry
            else:
                out["base_tables"][tc.name] = table_entry

        return out        
            
    def good_snapshot(self, input_tables=None) -> dict:
        """
        Return a simplified catalog:
        {
          "tables": {
             table_name: {
                "columns": {col: dtype},
                "created_by_sql": str | None,
                "description": str,
                "kind": "base" | "derived"
             }
          }
        }
        """
        if input_tables is None:
            items = self.tables.values()
        elif isinstance(input_tables, TableCard):
            items = [input_tables]
        else:
            items = input_tables

        out = {"tables": {}}

        for tc in items:
            # columns: name -> dtype
            cols = {}
            for c in tc.columns:
                dtype = c.data_type if c.data_type else ""
                col_entry = {"type": dtype}
                #if c.description:
                #    col_entry["description"] = c.description
                cols[c.name] = col_entry
                        
                #cols[c.name] = dtype
                #cols[c.name] = {
                #"type": dtype,
                #"description": c.description or ""
                #}

            # created_by_sql (you already store this in sql_examples or elsewhere?)
            #created_by_sql = None
            #if hasattr(tc, "created_by_sql"):
            #    created_by_sql = tc.created_by_sql
            #elif tc.sql_examples:
            #    # optional: pick first example as origin
            #    created_by_sql = tc.sql_examples[0].sql

            out["tables"][tc.name] = {
                "columns": cols,
                #"created_by_sql": created_by_sql,
                "description": tc.description,
                "kind": tc.kind or "base",
            }

        return out

    def yaml_snapshot(
        self,
        input_tables: None | TableCard | Iterable[TableCard] = None,
    ) -> str:
        """
        Returns a clean YAML snapshot of one or more table cards.

        Output shape:

        tables:
          - name: injectors
            ...
          - name: producers
            ...
        """

        if input_tables is None:
            items = list(self.tables.values())

        elif isinstance(input_tables, TableCard):
            items = [input_tables]

        elif isinstance(input_tables, Iterable):
            items = list(input_tables)

        else:
            raise TypeError(f"{type(input_tables).__name__} is not supported")

        tables = []

        for tc in sorted(items, key=lambda x: x.name):
            d = tc.model_dump(
                exclude_none=True,
                exclude_defaults=True,
                exclude_unset=True,
                mode="json",
            )

            tables.append(d)

        return yaml.dump(
            {"tables": tables},
            sort_keys=False,
            allow_unicode=True,
            width=1000,
    ).rstrip()    
                   
    def old_snapshot(self, input_tables: None | TableCard | Iterable[TableCard] = None ) -> str: # pyright: ignore[reportArgumentType]
        
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
            #sql_examples  = [] if not kwargs else kwargs.get('sql_exampled',  [])

        )

        return table_card
        
    def clear(self):
        self.tables = {} 

    def initialize_from_named_dataframes( self, df_dict: Dict[str,pd.DataFrame], 
                                         named_table_models:Dict[str,TableCard] ):
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
       
    def set_data(self,  df_dict: Dict[str,pd.DataFrame]):
        """
        Sets the new tables (data) assuming that the semantic model is already stored.
        Useful when chaning the project dataset, while still having the same table structure.
        Note that all derived tables will be lost.
        """
        temporal = {}
        for name, df in df_dict.items():
            if name not in self.tables:
                raise ValueError(f"Table named {name} is not in the known tables catalog")

            model = self.tables[name]
            model.row_count = df.shape[0]

            dt = datetime.now() if hasattr(datetime, "now") else datetime.datetime.now()  
            model.creation_date = str( dt )
            temporal[name] = model

        self.tables = temporal 




    def register_table(self, table_card: TableCard ):
        dt = datetime.now() if hasattr(datetime, "now") else datetime.datetime.now()  
             
        table_card.creation_date = str( dt )
        self.tables[ table_card.name ] = table_card

    def __repr__(self) -> str:
        return self.snapshot()

    def __getitem__(self, value):
        
        cards = None 
        if isinstance(value, slice):
            cards =  list(self.tables.values())[value] 

        if isinstance(value, str ):
            cards = self.tables[value]

        if isinstance(value, Iterable ):
            cards = [ self.tables[v] for v in value] 
 

        return cards  
