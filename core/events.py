from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

@dataclass(frozen=True)
class ProgressEvent:
    """A single progress update emitted during agent or orchestrator processing."""
    stage: str
    message: str
    agent_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat() + "Z")
    data: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        """Converts the event to a JSON-serializable dictionary."""
        return {
            "stage": self.stage,
            "message": self.message,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "data": self.data,
        }
