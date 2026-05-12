from typing import Any, Dict, List, Optional

from rag.base_vector_store import BaseVectorStore


class ChromaVectorStore(BaseVectorStore):
    name = "ChromaVectorStore"
    description = "Chroma 向量数据库适配器"

    def __init__(
        self,
        path: str = "./data/chroma",
        collection: str = "default",
    ):
        self.path = path
        self.collection = collection
        self._client = None
        self._collection = None

    def upsert(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        collection = self._get_collection()
        ids = [str(item["id"]) for item in documents]
        embeddings = [item["embedding"] for item in documents]
        texts = [item.get("text", "") for item in documents]
        metadatas = [item.get("metadata", {}) for item in documents]
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        return {"store": self.name, "inserted": len(documents)}

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        collection = self._get_collection()
        raw = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=filters,
        )
        results = []
        ids = raw.get("ids", [[]])[0]
        texts = raw.get("documents", [[]])[0]
        metadatas = raw.get("metadatas", [[]])[0]
        distances = raw.get("distances", [[]])[0]
        for index, item_id in enumerate(ids):
            results.append(
                {
                    "id": item_id,
                    "text": texts[index] if index < len(texts) else "",
                    "metadata": metadatas[index] if index < len(metadatas) else {},
                    "score": distances[index] if index < len(distances) else None,
                }
            )
        return results

    def health_check(self) -> Dict[str, Any]:
        try:
            self._get_collection()
            return {
                "status": "ok",
                "store": self.name,
                "path": self.path,
                "collection": self.collection,
            }
        except Exception as exc:
            return {
                "status": "degraded",
                "store": self.name,
                "path": self.path,
                "collection": self.collection,
                "error": str(exc),
            }

    def _get_collection(self):
        if self._collection is not None:
            return self._collection
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError("未安装 chromadb，无法启用 ChromaVectorStore") from exc

        self._client = chromadb.PersistentClient(path=self.path)
        self._collection = self._client.get_or_create_collection(self.collection)
        return self._collection
