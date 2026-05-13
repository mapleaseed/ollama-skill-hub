# Document Map

本文说明 `/doc` 下文件的存放逻辑、权威层级和阅读方式。

## 目录职责

```text
doc/
  project_goal.md
  process_log.md
  arrangement.md
  *_standard.md
  *_architecture_details.md
  agent_index/
  milestones/
```

### 根级文档

- `doc/project_goal.md`  
  项目目标基线。记录长期目标和当前阶段方向。可以根据实际进展更新，但目标偏移必须先问用户。

- `doc/process_log.md`  
  实时过程记录。每次设计、实现、验证、规则或阶段性结论变化，都应追加记录。

- `doc/arrangement.md`  
  受保护约定。默认遵循，但不是不可讨论的圣经；发现冲突或更优方案时主动向用户请示。

### 标准文档

- `doc/agent_skill_plugin_standard.md`  
  Agent/Skill 插件化、Registry、权限、Native PAOR、CommandSkill 等标准草案。

- `doc/context_memory_standard.md`  
  上下文记忆、`/compact`、记忆开关和上下文模式标准草案。

标准文档是优先参考，但不是最终真理。实现中发现更轻、更稳或更符合项目现状的方案时，应提出调整建议。

### 详细设计文档

- `doc/agent_skill_architecture_details.md`  
  Agent/Skill 架构详解，包含 PAOR、RunEvent、CommandSkill、MCP、第三方 Skill 和实施顺序。

- `doc/context_memory_architecture_details.md`  
  MemoryManager、ContextBuilder、compact boundary 和前后端边界详解。

详细设计用于理解背景和方案，不应被当成强制实现清单。

### Agent 索引文档

- `doc/agent_index/README.md`  
  索引入口。

- `doc/agent_index/current_state.md`  
  当前实现事实。

- `doc/agent_index/document_map.md`  
  本文件，说明文档架构。

- `doc/agent_index/working_rules.md`  
  工作规则、请示规则、文档维护规则。

- `doc/agent_index/next_steps.md`  
  下一步开发计划。

索引文档应该保持短小，面向接续工作。

### 里程碑文档

- `doc/milestones/README.md`
- `doc/milestones/2026-05-12-core-runtime-baseline.md`
- `doc/milestones/2026-05-12-web-experience.md`

里程碑文档记录发布级阶段成果。小修小改记录到 `doc/process_log.md`，同一发布目标只保留一个里程碑文件。做相关模块时可以阅读对应里程碑。

## 阅读策略

实现 Agent/Skill 元数据：

```text
doc/agent_index/next_steps.md
doc/agent_skill_plugin_standard.md
doc/agent_skill_architecture_details.md
```

实现上下文记忆：

```text
doc/context_memory_standard.md
doc/context_memory_architecture_details.md
history/sqlite_history_store.py
api/server.py
```

实现 PAOR 或 run events：

```text
doc/arrangement.md
doc/agent_skill_plugin_standard.md
doc/agent_skill_architecture_details.md
orchestrator/task_manager.py
agents/base_agent.py
```

修改 UI：

```text
doc/milestones/
web/chat.html
web/admin.html
api/server.py
```

更新项目方向：

```text
doc/project_goal.md
doc/arrangement.md
doc/process_log.md
Agent.md
```

涉及目标或受保护约定时，先问用户再改。
