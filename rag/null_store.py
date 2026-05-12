from typing import Any, Dict, List, Optional

from rag.base_vector_store import BaseVectorStore


class NullVectorStore(BaseVectorStore):
    name = "NullVectorStore"
    description = "空向量库适配器，用于未启用 RAG 时的默认占位"

    def upsert(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {"store": self.name, "inserted": 0, "ignored": len(documents)}

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        return []
