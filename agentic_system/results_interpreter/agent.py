
import sys

from langchain.agents import create_agent

from agentic_system.common.semantic_models import SemanticCatalog 
sys.path.append('../../')
sys.path.append('../')
sys.path.append('./')

from dataclasses import dataclass
import sys, pprint, pandas as pd , os, json, re, plotly.io as pio 
from pathlib import Path
from typing_extensions import Self
from typing import Any, cast

from agentic_system.common.get_llm import azure_llm_if as get_llm
from agentic_system.results_interpreter.prompts import RESULTS_INTERPRETER_PROMPT_TEMPLATE
from agentic_system.common.base_domain_tools import BaseDataComponent, BaseDomainTools


class ResultsInterpreterData( BaseDataComponent ):

    #def __init__(self):
    #    super().__init__()
           
    #def set_data(self, data:Any, metadata:Any|None = None ) -> None:
    #    """
    #    Set or replace the RAW domain data.
    #    """
    #    self._raw_data = data
    #    self._metadata = metadata

    
    def fetch_data_item_and_context( self, dataset_name: str )->str: 
        return 'dummy' 

    def record_response(self, question:str, response:str )->str:
        return 'dummy' 
    
    def interpret_data_item( self, question, dataset_name )->str:
        return  'dummy' 

    def get_simulation_config( self ):
        """
        Retrieves the simulation configuration file as a JSON string and a description of 
        the parameters defined there. This file contains information about all the parameters used in the simulation.
        """
        pass 

    def get_simulation_logs( self ):
        """
        Retrieves the simulation logs. These contain information on:
        - Errors in the modelling of specific wells
        - Reasons why specific wells were not modelled 
        - Other logs produced by the simulation engine 
        """
        pass 


    #def get_injector_performance_metrics():
    #    pass 

    #def get_injector_performance_metrics():
    #       pass 
          
class ResultsInterpreterTools(BaseDomainTools[ResultsInterpreterData]):

    def _no_generate_summary(self):
        """Generates a summary of simulation results."""
        return "all results were produced, status = 200"

    @property
    def data(self) -> ResultsInterpreterData:
        return self.data_component

    @property
    def raw_data(self) -> Any:
        return self.data_component.raw_data

    def get_connectivity_table(
        self,
        producer_names: list[str] | None = None,
        injector_names: list[str] | None = None,
    ) -> pd.DataFrame:
        """
        Return CRM injector-producer connectivity results.

        Each row represents one modeled injector-producer pair.

        Important column semantics:
        - GAIN:
          Fraction of water injected in an injector that is recovered as
          liquid production in the producer. GAIN is injector-centric.
        - PALLOCATION:
          Fraction of the producer's total liquid production attributed to
          injection from that specific injector. PALLOCATION is producer-centric.
        - GAIN_CLASS:
          Classification of GAIN. Gains below 0.05 are negligible.

        Parameters
        ----------
        producer_names:
            Optional list of producer well names to keep.

            If None:
                Do not filter by producer. Producers of any name may be returned.

            If provided:
                Return only rows whose PRODUCER value is one of the names
                in this list.

            Example:
                producer_names=["P1", "P2"]
                returns connectivity rows only for producers P1 and P2.

        injector_names:
            Optional list of injector well names to keep.

            If None:
                Do not filter by injector. Injectors of any name may be returned.

            If provided:
                Return only rows whose INJECTOR value is one of the names
                in this list.

            Example:
                injector_names=["I1"]
                returns connectivity rows only for injector I1.

        Filtering behavior
        ------------------
        If both producer_names and injector_names are provided, BOTH filters
        are applied. A row is returned only if its producer is in
        producer_names AND its injector is in injector_names.

        These parameters only filter rows by well name. They do not rank wells,
        apply GAIN thresholds, or change the meaning of the CRM results.
        """

        df = self.raw_data["connectivity_table"]

        if producer_names is not None:
            df = df[df["PRODUCER"].isin(producer_names)]

        if injector_names is not None:
            df = df[df["INJECTOR"].isin(injector_names)]

        return df.to_dict(orient='records')# df.copy()

    def get_simulation_quality_table(
        self,
        producer_names: list[str] | None = None,
    ) -> dict:#pd.DataFrame:
        """
        Return producer-level CRM history-match quality information.

        Each row represents the simulation quality for one producer.

        Parameters
        ----------
        producer_names:
            Optional list of producer well names to keep.

            If None:
                Return quality information for all producers.

            If provided:
                Return only rows whose PRODUCER value is one of the names
                in this list.

            Example:
                producer_names=["P1", "P3"]
                returns model-quality information only for P1 and P3.

        This parameter only filters producers by name. It does not filter by
        quality score, quality class, correlation, or any other quality metric.
        """

        df = self.raw_data["simulation_quality_table"]

        if producer_names is not None:
            df = df[df["PRODUCER"].isin(producer_names)]

        return df.to_dict(orient='records')#copy()

    def get_producer_model_table(
        self,
        producer_names: list[str] | None = None,
    ) -> dict:#pd.DataFrame:
        """
        Return producer-level current production and modeled-support information.

        Each row represents one producer.

        The table contains information such as:
        - current produced water and oil fractions
        - latest observed liquid production
        - current liquid production attributed to depletion
        - current liquid production attributed to injection
        - current liquid production attributed to pressure changes
        - pressure coefficient
        - total producer allocation from injectors
        - number of supporting injectors

        Parameters
        ----------
        producer_names:
            Optional list of producer well names to keep.

            If None:
                Return producer-model information for all producers.

            If provided:
                Return only rows whose NAME value is one of the producer names
                in this list.

            Example:
                producer_names=["P2"]
                returns the producer-model row for P2 only.

        This parameter only filters rows by producer name. It does not filter
        based on support level, production volume, water fraction, allocation,
        or any other metric.

        Use current_volume_liquid_produced together with current_produced_oil_fraction
        to estimate current oil production for a producer.

        """

        df = self.raw_data["producer_model_table"]

        if producer_names is not None:
            try:
                df = df[df["NAME"].isin(producer_names)]
            except:
                pass
            try:
                df = df[df["PRODUCER"].isin(producer_names)]
            except:
                pass
                        

        return df.to_dict(orient='records')# df.copy()

    def get_injector_summary(
        self,
        injector_names: list[str] | None = None,
    ) -> pd.DataFrame:
        """
        Use this tool for injector utility/support questions.

        Do NOT use this tool alone to estimate impact on oil production, because utility
        is based on GAIN and does not account for producer liquid rate or oil fraction.


        Injector utility is currently defined as the sum of GAIN across all
        modeled producer connections for that injector.

        Gains below 0.05 are considered negligible and do not count toward
        the number of supported producers.

        Parameters
        ----------
        injector_names:
            Optional list of injector well names to include in the summary.

            If None:
                Compute the summary for all injectors.

            If provided:
                Compute the summary only for injectors whose names appear in
                this list.

            Example:
                injector_names=["I1", "I3"]
                returns summary rows only for I1 and I3.

        This parameter selects which injectors are summarized. It does not
        specify producers, ranking order, GAIN thresholds, or a top-N limit.

        Returns
        -------
        pd.DataFrame
            One row per injector, including:
            - INJECTOR
            - UTILITY: sum of GAIN across producers
            - NUMBER_SUPPORTED_PRODUCERS: count of producers with GAIN >= 0.05
            - MAX_GAIN: largest individual GAIN for that injector
            - STRONGEST_CONNECTED_PRODUCER: producer associated with MAX_GAIN
        """

        df = self.raw_data["connectivity_table"]

        if injector_names is not None:
            df = df[df["INJECTOR"].isin(injector_names)]

        if df.empty:
            return pd.DataFrame(
                columns=[
                    "INJECTOR",
                    "UTILITY",
                    "NUMBER_SUPPORTED_PRODUCERS",
                    "MAX_GAIN",
                    "STRONGEST_CONNECTED_PRODUCER",
                ]
            )

        summary_rows = []

        for injector, group in df.groupby("INJECTOR", sort=False):

            strongest_idx = group["GAIN"].idxmax()
            strongest_row = group.loc[strongest_idx]

            summary_rows.append(
                {
                    "INJECTOR": injector,
                    "UTILITY": group["GAIN"].sum(),
                    "NUMBER_SUPPORTED_PRODUCERS": (
                        group.loc[group["GAIN"] >= 0.05, "PRODUCER"].nunique()
                    ),
                    "MAX_GAIN": strongest_row["GAIN"],
                    "STRONGEST_CONNECTED_PRODUCER": strongest_row["PRODUCER"],
                }
            )

        df= pd.DataFrame(summary_rows).sort_values("UTILITY", ascending=False).reset_index(drop=True)
        return df.to_dict( orient = 'records' )
    
    def excecute_sql(self, sql):
        """
        Execute a sql table to retrieve info from one or more tables.
        You can use this tool for aggregations, filtering, joints and any operation supported by 
        sql. 

        """
        print("sql", sql )
        return "sql execution failed, use another tool."


@dataclass 
class ResultsInterpreterConfig( ):
    promp_template: str | None = RESULTS_INTERPRETER_PROMPT_TEMPLATE 
    use_memory : bool = False 
    structured_output = Any = None 


class ResultsInterpreterComponent:
    """
    Specialist component for interpreting CRM simulation results.

    Combines simulation data, domain tools, semantic metadata, CRM interpretation
    knowledge, and an LLM to answer questions about model results.

    Typical responsibilities include:
    - comparing injectors, producers, and injector-producer relationships;
    - assessing injector utility and producer support;
    - interpreting GAIN, PALLOCATION, TAU, TAUP, LO, and pressure effects;
    - identifying important rankings, anomalies, and patterns;
    - interpreting production contributions from injection, depletion, and pressure;
    - qualifying conclusions using simulation-quality information;
    - producing synthesized summaries of simulation results.

    The component owns a ResultsInterpreterData instance and binds its domain tools
    to the same data source. Data and metadata can be updated without recreating
    the component.

    Hypothetical scenario evaluation, such as shutting wells or changing injection
    rates, is outside the scope of this component.

    Parameters
    ----------
    llm
        Language model used for interpretation and response generation.

    config : ResultsInterpreterConfig, optional
        Component configuration.

    data : ResultsInterpreterData, optional
        Simulation result data and semantic metadata.

    tools : ResultsInterpreterTools, optional
        Domain tools used to retrieve and analyze simulation results.
    """

    def __init__(self, 
                 llm, 
                 config:ResultsInterpreterConfig|None = None, 
                 data:ResultsInterpreterData|None = None, 
                 tools:ResultsInterpreterTools|None = None ):

        self.llm = llm 
        self.config = config or ResultsInterpreterConfig()
        self.data_component = data or  ResultsInterpreterData()
        self.domain_tools = tools or ResultsInterpreterTools()
        self.domain_tools.set_data_component( self.data_component )
        self.agent = None 

    @property
    def description(self) -> str:
        """Return the class docstring."""
        return self.__class__.__doc__ or ""

    def update_metadata( self, metadata:Any|None = None)->Self:
        self.data_component.update_metadata( metadata )
        return self 

    def update_data( self, raw_data:Any|None = None)->Self:
        self.data_component.update_data( raw_data )
        return self  
   
    def set_data(self, raw_data:Any, metadata:Any|None = None)->Self:
        self.data_component.set_data(raw_data, metadata)
        return self

    def _build_system_prompt(self,
        #template: str,
        #semantic_catalog: SemanticCatalog,
        #semantic_context: ResultsInterpreterSemanticContext,
    ) -> str:

        def format_list(items: list[str]) -> str:
            if not items:
                return "- None"
            return "\n".join(f"- {item}" for item in items)

        def format_table_catalog(catalog: SemanticCatalog) -> str:
            sections = []

            for table in catalog.tables:
                lines = [
                    f"## {table.name}",
                    table.description,
                    "",
                    "Columns:",
                ]

                for column in table.columns:
                    description = column.description or ""
                    lines.append(
                        f"- {column.name} ({column.data_type}): {description}"
                    )

                sections.append("\n".join(lines))

            return "\n\n".join(sections)

        template = self.config.promp_template 
        semantic_catalog = self.data_component.metadata['semantic_catalog'] # type: ignore
        semantic_context = self.data_component.metadata['semantic_context'] # type: ignore

        #semantic_catalog = self.data_component.metadata[]

        return template.format( # type: ignore
            definitions=format_list(
                semantic_context.definitions
            ),
            business_rules=format_list(
                semantic_context.business_rules
            ),
            domain_knowledge=format_list(
                semantic_context.domain_knowledge
            ),
            interpretation_guidelines=format_list(
                semantic_context.interpretation_guidelines
            ),
            table_catalog=format_table_catalog(
                semantic_catalog
            ),
        )

    def _build_agent(self):

        self.agent  = None 
        if not self.config.structured_output and  not self.config.use_memory:
            prompt = self._build_system_prompt()
            agent_tools = self.domain_tools.get_agent_tools()
            agent = create_agent(
                model=self.llm,
                system_prompt=prompt,
                tools=agent_tools
            )
            self.agent = agent 
            return agent 

        else:
            raise NotImplementedError("Only no-memory and no structured-output in this version")
    

    def run( self, query:str, background:str|None = None )->Any:

        if not self.agent:
            self._build_agent()     

        agent = self.agent 

        user_message = query
        if background:
            user_message = (
                f"BACKGROUND INFORMATION:\n"
                f"{background}\n\n"
                f"USER QUESTION:\n"
                f"{query}"
            )

        if agent is None:
            raise ValueError("Calling run with an un-initialized agent")

        response = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_message,
                    }
                ]
            }
        )

        if self.config.structured_output:
            return response['structured_response']

        raw_content = response['messages'][-1].content 
        fixed_content = raw_content.replace(r'\[', '$$').replace(r'\]', '$$')

        return fixed_content
    


