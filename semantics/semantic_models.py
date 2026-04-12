from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class ColumnCard(BaseModel):
    name: str = Field(description = 'column name')
    data_type: str 
    description: str = Field( description = "meaning of the data in the column")
    #is_categorical: Optional[bool] = Field(description='True if the column contains categorical values and False otherwise')
    business_rules: List[str] = Field(default_factory=list, description="Actionable business rules for this column, one rule per item.")

class Relationship(BaseModel):
    tables_involved: List[str] = Field(description="Tables participating in the relationship, typically [left_table, right_table].")
    join_type: Literal["inner", "left", "right", "full", "cross"] = Field(
        description="Recommended SQL join type for combining the tables."
    )
    join_condition: Optional[str] = Field(
        default=None,
        description=("SQL join condition, for example \"injectors.NAME = locations.NAME AND locations.WELL_TYPE = 'Injector'\". "))
    description: Optional[str] = Field(default=None,description="Business meaning of this relationship.")

class SQLExample(BaseModel):
    name: str = Field(description="Short name for the SQL example.")
    purpose: str = Field(description="What this query demonstrates or answers.")
    sql: str = Field(description="Executable SQL snippet.")
    notes: Optional[str] = Field(
        default=None,
        description="Optional assumptions, caveats, or interpretation guidance."
    )

class TableCard(BaseModel):
    name : str = Field( description = "table name")
    description : str = Field( description = "brief description of table contents")
    columns: List[ColumnCard] = Field(
        default_factory=list,
        description="Semantic metadata for columns in this table."
    )
    relationships: List[Relationship] = Field(
        default_factory=list,
        description="Relationships from this table to other tables."
    )
    sql_examples: List[SQLExample] = Field(
        default_factory=list,
        description="Representative SQL queries relevant to this table."
    )

class QueryCatalogItem(BaseModel):
    id: str = Field(description="Stable identifier for the query pattern.")
    question: str = Field(description="Natural-language intent answered by the query.")
    tables: List[str] = Field(default_factory=list, description="Tables used by the query.")
    sql: str = Field(description="Executable SQL query.")
    tags: List[str] = Field(default_factory=list, description="Search tags for retrieval/routing.")
    notes: Optional[str] = Field(default=None, description="Optional caveats or engine-specific guidance.")


class SemanticCatalog(BaseModel):
    semantic_constraints: List[str] = Field(default_factory=list, description="Global semantic constraints for the domain.")
    tables: List[TableCard] = Field(default_factory=list, description="Table metadata cards.")
    query_catalog: List[QueryCatalogItem] = Field(default_factory=list, description="Reusable SQL query templates.")

class SQLIdiom(BaseModel):
    topic: str = Field(description="Topic area for the SQL idiom.")
    rule: str = Field(description="Recommended SQL idiomatic rule.")
    examples: List[str] = Field(default_factory=list, description="Short SQL snippets that illustrate the rule.")
    notes: Optional[str] = Field(default=None, description="Optional caveats for the SQL dialect.")

class SQLIdiomsCatalog(BaseModel):
    dialect: str = Field(description="SQL dialect the idioms target.")
    idioms: List[SQLIdiom] = Field(default_factory=list, description="Dialect-specific SQL idioms.")

class SemanticContext(BaseModel):
    definitions: List[str] = Field(default_factory=list, description="Canonical definitions for domain terms.")
    business_rules: List[str] = Field(default_factory=list, description="Business-level rules and policies.")
    domain_knowledge: List[str] = Field(default_factory=list, description="General domain guidance and assumptions.")
