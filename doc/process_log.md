进程记录:
1. 确定 Hermes-Lite 目标
2. 设计模块化框架
3. 定义 Agent / Skill 接口
4. 设计插件注册加载机制
5. 配置驱动 Agent 与 Skill 权限
6. 集成 OllamaSkill 与 MCPSkill
7. 准备 /doc 记录项目目标与思考过程
8. 实现配置驱动插件加载器、运行时注册表与 Agent/Skill 权限绑定
9. 实现 TaskManager、TaskQueue、依赖解析与 FastAPI 任务接口
10. OllamaSkill 切换为 Ollama `/api/chat` 调用格式，并增加健康检查
11. 增加 `/registry`、`/agents`、`/skills`、`/admin/reload` 等运行接口
12. 增加模型适配器与 RAG 向量库适配器，默认适配 `qwen3:14b`
13. 预留 `qwen3-vl:8b`、`bge-m3:latest`、Chroma、Milvus 的可插拔配置
14. 增加 `/admin` 管理页面，支持查看和调整 Agent、Skill、模型、RAG、Thinking 和输出方式等运行配置
15. 增加 `/chat` 会话页面，形成左侧会话列表、中间消息流、底部输入框的基础聊天工作台
16. 新增 SQLite 历史会话存储 `SQLiteHistoryStore`，支持 sessions/messages 持久化、会话创建、查询、删除和标题更新
17. 完成 `/api/sessions` 系列接口，支持历史会话列表、会话详情、会话运行和流式会话输出
18. 优化会话标题逻辑：标题可编辑，手动编辑不刷新 `updated_at`，首次回答后可自动生成摘要式标题
19. 增强 `/chat` 页面配置体验，将 Agent、Skill、RAG、Thinking、stream 等高级设置收敛到低噪声配置入口
20. 将 `/chat` 调整为接近 Codex 的工作台风格，保留模型名称为主显示，适配器等技术信息作为辅助信息
21. 增强 Markdown 渲染，支持标题、段落、列表、引用、链接、行内代码和 fenced code block
22. 优化流式输出体验，避免每个 token 都强制重绘，用户上滑查看历史时不强制拉回底部
23. 增加 Assistant thinking 折叠展示，支持流式输出时同步收集 content 和 thinking
24. 增强文件上传能力，支持最多 5 个文件、图片 base64 传入模型、文本附件注入任务上下文
25. 优化附件 UI，支持多次选择累计、文件卡片展示、单独移除和常见文件类型识别
26. 新增 `doc/milestones/` 里程碑记录体系，记录 chat history、markdown/scroll、config UX 和 Codex UI 等阶段性改动
27. 完成当前架构评审，确认项目已具备 Hermes-Lite 雏形：配置驱动、Registry、Agent/Skill、ModelAdapter、RAGStore、HistoryStore 和 FastAPI/UI 主链路已形成
28. 新增 `doc/agent_skill_plugin_standard.md`，定义 Agent/Skill 插件标准、manifest 方向、权限边界、事件持久化和 CommandSkill 验收场景
29. 新增 `doc/agent_skill_architecture_details.md`，展开说明 Agent/Skill 设计原则、Registry、权限、事件、RunEvent、CommandSkill、MCP 和第三方 Skill 接入边界
30. 新增 `doc/context_memory_standard.md`，定义上下文记忆、`/compact`、记忆开关、RecentTurnContext 和 CompactSummaryContext 标准
31. 新增 `doc/context_memory_architecture_details.md`，展开说明 MemoryManager、ContextBuilder、compact boundary、前端上下文 tab 和后端边界
32. 在 `Agent.md` 中补充基本文档维护要求：`doc/process_log.md` 必须实时维护，`doc/project_goal.md` 和 `doc/arrangement.md` 如需因实际偏移变更，必须先向用户请示确认
33. 新增 `doc/arrangement.md`，记录当前系统受保护的架构约定：配置优先、Registry 事实源、Agent/Skill 白名单、事件化、轻量化和安全默认关闭
34. 将复杂任务编排方向正式调整为轻量 Native PAOR：`Plan -> Act -> Observe -> Reflect -> Answer`
35. 在 `doc/agent_skill_plugin_standard.md` 中补充 Native PAOR Orchestration 标准，明确 Reflect JSON、replan 校验、PAOR 事件和验收要求
36. 在 `doc/agent_skill_architecture_details.md` 中将编排内核详解改写为详细 PAOR 设计，补充 RunContext、NativePlanActEngine、NativePAOREngine、Plan 校验、Observe、Reflect、Replan、Answer、伪代码和实施顺序
37. 在 `doc/arrangement.md` 中同步补充 PAOR 作为复杂任务长期标准
38. 重构 `Agent.md` 为轻量交接入口，增加全项目工作文件路径地图、文档权威层级、下一步承接规则和任务完成后的固定动作
39. 新增 `doc/agent_index/` 索引目录，包含 `README.md`、`current_state.md`、`document_map.md`、`working_rules.md`、`next_steps.md`，用于按需读取项目状态、文档架构、工作规则和后续计划
40. 修正里程碑记录规则：里程碑作为发布级成果记录，不按每次 UI 或代码微调拆分；同一发布目标只保留一个里程碑文件
41. 合并原有多个 Chat/UI 里程碑为 `doc/milestones/2026-05-12-web-experience.md`，并保留 `doc/milestones/README.md` 原有目录说明风格，仅调整里程碑粒度理解
42. 强化里程碑 README 同步规则：任何里程碑文件新增、合并、重命名、废弃或粒度调整，都必须同步更新 `doc/milestones/README.md`，并将该规则写入 `Agent.md` 和 `doc/agent_index/working_rules.md`
43. 根据用户确认的发布级里程碑口径，补充 `doc/milestones/2026-05-12-core-runtime-baseline.md`，并将 Model/RAG Adapter Baseline 合并进 Core Runtime Baseline
44. 更新计划里程碑顺序，在 Native PAOR Runtime 之后、Session Memory and Run Visibility 之前加入 Context Compact and Memory Modes，包含 `/compact`、`RecentTurnContext` 和 `CompactSummaryContext`
45. 同步更新 `Agent.md`、`doc/agent_index/next_steps.md`、`doc/agent_index/document_map.md` 和 `doc/project_goal.md`，确保下一次会话能看到新的里程碑路线
