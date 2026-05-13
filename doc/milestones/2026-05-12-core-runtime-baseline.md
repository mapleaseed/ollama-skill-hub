# Core Runtime Baseline Milestone

时间：2026-05-12

## 发布摘要

本里程碑记录 Ollama Skill Hub 完成基础运行时架构，从项目目标和模块设想进入可运行的 Hermes-Lite 基础框架。

这一版本的核心价值是：系统已经具备配置驱动、插件注册、Agent/Skill 调度、模型适配器、RAG 适配器和基础 API。后续 Agent 扩展、PAOR、记忆、RAG 实接和 Shell 能力都应建立在这个运行时底座上。

## 发布前状态

发布前项目主要处于目标和结构设计阶段：

- 已明确 Hermes-Lite 风格目标。
- 已有 Agent/Skill、插件加载、配置驱动等方向设想。
- 尚未形成可运行的统一注册表和任务调度链路。
- 模型、RAG、MCP 还未被纳入统一适配器和 Skill 边界。

## 设计考量

本阶段优先解决“系统能否作为轻量编排框架跑起来”的问题。

因此选择：

- 用 FastAPI 暴露运行接口。
- 用 `config.yaml` 作为控制面。
- 用 `PluginRegistry` 管理 Agent、Skill、ModelAdapter、RAGStore、HistoryStore。
- 先保留单文件 `path` 加载，后续再引入 package + manifest。
- 让 Agent 通过 `enabled_skills` 控制 Skill 权限。
- 让模型能力和向量库能力通过 Adapter/Strategy 边界接入。
- 默认保持轻量，不引入 LangChain/LangGraph 作为核心依赖。

## 发布内容

### 配置驱动运行时

- 新增 `config.yaml` 作为运行配置入口。
- 支持配置 Ollama 地址、默认模型、模型适配器、RAG store、history store、Agent 和 Skill。
- 支持启用或禁用具体插件。

### 插件注册与加载

- 新增 `utils/plugin_loader.py`。
- 实现 `PluginRegistry`。
- 支持从配置加载 Agent、Skill、ModelAdapter、RAGStore、HistoryStore。
- 支持运行时查看 registry。

### Agent / Skill 基础链路

- 新增 `BaseAgent`。
- 新增 `DefaultPlanner`。
- 新增 `BaseSkill`。
- 新增 `OllamaSkill`、`MCPSkill`、`LocalSkill`、`RAGSkill`。
- Agent 通过 `enabled_skills` 白名单限制可调用 Skill。
- `TaskManager` 负责选择 Agent、生成计划、依赖排序、逐步 dispatch 和汇总结果。

### 任务编排基础

- 新增 `TaskManager`。
- 新增 `TaskQueue`。
- 新增 `dependency_resolver`，支持 workflow 依赖排序和循环依赖检测。
- 支持单步任务和简单多步 workflow。
- 支持 RAG 两步链路雏形：`RAGSkill -> OllamaSkill`。

### 模型适配器

模型适配能力属于本 Core Runtime Baseline 的一部分，不单独作为里程碑。

- 新增 `BaseModelAdapter`。
- 新增 `Qwen3ChatAdapter`，默认模型 `qwen3:14b`。
- 新增 `Qwen3VLAdapter`，预留 `qwen3-vl:8b` 多模态入口。
- 新增 `BgeM3EmbeddingAdapter`，预留 `bge-m3:latest` embedding 能力。
- OllamaSkill 通过模型适配器调用本地 Ollama。

### RAG Store 适配器

RAG store 适配能力也属于本 Core Runtime Baseline 的一部分。

- 新增 `BaseVectorStore`。
- 新增 `NullVectorStore` 作为默认占位。
- 预留 `ChromaVectorStore`。
- 预留 `MilvusVectorStore`。
- `RAGSkill` 可通过配置选择 embedding adapter 和 vector store。

### API 能力

- 新增任务提交接口。
- 新增任务流式接口。
- 新增 registry 查询接口。
- 新增 agents、skills、model-adapters、rag-stores、history-store 查询接口。
- 新增 health 检查接口。
- 新增配置 reload 接口。

## 主要改动范围

- `config.yaml`
- `api/server.py`
- `utils/plugin_loader.py`
- `orchestrator/task_manager.py`
- `orchestrator/task_queue.py`
- `orchestrator/dependency_resolver.py`
- `agents/base_agent.py`
- `agents/default_planner.py`
- `skills/base_skill.py`
- `skills/ollama_skill.py`
- `skills/mcp_skill.py`
- `skills/local_skill.py`
- `skills/rag_skill.py`
- `adapters/base_model_adapter.py`
- `adapters/ollama_adapter.py`
- `rag/base_vector_store.py`
- `rag/null_store.py`
- `rag/chroma_store.py`
- `rag/milvus_store.py`

## 发布后差异

发布后项目从“设计设想”变成“可运行的轻量编排框架”：

- 可以通过配置加载 Agent 和 Skill。
- 可以通过 Agent 白名单控制 Skill 权限。
- 可以通过统一 Registry 查看系统能力。
- 可以调用本地 Ollama 生成文本。
- 可以预留多模型、多模态、embedding 和 RAG store 能力。
- 可以提交单步和简单多步任务。
- 后续复杂能力有了明确承载点。

## 验收方式

基础验证：

```powershell
python -m compileall -q api history adapters agents orchestrator rag skills utils
```

接口验证：

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8008/registry -UseBasicParsing
Invoke-WebRequest -Uri http://127.0.0.1:8008/health -UseBasicParsing
```

## 后续注意

- Model/RAG Adapter Baseline 不再单独拆里程碑，它属于 Core Runtime Baseline。
- 下一阶段不是 PAOR，而是先完成 Agent/Skill 插件兼容和两个不同 Agent 的基础接入。
- PAOR、Run Events、Memory、真实 RAG、Shell 运维能力和 Spark mock 验收链路应作为后续独立发布级里程碑推进。
