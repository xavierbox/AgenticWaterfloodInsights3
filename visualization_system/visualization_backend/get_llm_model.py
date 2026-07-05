import os 
import os 

#print( os.environ['AZURE_OPENAI_API_KEY'])





import uuid,pandas as pd, numpy as np, os,datetime,json,pprint,copy, pickle 
import json,pprint, time 
from pydantic import BaseModel, Field
from uuid import uuid4
import uuid,pandas as pd, numpy as np, os,datetime,json,pprint,copy, pickle 
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables import Runnable
 
from langchain.tools import tool, ToolRuntime
from langgraph.runtime import get_runtime 
from langchain.agents import create_agent
from langchain_core.runnables import RunnableLambda


from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables import Runnable
#from dataiku import pandasutils as pdu
 
from langchain.tools import tool, ToolRuntime
from langgraph.runtime import get_runtime 
from langchain.agents import create_agent
from langchain_core.runnables import RunnableLambda
import os 
from langchain_openai import AzureChatOpenAI
print('imported')


def azure_llm_if():

    endpoint = os.environ['AZURE_OPENAI_ENDPOINT']
    #model_name = "gpt-4o"
    model_name = "gpt-4.1"
    
    deployment = "gpt-4"

    #model_name = "gpt-4o-mini"
    #deployment = "gpt-4o-mini"

    api_version = "2024-12-01-preview"
    
    print('zero temp, seed 42, top_p = 1')
    llm = AzureChatOpenAI(
        azure_deployment=deployment,
        model=model_name,
        temperature=0.0,
        top_p=1.0,
        seed=42,
        azure_endpoint=endpoint,
        api_key=os.environ['AZURE_OPENAI_API_KEY'], # type: ignore
        api_version=api_version,
    )
     
    return llm 

