from typing import Dict


class HealthMonitor:
    def __init__(self, task_manager):
        self.task_manager = task_manager

    def check(self) -> Dict:
        return self.task_manager.health()
