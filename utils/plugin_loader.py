import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Type

import yaml

from adapters.base_model_adapter import BaseModelAdapter
from agents.base_agent import BaseAgent
from history.base_history_store import BaseHistoryStore
from rag.base_vector_store import BaseVectorStore
from skills.base_skill import BaseSkill
from utils.logger import get_logger


logger = get_logger(__name__)


class PluginRegistry:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_adapters: Dict[str, BaseModelAdapter] = {}
        self.rag_stores: Dict[str, BaseVectorStore] = {}
        self.history_store: Optional[BaseHistoryStore] = None
        self.skills: Dict[str, BaseSkill] = {}
        self.agents: Dict[str, BaseAgent] = {}

    def as_dict(self) -> Dict[str, Any]:
        return {
            "model_adapters": {
                name: adapter.as_dict()
                for name, adapter in self.model_adapters.items()
            },
            "rag_stores": {
                name: store.as_dict()
                for name, store in self.rag_stores.items()
            },
            "history_store": self.history_store.as_dict() if self.history_store else None,
            "agents": {
                name: {
                    "description": agent.description,
                    "enabled_skills": agent.enabled_skills,
                }
                for name, agent in self.agents.items()
            },
            "skills": {
                name: {"description": skill.description}
                for name, skill in self.skills.items()
            },
        }


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    path = Path(config_path).resolve()
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def load_registry(config_path: str = "config.yaml") -> PluginRegistry:
    config = load_config(config_path)
    base_dir = Path(config_path).resolve().parent
    registry = PluginRegistry(config)

    for entry in config.get("model_adapters", []):
        if not entry.get("enabled", True):
            continue
        adapter = _load_model_adapter(entry, config, base_dir)
        registry.model_adapters[adapter.name] = adapter
        logger.info("loaded model adapter: %s", adapter.name)

    for entry in config.get("rag_stores", []):
        if not entry.get("enabled", True):
            continue
        store = _load_rag_store(entry, base_dir)
        registry.rag_stores[store.name] = store
        logger.info("loaded rag store: %s", store.name)

    history_entry = config.get("history_store")
    if history_entry and history_entry.get("enabled", True):
        registry.history_store = _load_history_store(history_entry, base_dir)
        logger.info("loaded history store: %s", registry.history_store.name)

    for entry in config.get("skills", []):
        if not entry.get("enabled", True):
            continue
        skill = _load_skill(entry, config, base_dir, registry)
        registry.skills[skill.name] = skill
        logger.info("loaded skill: %s", skill.name)

    for entry in config.get("agents", []):
        if not entry.get("enabled", True):
            continue
        agent = _load_agent(entry, base_dir, registry.skills)
        registry.agents[agent.name] = agent
        logger.info("loaded agent: %s", agent.name)

    return registry


def _load_model_adapter(
    entry: Dict[str, Any],
    config: Dict[str, Any],
    base_dir: Path,
) -> BaseModelAdapter:
    cls = _load_class(entry, base_dir, BaseModelAdapter)
    kwargs = dict(entry.get("config") or {})
    ollama_config = config.get("ollama", {})
    kwargs.setdefault("base_url", ollama_config.get("base_url"))
    kwargs.setdefault("url", ollama_config.get("url"))
    kwargs.setdefault("timeout", ollama_config.get("timeout"))
    kwargs = {key: value for key, value in kwargs.items() if value is not None}
    return _instantiate(cls, kwargs)


def _load_rag_store(
    entry: Dict[str, Any],
    base_dir: Path,
) -> BaseVectorStore:
    cls = _load_class(entry, base_dir, BaseVectorStore)
    kwargs = dict(entry.get("config") or {})
    return _instantiate(cls, kwargs)


def _load_history_store(
    entry: Dict[str, Any],
    base_dir: Path,
) -> BaseHistoryStore:
    cls = _load_class(entry, base_dir, BaseHistoryStore)
    kwargs = dict(entry.get("config") or {})
    return _instantiate(cls, kwargs)


def _load_skill(
    entry: Dict[str, Any],
    config: Dict[str, Any],
    base_dir: Path,
    registry: PluginRegistry,
) -> BaseSkill:
    cls = _load_class(entry, base_dir, BaseSkill)
    kwargs = dict(entry.get("config") or {})

    if entry["name"] == "OllamaSkill":
        ollama_config = config.get("ollama", {})
        kwargs.setdefault("base_url", ollama_config.get("base_url"))
        kwargs.setdefault("url", ollama_config.get("url"))
        kwargs.setdefault("model", ollama_config.get("default_model"))
        kwargs.setdefault("adapter_name", ollama_config.get("default_adapter"))
        kwargs.setdefault("model_adapters", registry.model_adapters)
    elif entry["name"] == "MCPSkill":
        mcp_config = config.get("mcp", {})
        kwargs.setdefault("mcp_url", mcp_config.get("url"))

    kwargs.setdefault("model_adapters", registry.model_adapters)
    kwargs.setdefault("rag_stores", registry.rag_stores)
    kwargs = {key: value for key, value in kwargs.items() if value is not None}
    return _instantiate(cls, kwargs)


def _load_agent(
    entry: Dict[str, Any],
    base_dir: Path,
    skills: Dict[str, BaseSkill],
) -> BaseAgent:
    cls = _load_class(entry, base_dir, BaseAgent)
    enabled_skills = entry.get("enabled_skills", [])
    agent = _instantiate(cls, {"enabled_skills": enabled_skills, "skills": skills})
    agent.bind_skills(skills)
    return agent


def _load_class(
    entry: Dict[str, Any],
    base_dir: Path,
    expected_base: Type,
) -> Type:
    path = (base_dir / entry["path"]).resolve()
    module_name = f"ollama_skill_hub_plugins_{path.stem}_{abs(hash(path))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载插件文件: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    cls = getattr(module, entry["name"], None)
    if cls is None:
        cls = _find_class(module, expected_base)
    if cls is None or not issubclass(cls, expected_base):
        raise TypeError(f"{entry['name']} 不是有效的 {expected_base.__name__}")
    return cls


def _find_class(module: Any, expected_base: Type) -> Optional[Type]:
    for _, value in vars(module).items():
        if inspect.isclass(value) and issubclass(value, expected_base) and value is not expected_base:
            return value
    return None


def _instantiate(cls: Type, kwargs: Dict[str, Any]):
    signature = inspect.signature(cls)
    params = signature.parameters
    if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in params.values()):
        return cls(**kwargs)

    accepted = {
        key: value
        for key, value in kwargs.items()
        if key in params
    }
    try:
        return cls(**accepted)
    except TypeError:
        instance = cls()
        for key, value in kwargs.items():
            setattr(instance, key, value)
        return instance
