
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

        prompt = f"""You are an expert SQL generator for DuckDB.

        Available tables:
        {context}

        User request:
        {user_query}

        Generate a valid DuckDB SQL query only.
        """
        return self._llm(prompt, **kwargs)

    # -----------------------------
    # SQL GENERATION
    # -----------------------------
    def generate_sql_baseline(self, user_query: str, **kwargs) -> str:
        if self._llm is None:
            raise ValueError("LLM is not set")

        context_lines = []
        for table in self.tables:
            context_lines.append(f"Table: {table}\nDescription: {desc}\nColumns: {', '.join(cols)}")

        context = "\n\n".join(context_lines)

        prompt = f"""You are an expert SQL generator for DuckDB.

Available tables:
{context}

User request:
{user_query}

Generate a valid DuckDB SQL query only.
"""
        return self._llm(prompt, **kwargs)


inj = pd.read_csv("./datasets/IX5I_4P/injectors.csv")
inj['DATE'] = pd.to_datetime( inj['DATE'],dayfirst=True)
inj['DAY']   = inj['DATE'].dt.day
inj['MONTH'] = inj['DATE'].dt.month
inj['YEAR']  = inj['DATE'].dt.year
print( inj.sample(3))


llm = azure_llm_if()
print( llm )

data = SmartData(llm=llm)
data.register_table("injectors", inj)


#generate_sql_baseline('How many injectors are there?')

inj.describe()
