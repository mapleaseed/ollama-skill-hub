from abc import ABC
from typing import Any, Dict, List, Optional


class BaseModelAdapter(ABC):
    name: str = "BaseModelAdapter"
    description: str = "模型适配器基类"
    model: str = ""
    capability: str = "chat"
    supports_multimodal: bool = False
    supports_embeddings: bool = False

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        raise NotImplementedError(f"{self.name} 不支持文本生成")

    def embed(self, texts: List[str], **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError(f"{self.name} 不支持向量化")

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "adapter": self.name,
            "model": self.model,
            "capability": self.capability,
        }

    def as_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "model": self.model,
            "capability": self.capability,
            "supports_multimodal": self.supports_multimodal,
            "supports_embeddings": self.supports_embeddings,
        }
