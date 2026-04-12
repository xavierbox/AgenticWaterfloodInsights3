
from pathlib import Path
from typing import Any, Dict
import json

from get_llm_model import *
import pandas as pd, numpy as np
import duckdb

import pprint 

class SmartData:
    def __init__(self, llm=None):
        self.con = duckdb.connect()
        self.tables = set()
        self.semantic = {}
        self.semantic_model = load_semantic_model()
        self.columns = {}
        self._llm = llm

    # -----------------------------
    # LLM PROPERTY
    # -----------------------------
    @property
    def llm(self):
        return self._llm

    @llm.setter
    def llm(self, model):
        self._llm = model

    # -----------------------------
    # CORE EXECUTION
    # -----------------------------
    def execute_query(self, sql: str):
        return self.con.execute(sql).fetchdf()

    # -----------------------------
    # INTERNAL: SANITIZE DATAFRAME
    # -----------------------------
    def _sanitize_df(self, df):
        import pandas as pd

        df = df.copy()

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

    # -----------------------------
    # TABLE REGISTRATION
    # -----------------------------
    def register_tables(self, tables: Dict[str, Any]):
        for name, df in tables.items():
            df = self._sanitize_df(df)
            self.con.register(name, df)
            self.tables.add(name)
            self.columns[name] = list(df.columns)

    def register_table(self, name: str, df):
        df = self._sanitize_df(df)
        self.con.register(name, df)
        self.tables.add(name)
        self.columns[name] = list(df.columns)

    # -----------------------------
    # SEMANTIC REGISTRATION
    # -----------------------------
    def register_semantic(self, name: str, description: str):
        if name not in self.tables:
            raise ValueError(f"Table '{name}' is not registered")
        self.semantic[name] = description

    # -----------------------------
    # SQL GENERATION
    # -----------------------------
    def generate_sql(self, user_query: str, **kwargs) -> str:
        if self._llm is None:
            raise ValueError("LLM is not set")

        context_lines = []
        for table in self.tables:
            desc = self.semantic.get(table, "")
            cols = self.columns.get(table, [])
            context_lines.append(
                f"Table: {table}\nDescription: {desc}\nColumns: {', '.join(cols)}"
            )

        context = "\n\n".join(context_lines)

        prompt = f"""
You are an expert SQL generator for DuckDB.

Available tables:
{context}

User request:
{user_query}

Generate a valid DuckDB SQL query only.
"""

        return self._llm(prompt, **kwargs)
    

llm = azure_llm_if()
print( llm )


inj = pd.read_csv("./datasets/IX5I_4P/injectors.csv")
inj['DATE'] = pd.to_datetime( inj['DATE'],dayfirst=True)
inj['DAY']   = inj['DATE'].dt.day
inj['MONTH'] = inj['DATE'].dt.month
inj['YEAR']  = inj['DATE'].dt.year
print( inj )

prompt = f"""
You are an expert SQL generator 
Generate a valid  SQL to answer user questions
"""

def run_agent(agent, messages):
    
    last_tool = None  
    for chunk in agent.stream(messages):
        for step, response in chunk.items():

            print(f"\n--- {step.upper()} ---")

            msg = response["messages"][-1]

            # MODEL STEP (may contain tool calls)
            if step == "model":
                if hasattr(msg, "content_blocks"):
                    for block in msg.content_blocks:

                        if block["type"] == "tool_call":
                            print("MODEL → TOOL CALL")
                            print("Tool:", block["name"])
                            print("Arguments:")
                            print(block["args"])
                            last_tool = block["name"]
                        elif block["type"] == "text":
                            print("MODEL TEXT:")
                            print(block["text"])
                else:
                    print(msg.content)

            # TOOL STEP (tool result)
            elif step == "tools":
                if hasattr(msg, "content_blocks"):
                    for block in msg.content_blocks:
                        print("TOOL RESULT:",block["type"], type(block))
                        
                        if 'catalog' not in last_tool:
                        
                            if block["type"] == "text":
                                try:
                                    parsed = json.loads(block["text"])
                                    pprint(parsed[0:100])
                                except Exception as e:
                                    print('*******error******')
                                    print(block["text"], e )
                            else:
                                print(block)
                                
                        else:
                            d = json.loads(block['text'])
                            print('catalog keys', d['tables'].keys())
                else:
                    print(msg.content)

            # FINAL OUTPUT
            else:
                print("OTHER STEP:")
                print(msg.content)

            
    return response 


user_query= "how many wells are there?"
agent = create_agent( model = llm,system_prompt=prompt )


messages = {"messages": [{"role": "user", "content": user_query}]}
run_agent(agent, messages)

print( prompt )