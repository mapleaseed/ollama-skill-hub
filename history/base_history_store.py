from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseHistoryStore(ABC):
    name: str = "BaseHistoryStore"
    description: str = "历史会话存储适配器基类"

    @abstractmethod
    def create_session(self, title: Optional[str] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def list_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        pass

    @abstractmethod
    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        thinking: str = "",
        run_config: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update_session(
        self,
        session_id: str,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        status: Optional[str] = None,
        last_model: Optional[str] = None,
        last_skill: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        pass

    def health_check(self) -> Dict[str, Any]:
        return {"status": "ok", "store": self.name}

    def as_dict(self) -> Dict[str, Any]:
        return {"description": self.description}
