from __future__ import annotations
from runtime.v4.analyst_agent.catalog import * 
#from runtime.v4.analyst_agent.smart_data import SmartData

from typing import Dict, List, Tuple, Optional, Any 
from langchain_core.tools import StructuredTool, Tool
from typing import Iterable
 
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from runtime.v4.analyst_agent.smart_data import SmartData



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
        return self.format_catalog_snapshot( snapshot )

    def old_catalog_snapshot(
        self,
        input_tables: None | str | Iterable[str] = None
    ) -> str:
        """
        Returns LLM-friendly textual catalog snapshot.

        Designed for:
        - planner prompts
        - executor prompts
        - schema grounding

        Output:
        Structured readable text, not raw dict/json.
        """

        # =====================================================
        # GET STRUCTURED SNAPSHOT
        # =====================================================

        snapshot = self._data.catalog_snapshot(input_tables)

        lines = []

        # =====================================================
        # HEADER
        # =====================================================

        lines.append("DATABASE CATALOG SNAPSHOT")
        lines.append("=" * 79)

        # =====================================================
        # BASE TABLES
        # =====================================================

        if snapshot.base_tables:
            lines.append("\nBASE TABLES:")
            lines.append("-" * 79)

            for table in snapshot.base_tables:

                lines.append(f"\nTable: {table.name}")
                lines.append(f"Kind: base")

                if table.description:
                    lines.append(f"Description: {table.description}")

                if table.row_count is not None:
                    lines.append(f"Row Count: {table.row_count}")

                lines.append("Columns:")

                for col in table.columns:

                    col_line = f"  - {col.name} ({col.data_type}"

                    #if col.semantic_type:
                    #    col_line += f", semantic: {col.semantic_type}"

                    col_line += ")"

                    if col.description:
                        col_line += f": {col.description}"

                    lines.append(col_line)

        # =====================================================
        # DERIVED TABLES
        # =====================================================

        if snapshot.derived_tables:
            lines.append("\nDERIVED TABLES:")
            lines.append("-" * 79)

            for table in snapshot.derived_tables:

                lines.append(f"\nTable: {table.name}")
                lines.append(f"Kind: derived")

                if table.description:
                    lines.append(f"Description: {table.description}")

                if table.row_count is not None:
                    lines.append(f"Row Count: {table.row_count}")

                if getattr(table, "created_by_sql", None):
                    lines.append(f"Created By SQL: {table.created_by_sql}")

                lines.append("Columns:")

                for col in table.columns:

                    col_line = f"  - {col.name} ({col.data_type}"

                    #if col.semantic_type:
                    #    col_line += f", semantic: {col.semantic_type}"

                    col_line += ")"

                    if col.description:
                        col_line += f": {col.description}"

                    lines.append(col_line)

        # =====================================================
        # GLOBAL RULES
        # =====================================================

        lines.append("\nGLOBAL RULES:")
        lines.append("-" * 79)
        lines.append("- Only listed tables and columns exist.")
        lines.append("- Never invent tables or columns.")
        lines.append("- Prefer reuse of derived tables when possible.")
        lines.append("- Base tables are original datasets.")
        lines.append("- Derived tables are previously materialized analytical outputs.")

        # =====================================================
        # FINAL TEXT
        # =====================================================

        return "\n".join(lines)


    def old_catalog_snapshot(self, input_tables: None | str | Iterable[str] = None):# -> str:
        """
        Returns an agent-facing catalog snapshot with global SQL rules,
        semantic constraints, and table schemas.
        """

        return self._data.catalog_snapshot(input_tables)
        #table_snapshot = self._data.catalog_snapshot(input_tables)
        #return f"{table_snapshot}"

    def _get_table_names( self ):
        """Returns the table names"""
        return  self._data.get_table_names() 
    
    def get_tables_creation_datetime( self )-> Dict[str,str]  :
        """Returns the creation date of each table"""
        return self._data.get_tables_creation_datetime()
        
    def get_tables_brief_description( self ):
        """Returns a brief textual description of the tables"""
        return self._data.get_tables_brief_description() 

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
                        description=attr.__doc__,
                    )
                )
        return tools
    
    def materialize_select( self, table_name, rows )->str:
        """Return a full table to produce a textual response. Dont call this unless the table has less than 10 rows"""
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

        return self._data.conn.execute(f'SELECT * FROM "{safe_name}" LIMIT 5').fetchdf()

    def sql_materialize( self, sql:str, materialized_table_name:str, detailed_table_description:str ):
        """
        materialize a table by executing sql and stores it in the database as a 'derived' table.  
        Args:
            sql(str): sql query to execute. Must start with WITH or SELECT 
            materialized_table_name: name given to the new table. 
            detailed_table_description: detailed description of the resulting table  

        Returns:
            Message indicating that the table was generated and stored or a message indicating failure when an error occured
            This tool will  never return a table 
        """
        retries = 0 

        try:
            df_result = self._data.execute_sql(sql, detailed_table_description)
            self._data.register_derived_table( df_result, materialized_table_name, detailed_table_description)
        
            snapshot = self._data.catalog_snapshot(materialized_table_name)
            txt_snapshot = self.format_catalog_snapshot( snapshot )
            return f"Observation: table {materialized_table_name} created. \n"#\n{txt_snapshot}"

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
        
    
