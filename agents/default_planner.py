from agents.base_agent import BaseAgent

class DefaultPlanner(BaseAgent):
    name = 'DefaultPlanner'
    description = '默认 Hermes-Lite 任务规划 Agent'

    def plan(self, task_description: str, params: dict = None):
        params = params or {}
        workflow = params.get('workflow')
        if workflow:
            return [self._normalize_step(index, step) for index, step in enumerate(workflow, start=1)]

        requested_skill = params.get('skill')
        if (
            params.get('rag_enabled')
            and requested_skill in (None, '', 'OllamaSkill')
            and 'RAGSkill' in self.enabled_skills
            and 'OllamaSkill' in self.enabled_skills
        ):
            return [
                {
                    'id': 'step-1',
                    'name': 'retrieve_context',
                    'skill': 'RAGSkill',
                    'prompt': task_description,
                    'params': {'mode': 'search'},
                    'depends_on': [],
                },
                {
                    'id': 'step-2',
                    'name': 'reason_with_context',
                    'skill': 'OllamaSkill',
                    'prompt': task_description,
                    'depends_on': ['step-1'],
                },
            ]

        skill_name = self._select_skill(task_description, params)
        return [
            {
                'id': 'step-1',
                'name': 'reason_and_execute',
                'skill': skill_name,
                'prompt': task_description,
                'depends_on': [],
            }
        ]

    def dispatch(self, step: dict, params: dict):
        skill_inputs = self.build_skill_inputs(step, params)
        skill = self.get_skill(step['skill'])
        return skill.execute(skill_inputs)

    def build_skill_inputs(self, step: dict, params: dict):
        skill_name = step['skill']
        skill_inputs = {
            **params,
            **step.get('params', {}),
            'prompt': step.get('prompt') or params.get('prompt') or '',
        }

        if skill_name == 'OllamaSkill':
            skill_inputs.setdefault('system', self._hermes_system_prompt())
            context = skill_inputs.get('context')
            if context:
                skill_inputs['prompt'] = (
                    '请基于以下上下文回答用户任务。\n\n'
                    f'上下文:\n{context}\n\n'
                    f'用户任务:\n{skill_inputs["prompt"]}'
                )

        return skill_inputs

    def monitor(self, step: str, result: dict) -> bool:
        return not result.get('error')

    def _select_skill(self, task_description: str, params: dict) -> str:
        requested = params.get('skill')
        if requested:
            return requested

        text = task_description.lower()
        if 'mcp' in text and 'MCPSkill' in self.enabled_skills:
            return 'MCPSkill'
        if any(keyword in text for keyword in ('rag', '检索', '知识库', '向量库')) and 'RAGSkill' in self.enabled_skills:
            return 'RAGSkill'
        if 'local' in text and 'LocalSkill' in self.enabled_skills:
            return 'LocalSkill'
        if 'OllamaSkill' in self.enabled_skills:
            return 'OllamaSkill'
        if self.enabled_skills:
            return self.enabled_skills[0]
        raise RuntimeError(f'{self.name} 没有可用 Skill')

    def _normalize_step(self, index: int, step) -> dict:
        if isinstance(step, str):
            return {
                'id': f'step-{index}',
                'name': f'step-{index}',
                'skill': self._select_skill(step, {}),
                'prompt': step,
                'depends_on': [],
            }
        return {
            'id': step.get('id', f'step-{index}'),
            'name': step.get('name', f'step-{index}'),
            'skill': step.get('skill') or self._select_skill(step.get('prompt', ''), {}),
            'prompt': step.get('prompt', ''),
            'params': step.get('params', {}),
            'depends_on': step.get('depends_on', []),
        }

    @staticmethod
    def _hermes_system_prompt() -> str:
        return (
            '你是 Hermes-Lite Agent。你需要先理解用户目标，再给出可靠、可执行的结果。'
            '如果任务包含多步，请用清晰的小节组织答案；如果信息不足，请说明假设。'
            '你可以被外部编排器授予 Skill，但当前回答只输出最终内容，不要虚构未调用的工具结果。'
        )
