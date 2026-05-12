from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class BaseAgent(ABC):
    name: str
    description: str
    enabled_skills: List[str] = []

    def __init__(
        self,
        enabled_skills: Optional[List[str]] = None,
        skills: Optional[Dict[str, object]] = None,
    ):
        self.enabled_skills = list(enabled_skills or self.enabled_skills or [])
        self.skills = skills or {}

    def bind_skills(self, skills: Dict[str, object]) -> None:
        self.skills = skills

    def get_skill(self, skill_name: str):
        if skill_name not in self.enabled_skills:
            raise PermissionError(f"{self.name} 不允许调用 {skill_name}")
        if skill_name not in self.skills:
            raise KeyError(f"Skill 未加载: {skill_name}")
        return self.skills[skill_name]

    @abstractmethod
    def plan(self, task_description: str, params: Optional[Dict] = None) -> List[Dict]:
        pass

    @abstractmethod
    def dispatch(self, step: Dict, params: Dict) -> Dict:
        pass

    @abstractmethod
    def monitor(self, step: Dict, result: Dict) -> bool:
        pass
