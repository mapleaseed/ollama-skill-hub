# Milestones

本目录用于记录 Ollama Skill Hub 的发布级里程碑。

里程碑可以理解为本项目对外发布的版本：完成了一个大的功能模块，或者进行了一次重大能力调整。它可以作为 GitHub release note 的基础材料。

## 记录约定

- 一项发布目标只保留一个里程碑文件。
- 里程碑应记录：发布前状态、设计考量、修改内容、发布后差异、主要改动范围和验证方式。
- 小修小改、过程调整、内部讨论和临时设计变更记录到 `doc/process_log.md`，不单独生成里程碑文件。
- 过程性能力属于对应发布目标的一部分，不单独拆里程碑。例如 run events、结构化参数、命令日志事件应归入各自里程碑。
- 文档治理、索引、过程规则、约定梳理属于项目管控，不是对外产品能力，不作为发布里程碑。
- 任何里程碑文件新增、合并、重命名、废弃或粒度调整时，必须同步更新本文件。
- 如果里程碑代表项目目标或受保护约定变化，先向用户请示，再更新 `doc/project_goal.md` 或 `doc/arrangement.md`。

## 已发布里程碑

| 顺序 | 时间 | 文件 | 摘要 |
| --- | --- | --- | --- |
| 1 | 2026-05-12 | `2026-05-12-core-runtime-baseline.md` | 完成基础运行时架构：FastAPI、配置驱动、Registry、Agent/Skill、TaskManager、模型适配器、RAG store 适配器和基础 API。 |
| 2 | 2026-05-12 | `2026-05-12-web-experience.md` | 发布 Web 会话工作台：新增 `/chat`、SQLite 历史会话、Markdown 输出、流式滚动控制、低噪声配置、Codex 风格 UI 和附件体验。 |

## 计划里程碑

| 顺序 | 里程碑 | 状态 | 范围 |
| --- | --- | --- | --- |
| 3 | Agent/Skill Compatibility Baseline | 下一步 | 完成目前占位的 Agent 和 Skill 兼容能力，实现两个不同 Agent 的基础接入、Agent 选择、Agent 可用 Skill 权限边界和 Registry 元数据展示；不落地 PAOR。 |
| 4 | Native PAOR Runtime | 计划中 | 用户提出一次会话后，模型可以按计划自主执行 `Plan -> Act -> Observe -> Reflect -> Answer`；支持计划、观察、反思、重规划和最终回答。 |
| 5 | Context Compact and Memory Modes | 计划中 | 实现 `/compact`、MemoryManager 和上下文模式配置；支持 `RecentTurnContext` 最近轮会话模式和 `CompactSummaryContext` 摘要压缩模式，保留原始 messages，不删除历史。 |
| 6 | Session Memory and Run Visibility | 计划中 | 实现模型记忆、刷新后恢复当前任务进度、停止本次会话按钮、一次会话过程中的模型调用展开、thinking 和中间输出查看，避免用户只能等待最后结果。 |
| 7 | Real RAG Integration | 计划中 | 接入真实 RAG 能力，不再只是 Null/Chroma/Milvus 占位；支持实际写入、检索、引用和回答链路。 |
| 8 | Shell Operations Skill | 计划中 | 模型具备受控 Shell 能力：基于大数据集群配置、白名单命令、指定目录脚本、日志截断分析和运维手册对照，执行健康检查和受控脚本。 |
| 9 | Spark Mock Acceptance Flow | 计划中 | 跑通 Spark mock 验收链路，验证 RAG、Command/Shell、日志事件、Agent 分析和最终回答的端到端闭环。 |

## 整理说明

2026-05-13 对里程碑粒度进行整理：

- `Model/RAG Adapter Baseline` 不单独作为里程碑，已合并进 `Core Runtime Baseline`。
- 原 `2026-05-12-chat-history.md`
- 原 `2026-05-12-chat-markdown-scroll.md`
- 原 `2026-05-12-chat-config-ux.md`
- 原 `2026-05-12-chat-codex-ui.md`

以上四个 Chat/UI 文件本质上都属于同一个 Web 会话工作台发布目标，现已合并为 `2026-05-12-web-experience.md`，不再分别维护。

`Documentation & Governance Baseline` 不作为里程碑；文档管控、交接索引、过程规则和约定变更属于项目治理，不是对外产品发布。
