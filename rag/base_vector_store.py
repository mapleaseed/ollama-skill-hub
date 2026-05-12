from abc import ABC
from typing import Any, Dict, List, Optional


class BaseVectorStore(ABC):
    name: str = "BaseVectorStore"
    description: str = "向量数据库适配器基类"

    def upsert(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        raise NotImplementedError(f"{self.name} 不支持写入")

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError(f"{self.name} 不支持检索")

    def health_check(self) -> Dict[str, Any]:
        return {"status": "ok", "store": self.name}

    def as_dict(self) -> Dict[str, Any]:
        return {"description": self.description}
