import inspect

from langchain_core.tools import StructuredTool


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
        self._data = None

    @abstractmethod
    def set_data(self, *args, **kwargs) -> Self:
        """
        Set or replace the domain data.
        """
        raise NotImplementedError

    def _check_if_data(self) -> None:
        """
        Raise an error if data has not been set.
        """
        if self._data is None:
            raise RuntimeError(
                "No data has been set. Call set_data(...) first."
            )

class BaseDomainTools:
    """
    Base class for domain-specific tools exposed to an LLM agent.

    Concrete subclasses define public methods with docstrings.
    Those methods are automatically exposed as StructuredTools.
    """

    def __init__(self):
        self._data_component = None

    def set_data_component(self, data_component: BaseDataComponent) -> None:
        """
        Attach the data component used by these tools.
        """
        self._data_component = data_component

    def _check_if_data_component(self) -> None:
        """
        Return the attached data component or raise if none is available.
        """
        if self._data_component is None:
            raise RuntimeError(
                "No data component has been assigned. "
                "Call set_data_component(...) first."
            )

        return None 

    def get_agent_tools(self) -> list[StructuredTool]:
        """
        Return the public documented methods exposed to the LLM agent.
        """
        tools = []

        excluded_methods = {
            "set_data_component",
            "get_agent_tools",
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


    