from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any
from core.events import ProgressEvent

class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    Enforces a standard API for interaction by the Orchestrator.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier/name for this agent."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description to help the Orchestrator decide when to route to this agent."""
        pass

    @abstractmethod
    async def run(self, task: str) -> Dict[str, Any]:
        """
        Standard non-streaming execution pattern.
        Returns a dictionary representing the finalized state/response.
        Keys conventionally include 'text', 'data', or 'master_task'.
        """
        pass

    @abstractmethod
    async def run_streaming(self, task: str) -> AsyncGenerator[ProgressEvent, None]:
        """
        Streaming execution pattern for yielding ProgressEvents.
        """
        # Base implementation providing a single unimplemented event, 
        # meant to be overridden.
        yield ProgressEvent(
            stage="unimplemented", 
            message="Streaming not implemented for this agent.",
            agent_id=self.name
        )
