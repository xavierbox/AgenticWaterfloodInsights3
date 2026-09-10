import inspect

from langchain_core.tools import StructuredTool

from typing import Generic, TypeVar

from abc import ABC, abstractmethod
from typing import Any
import pandas  as pd 
from typing_extensions import Self


class BaseDataComponent(ABC):
    """
    Base class for stateful domain data components.

    Concrete implementations define how raw domain data is stored
    and exposed to the rest of the system.
    """

    def __init__(self):
        self._raw_data = None
        self._metadata = None

    def set_data(self, data:Any, metadata:Any|None = None ) -> None:
        """
        Set or replace the RAW domain data.
        """
        self._raw_data = data
        self._metadata = metadata
        
        

    @property
    def raw_data(self) -> Any:
        self._check_if_data()
        return self._raw_data

    @property
    def metadata(self) -> Any | None:
        return self._metadata
    

    
    def set_raw_data(self, data:Any, metadata:Any|None = None ) -> None:
        """
        Set or replace the RAW domain data.
        """
        return self.set_data(data, metadata)



    def _check_if_data(self) -> None:
        """
        Raise an error if data has not been set.
        """
        if self._raw_data is None:
            raise RuntimeError( "No data has been set. Call set_data(...) first.")
        

    def _check_if_raw_data(self) -> None:
        """
        Raise an error if data has not been set.
        """
        return self._check_if_data()
    
      
TData = TypeVar("TData", bound=BaseDataComponent)

class BaseDomainTools(Generic[TData]):
    """
    Base class for domain-specific tools exposed to an LLM agent.

    Concrete subclasses define public methods with docstrings.
    Those methods are automatically exposed as StructuredTools.
    """

    def __init__(self, llm = None ):
        self._data_component: TData | None = None
        self.llm = llm 


    @property
    def data_component(self) -> TData:
        """
        Return the attached data component.

        Raises:
            RuntimeError: If no data component has been assigned.
        """
        if self._data_component is None:
            raise RuntimeError(
                "No data component has been assigned. "
                "Call set_data_component(...) first."
            )

        return self._data_component

    
    def set_data_component(self, data_component: TData) -> None:
        """
        Attach the data component used by these tools.
        """
        self._data_component = data_component

    def _check_if_data_component(self) -> None:
        """
        Return the attached data component or raise if none is available.
        """
        _ = self.data_component

        return None 

    def get_tools(self) -> list[StructuredTool]:
        return self.get_agent_tools()
    
    def get_agent_tools(self) -> list[StructuredTool]:
        """
        Return the public documented methods exposed to the LLM agent.
        """
        tools = []

        excluded_methods = {
            "set_data_component",
            "get_agent_tools",
            "get_tools"
        }

        for name in dir(self):
            if name.startswith("_") or name in excluded_methods:
                continue

            attr = getattr(self, name)

            if not callable(attr):
                continue

            doc = inspect.getdoc(attr)

            if not doc:
                continue

            tools.append(
                StructuredTool.from_function(
                    func=attr,
                    name=name,
                    description=doc,
                )
            )

        return tools


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

