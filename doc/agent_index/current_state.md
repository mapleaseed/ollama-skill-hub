# Current State

## 项目状态

Ollama Skill Hub 当前是一个可运行的 Hermes-Lite 雏形，核心链路已经形成：

```text
FastAPI / Web UI
 -> TaskManager
 -> Agent
 -> Skill
 -> ModelAdapter / RAGStore / HistoryStore
```

当前实现偏轻量，许多高级能力已经有设计文档，但尚未全部落地。

## 已有能力

- `config.yaml` 驱动 Agent、Skill、ModelAdapter、RAGStore、HistoryStore 加载。
- `PluginRegistry` 作为运行时注册表。
- `DefaultPlanner` 作为默认 Agent。
- `OllamaSkill`、`RAGSkill`、`LocalSkill`、`MCPSkill` 作为基础 Skill。
- `Qwen3ChatAdapter`、`Qwen3VLAdapter`、`BgeM3EmbeddingAdapter` 作为 Ollama 适配器。
- `NullVectorStore`、`ChromaVectorStore`、`MilvusVectorStore` 作为 RAG store 适配器。
- `SQLiteHistoryStore` 保存 sessions 和 messages。
- `/admin` 和 `/chat` 已可用。
- `/api/sessions` 支持历史会话。
- 文件上传支持最多 5 个文件，图片传 base64，文本可注入上下文。
- Markdown、流式输出、thinking 折叠和附件 UI 已实现。

## 关键源码入口

- `api/server.py`：FastAPI 接口、页面入口、会话接口、上传处理。
- `utils/plugin_loader.py`：配置加载、插件加载、Registry。
- `orchestrator/task_manager.py`：当前任务编排主链路。
- `orchestrator/dependency_resolver.py`：workflow 依赖排序和循环检测。
- `agents/base_agent.py`：Agent 基类和 Skill 白名单校验。
- `agents/default_planner.py`：默认规划策略。
- `skills/base_skill.py`：Skill 基类。
- `skills/ollama_skill.py`：Ollama 推理 Skill。
- `skills/rag_skill.py`：RAG 检索和写入 Skill。
- `adapters/ollama_adapter.py`：Ollama chat、stream、embedding 适配器。
- `history/sqlite_history_store.py`：SQLite 会话历史。
- `web/chat.html`：聊天界面。
- `web/admin.html`：管理界面。

## 当前主要差距

- `BaseSkill` 元数据还不完整。
- `BaseAgent` 缺少 `strategy/as_dict/observe/reflect/answer` 等增量接口。
- `PluginRegistry.as_dict()` 返回信息仍偏薄。
- `TaskManager.stream()` 仍有 `OllamaSkill` 类名硬编码。
- `manifest.yaml` 插件包标准尚未落地。
- `RunScheduler`、`runs/run_steps/run_events` 尚未落地。
- `MemoryManager` 和 `/compact` 尚未落地。
- `CommandSkill` 尚未落地。
- Native PAOR 目前是设计方案，还未进入运行时代码。

## 常用验证

```powershell
python -m compileall -q api history adapters agents orchestrator rag skills utils
```

如果涉及前端脚本，可参考历史验证方式：

```powershell
node -e "const fs=require('fs'); const html=fs.readFileSync('web/chat.html','utf8'); const script=html.match(/<script>([\s\S]*)<\/script>/)[1]; new Function(script); console.log('chat js syntax ok');"
```

如果启动服务验证，优先使用当前项目约定端口，遇到占用再换端口。
