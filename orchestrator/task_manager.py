from typing import Dict, Optional

from orchestrator.dependency_resolver import resolve_steps
from orchestrator.task_queue import TaskQueue
from utils.plugin_loader import PluginRegistry, load_registry


class TaskManager:
    def __init__(self, registry: PluginRegistry):
        self.registry = registry
        self.queue = TaskQueue()

    @classmethod
    def from_config(cls, config_path: str = "config.yaml") -> "TaskManager":
        return cls(load_registry(config_path))

    def submit(
        self,
        task: str,
        agent_name: Optional[str] = None,
        params: Optional[Dict] = None,
    ) -> Dict:
        if not task:
            raise ValueError("task 不能为空")

        params = params or {}
        agent = self._get_agent(agent_name)
        record = self.queue.create(task=task, agent=agent.name)

        try:
            self.queue.update(record.id, status="planning")
            planned_steps = agent.plan(task, params)
            steps = resolve_steps(planned_steps)
            step_results = []

            self.queue.update(record.id, status="running", steps=steps)
            for step in steps:
                result = agent.dispatch(step, params)
                ok = agent.monitor(step, result)
                step_result = {
                    "id": step["id"],
                    "name": step.get("name"),
                    "skill": step["skill"],
                    "ok": ok,
                    "result": result,
                }
                step_results.append(step_result)
                if not ok:
                    raise RuntimeError(f"步骤执行失败: {step['id']}")

            final_result = {
                "task_id": record.id,
                "agent": agent.name,
                "status": "success",
                "steps": step_results,
                "content": self._last_content(step_results),
            }
            self.queue.update(record.id, status="success", result=final_result)
            return final_result
        except Exception as exc:
            error_result = {
                "task_id": record.id,
                "agent": agent.name,
                "status": "failed",
                "error": str(exc),
            }
            self.queue.update(record.id, status="failed", error=str(exc), result=error_result)
            return error_result

    def get_task(self, task_id: str) -> Optional[Dict]:
        record = self.queue.get(task_id)
        return record.to_dict() if record else None

    def list_tasks(self) -> Dict:
        return {"tasks": [record.to_dict() for record in self.queue.list()]}

    def describe(self) -> Dict:
        return self.registry.as_dict()

    def health(self) -> Dict:
        model_adapters = {
            name: adapter.health_check()
            for name, adapter in self.registry.model_adapters.items()
        }
        rag_stores = {
            name: store.health_check()
            for name, store in self.registry.rag_stores.items()
        }
        skills = {
            name: skill.health_check()
            for name, skill in self.registry.skills.items()
        }
        status = "ok"
        checks = [*model_adapters.values(), *rag_stores.values(), *skills.values()]
        if any(item.get("status") == "degraded" for item in checks):
            status = "degraded"
        return {
            "status": status,
            "agents": list(self.registry.agents),
            "model_adapters": model_adapters,
            "rag_stores": rag_stores,
            "skills": skills,
        }

    def _get_agent(self, agent_name: Optional[str]):
        if agent_name:
            if agent_name not in self.registry.agents:
                raise KeyError(f"Agent 未加载: {agent_name}")
            return self.registry.agents[agent_name]

        if not self.registry.agents:
            raise RuntimeError("没有可用 Agent")
        return next(iter(self.registry.agents.values()))

    @staticmethod
    def _last_content(step_results) -> str:
        if not step_results:
            return ""
        result = step_results[-1].get("result", {})
        return result.get("content") or str(result)
