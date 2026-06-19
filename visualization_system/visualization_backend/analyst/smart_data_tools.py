from __future__ import annotations
from visualization_system.visualization_backend.analyst.catalog import * 
#from runtime.v4.analyst_agent.smart_data import SmartData

from typing import Dict, List, Tuple, Optional, Any 
from langchain_core.tools import StructuredTool, Tool
from typing import Iterable
 
import inspect
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from visualization_system.visualization_backend.analyst.smart_data import SmartData



class SmartDataTools:

    def __init__(self, data:SmartData):
        self._data = data 

    # ----------------------------------------
    def record_plan(self, plan: str) -> str:
        """
        Records the execution plan. Does NOT affect execution.
        """
        print("\n===== PLAN (TOOL) =====")
        print(plan)
        print("=======================\n")
        return "OK"

    def format_catalog_snapshot(self, snapshot: CatalogTablesSnapshot) -> str:
        def clean(obj):
            if isinstance(obj, dict):
                return {
                        k: clean(v)
                        for k, v in obj.items()
                        if v not in [None, "", [], {}]
                }

            elif isinstance(obj, list):
                return [
                    clean(v)
                    for v in obj
                    if v not in [None, "", [], {}]
                    ]

            return obj
        
        import json

        lines = []

        def format_tables(title: str, tables: list[TableCard] | None):
            if not tables:
                return

            lines.append(title)
            lines.append("-" * 60)

            for t in tables:
                d = json.loads(
                    t.model_dump_json(
                        indent=2,
                        #exclude_unset=True,
                        exclude_none=True,
                    )
                )
                ## scan all the keys, when values are None, [] or empty, pop them
                d = clean( d )
                lines.append(f"\nTable: {d['name']}")

                for k, v in d.items():
                    if k == "name":
                        continue

                    if k == "columns":
                        lines.append("  Columns:")
                        for c in v:
                            parts = [f"{ck}: {cv}" for ck, cv in c.items()]
                            lines.append(f"    - {' | '.join(parts)}")

                    elif k == "relationships":
                        lines.append("  Relationships:")
                        for r in v:
                            parts = [f"{rk}: {rv}" for rk, rv in r.items()]
                            lines.append(f"    - {' | '.join(parts)}")

                    else:
                        lines.append(f"  {k}: {v}")

            lines.append("")

        #format_tables("BASE TABLES", snapshot.base_tables)
        #format_tables("DERIVED TABLES", snapshot.derived_tables)
        format_tables(" ", snapshot.base_tables)
        format_tables(" ", snapshot.derived_tables)
        return "\n".join(lines).strip()

    def catalog_snapshot(
        self,
        input_tables: None | str | Iterable[str] = None
    ) -> str:
        """
        Return an LLM-friendly textual snapshot of the data catalog.

        This method is intended to ground agents with the available table
        schemas, descriptions, columns, and relevant metadata before they plan
        or execute data tasks.

        Parameters
        ----------
        input_tables : None | str | Iterable[str], optional
            Tables to include in the snapshot.

            - None:
                Include all tables in the catalog.
            - str:
                Include only the table with this name.
            - Iterable[str]:
                Include only the listed table names.

        Returns
        -------
        str
            A structured, readable catalog description suitable for use in
            planner prompts, executor prompts, and schema-grounded reasoning.
        """

        # =====================================================
        # GET STRUCTURED SNAPSHOT
        # =====================================================

        snapshot = self._data.catalog_snapshot(input_tables)
        print(snapshot)
        return self.format_catalog_snapshot( snapshot )

    def _get_table_names( self ):
        """Returns the table names"""
        return  self._data.get_table_names() 
    
    def get_tables_creation_datetime( self )-> Dict[str,str]  :
        """Returns the creation date of each table"""
        return self._data.get_tables_creation_datetime()
        
    def get_tables_brief_description( self ):
        """Returns a brief textual description of the tables"""
        return self._data.get_tables_brief_description() 

    def get_single_table_brief_description( self, table_name:str ):
        """Returns a brief textual description of a single table"""
        return self._data.get_single_table_brief_description( table_name )  



    def get_tools(self):#, include_planning_tools: bool = False):
        tools = []
        
        for name in dir(self):
            if name.startswith("_") or name == "get_tools":
                continue
            #if not include_planning_tools and name in planning_tools:
            #    continue
                
            attr = getattr(self, name)
            if not attr.__doc__:
                continue


            if callable(attr) and attr.__doc__:
                tools.append(
                    StructuredTool.from_function(
                        func=attr,
                        name=name,
                        description=inspect.getdoc(attr),
                    )
                )
        return tools
    
    def materialize_select( self, table_name, rows )->str:
        """
        Return a full table to produce a textual response. 
        **Do not call this tool ** unless the table has less than 20 rows
        """
        #return self._conn.execute(f'SELECT * FROM "{table_name}"').fetchdf()
        if not table_name:
            return "table_name cannot be empty"

        # Validate table exists
        exists = self._data.conn.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = ?
            """,
            [table_name],
        ).fetchone()[0]

        if exists == 0:
            raise ValueError(f"Table '{table_name}' does not exist in DuckDB")

        # Safe quoting for table names
        safe_name = table_name.replace('"', '""')
        limit = min(20, int(rows))
        return self._data.conn.execute(f'SELECT * FROM "{safe_name}" LIMIT {limit}').fetchdf().to_string()

    def sql_materialize( self, sql:str, materialized_table_name:str, detailed_table_description:str ):
        """
        materialize a table by executing sql and stores it in the database as a 'derived' table.  
        Args:
            sql(str): sql query to execute. Must start with WITH or SELECT 
            materialized_table_name: name given to the new table. 
            detailed_table_description: detailed description of the resulting table  

        Returns:
            Message indicating that the table was generated and stored or a message indicating 
            failure when an error occured
            If the resulting table is small, also returns a string preview of the table.
        """
        retries = 0 

        try:
            df_result = self._data.execute_sql(sql, detailed_table_description)
            self._data.register_derived_table( df_result, materialized_table_name, detailed_table_description)
        
            snapshot = self._data.catalog_snapshot(materialized_table_name)
            txt_snapshot = self.format_catalog_snapshot( snapshot )
            n_rows, n_cols = df_result.shape

            table_preview = ""
            if n_rows < 10 and n_cols < 5:
                table_preview = f"Table {materialized_table_name} preview:\n{df_result.to_string(index=True)}\n"
                

            return (
                        f"Observation: table {materialized_table_name} created.\n"
                        f"\n{txt_snapshot}\n"
                        f"{table_preview}"
                    )
            #return f"Observation: table {materialized_table_name} created.\nTable metadata:\n{txt_snapshot}\n"

        except Exception as e:
            error_msg = (
                        f"Observation: Materialization failed for table '{materialized_table_name}'.\n"
                        f"Error Type: {type(e).__name__}\n"
                        f"Error Detail: {str(e)}\n"
                        f"Failed SQL: {sql}\n"
                    )
            return error_msg

    def reuse_derived_table(self, derived_table_name:str, table_description:str):
        """Call this function to reuse a **derived** table present in the catalog."""

        if derived_table_name in self._get_table_names():
            return f"Table {derived_table_name} is in the catalog and can be reused.\ndescription: {table_description} "
        else:
            return f"Table {derived_table_name} **IS NOT in the catalog** and **CANNOT** be reused. "
        
    
