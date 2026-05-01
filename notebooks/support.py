
import sys, pathlib, json, pprint, pandas as pd 
from pathlib import Path
from pydantic import Field,BaseModel 
sys.path.append('../../')
sys.path.append('../')
sys.path.append('./')

from runtime.v4.semantics.load_semantics import load_semantics
from runtime.v4.semantics.semantic_models import * 
from runtime.v4.analyst_agent.catalog import Catalog
from runtime.v4.analyst_agent.smart_data import SmartData
from runtime.v4.analyst_agent.smart_data_tools  import SmartDataTools

import  os  
from datetime import datetime 
from langchain_core.tools import StructuredTool, Tool


import duckdb
from typing import Any, Dict, List, Iterable, Union, Optional 
import yaml
import pprint
import pandas as pd, numpy as np
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig, Runnable, RunnableLambda
 
from langchain.tools import tool, ToolRuntime
from langgraph.runtime import get_runtime 
from langchain.agents import create_agent
from langchain_core.runnables import RunnableLambda
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables import Runnable
from langchain.tools import tool, ToolRuntime
from langgraph.runtime import get_runtime 
from langchain.agents import create_agent
 
import tiktoken
def count_tokens(text: str, model="gpt-4o"):
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))


def run_agent_stream_values(agent, messages):
    config = {"recursion_limit": 20}

    last_seen = 0
    last_state = None

    for state in agent.stream(
        messages,
        config=config,
        stream_mode="values",
    ):
        last_state = state  # <-- capture

        msgs = state.get("messages", [])

        for msg in msgs[last_seen:]:
            print(f"\n--- {type(msg).__name__} ---")
            print("name:", getattr(msg, "name", None))

            content = getattr(msg, "content", None) or ""
            if content.strip():
                print(content[:1200])

            tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls:
                for tc in tool_calls:
                    print("TOOL CALL:", tc.get("name"))
                    print("ARGS:", tc.get("args"))

        last_seen = len(msgs)

    print("\n--- STREAM ENDED ---")
    return last_state

query1 = "how many wells are there?"
query2 = "What is the total water injection volume by year?"
query3 = "Tell me the mean yearly water injection volume for each subzone"
query4 = "rank wells by their variability (std) in water injection volume (the higher the grater the rank)?"
query5 = "whats the frequency of observations in the dataset (D, M, Y) ?"
query6 = "summarize the injection data"
query7 = "Which well had the single highest WATER_INJECTION_VOLUME reading at any point in time and what was that reading?"
query8 = "What is the average monthly injection volume per well grouped by NAME and MONTH?"
query9 = """For each SUBZONE compute the year-over-year percentage change in total injection 
volume and report the largest drop
"""
query1 = "how many wells are there?"
query1_2 = "what proportion of those are injectors"
query2 = "What is the total water injection volume by year?"
query3 = "Tell me the total water injection volume for each subzone each year"
query4 = "rank wells by their variability (std) in water injection volume (the higher the grater the rank)?"
query4_1 = "whats the highest ranked well?"
query5 = "whats the frequency of observations in the dataset (D, M, Y) ?"
query6 = "summarize the injection data"
query7 = "Which well had the single highest WATER_INJECTION_VOLUME reading at any point in time and what was that reading?"
query8 = "What is the average monthly injection volume per well grouped by NAME and MONTH?"
query9 = """For each SUBZONE compute the year-over-year percentage change in total injection 
volume and report the largest drop
"""
query10 = "For each injector well, calculate its total water injection volume and join it with the well location information. Return a table with the well name, total injected water, latitude, longitude, and any available location/type fields."
query11="Create two separate tables: one ranking injector wells by total water injection volume, and another ranking producer wells by total oil production volume."
 

iii = """I want to compare the liquid production cummulated among wells for which the 
distance to the closes injected is in the range 0-400, 400-800, 800-1200  . Only year 2018 
"""

system_prompt_sql_executor_template = """

You are an analytical SQL agent that generates and executes sql code.
You will be provided with a high-level plan and tools.
Your job is to translate the plan into sql code that generates one or more tables in a 
dataset. 

===============================================================================
Workflow:
===============================================================================
 
1. Analyze the plan provided

2. Indentify in the plan the list of tables already present in the catalog that will be used
and get the schema of those tables from the catalog 
Examples:
    - catalog_snapshot(input_tables = [table_name1, table_name2,...]]) ->
     

3. Yo can call sql_* tools after understanding the plan and calling catalog_snapshot. 

4. Always materialize the final result as one or more tables using sql_materialize.


5. Each sql_materialize call creates exactly ONE table.


6. If multiple output tables are required:
   - call sql_materialize once per target table
   - materialize one table at a time
   - after each materialization, continue to the next required table
   - do not stop until all target tables are created

7. If a query depends on another derived table, materialize the dependency first.

8. You are allowed to execute more than one step of the plan in a single sql_materialize but 
never produce more than one target table per call to sql_materialize

9. Your task is complete only when all target tables are confirmed present.


===============================================================================
Output constraints:
===============================================================================
- Do NOT produce narrative answers about query results.
- Do NOT summarize result rows.
- Never manually format rows.
- Never describe result values in text.
- Tool calls are allowed and required.
- The PLAN and final DONE block are the only allowed text outputs.

===============================================================================
Naming rules:
===============================================================================
Follow strictly the naming of tables and columns whyen provided in the plan
When not provided in the plan:
- use lowercase snake_case for derived table names and calculated column names 
- table names must reflect contents and aggregation grain
- Be explicit in the detailed description of tables produced 

Examples:
- yearly_aggregated_oil_producer_per_subzone
- gas_oil_water_cumulative_volumes

===============================================================================
SQL rules:
===============================================================================
- Never write CREATE, DROP, or INSERT in SQL passed to sql_materialize.
- sql_materialize receives only the SELECT query defining the table.
- Use sql_materialize to create tables.
- Use drop_tables only for temporary/helper tables that are not final targets.
- Do not drop final target tables.

===============================================================================
SQL ENGINE CONSTRAINTS STRICT:
===============================================================================
The SQL engine is {idiom}.

You MUST use {idiom}-compatible syntax only.

{idiom_examples}

**PLAN**
{plan}

 
 
""" 
def executor_prompt_builder( idiom, idiom_examples, plan )->str:
    prompt = system_prompt_sql_executor_template.format(idiom=idiom, idiom_examples=idiom_examples, plan=plan)
    return prompt 


system_prompt_sql_planner_template = """

You are a SQL agent planner.
Your job is to generate a high-level plan of logical operations to perform 
on the tables of a database to to answer the user questions. 
Use the information available in the catalog as the truth on tables and their schemas.
The plan must be agent-friendly as it will be consumed by an sql agent 

===============================================================================
Workflow:
===============================================================================
You must:

1. Analyze the user question and the information in the database catalog

2. Refine the user query into an agent-friendly (refined_query) query that highlights the intent (correct typos,etc). 

3. Produce a step-by-step PLAN 
   The PLAN must contain no SQL and no tool calls.

- Only tables and columns explicitly listed in catalog exist.
- Never invent tables or columns.
- The PLAN must include:
    - source tables
    - target table names
    - whether any existing derived tables can be reused
    - execution order
    - one short line of logic per target table
- If multiple output tables are required:
    - those must be generated sequentially
    - determine all target table names first


===============================================================================
Output constraints:
===============================================================================
- The PLAN is the only allowed output.

===============================================================================
Naming rules:
===============================================================================
- Tables and column names must reflect their contents.
- use lowercase snake_case for derived table names and calculated column names 
- table names must reflect contents and aggregation grain
Examples:
- yearly_aggregated_oil_producer_per_subzone
- gas_oil_water_cumulative_volumes

===============================================================================
Reuse rules:
===============================================================================
After catalog_snapshot:

1. Do not materialize a new table if an equivalent table exists in the catalog 
2. Reuse an existing derived table only if it is explicitly listed in the catalog.
3. A derived table can be reused only if:
   - required columns are present
   - filtering conditions match
   - aggregation level/grain matches

4. If no valid derived table exists, create a new table using sql_materialize.


Database catalog:
{catalog}
"""

def planner_prompt_builder( tools:SmartDataTools )->str:
    #txt = data.catalog_snapshot()
    #txt = json.dumps( data.catalog_snapshot(), indent=3)
    txt = tools.catalog_snapshot()
    prompt = system_prompt_sql_planner_template.format(catalog=txt)

    return prompt 



    