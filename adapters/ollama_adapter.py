from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse

import requests

from adapters.base_model_adapter import BaseModelAdapter


class OllamaModelAdapter(BaseModelAdapter):
    name = "OllamaModelAdapter"
    description = "Ollama 通用模型适配器"

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        url: Optional[str] = None,
        model: str = "qwen3:14b",
        timeout: int = 120,
        options: Optional[Dict[str, Any]] = None,
        think: Optional[bool] = None,
    ):
        self.base_url = self._normalize_base_url(base_url, url)
        self.chat_url = url or f"{self.base_url}/api/chat"
        self.model = model
        self.timeout = timeout
        self.options = options or {}
        self.think = think

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        model = kwargs.get("model") or kwargs.get("model_name") or self.model
        stream = kwargs.get("stream", False)
        options = {**self.options, **(kwargs.get("options") or {})}
        images = kwargs.get("images") or []

        if self.chat_url.endswith("/api/generate"):
            payload: Dict[str, Any] = {
                "model": model,
                "prompt": prompt,
                "stream": stream,
            }
            if system:
                payload["system"] = system
            if options:
                payload["options"] = options
        else:
            user_message: Dict[str, Any] = {"role": "user", "content": prompt}
            if images:
                user_message["images"] = images
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append(user_message)
            payload = {"model": model, "messages": messages, "stream": stream}
            if options:
                payload["options"] = options

        keep_alive = kwargs.get("keep_alive")
        if keep_alive is not None:
            payload["keep_alive"] = keep_alive

        think = kwargs.get("think", self.think)
        if think is not None:
            payload["think"] = think

        resp = requests.post(self.chat_url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        raw = resp.json()
        return {
            "adapter": self.name,
            "model": model,
            "content": self._extract_content(raw),
            "thinking": self._extract_thinking(raw),
            "raw": raw,
        }

    def health_check(self) -> Dict[str, Any]:
        try:
            resp = requests.get(self._tags_url(), timeout=3)
            resp.raise_for_status()
            data = resp.json()
            models = [item.get("name") for item in data.get("models", [])]
            status = "ok" if self.model in models else "degraded"
            result = {
                "status": status,
                "adapter": self.name,
                "model": self.model,
                "base_url": self.base_url,
                "models": models,
            }
            if status != "ok":
                result["error"] = f"模型未安装或不可见: {self.model}"
            return result
        except Exception as exc:
            return {
                "status": "degraded",
                "adapter": self.name,
                "model": self.model,
                "base_url": self.base_url,
                "error": str(exc),
            }

    def _tags_url(self) -> str:
        return f"{self.base_url}/api/tags"

    @staticmethod
    def _normalize_base_url(base_url: str, url: Optional[str]) -> str:
        candidate = url or base_url
        parsed = urlparse(candidate)
        if parsed.path.startswith("/api/"):
            return urlunparse((parsed.scheme, parsed.netloc, "", "", "", "")).rstrip("/")
        return candidate.rstrip("/")

    @staticmethod
    def _extract_content(raw: Dict[str, Any]) -> str:
        if "message" in raw and isinstance(raw["message"], dict):
            return raw["message"].get("content", "")
        if "response" in raw:
            return raw.get("response", "")
        return str(raw)

    @staticmethod
    def _extract_thinking(raw: Dict[str, Any]) -> str:
        if "message" in raw and isinstance(raw["message"], dict):
            return raw["message"].get("thinking", "")
        return ""


class Qwen3ChatAdapter(OllamaModelAdapter):
    name = "Qwen3ChatAdapter"
    description = "Qwen3 文本推理模型适配器"
    capability = "chat"

    def __init__(self, model: str = "qwen3:14b", think: Optional[bool] = False, **kwargs: Any):
        kwargs.setdefault("think", think)
        super().__init__(model=model, **kwargs)


class Qwen3VLAdapter(OllamaModelAdapter):
    name = "Qwen3VLAdapter"
    description = "Qwen3-VL 多模态模型适配器"
    capability = "vision_chat"
    supports_multimodal = True

    def __init__(self, model: str = "qwen3-vl:8b", **kwargs: Any):
        super().__init__(model=model, **kwargs)


class BgeM3EmbeddingAdapter(OllamaModelAdapter):
    name = "BgeM3EmbeddingAdapter"
    description = "BGE-M3 向量模型适配器"
    capability = "embedding"
    supports_embeddings = True

    def __init__(self, model: str = "bge-m3:latest", **kwargs: Any):
        super().__init__(model=model, **kwargs)

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        raise NotImplementedError(f"{self.name} 是向量模型，不支持文本生成")

    def embed(self, texts: List[str], **kwargs: Any) -> Dict[str, Any]:
        model = kwargs.get("model") or kwargs.get("model_name") or self.model
        input_value: Any = texts if len(texts) != 1 else texts[0]
        payload = {"model": model, "input": input_value}

        resp = requests.post(f"{self.base_url}/api/embed", json=payload, timeout=self.timeout)
        if resp.status_code == 404:
            legacy_embeddings = []
            legacy_raw = []
            for text in texts:
                legacy_resp = requests.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": model, "prompt": text},
                    timeout=self.timeout,
                )
                legacy_resp.raise_for_status()
                item = legacy_resp.json()
                legacy_raw.append(item)
                legacy_embeddings.append(item.get("embedding", []))
            return {
                "adapter": self.name,
                "model": model,
                "embeddings": legacy_embeddings,
                "raw": legacy_raw,
            }
        resp.raise_for_status()
        raw = resp.json()
        embeddings = raw.get("embeddings")
        if embeddings is None and "embedding" in raw:
            embeddings = [raw["embedding"]]
        return {
            "adapter": self.name,
            "model": model,
            "embeddings": embeddings or [],
            "raw": raw,
        }
