
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
import pandas as pd, io  
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
    p = """
    PRODUCER  current_produced_water_fraction  current_produced_oil_fraction  current_volume_liquid_produced  current_liquid_production_due_to_depletion  current_liquid_production_due_to_injection  current_liquid_production_due_to_pressure  pressure_coefficient  total_allocation  number_supporting_injectors  TAU  TAUP  LO
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
    return raw_data 


def get_default_results_intertpreter( )->ResultsInterpreterComponent:

    config = ResultsInterpreterConfig( promp_template=RESULTS_INTERPRETER_PROMPT_TEMPLATE)
    llm = get_llm() 
    
    BASE = Path(inspect.getfile(ResultsInterpreterComponent)).resolve().parent

    semantic_catalog_file = BASE /  "semantic_catalog.json"
    semantic_context_file = BASE /  "semantic_context.json"
    semantic_catalog = catalog_from_file(semantic_catalog_file)
    semantic_context = context_from_file(semantic_context_file, context_type=ResultsInterpreterSemanticContext)

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



data = load_interpreter_data_mock()
interpreter = get_default_results_intertpreter()
interpreter.update_data( data )

query = golden_questions[-1]
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
