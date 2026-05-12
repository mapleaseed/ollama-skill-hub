from typing import Any, Dict, List, Optional

from rag.base_vector_store import BaseVectorStore


class MilvusVectorStore(BaseVectorStore):
    name = "MilvusVectorStore"
    description = "Milvus 向量数据库适配器"

    def __init__(
        self,
        uri: str = "http://localhost:19530",
        collection: str = "default",
        token: Optional[str] = None,
    ):
        self.uri = uri
        self.collection = collection
        self.token = token
        self._client = None

    def upsert(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        client = self._get_client()
        data = [
            {
                "id": item["id"],
                "vector": item["embedding"],
                "text": item.get("text", ""),
                "metadata": item.get("metadata", {}),
            }
            for item in documents
        ]
        client.upsert(collection_name=self.collection, data=data)
        return {"store": self.name, "inserted": len(documents)}

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        client = self._get_client()
        raw = client.search(
            collection_name=self.collection,
            data=[query_vector],
            limit=top_k,
            filter=self._filter_to_expr(filters),
            output_fields=["text", "metadata"],
        )
        results = []
        for hit in raw[0] if raw else []:
            entity = hit.get("entity", {})
            results.append(
                {
                    "id": hit.get("id"),
                    "text": entity.get("text", ""),
                    "metadata": entity.get("metadata", {}),
                    "score": hit.get("distance"),
                }
            )
        return results

    def health_check(self) -> Dict[str, Any]:
        try:
            self._get_client()
            return {
                "status": "ok",
                "store": self.name,
                "uri": self.uri,
                "collection": self.collection,
            }
        except Exception as exc:
            return {
                "status": "degraded",
                "store": self.name,
                "uri": self.uri,
                "collection": self.collection,
                "error": str(exc),
            }

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from pymilvus import MilvusClient
        except ImportError as exc:
            raise RuntimeError("未安装 pymilvus，无法启用 MilvusVectorStore") from exc

        self._client = MilvusClient(uri=self.uri, token=self.token)
        return self._client

    @staticmethod
    def _filter_to_expr(filters: Optional[Dict[str, Any]]) -> str:
        if not filters:
            return ""
        clauses = []
        for key, value in filters.items():
            if isinstance(value, str):
                clauses.append(f'{key} == "{value}"')
            else:
                clauses.append(f"{key} == {value}")
        return " and ".join(clauses)
