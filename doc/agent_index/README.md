# Agent Index

这个目录是给后续 Agent 使用的轻量索引层。`Agent.md` 保留启动规则、全项目工作文件路径地图和导航；具体上下文按需读取本目录文件，避免一开始加载过多历史内容。

## 读取顺序

普通开发任务：

```text
Agent.md
 -> doc/agent_index/working_rules.md
 -> doc/agent_index/next_steps.md
 -> 相关源码
```

架构或设计任务：

```text
Agent.md
 -> doc/agent_index/document_map.md
 -> doc/arrangement.md
 -> 相关 standard/details 文档
```

状态梳理或交接任务：

```text
Agent.md
 -> doc/agent_index/current_state.md
 -> doc/process_log.md
 -> doc/project_goal.md
```

## 文件说明

- `current_state.md`：当前实现事实、模块入口和已知能力。
- `document_map.md`：文档架构和权威层级。
- `working_rules.md`：开发决策、主动请示、文档维护和验证规则。
- `next_steps.md`：下一步可执行计划。

## 关键原则

不要把设计文档当成不可调整的唯一答案。开发中如果发现更好的轻量方案、现实约束或与 `doc/arrangement.md` 的冲突，应主动向用户说明并请求决策。
