# Ollama Skill Hub 不可变更约定

本文用于记录当前系统的架构底线和协作约定。后续实现可以演进，模块可以重构，插件可以增加，但不得破坏本文列出的核心约定。

## 1. 项目定位不可变

本项目定位为一个 Hermes-Lite 风格的轻量任务编排框架。

核心公式固定为：

```text
可定制 Agent + 可插拔 Skill + 配置驱动组合 + Ollama 推理底座
```

Ollama 只作为模型推理底座，不承担应用层治理职责。长期记忆、上下文构造、任务编排、权限控制、插件注册、事件记录、工具执行和审计都由本项目应用层负责。

本项目不应退化为单纯的 Ollama HTTP API 包装器，也不应把所有能力绑定到某个重型第三方编排框架。

## 2. 配置优先于编码

配置驱动是本项目核心思想，不得改变。

以下内容必须优先通过 `config.yaml`、插件 manifest 或等价配置声明，而不是写死在业务代码中：

- 启用哪些 Agent。
- 启用哪些 Skill。
- Agent 可调用哪些 Skill。
- 默认模型适配器和模型名。
- RAG store 选择。
- History store 选择。
- Skill 默认参数。
- 高风险能力的权限与白名单。

允许代码提供默认值，但默认值不能替代配置层的最终控制权。

## 3. Registry 是事实源

所有 Agent、Skill、ModelAdapter、RAGStore、HistoryStore 必须进入 Registry 后才能被系统调用。

不得绕过 Registry 直接在业务链路中实例化或调用插件能力。这样做是为了保证：

- `/registry` 能完整展示系统能力。
- 健康检查能定位插件状态。
- Agent 权限判断有统一依据。
- 前端配置项来自同一个事实源。
- 后续插件市场、manifest、热重载能平滑接入。

插件加载失败不应拖垮整个系统。失败信息应进入 Registry 或健康检查结果，供用户判断。

## 4. Agent 和 Skill 职责边界

Agent 是决策者，负责理解任务、规划步骤、选择 Skill、观察结果、决定是否继续和组织最终回答。

Skill 是能力单元，负责执行一个明确能力，例如模型生成、RAG 检索、MCP 调用、本地脚本、命令白名单执行或第三方工具调用。

固定边界：

- Agent 不直接访问底层模型 API。
- Agent 不直接访问向量库底层实现。
- Agent 不直接执行 shell 或脚本。
- Skill 不决定全局任务流程。
- Skill 不绕过权限治理调用其他高风险能力。
- ModelAdapter 只屏蔽模型 API 差异。
- RAGStore 只负责向量写入和检索。
- HistoryStore 只负责会话和消息持久化。

## 5. Agent 白名单不可绕过

Agent 只能调用自己 `enabled_skills` 白名单内的 Skill。

即使模型、用户参数或 workflow 指定了某个 Skill，只要该 Skill 不在当前 Agent 白名单内，就必须拒绝调用。

这条约定优先级高于模型输出、用户输入和前端选择。

## 6. Skill 必须声明元数据

长期标准中，每个 Skill 都应具备可被系统理解的元数据。

最小元数据包括：

- `name`
- `description`
- `category`
- `capabilities`
- `supports_stream`
- `input_schema`
- `output_schema`
- `config_schema`
- `permissions`
- `requires`

旧版单文件 `path` 加载可以继续兼容，但新增插件应优先采用包目录加 manifest 的形式。

## 7. 流式输出必须能力化

是否支持流式输出由 Skill 能力决定，不应依赖具体类名判断。

正确判断方式应类似：

```text
skill.supports_stream == true
+ 存在 stream_execute 能力
```

不得长期保留 `if skill == "OllamaSkill"` 这类硬编码作为框架级判断。

## 8. 复杂任务必须事件化

复杂任务不是一次请求一次响应，而是一段可观察、可恢复、可审计的运行过程。

复杂任务的长期标准流程固定为：

```text
Plan -> Act -> Observe -> Reflect -> Answer
```

这套流程应由轻量 Native PAOR engine 承载。LangGraph 等重型框架只能作为二期可选 engine，不能替代项目自己的 Agent/Skill/Registry/权限/事件标准。

长期运行态必须支持：

- `runs`
- `run_steps`
- `run_events`
- 必要时的 `command_invocations`

事件类型至少覆盖：

- `planning`
- `plan_step`
- `plan_validated`
- `step_start`
- `tool_call`
- `tool_result`
- `observation`
- `command_log`
- `reflection`
- `replan`
- `content`
- `done`
- `error`

SSE 可以作为展示通道，但不应成为唯一状态来源。刷新页面后应能从持久化事件恢复运行过程。

## 9. 同一会话串行

同一个 session 默认只能有一个 active run。

原因：

- 同一会话共享上下文。
- 并发写 message 会造成顺序混乱。
- MemoryManager 难以判断哪条 observation 应进入上下文。
- 前端恢复事件时需要稳定顺序。

不同 session 可以并行。模型调用、命令执行和后台任务并发数应由调度层统一限制。

## 10. 命令执行必须白名单化

任何命令、脚本或本地高风险操作都必须通过受控 Skill，例如 `CommandSkill`。

固定规则：

- 模型不得直接传 shell。
- 用户输入不得直接拼接成 shell。
- Agent 只能传 `command_id` 和结构化参数。
- `CommandSkill` 根据白名单查找真实命令。
- 参数必须按 schema 校验。
- stdout/stderr 应写入 run events。
- 执行完成后再由 Agent 或 Ollama 汇总解释。

不得为了方便调试引入任意命令执行入口。

## 11. 记忆与历史不可混淆

SQLite messages 是原始历史，必须完整保留。

记忆上下文是每次模型调用前构造出来的视图，不等于原始历史本身。

`/compact` 的固定原则：

- 不删除原始 messages。
- 不覆盖原始 messages。
- 只生成摘要并写入 session summary。
- 必须记录 compact boundary。
- 后续上下文由 summary、boundary 之后最近消息和当前用户问题构成。
- 当前用户问题始终完整保留并放在最后。
- 当前用户问题优先级最高。

MemoryManager 只负责上下文构造，不负责 RAG、模型选择、Thinking、stream、Agent 或 Skill 选择。

## 12. RAG 是 Skill，不是全局隐式能力

RAG 能力必须通过 `RAGSkill` 或等价 Skill 暴露。

RAGSkill 只负责检索和写入，不负责最终回答。最终回答应由 Agent 组合 RAG 结果后交给模型生成。

RAG store 和 embedding model 必须可配置、可替换，不得把 Chroma、Milvus、BGE 或某个具体模型写死为唯一实现。

## 13. ModelAdapter 是模型差异屏蔽层

上层 Skill 不应直接关心 Ollama 的具体 API 差异。

文本模型、视觉模型、embedding 模型应通过 ModelAdapter 暴露统一能力：

- `generate`
- `stream_generate`
- `embed`
- `health_check`
- `as_dict`

新增模型时应优先新增或扩展 Adapter，而不是把模型差异写进 Agent。

## 14. MCP 是内部接口入口，不是所有能力入口

`MCPSkill` 的定位是内部 MCP 服务、项目接口和公司资产的统一入口。

第三方能力不必强行塞进 MCP。第三方工具可以作为独立 Skill 接入，但进入系统后仍必须实现 `BaseSkill`，注册到 Registry，并受 Agent 白名单控制。

## 15. 前端只消费后端事实源

前端可展示和切换配置，但不应自行定义系统能力。

Agent、Skill、ModelAdapter、RAGStore、HistoryStore 的可选项应来自 `/registry` 或相关后端接口。

前端可以隐藏技术细节，但不能绕过后端权限校验。

## 16. 管理面与聊天面不能破坏核心边界

`/admin` 和 `/chat` 是交互入口，不是编排内核。

它们可以：

- 展示 Registry。
- 提交任务。
- 切换配置。
- 上传文件。
- 展示流式输出。
- 展示历史和事件。

它们不应：

- 直接执行 Skill。
- 直接执行命令。
- 绕过 Agent 白名单。
- 自行拼接高风险调用。

## 17. 文件上传必须受控

上传文件进入模型或历史前必须受大小、数量和类型约束。

图片可以转换为 base64 传给多模态模型。文本文件可以注入任务上下文。二进制文件不应无约束进入 prompt。

附件记录可以保存预览或元数据，但不应在历史记录中无限制保存大体积原始内容。

## 18. 轻量化优先

本项目的优先级是最小可用、可理解、可维护。

一期不应把 LangChain、LangGraph、Celery、复杂插件市场、分布式调度作为核心依赖。

可以预留接口：

- `OrchestrationEngine`
- `NativePlanActEngine`
- `LangGraphEngine`
- `MemoryProvider`
- `ContextEngine`

但这些能力只能作为可选扩展，不能替代本项目自己的 Agent/Skill/Registry/权限/事件标准。

## 19. 兼容旧配置

现有单文件 `path` 加载方式必须保持兼容。

新增包目录和 manifest 标准时，应采用增量策略：

```text
优先支持 package + manifest.yaml
继续支持 path + class name
两者进入同一个 Registry
```

不得通过一次性迁移破坏现有 `/chat`、`/admin`、`DefaultPlanner`、`OllamaSkill`、`RAGSkill` 和历史会话能力。

## 20. 安全默认关闭

高风险能力默认关闭，必须显式启用。

包括但不限于：

- MCP 调用。
- 命令执行。
- 外部网络工具。
- 第三方插件。
- 项目本地插件自动扫描。
- 文件系统写操作。

配置启用不等于自动授权。Agent 白名单、Skill 权限、参数 schema 和命令白名单仍然必须生效。

## 21. 测试和验收约定

每次架构性改动至少应验证：

- Python 模块可编译。
- `/registry` 能返回完整能力。
- `/health` 能展示降级状态。
- Agent 不能调用白名单外 Skill。
- 禁用的 Skill 不会被加载或调用。
- 流式输出不依赖具体类名。
- 现有 `/chat` 和 `/admin` 不被破坏。

推荐基础命令：

```powershell
python -m compileall -q api history adapters agents orchestrator rag skills utils
```

## 22. 当前实现事实

当前系统已经具备：

- `config.yaml` 驱动 Agent、Skill、ModelAdapter、RAGStore、HistoryStore 加载。
- `PluginRegistry` 作为运行时注册表。
- `DefaultPlanner` 作为默认 Agent。
- `OllamaSkill`、`RAGSkill`、`LocalSkill`、`MCPSkill` 作为基础 Skill。
- `Qwen3ChatAdapter`、`Qwen3VLAdapter`、`BgeM3EmbeddingAdapter` 作为 Ollama 适配器。
- `NullVectorStore`、`ChromaVectorStore`、`MilvusVectorStore` 作为 RAG store 适配器。
- `SQLiteHistoryStore` 保存 sessions 和 messages。
- `/admin`、`/chat`、`/registry`、`/health`、任务提交和流式接口。

当前系统尚未完全落地但已被设计为长期方向的能力：

- Agent/Skill manifest 标准。
- 完整 Skill 元数据协议。
- `supports_stream` 框架级判断。
- Native PAOR 编排引擎。
- `BaseAgent.observe/reflect/answer` 增量接口。
- `RunScheduler`。
- `runs/run_steps/run_events` 持久化。
- `MemoryManager`。
- `/compact` compact boundary。
- `CommandSkill` 白名单执行。
- `HermesOrchestratorAgent`。
- `SkillRouterAgent`。
- 可选 LangGraph engine。

## 23. 最高优先级约束

后续所有修改都必须同时满足以下条件：

```text
配置优先于编码
Registry 是事实源
Agent 只能调用白名单 Skill
Skill 必须可插拔
高风险操作必须受权限和白名单控制
复杂任务必须走 Plan/Act/Observe/Reflect/Answer
复杂任务过程必须可观察和可恢复
Ollama 不承担应用层治理
轻量化优先，重框架只能作为可选扩展
```

如果某个改动与以上约束冲突，应优先调整改动方案，而不是修改这些约定。
