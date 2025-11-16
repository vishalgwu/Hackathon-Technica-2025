from abc import ABC, abstractmethod
from typing import Any, Dict

class Agent(ABC):
    @abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Each agent must update and return the shared state."""
        pass
