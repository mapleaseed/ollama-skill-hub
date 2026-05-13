# Agent Handoff

时间：2026-05-13  
项目：Ollama Skill Hub

## 启动结论

只读本文件后，新的 Agent 应该能马上接续工作：

1. 确认工作目录和 Git 状态。
2. 按任务类型读取 `doc/agent_index/` 下的索引文件。
3. 如涉及代码，先读相关源码，再按现有风格小步实现。
4. 完成阶段性工作后更新过程文件，并给下一次会话留下明确待办。

不要把历史设计文档当成唯一标准答案。设计文档是当前方案和上下文；真正需要默认遵守的是 `doc/arrangement.md` 中的受保护约定。但即使发现优化方案与 `doc/arrangement.md` 冲突，也应主动向用户说明冲突、给出建议并请求确认，而不是机械执行历史约定。

## 环境速查

- 工作目录：`E:\WorkSpace\Agents\ollama_skill_hub`
- Shell：PowerShell
- Python 环境：`conda env ollama_env`
- 本地 Ollama：`http://localhost:11434`
- 已知模型：
  - `qwen3:14b`
  - `qwen3-vl:8b`
  - `bge-m3:latest`
- 常用服务入口：
  - `/admin`
  - `/chat`
  - `/registry`
  - `/api/sessions`
- Git 分支：`main`
- Git remote：`https://github.com/mapleaseed/ollama-skill-hub.git`

不要在项目文件中写入账号、密码、Token 等敏感信息。

## 必读索引

详细上下文不要继续塞进 `Agent.md`。需要时按索引读取：

- `doc/agent_index/README.md`：Agent 可读索引入口，说明不同任务该读哪些文件。
- `doc/agent_index/current_state.md`：当前系统实现事实、已完成能力、主要代码入口。
- `doc/agent_index/document_map.md`：文档架构、哪些是标准、哪些是设计、哪些是过程记录。
- `doc/agent_index/working_rules.md`：开发决策、请示规则、文档维护规则。
- `doc/agent_index/next_steps.md`：下一步开发计划和承接方式。

## 项目文件路径地图

以下是当前工作区内需要 Agent 知悉的项目文件路径。不包括 `.git/`、`.venv/`、`.python_deps/`、`.idea/`、`data/`、`logs/` 等本地依赖、缓存、运行数据和 IDE 文件。

根目录：

```text
Agent.md
README.md
config.yaml
environment.yml
requirements.txt
```

API 与前端：

```text
api/__init__.py
api/server.py
web/admin.html
web/chat.html
```

Agent 与编排：

```text
agents/__init__.py
agents/base_agent.py
agents/default_planner.py
orchestrator/__init__.py
orchestrator/dependency_resolver.py
orchestrator/task_manager.py
orchestrator/task_queue.py
```

Skill、模型适配器、RAG、历史：

```text
skills/__init__.py
skills/base_skill.py
skills/local_skill.py
skills/mcp_skill.py
skills/ollama_skill.py
skills/rag_skill.py
adapters/__init__.py
adapters/base_model_adapter.py
adapters/ollama_adapter.py
rag/__init__.py
rag/base_vector_store.py
rag/chroma_store.py
rag/milvus_store.py
rag/null_store.py
history/__init__.py
history/base_history_store.py
history/sqlite_history_store.py
```

工具与监控：

```text
utils/__init__.py
utils/logger.py
utils/plugin_loader.py
monitors/__init__.py
monitors/consistency_checker.py
monitors/health_monitor.py
```

文档与索引：

```text
doc/project_goal.md
doc/process_log.md
doc/arrangement.md
doc/agent_skill_plugin_standard.md
doc/agent_skill_architecture_details.md
doc/context_memory_standard.md
doc/context_memory_architecture_details.md
doc/agent_index/README.md
doc/agent_index/current_state.md
doc/agent_index/document_map.md
doc/agent_index/working_rules.md
doc/agent_index/next_steps.md
doc/milestones/README.md
doc/milestones/2026-05-12-core-runtime-baseline.md
doc/milestones/2026-05-12-web-experience.md
```

## 文档权威层级

- `doc/arrangement.md`：受保护约定。默认遵循，但不是不可讨论的圣经；有更优方案或现实冲突时先向用户请示。
- `doc/project_goal.md`：项目目标和当前阶段。阶段性成果或目标状态变化后应检查是否需要更新；涉及目标偏移时先问用户。
- `doc/process_log.md`：实时过程记录。任何架构判断、设计改写、核心代码改动、阶段性验证、文档规则变化都要同轮追加。
- `doc/*_standard.md`：当前标准草案，优先参考，但可以在发现更优方案时提出调整。
- `doc/*_architecture_details.md`：详细设计说明，用于理解上下文，不等同于强制实现。
- `doc/milestones/`：发布级里程碑记录，可作为 GitHub release note 基础；不按每次小调整拆文件。

## 里程碑维护规则

- 里程碑就是本项目对外发布的版本：完成一个大的功能模块，或进行一次重大能力调整。
- 里程碑只记录发布级成果，不记录过程流水账。
- 文档治理、索引、过程规则和约定梳理属于项目管控，不是对外产品能力，不作为里程碑。
- 同一发布目标只保留一个里程碑文件；小修小改更新 `doc/process_log.md`。
- 里程碑应说明：发布前状态、设计考量、修改内容、发布后差异、主要改动范围和验证方式。
- 完成里程碑级任务时，必须更新 `doc/milestones/README.md` 和对应里程碑文件。
- 任何里程碑文件的新增、合并、重命名、废弃、粒度调整，都必须在同一轮同步更新 `doc/milestones/README.md`，让目录摘要准确反映当前文件结构。
- 如果开发过程中多次调整同一发布目标，不新建多个碎片里程碑；应更新同一个里程碑文件，并同步更新 `doc/milestones/README.md` 的摘要或整理说明。
- 里程碑内容应能转化为 GitHub release note。
- 如果里程碑代表项目目标或受保护约定变化，先向用户请示，再更新 `doc/project_goal.md` 或 `doc/arrangement.md`。

## 当前方向

当前项目是 Hermes-Lite 风格的轻量任务编排框架：

```text
可定制 Agent + 可插拔 Skill + 配置驱动组合 + Ollama 推理底座
```

当前优先级：

1. 下一里程碑是 Agent/Skill Compatibility Baseline：完成目前仅占位的 Agent 和 Skill 兼容，接入两个不同 Agent，明确 Agent 选择和 Skill 权限边界；暂不落地 PAOR。
2. 再下一里程碑是 Native PAOR Runtime：一次会话中模型可以按计划自主运转。
3. 再下一里程碑是 Context Compact and Memory Modes：实现 `/compact`、MemoryManager、`RecentTurnContext` 和 `CompactSummaryContext` 配置。
4. 后续里程碑依次是 Session Memory and Run Visibility、Real RAG Integration、Shell Operations Skill、Spark Mock Acceptance Flow。
5. run events、白名单命令、结构化参数、命令日志事件等属于对应里程碑内部过程能力，不单独作为里程碑。

## 下一步承接

下一项建议任务见 `doc/agent_index/next_steps.md`。

如果用户说“开始下一步开发”，默认先做最小可交付切片：

```text
BaseSkill / BaseAgent 元数据
PluginRegistry.as_dict() 增强
TaskManager.stream() 去 OllamaSkill 硬编码
两个 Agent 的基础接入准备
基础验证与过程文档更新
```

开工前读取：

- `doc/agent_index/next_steps.md`
- `doc/agent_index/working_rules.md`
- `skills/base_skill.py`
- `agents/base_agent.py`
- `utils/plugin_loader.py`
- `orchestrator/task_manager.py`

## 完成任务后的固定动作

每完成一项阶段性任务，必须做以下检查：

1. 更新 `doc/process_log.md`。
2. 检查 `doc/project_goal.md` 是否需要更新当前阶段、进展或目标状态；如果涉及目标偏移，先问用户。
3. 如果改变了受保护约定，必须先获得用户确认，再更新 `doc/arrangement.md`。
4. 更新 `doc/agent_index/next_steps.md`，留下下一项可直接承接的待办。
5. 如启动方向、规则或索引结构变化，更新本 `Agent.md`。
