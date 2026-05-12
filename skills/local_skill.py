from skills.base_skill import BaseSkill

class LocalSkill(BaseSkill):
    name = 'LocalSkill'
    description = '本地脚本 Skill 示例'

    def execute(self, inputs: dict) -> dict:
        return {
            'skill': self.name,
            'content': f"执行了本地任务: {inputs.get('prompt','')}",
        }
