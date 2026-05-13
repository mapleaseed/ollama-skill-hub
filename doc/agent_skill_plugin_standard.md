# Agent/Skill 插件化与编排设计基线

## Summary

项目的根本定位是：**可定制 Agent + 可插拔 Skill + 配置驱动组合**。Ollama 只作为推理底座；记忆、任务编排、权限治理、工具执行、事件持久化都由应用层负责。

一期使用纯 Python 自研轻量编排内核，保持架构可控。二期可接入 LangChain/LangGraph，但只能作为可选执行引擎或生态适配层，不能替代项目自己的 Agent/Skill 标准。

## Design Principles

- Agent 是决策者：负责规划、路由、反思、控制执行流程。
- Skill 是能力单元：负责执行明确工具能力，例如 RAG、MCP、命令脚本、UI 风格辅助。
- Registry 是核心：所有 Agent/Skill 都必须注册后才能被调用。
- 配置优先：通过 manifest 和 `config.yaml` 组合 Agent/Skill。
- 权限优先：Agent 只能调用白名单 Skill；命令只能走白名单。
- 事件优先：长任务过程必须写入事件日志，便于恢复和审计。
- 框架可替换：一期 Native engine，二期可加 LangGraph engine。

## Plugin Standard

Agent/Skill 采用“包目录 + `manifest.yaml`”标准，同时兼容现有单文件 `path` 加载。

示例结构：

```text
agents/hermes_orchestrator/
  manifest.yaml
  agent.py
  prompts/

skills/command_skill/
  manifest.yaml
  skill.py
  README.md
```

manifest 基础字段：

```yaml
schema_version: 1
kind: agent | skill
id: unique_plugin_id
name: PythonClassName
version: 0.1.0
entry: agent.py:ClassName
description: 插件说明
permissions: []
config: {}
```

Skill 需要额外声明：

```yaml
category: operations | rag | mcp | ui | local
supports_stream: true | false
input_schema: {}
output_schema: {}
capabilities: []
```

## Agent Types

一期接入两个示例 Agent。

`HermesOrchestratorAgent`：

- 面向慢任务、复杂任务、多轮自主执行。
- 使用 Native PAOR 流程：`Plan -> Act -> Observe -> Reflect -> Answer`。
- 使用 JSON 计划，系统负责 schema 校验、权限校验、步骤限制。
- 适合大数据 AI 运维场景：日志分析、RAG 查手册、调用脚本、汇总结果。
- 不追求快速响应，追求可靠、可审计、可恢复。

`SkillRouterAgent`：

- 面向快问快答和少量工具调用。
- 优先使用 Ollama tool calling 判断是否调用 Skill。
- 简单问题直接回答。
- 需要知识库时调用 `RAGSkill`。
- 需要内部接口时调用 `MCPSkill`。
- 需要第三方能力时调用独立第三方 Skill。

## YAML / JSON / Tool Calling

三者分工固定：

- YAML：用于插件配置、白名单配置、Agent/Skill manifest。
- JSON：用于 `HermesOrchestratorAgent` 的结构化任务计划，便于系统校验。
- Tool calling：用于 `SkillRouterAgent` 的快速工具选择。

推荐组合：

```text
YAML manifest + JSON 编排计划 + Ollama tool calling 快速路由
```

## Native PAOR Orchestration

一期复杂任务编排采用轻量 Native PAOR，不引入 LangGraph 作为核心依赖。

固定流程：

```text
Create Run
 -> Plan
 -> Validate Plan
 -> Act
 -> Observe
 -> Reflect
 -> Replan or Continue
 -> Answer
 -> Persist Result
```

阶段职责：

- `Plan`：Agent 基于用户任务、记忆上下文和可用 Skill 生成 JSON 计划。
- `Validate Plan`：系统校验 step 数量、依赖关系、Skill 白名单、参数 schema 和命令白名单。
- `Act`：系统按计划调用 Skill，Agent 不直接执行底层工具。
- `Observe`：系统把 Skill 返回结果规范化为 observation，写入 run events。
- `Reflect`：Agent 基于 observations 判断继续、重规划、完成或失败。
- `Replan or Continue`：系统只接受通过校验的新计划或下一步。
- `Answer`：Agent 汇总 observations，调用模型生成最终答复。
- `Persist Result`：最终答复写入 history store，执行过程保留在 run events。

`Reflect` 的返回值必须是结构化 JSON：

```json
{
  "decision": "continue | replan | finish | fail",
  "reason": "判断原因",
  "next_steps": []
}
```

硬性限制：

- 每个 run 必须有 `max_steps`。
- 每个 run 必须有 `max_reflect_rounds`。
- `replan` 产生的新步骤必须重新校验。
- `finish` 之后只能进入 `Answer`，不得继续调用 Skill。
- `fail` 必须写入 error event。
- `DefaultPlanner` 可以继续使用当前轻量 `Plan -> Act -> Monitor` 流程。
- PAOR 只作为 `HermesOrchestratorAgent` 或显式配置的复杂任务策略启用。

## Persistence And Concurrency

一期采用事件日志恢复方案。

新增运行时概念：

```text
runs
run_steps
run_events
command_invocations
```

执行模型：

```text
创建 run
 -> 后台线程执行 Native PAOR
 -> 每个阶段写 run_events
 -> 前端通过 run_id 拉取/订阅事件
 -> 刷新页面后按事件恢复已产生内容
 -> 完成后写 assistant message
```

并发规则：

- 同一 session 默认串行，只允许一个 active run。
- 不同 session 可以并行。
- 并发数由 `RunScheduler` 控制。
- Ollama 调用用 semaphore 控制，不依赖 FastAPI/Ollama 默认并发行为。
- 多机器一期只要求共享数据库后可查看进度，不要求实时跨机器接管。

## CommandSkill Acceptance Scenario

一期必须实现 `CommandSkill`，作为任务编排、RAG、Skill 联通的验收标准。

安全规则：

- 只执行白名单命令或脚本。
- 不允许模型传任意 shell。
- 使用结构化 `command_id + args`。
- 不做自动重试。
- 执行日志按行写入 `run_events`。
- 模型不干预脚本执行过程，只读取执行日志和退出码。

Spark 验收链路：

```text
用户问：为什么我的 Spark 进程终止了？
 -> HermesOrchestratorAgent 规划
 -> RAGSkill 检索 Spark 修复手册
 -> Agent 选择白名单修复脚本
 -> CommandSkill 执行脚本
 -> 实时记录脚本日志
 -> Ollama 基于手册、日志、exit_code 生成最终答复
```

## MCP And Third-Party Skills

`MCPSkill` 定位为公司内部 MCP/接口资产管理入口，不强制统一所有第三方 Skill。

边界：

- `MCPSkill`：管理内部 MCP 服务、项目接口、URL、端口、入参出参、调用准则。
- 第三方 Skill：作为独立插件目录接入，例如 UI 风格 Skill、代码生成 Skill、外部工具 Skill。
- 所有外部能力进入系统后，都必须适配为 `BaseSkill`，再由 Registry 管理。

目标使用方式：

```text
把 Skill 目录放到 skills/
 -> 配置 package 或自动扫描
 -> 校验 manifest
 -> 加载 Python class
 -> 注册到 SkillRegistry
 -> Agent 白名单启用
 -> Ollama 可调用
```

## LangChain / LangGraph Position

一期不把 LangChain/LangGraph 作为核心依赖。

预留接口：

```text
OrchestrationEngine
  - NativePlanActEngine
  - LangGraphEngine（二期）
```

二期改造原则：

- LangGraph 只作为复杂 Agent 的执行引擎。
- LangChain 只作为第三方 tool/RAG 生态适配层。
- 项目自己的 Skill manifest、权限、事件、记忆标准不被替换。
- `BaseSkill` 后续可增加 `to_langchain_tool()` 适配方法。

LangChain/Ollama 兼容性判断：

- LangChain 支持 Ollama，但工具调用稳定性取决于具体本地模型。
- API Key 大模型通常在 tool calling 和结构化输出上更稳定。
- 因此复杂编排不完全依赖 tool calling，优先 JSON 计划 + 系统校验。

## Test And Acceptance

一期验收必须覆盖：

- 新旧插件加载兼容。
- Agent/Skill manifest 校验。
- `/registry` 展示完整 Agent/Skill 元数据。
- `SkillRouterAgent` 可快速调用 RAG/MCP/第三方 Skill。
- `HermesOrchestratorAgent` 可执行 Native PAOR 多步计划。
- `Reflect` 可返回 `continue/replan/finish/fail`，且系统会校验 replan 后的新步骤。
- `CommandSkill` 只能执行白名单命令。
- Spark 修复链路端到端跑通。
- 刷新页面后能恢复 run events 和已输出内容。
- 同 session 串行、不同 session 并行。
- 现有 `/chat`、`/admin`、`DefaultPlanner` 不破坏。

## Assumptions

- 后续正式固化到 `doc/standards/agent-skill-plugin-standard.md`。
- 标准文档使用中文，保留必要英文术语。
- 一期优先完成插件标准、Native PAOR、两个 Agent、CommandSkill、事件持久化和 Spark 验收链路。
- LangGraph/LangChain 作为二期能力，不影响一期核心设计。
