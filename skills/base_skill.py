from abc import ABC, abstractmethod
from typing import Dict

class BaseSkill(ABC):
    name: str
    description: str

    @abstractmethod
    def execute(self, inputs: Dict) -> Dict:
        pass

    def health_check(self) -> Dict:
        return {"status": "ok", "skill": self.name}
