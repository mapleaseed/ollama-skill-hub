from typing import Dict, Optional

from adapters.ollama_adapter import Qwen3ChatAdapter
from skills.base_skill import BaseSkill

class OllamaSkill(BaseSkill):
    name = 'OllamaSkill'
    description = '调用本地 Ollama 执行模型推理'

    def __init__(
        self,
        base_url: str = 'http://localhost:11434',
        url: str = 'http://localhost:11434/api/chat',
        model: str = 'qwen3:14b',
        adapter_name: str = 'Qwen3ChatAdapter',
        model_adapters: Optional[Dict[str, object]] = None,
        timeout: int = 120,
    ):
        self.base_url = base_url
        self.url = url
        self.model = model
        self.adapter_name = adapter_name
        self.model_adapters = dict(model_adapters or {})
        if adapter_name not in self.model_adapters:
            self.model_adapters[adapter_name] = Qwen3ChatAdapter(
                base_url=base_url,
                url=url,
                model=model,
                timeout=timeout,
            )

    def execute(self, inputs: dict) -> dict:
        prompt = inputs['prompt']
        adapter = self._select_adapter(inputs)
        system = inputs.get('system')
        options = dict(inputs)
        options.pop('prompt', None)
        options.pop('system', None)
        options['stream'] = False
        result = adapter.generate(prompt=prompt, system=system, **options)
        return {
            'skill': self.name,
            **result,
        }

    def stream_execute(self, inputs: dict):
        prompt = inputs['prompt']
        adapter = self._select_adapter(inputs)
        system = inputs.get('system')
        options = dict(inputs)
        options.pop('prompt', None)
        options.pop('system', None)
        yield from adapter.stream_generate(prompt=prompt, system=system, **options)

    def health_check(self) -> dict:
        adapter = self.model_adapters.get(self.adapter_name)
        if adapter is None:
            return {
                'status': 'degraded',
                'skill': self.name,
                'adapter': self.adapter_name,
                'error': f'模型适配器未加载: {self.adapter_name}',
            }
        result = adapter.health_check()
        return {'skill': self.name, **result}

    def _select_adapter(self, inputs: dict):
        adapter_name = (
            inputs.get('model_adapter')
            or inputs.get('adapter')
            or self.adapter_name
        )
        if adapter_name not in self.model_adapters:
            raise KeyError(f'模型适配器未加载: {adapter_name}')
        return self.model_adapters[adapter_name]
