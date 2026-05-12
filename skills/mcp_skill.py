from skills.base_skill import BaseSkill
import requests

class MCPSkill(BaseSkill):
    name = 'MCPSkill'
    description = '通过 MCP 调用多模型执行任务'

    def __init__(self, mcp_url='http://localhost:8000'):
        self.mcp_url = mcp_url

    def execute(self, inputs: dict) -> dict:
        payload = {
            'model': inputs.get('model') or inputs.get('model_name', 'llama3.2'),
            'context': inputs.get('context',''),
            'prompt': inputs['prompt'],
        }
        resp = requests.post(f'{self.mcp_url}/run', json=payload, timeout=30)
        resp.raise_for_status()
        return {'skill': self.name, 'raw': resp.json()}

    def health_check(self) -> dict:
        try:
            resp = requests.get(f'{self.mcp_url}/health', timeout=3)
            resp.raise_for_status()
            return {'status': 'ok', 'skill': self.name, 'url': self.mcp_url}
        except Exception as exc:
            return {
                'status': 'degraded',
                'skill': self.name,
                'url': self.mcp_url,
                'error': str(exc),
            }
