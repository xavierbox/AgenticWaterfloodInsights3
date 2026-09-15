
#from dataclasses import dataclass
#from typing import Any
#from pydantic import BaseModel
#from typing_extensions  import Self
#from agentic_system.results_interpreter.agent import ResultsInterpreterComponent, ResultsInterpreterConfig, ResultsInterpreterTools, ResultsInterpreterData # type: ignore
import sys 
sys.path.append("./")
sys.path.append("../")
sys.path.append("../../")
import inspect
import pandas as pd, io, numpy as np   
from pathlib import Path 
from langchain.agents import create_agent
from IPython.display import display, Markdown


from agentic_system.common.get_llm import azure_llm_if as get_llm  
from agentic_system.common.semantic_models import SemanticCatalog, catalog_from_file,context_from_file

from agentic_system.results_interpreter.semantic_models import ResultsInterpreterSemanticContext
from agentic_system.results_interpreter.agent import ResultsInterpreterComponent,ResultsInterpreterData, ResultsInterpreterTools, ResultsInterpreterConfig
from agentic_system.results_interpreter.prompts import RESULTS_INTERPRETER_PROMPT_TEMPLATE 

golden_questions = [
    "Which injector has the highest utility, and why?",
    "Which producer is the best supported by injection, and what evidence supports that conclusion?",
    "Which producers appear poorly supported by injection, and how reliable is that conclusion given their history-match quality?",
    "Summarize the quality of the CRM models and identify the producers whose results should be interpreted with caution.",
    "Is there evidence of potential channeling or thief-zone behavior? Identify the most suspicious injector-producer relationships and explain why.",
    "Is there evidence of possible aquifer or external reservoir support? Which producers are the strongest candidates and why?",
    "Which injectors appear poorly utilized or potentially stranded, and what evidence supports that interpretation?",
    "Which producers are primarily injection-driven, depletion-driven, or pressure-driven?",
    "Rank the injectors by utility and explain the main differences between the highest- and lowest-ranked injectors.",
    "Give me an overall summary of the CRM results, focusing on injector support, poorly supported producers, important connectivity patterns, potential channeling, production drivers, and model quality.",
]




def generate_model_table(producer_model_df, historical_df):
    """
    producer_model_df:
        Dated producer production/support table.

    historical_df:
        Injector-producer CRM results containing GAIN, PRODUCTIVITY,
        TAU, TAUP, and LO.
    """
    production = producer_model_df.copy()
    crm = historical_df.copy()

    production.columns = production.columns.str.strip()
    crm.columns = crm.columns.str.strip()

    production["DATE"] = pd.to_datetime(
        production["DATE"],
        dayfirst=True,
        errors="coerce",
    )

    # Latest available record for each producer.
    current = (
        production
        .dropna(subset=["DATE"])
        .sort_values(["PRODUCER", "DATE"])
        .drop_duplicates(subset="PRODUCER", keep="last")
        .copy()
    )

    production_numeric_columns = [
        "LIQUID_VOLUME",
        "WATER_VOLUME",
        "OIL_VOLUME",
        "PRIMARY_SUPPORT",
        "INJECTION_SUPPORT",
        "PRESSURE_DEPLETION",
    ]

    for column in production_numeric_columns:
        current[column] = pd.to_numeric(
            current[column],
            errors="coerce",
        ).fillna(0.0)

    crm_numeric_columns = [
        "GAIN",
        "PRODUCTIVITY",
        "TAU",
        "TAUP",
        "LO",
    ]

    for column in crm_numeric_columns:
        crm[column] = pd.to_numeric(
            crm[column],
            errors="coerce",
        )

    # Remove accidental duplicate injector-producer connections.
    connections = crm.drop_duplicates(
        subset=["INJECTOR", "PRODUCER"],
        keep="last",
    )

    # TAU, TAUP, PRODUCTIVITY, and LO are repeated for each producer.
    crm_summary = (
        connections
        .groupby("PRODUCER", as_index=False)
        .agg(
            TAU=("TAU", "first"),
            TAUP=("TAUP", "first"),
            LO=("LO", "first"),
            pressure_coefficient=("PRODUCTIVITY", "first"),
            number_supporting_injectors=(
                "GAIN",
                lambda gain: int((gain.fillna(0.0) >= 0.05).sum()),
            ),
        )
    )

    result = current.merge(
        crm_summary,
        on="PRODUCER",
        how="left",
        validate="one_to_one",
    )

    liquid = result["LIQUID_VOLUME"].replace(0.0, np.nan)

    result["current_produced_water_fraction"] = (
        result["WATER_VOLUME"] / liquid
    ).fillna(0.0)

    result["current_produced_oil_fraction"] = (
        result["OIL_VOLUME"] / liquid
    ).fillna(0.0)

    result["current_volume_liquid_produced"] = (
        result["LIQUID_VOLUME"]
    )

    result["current_liquid_production_due_to_depletion"] = (
        result["PRIMARY_SUPPORT"]
    )

    result["current_liquid_production_due_to_injection"] = (
        result["INJECTION_SUPPORT"]
    )

    result["current_liquid_production_due_to_pressure"] = (
        result["PRESSURE_DEPLETION"]
    )

    result["total_allocation"] = (
        result["INJECTION_SUPPORT"] / liquid
    ).fillna(0.0)

    result["number_supporting_injectors"] = (
        result["number_supporting_injectors"]
        .fillna(0)
        .astype(int)
    )

    #result = result.rename(columns={"PRODUCER": "name"})

    output_columns = [
        "PRODUCER",
        "current_produced_water_fraction",
        "current_produced_oil_fraction",
        "current_volume_liquid_produced",
        "current_liquid_production_due_to_depletion",
        "current_liquid_production_due_to_injection",
        "current_liquid_production_due_to_pressure",
        "pressure_coefficient",
        "total_allocation",
        "number_supporting_injectors",
        "TAU",
        "TAUP",
        "LO",
    ]

    return (
        result[output_columns]
        .sort_values("PRODUCER")
        .reset_index(drop=True)
    )

def load_interpreter_data_mock():

    c = """
    INJECTOR	PRODUCER PALLOCATION	GAIN	GAIN_CLASS  
    0	I1	P1	0.508456	0.38   meaningful
    1	I2	P1	0.432001	0.30   meaningful
    2	I3	P1	0.007279	0.001  negligible
    3	I1	P2	0.463442	0.4    meaningful
    4	I3	P2	0.226982	0.15   meaningful
    """
    q="""	PRODUCER	CORRELATION	VARIANCE_RATIO	QUALITY_SCORE	QUALITY_CLASS
    0	P1	0.802377	0.929430	0.864767	good
    1	P2	0.929300	1.324738	0.886701	good
    2	P3	0.754035	1.020565	0.833949	good
    3	P4	0.925126	1.205418	0.917859	good
    """
    p = """PRODUCER  current_produced_water_fraction current_produced_oil_fraction  current_liquid_production  current_liquid_production_due_to_depletion current_liquid_production_due_to_injection  current_liquid_production_due_to_pressure pressure_coefficient  total_allocation  number_supporting_injectors  TAU  TAUP  LO 
    0 P1 0.72 0.28 1200.0 420.0 660.0 120.0 0.18 0.55 2 4.5 120.0 0.35
    1 P2 0.35 0.65 950.0 570.0 285.0 95.0 0.10 0.30 2 12.0 240.0 0.60
    2 P3 0.88 0.12 700.0 140.0 490.0 70.0 0.22 0.70 1 1.4 450.0 0.20
    3 P4 0.20 0.80 1500.0 1050.0 300.0 150.0 0.08 0.20 0 28.0 800.0 0.75
    """

    # Read the string into a DataFrame
    # 'sep=r"\s+"' handles any whitespace (tabs or multiple spaces)
    # 'index_col=0' uses the first column (0, 1, 2...) as the row index
    connectivity_table  = pd.read_csv(io.StringIO(c), sep=r"\s+", index_col=0)
    simulation_quality_table = pd.read_csv(io.StringIO(q), sep=r"\s+", index_col=0)
    producer_model_table = pd.read_csv(io.StringIO(p), sep=r"\s+", index_col=0)

    raw_data = {
        "connectivity_table": connectivity_table,
        "simulation_quality_table": simulation_quality_table,
        "producer_model_table": producer_model_table,
    }

    print("Data keys", raw_data.keys() )


    print("Data produced")
    print( raw_data['connectivity_table'])
    print( raw_data['simulation_quality_table'])
    print( raw_data['producer_model_table'].T)

            

    return raw_data 

def load_sector1_real_data():
    import numpy as np 

    def score_gain( value ):
        if value > 0.9: return 'very high'
        if value > 0.7: return 'high'
        if value < 0.1: return 'low'
        if value > 0.05: return 'negligible'
        return "moderate"        
    
    def score_class( value ):

        if value > 0.9: return 'excellent'
        if value > 0.8: return 'good'
        if value < 0.4: return 'poor'
        if value > 0.2: return 'very poor'
        return "moderate"
                
 

    parent_dir = Path(__file__).parent.parent / "datasets/BalancedModelExample/ExampleSector1"
    #print(f"Parent Path: {parent_dir.resolve()}")

    path = parent_dir/"historical_liquid_crm.csv"
    historical_liquid_crm = pd.read_csv(path)
    historical_liquid_crm=historical_liquid_crm[['PRODUCER','CORRELATION','QUALITY_SCORE']]#,QUALITY_CLASS']
    historical_liquid_crm['QUALITY_CLASS'] = historical_liquid_crm['QUALITY_SCORE'].apply( score_class) 
    #print( historical_liquid_crm.sample(4))

    path = parent_dir/"historical_liquid_crm.csv"
    liquid_crm_params = pd.read_csv(path)[['INJECTOR','PRODUCER','GAIN']]
    #liquid_crm_params['GAIN'] = liquid_crm_params['ALLOCATION']

    noise = np.random.normal(0, 0.005, size=len(liquid_crm_params)) 
    liquid_crm_params['PALLOCATION'] = liquid_crm_params['GAIN']*(1+noise)
    liquid_crm_params['GAIN_CLASS'] = liquid_crm_params['GAIN'].apply( score_gain) 
    #liquid_crm_params.drop( ['ALLOCATION'], axis = 1, inplace=True )
    #print(liquid_crm_params)


    target = 1.0 - 1e-9
    df = liquid_crm_params
    allocation_sum = df.groupby("PRODUCER")["PALLOCATION"].transform("sum")

    scale_factor = np.where(
        allocation_sum >= 1.0,
        target / allocation_sum,
        1.0,
    )

    df["PALLOCATION"] = df["PALLOCATION"] * scale_factor





    
    path = parent_dir/"producer_model.csv"
    producer_model_df = pd.read_csv(path)
    path = parent_dir/"historical_liquid_crm.csv"
    historical_df = pd.read_csv(path)


    #print(100*'+')
    #print( historical_df )
    #print(producer_model_df)
    #print()


    p_model = generate_model_table(producer_model_df, historical_df)
    #print('****************')
    #print( p_model )
    #print('****************')
    #current_produced_water_fraction  
    #current_produced_oil_fraction  
    #current_volume_liquid_produced  
    #current_liquid_production_due_to_depletion  
    #current_liquid_production_due_to_injection  
    #current_liquid_production_due_to_pressure  
    #pressure_coefficient  
    #total_allocation  
    #number_supporting_injectors  


    #DATE,LIQUID_VOLUME_sim,CUM_WATER_INJECTED_sim,LIQUID_VOLUME,PRIMARY_SUPPORT,PRESSURE_DEPLETION,ACTIVITY,WATER_VOLUME,OIL_VOLUME,INJECTION_SUPPORT,NAME,TRAIN,ID,SUBZONE
    #producer_model['current_volume_liquid_produced']=producer_model['LIQUID_VOLUME']
     
    

    # Read the string into a DataFrame
    # 'sep=r"\s+"' handles any whitespace (tabs or multiple spaces)
    # 'index_col=0' uses the first column (0, 1, 2...) as the row index
    #connectivity_table  = pd.read_csv(io.StringIO(c), sep=r"\s+", index_col=0)
    #simulation_quality_table = pd.read_csv(io.StringIO(q), sep=r"\s+", index_col=0)
    #producer_model_table = pd.read_csv(io.StringIO(p), sep=r"\s+", index_col=0)

    raw_data = {
        "connectivity_table": liquid_crm_params,
        "simulation_quality_table": historical_liquid_crm,
        "producer_model_table": p_model
    }



    print(100*'*')
    print(raw_data["connectivity_table"].head(5)) 
    print(raw_data["simulation_quality_table"].head(5)) 
    print(raw_data["producer_model_table"].T) 
    print(100*'*')
        
    return raw_data


    #print("Data keys", raw_data.keys() )
    #return raw_data 

def get_default_results_intertpreter( )->ResultsInterpreterComponent:

    config = ResultsInterpreterConfig( promp_template=RESULTS_INTERPRETER_PROMPT_TEMPLATE)
    llm = get_llm() 
    
    BASE = Path(inspect.getfile(ResultsInterpreterComponent)).resolve().parent

    semantic_catalog_file = BASE /  "semantic_catalog.json"
    semantic_context_file = BASE /  "semantic_context.json"
    semantic_catalog = catalog_from_file(semantic_catalog_file)
    semantic_context = context_from_file(semantic_context_file, context_type=ResultsInterpreterSemanticContext)

    #print(semantic_catalog )
    #print()


    print("Catalog keys ")
    table_names = [ t.name for t in semantic_catalog.tables ]
    print( table_names )

    data_component = ResultsInterpreterData()
    data_component.update_metadata( {
        'semantic_catalog':semantic_catalog,
        'semantic_context':semantic_context
    }) 
    domain_tools   = ResultsInterpreterTools(llm=llm) 
    #domain_tools.set_data_component( data_component )

    return ResultsInterpreterComponent(
        llm, 
        config,
        data_component,domain_tools
        )


data = load_sector1_real_data()
#data = load_interpreter_data_mock()

interpreter = get_default_results_intertpreter()
interpreter.update_data( data )

query = golden_questions[-1]

other_queries = [
"""Give me summary but focus on:
1. Identify and list inconsistencies if any
2. Rank the producers accoring to how well they are supported but always indicate how reliable is 
such rank for each producer given the history match quality
3. Are there producers that arent supported at all?
4. Any evidence of chanelling?
5. Which producer are mainly producing by depletion.
6. Are all the injectors balanced?
7. Was BHP used? 

""",

"""Which injectors can I shut while affecting the less possible the amount of oil produced? 
Generate a table with the injector names, the amount of oil attributable to each in percent terms 
and the amount of water (percent) that they inject
""",

"""compute the oil attributable to each injector and explain the math""",  

"make a table of injector name, % water injected of the total, % of oil pruced total due to this injector",

"""Pick a injector at random, print its name and then tell me the utility or it, the supported producers, 
with the gain and the fraction of oil in each of those producers.
Tell me also the oil attributable to that injector injection
Present the results in tables
""",

"""I want to find some injectors to shut-in. 
Rank the injectors by utility. What can you say about those injectors?
Is there anything interesting in these results that could be an optimization opportunity?
""",

"""Rank the producers accordintg to their utility. 
Then for the one with the highest utility, find the supporting injectors. """
]

query = """Rank the producers accordintg to their utility. 
Then for the first 4 with the highest utility, find the supporting injectors and show the history match 
quality together with the amount of liquid produced and the watercut
"""

query = "Find optimization opportunities. Analyze the data before answering. Provide details on how you get to your answer"

print( query )
response = interpreter.run( query )

from rich.console import Console
from rich.markdown import Markdown
console = Console()
console.print(Markdown(response))
with open("report.md", "w", encoding="utf-8") as file:
    file.write(response)
print("Markdown file saved successfully as 'report.md'!")
print()
