from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Dict, List, Optional
from uuid import uuid4


@dataclass
class TaskRecord:
    id: str
    task: str
    agent: str
    status: str = "queued"
    steps: List[Dict] = field(default_factory=list)
    result: Optional[Dict] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "task": self.task,
            "agent": self.agent,
            "status": self.status,
            "steps": self.steps,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class TaskQueue:
    def __init__(self):
        self._tasks: Dict[str, TaskRecord] = {}
        self._lock = Lock()

    def create(self, task: str, agent: str) -> TaskRecord:
        record = TaskRecord(id=str(uuid4()), task=task, agent=agent)
        with self._lock:
            self._tasks[record.id] = record
        return record

    def update(self, task_id: str, **changes) -> TaskRecord:
        with self._lock:
            record = self._tasks[task_id]
            for key, value in changes.items():
                setattr(record, key, value)
            record.updated_at = datetime.utcnow().isoformat() + "Z"
            return record

    def get(self, task_id: str) -> Optional[TaskRecord]:
        with self._lock:
            return self._tasks.get(task_id)

    def list(self) -> List[TaskRecord]:
        with self._lock:
            return list(self._tasks.values())
