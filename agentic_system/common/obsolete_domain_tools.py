from __future__ import annotations

from typing import Dict, List, Tuple, Optional, Any 
from langchain_core.tools import StructuredTool, Tool
from typing import Iterable
 
import inspect

class obsoleteDomainToolkit:

    def __init__(self ):
        pass

    def get_tools(self):#, include_planning_tools: bool = False):
        print("getting some tools here ")
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

