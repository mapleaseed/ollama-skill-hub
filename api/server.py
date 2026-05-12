from pathlib import Path
import base64
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field

from orchestrator.task_manager import TaskManager


CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.yaml"
WEB_DIR = Path(__file__).resolve().parents[1] / "web"
MAX_UPLOAD_FILES = 5
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class TaskSubmitRequest(BaseModel):
    task: str
    agent: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)


app = FastAPI(title="ollama-skill-hub", version="0.1.0")
task_manager = TaskManager.from_config(str(CONFIG_PATH))


@app.get('/')
def root():
    return RedirectResponse(url="/admin")


@app.get('/admin')
def admin_page():
    return FileResponse(WEB_DIR / "admin.html")


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


@app.post('/task/submit-form')
async def submit_task_form(
    task: str = Form(...),
    agent: Optional[str] = Form(None),
    skill: Optional[str] = Form(None),
    model_adapter: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    rag_enabled: bool = Form(False),
    vector_store_name: Optional[str] = Form(None),
    top_k: int = Form(5),
    think: Optional[bool] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
):
    params, task_text = await _build_form_params(
        task=task,
        skill=skill,
        model_adapter=model_adapter,
        model=model,
        rag_enabled=rag_enabled,
        vector_store_name=vector_store_name,
        top_k=top_k,
        think=think,
        files=files,
        stream=False,
    )
    try:
        return task_manager.submit(task=task_text, agent_name=agent, params=params)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post('/task/stream')
async def stream_task_form(
    task: str = Form(...),
    agent: Optional[str] = Form(None),
    skill: Optional[str] = Form(None),
    model_adapter: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    rag_enabled: bool = Form(False),
    vector_store_name: Optional[str] = Form(None),
    top_k: int = Form(5),
    think: Optional[bool] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
):
    params, task_text = await _build_form_params(
        task=task,
        skill=skill,
        model_adapter=model_adapter,
        model=model,
        rag_enabled=rag_enabled,
        vector_store_name=vector_store_name,
        top_k=top_k,
        think=think,
        files=files,
        stream=True,
    )
    return StreamingResponse(
        task_manager.stream(task=task_text, agent_name=agent, params=params),
        media_type="text/event-stream",
    )


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


@app.post('/admin/agent-skills')
def update_agent_skills(payload: Dict[str, Any]):
    agent_name = payload.get("agent")
    enabled_skills = payload.get("enabled_skills")
    if not agent_name or not isinstance(enabled_skills, list):
        raise HTTPException(status_code=400, detail="agent 和 enabled_skills 必填")
    if agent_name not in task_manager.registry.agents:
        raise HTTPException(status_code=404, detail=f"Agent 未加载: {agent_name}")

    missing = [
        skill_name
        for skill_name in enabled_skills
        if skill_name not in task_manager.registry.skills
    ]
    if missing:
        raise HTTPException(status_code=400, detail=f"Skill 未加载: {missing}")

    agent = task_manager.registry.agents[agent_name]
    agent.enabled_skills = enabled_skills
    return {"status": "updated", "agent": agent_name, "enabled_skills": enabled_skills}


async def _build_form_params(
    task: str,
    skill: Optional[str],
    model_adapter: Optional[str],
    model: Optional[str],
    rag_enabled: bool,
    vector_store_name: Optional[str],
    top_k: int,
    think: Optional[bool],
    files: Optional[List[UploadFile]],
    stream: bool,
):
    params: Dict[str, Any] = {"stream": stream}
    if skill:
        params["skill"] = skill
    if model_adapter:
        params["model_adapter"] = model_adapter
    if model:
        params["model"] = model
    if think is not None:
        params["think"] = think
    if rag_enabled:
        params["rag_enabled"] = True
        params["top_k"] = top_k
    if vector_store_name:
        params["vector_store_name"] = vector_store_name

    upload_payload = await _read_uploads(files or [])
    params.update(upload_payload["params"])

    task_parts = [task]
    if upload_payload["text_context"]:
        task_parts.append("上传文件内容:\n" + "\n\n".join(upload_payload["text_context"]))
    return params, "\n\n".join(part for part in task_parts if part)


async def _read_uploads(files: List[UploadFile]) -> Dict[str, Any]:
    if len(files) > MAX_UPLOAD_FILES:
        raise HTTPException(status_code=400, detail=f"最多上传 {MAX_UPLOAD_FILES} 个文件")

    images = []
    attachments = []
    text_context = []
    for file in files:
        content = await file.read()
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=400, detail=f"{file.filename} 超过 10MB 限制")

        content_type = file.content_type or "application/octet-stream"
        encoded = base64.b64encode(content).decode("ascii")
        attachment = {
            "filename": file.filename,
            "content_type": content_type,
            "size": len(content),
            "base64": encoded,
        }
        attachments.append(attachment)

        if content_type.startswith("image/"):
            images.append(encoded)
        elif _is_text_upload(file.filename or "", content_type):
            try:
                text_context.append(
                    f"文件: {file.filename}\n{content.decode('utf-8')}"
                )
            except UnicodeDecodeError:
                text_context.append(
                    f"文件: {file.filename}\n{content.decode('utf-8', errors='replace')}"
                )

    return {
        "params": {
            "images": images,
            "attachments": attachments,
        },
        "text_context": text_context,
    }


def _is_text_upload(filename: str, content_type: str) -> bool:
    if content_type.startswith("text/"):
        return True
    suffix = Path(filename).suffix.lower()
    return suffix in {".txt", ".md", ".json", ".yaml", ".yml", ".py", ".js", ".ts", ".csv"}
