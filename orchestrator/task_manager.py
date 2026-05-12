import json
from typing import Dict, Iterator, Optional

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
                runtime_params = self._params_with_context(params, step_results)
                result = agent.dispatch(step, runtime_params)
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

    def stream(
        self,
        task: str,
        agent_name: Optional[str] = None,
        params: Optional[Dict] = None,
    ) -> Iterator[str]:
        if not task:
            yield self._sse({"event": "error", "error": "task 不能为空"})
            return

        params = params or {}
        agent = self._get_agent(agent_name)
        record = self.queue.create(task=task, agent=agent.name)
        step_results = []

        try:
            self.queue.update(record.id, status="planning")
            planned_steps = agent.plan(task, params)
            steps = resolve_steps(planned_steps)
            self.queue.update(record.id, status="running", steps=steps)
            yield self._sse({"event": "task", "task_id": record.id, "status": "running"})

            for index, step in enumerate(steps):
                runtime_params = self._params_with_context(params, step_results)
                is_last_step = index == len(steps) - 1
                if is_last_step and step["skill"] == "OllamaSkill":
                    skill = agent.get_skill(step["skill"])
                    if not hasattr(skill, "stream_execute"):
                        raise RuntimeError("OllamaSkill 不支持流式输出")
                    skill_inputs = agent.build_skill_inputs(step, runtime_params)
                    content_parts = []
                    thinking_parts = []
                    for chunk in skill.stream_execute(skill_inputs):
                        content = chunk.get("content") or ""
                        thinking = chunk.get("thinking") or ""
                        if content:
                            content_parts.append(content)
                            yield self._sse({"event": "content", "delta": content})
                        if thinking:
                            thinking_parts.append(thinking)
                            yield self._sse({"event": "thinking", "delta": thinking})

                    result = {
                        "skill": skill.name,
                        "adapter": skill_inputs.get("model_adapter") or skill_inputs.get("adapter"),
                        "model": skill_inputs.get("model") or skill_inputs.get("model_name"),
                        "content": "".join(content_parts),
                        "thinking": "".join(thinking_parts),
                    }
                else:
                    result = agent.dispatch(step, runtime_params)

                ok = agent.monitor(step, result)
                step_result = {
                    "id": step["id"],
                    "name": step.get("name"),
                    "skill": step["skill"],
                    "ok": ok,
                    "result": result,
                }
                step_results.append(step_result)
                yield self._sse({"event": "step", "step": step_result})
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
            yield self._sse({"event": "done", "result": final_result})
        except Exception as exc:
            error_result = {
                "task_id": record.id,
                "agent": agent.name,
                "status": "failed",
                "error": str(exc),
            }
            self.queue.update(record.id, status="failed", error=str(exc), result=error_result)
            yield self._sse({"event": "error", **error_result})

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
        history_store = (
            self.registry.history_store.health_check()
            if self.registry.history_store
            else {"status": "disabled"}
        )
        skills = {
            name: skill.health_check()
            for name, skill in self.registry.skills.items()
        }
        status = "ok"
        checks = [
            *model_adapters.values(),
            *rag_stores.values(),
            history_store,
            *skills.values(),
        ]
        if any(item.get("status") == "degraded" for item in checks):
            status = "degraded"
        return {
            "status": status,
            "agents": list(self.registry.agents),
            "model_adapters": model_adapters,
            "rag_stores": rag_stores,
            "history_store": history_store,
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

    @staticmethod
    def _params_with_context(params: Dict, step_results) -> Dict:
        context_parts = []
        if params.get("context"):
            context_parts.append(str(params["context"]))
        for step_result in step_results:
            result = step_result.get("result", {})
            content = result.get("content")
            if content:
                context_parts.append(str(content))
        if not context_parts:
            return params
        return {**params, "context": "\n\n".join(context_parts)}

    @staticmethod
    def _sse(payload: Dict) -> str:
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
