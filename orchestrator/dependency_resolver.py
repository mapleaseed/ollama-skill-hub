from typing import Dict, List


def resolve_steps(steps: List[Dict]) -> List[Dict]:
    if not steps:
        return []

    by_id = {step["id"]: step for step in steps}
    ordered = []
    visiting = set()
    visited = set()

    def visit(step_id: str) -> None:
        if step_id in visited:
            return
        if step_id in visiting:
            raise ValueError(f"任务步骤存在循环依赖: {step_id}")
        if step_id not in by_id:
            raise ValueError(f"任务步骤依赖不存在: {step_id}")

        visiting.add(step_id)
        for dependency in by_id[step_id].get("depends_on", []):
            visit(dependency)
        visiting.remove(step_id)
        visited.add(step_id)
        ordered.append(by_id[step_id])

    for step in steps:
        visit(step["id"])

    return ordered
