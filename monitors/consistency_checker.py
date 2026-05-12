from typing import Dict, List


class ConsistencyChecker:
    def check_agent_permissions(self, registry) -> Dict:
        missing: List[Dict] = []
        for agent_name, agent in registry.agents.items():
            for skill_name in agent.enabled_skills:
                if skill_name not in registry.skills:
                    missing.append({"agent": agent_name, "skill": skill_name})

        return {
            "status": "ok" if not missing else "failed",
            "missing_skills": missing,
        }

    def check_skill_dependencies(self, registry) -> Dict:
        missing: List[Dict] = []
        for skill_name, skill in registry.skills.items():
            adapter_name = getattr(skill, "adapter_name", None)
            if adapter_name and adapter_name not in registry.model_adapters:
                missing.append(
                    {
                        "skill": skill_name,
                        "dependency": "model_adapter",
                        "name": adapter_name,
                    }
                )

            embedding_adapter_name = getattr(skill, "embedding_adapter_name", None)
            if embedding_adapter_name and embedding_adapter_name not in registry.model_adapters:
                missing.append(
                    {
                        "skill": skill_name,
                        "dependency": "embedding_adapter",
                        "name": embedding_adapter_name,
                    }
                )

            vector_store_name = getattr(skill, "vector_store_name", None)
            if vector_store_name and vector_store_name not in registry.rag_stores:
                missing.append(
                    {
                        "skill": skill_name,
                        "dependency": "vector_store",
                        "name": vector_store_name,
                    }
                )

        return {
            "status": "ok" if not missing else "failed",
            "missing_dependencies": missing,
        }
