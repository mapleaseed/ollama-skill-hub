# Next Steps

## 当前推荐下一步

下一里程碑是 **Agent/Skill Compatibility Baseline**。

目标不是落地 PAOR，而是完成目前仅占位的 Agent 和 Skill 兼容能力：系统能够接入两个不同 Agent，用户或配置可以选择 Agent，每个 Agent 有明确的 Skill 权限边界，Registry 能展示这些能力。

先做 Agent/Skill 元数据和流式能力去硬编码，这是该里程碑的前置切片，也是后续 manifest、PAOR、UI registry 展示的共同基础。

最小可交付切片：

```text
BaseSkill 元数据
BaseAgent 元数据
PluginRegistry.as_dict() 增强
TaskManager.stream() 去 OllamaSkill 硬编码
两个 Agent 基础接入准备
基础验证
过程文档更新
```

## 开工前读取

```text
Agent.md
doc/agent_index/working_rules.md
doc/agent_skill_plugin_standard.md
doc/agent_skill_architecture_details.md
skills/base_skill.py
agents/base_agent.py
utils/plugin_loader.py
orchestrator/task_manager.py
skills/ollama_skill.py
agents/default_planner.py
```

## 建议实现顺序

1. `skills/base_skill.py`
   - 增加 `category`
   - 增加 `capabilities`
   - 增加 `supports_stream`
   - 增加 `input_schema/output_schema/config_schema`
   - 增加 `permissions/requires`
   - 增加 `as_dict()`

2. `skills/ollama_skill.py`
   - 标记 `supports_stream = True`
   - 补充基础 capabilities

3. `agents/base_agent.py`
   - 增加 `strategy`
   - 增加 `default_skill`
   - 增加 `max_steps/max_reflect_rounds`
   - 增加 `as_dict()`
   - 可先不实现完整 PAOR，只预留默认字段

4. `utils/plugin_loader.py`
   - `PluginRegistry.as_dict()` 使用 Agent/Skill 自身 `as_dict()`
   - 保持旧配置兼容

5. `orchestrator/task_manager.py`
   - 将最后一步流式判断从 `step["skill"] == "OllamaSkill"` 改为 `skill.supports_stream`
   - 保持现有 SSE payload 不破坏前端

6. 验证：
   - Python compileall
   - `/registry` 返回结构可用
   - `/chat` 和 `/admin` 不受破坏

7. 文档：
   - 更新 `doc/process_log.md`
   - 如下一步计划变化，更新本文件

## 后续队列

完成元数据切片后，候选下一步：

- 新增第二个基础 Agent，例如面向快速 Skill 路由的 `SkillRouterAgent`。
- 完成 Agent 选择和权限边界在 `/registry` 的展示。
- 新增 `manifest.yaml` 包目录加载兼容。
- 下一里程碑再开始 PAOR：抽出 `NativePlanActEngine`，新增 `BaseAgent.observe/reflect/answer` 和 `NativePAOREngine`。
- PAOR 之后进入 Context Compact and Memory Modes：实现 `/compact`、MemoryManager、`RecentTurnContext` 和 `CompactSummaryContext`。
- 再之后进入 Session Memory and Run Visibility：实现刷新恢复任务进度、停止本次会话、模型调用过程展开和中间 thinking/output 可见。

## 当前决策点

暂无必须中断开发的决策点。

如果实现过程中发现 `doc/arrangement.md` 的受保护约定与更优轻量方案冲突，应暂停并向用户请示。
