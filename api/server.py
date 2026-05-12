from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from orchestrator.task_manager import TaskManager


CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.yaml"


class TaskSubmitRequest(BaseModel):
    task: str
    agent: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)


app = FastAPI(title="ollama_skill_hub", version="0.1.0")
task_manager = TaskManager.from_config(str(CONFIG_PATH))


@app.post('/task/submit')
def submit_task(request: TaskSubmitRequest):
    try:
        return task_manager.submit(
            task=request.task,
            agent_name=request.agent,
            params=request.params,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get('/task/{task_id}')
def get_task(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@app.get('/tasks')
def list_tasks():
    return task_manager.list_tasks()


@app.get('/registry')
def registry():
    return task_manager.describe()


@app.get('/agents')
def agents():
    return {"agents": task_manager.describe()["agents"]}


@app.get('/skills')
def skills():
    return {"skills": task_manager.describe()["skills"]}

@app.get('/model-adapters')
def model_adapters():
    return {"model_adapters": task_manager.describe()["model_adapters"]}

@app.get('/rag-stores')
def rag_stores():
    return {"rag_stores": task_manager.describe()["rag_stores"]}

@app.get('/health')
def health_check():
    return task_manager.health()


@app.post('/admin/reload')
def reload_config():
    global task_manager
    task_manager = TaskManager.from_config(str(CONFIG_PATH))
    return {"status": "reloaded", **task_manager.describe()}
