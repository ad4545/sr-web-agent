from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseTool(ABC):
    """
    Abstract base class for all tools in the system.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the tool (for LLM routing and registry)."""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the tool for the LLM."""
        pass
        
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Executes the tool logic.
        Should always return a dictionary (serializable to JSON).
        If an error occurs, conventionally return a dict with an 'error' key.
        """
        pass
