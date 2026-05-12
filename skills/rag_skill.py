from typing import Dict, Optional

from skills.base_skill import BaseSkill


class RAGSkill(BaseSkill):
    name = "RAGSkill"
    description = "基于可插拔向量库和向量模型的 RAG Skill"

    def __init__(
        self,
        embedding_adapter_name: str = "BgeM3EmbeddingAdapter",
        vector_store_name: str = "NullVectorStore",
        model_adapters: Optional[Dict[str, object]] = None,
        rag_stores: Optional[Dict[str, object]] = None,
    ):
        self.embedding_adapter_name = embedding_adapter_name
        self.vector_store_name = vector_store_name
        self.model_adapters = model_adapters or {}
        self.rag_stores = rag_stores or {}

    def execute(self, inputs: dict) -> dict:
        mode = inputs.get("mode", "search")
        if mode == "upsert":
            return self._upsert(inputs)
        return self._search(inputs)

    def health_check(self) -> dict:
        embedding = self.model_adapters.get(self.embedding_adapter_name)
        store = self.rag_stores.get(self.vector_store_name)
        status = "ok" if embedding and store else "degraded"
        result = {
            "status": status,
            "skill": self.name,
            "embedding_adapter": self.embedding_adapter_name,
            "vector_store": self.vector_store_name,
        }
        if not embedding:
            result["embedding_error"] = f"向量模型适配器未加载: {self.embedding_adapter_name}"
        if not store:
            result["store_error"] = f"向量库适配器未加载: {self.vector_store_name}"
        return result

    def _search(self, inputs: dict) -> dict:
        prompt = inputs["prompt"]
        top_k = int(inputs.get("top_k", 5))
        embedding = self._get_embedding_adapter(inputs)
        store = self._get_vector_store(inputs)
        vector_result = embedding.embed([prompt])
        embeddings = vector_result.get("embeddings") or []
        if not embeddings:
            return {
                "skill": self.name,
                "content": "",
                "matches": [],
                "error": "向量模型未返回 embedding",
            }
        matches = store.search(
            query_vector=embeddings[0],
            top_k=top_k,
            filters=inputs.get("filters"),
        )
        return {
            "skill": self.name,
            "content": "\n".join(item.get("text", "") for item in matches),
            "matches": matches,
        }

    def _upsert(self, inputs: dict) -> dict:
        documents = inputs.get("documents") or []
        if not documents:
            return {"skill": self.name, "store": self.vector_store_name, "inserted": 0}
        embedding = self._get_embedding_adapter(inputs)
        store = self._get_vector_store(inputs)
        texts = [item.get("text", "") for item in documents]
        vector_result = embedding.embed(texts)
        embeddings = vector_result.get("embeddings") or []
        enriched = []
        for index, item in enumerate(documents):
            if index >= len(embeddings):
                break
            enriched.append({**item, "embedding": embeddings[index]})
        result = store.upsert(enriched)
        return {"skill": self.name, **result}

    def _get_embedding_adapter(self, inputs: dict):
        adapter_name = inputs.get("embedding_adapter_name") or self.embedding_adapter_name
        if adapter_name not in self.model_adapters:
            raise KeyError(f"向量模型适配器未加载: {adapter_name}")
        return self.model_adapters[adapter_name]

    def _get_vector_store(self, inputs: dict):
        store_name = inputs.get("vector_store_name") or inputs.get("rag_store") or self.vector_store_name
        if store_name not in self.rag_stores:
            raise KeyError(f"向量库适配器未加载: {store_name}")
        return self.rag_stores[store_name]
