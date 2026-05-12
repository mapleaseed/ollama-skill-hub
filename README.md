# ollama_skill_hub

开箱即用的 Hermes-Lite 风格轻量任务编排框架，支持 Ollama、MCP 和本地 Skill，可通过配置热插拔 Agent/Skill。

## 当前能力

- 启动时读取 `config.yaml`，加载启用的 Agent 和 Skill。
- 支持为每个 Agent 配置可调用 Skill 白名单。
- 默认 `DefaultPlanner` 可按白名单将任务派发到已启用的 Skill。
- `OllamaSkill` 通过模型适配器调用 Ollama，默认使用 `qwen3:14b`。
- 支持模型适配器和 RAG 向量库适配器，后续可通过配置切换 `qwen3-vl:8b`、`bge-m3:latest`、Chroma、Milvus。
- FastAPI 暴露任务提交、注册表查看、健康检查、配置重载接口。

## 安装依赖

推荐使用 Conda 环境：

```bash
conda env create -f environment.yml
conda activate ollama_env
```

如果环境已存在：

```bash
conda activate ollama_env
python -m pip install -r requirements.txt
```

PyCharm 中建议选择该解释器：

```text
D:\Environment\Env\python\miniconda\envs\ollama_env\python.exe
```

也可以直接使用 pip：

```bash
python -m pip install -r requirements.txt
```

## 启动服务

```bash
uvicorn api.server:app --host 127.0.0.1 --port 8008 --reload
```

启动后访问：

- `GET /admin`：打开管理页面
- `GET /chat`：打开临时历史会话页面
- `GET /health`：查看框架与外部服务状态
- `GET /registry`：查看已加载 Agent/Skill
- `GET /model-adapters`：查看已加载模型适配器
- `GET /rag-stores`：查看已加载 RAG 向量库适配器
- `POST /task/submit`：提交任务
- `POST /task/submit-form`：表单提交任务，支持最多 5 个上传文件
- `POST /task/stream`：SSE 流式任务输出
- `GET /api/sessions`：查看历史会话
- `POST /api/sessions`：创建历史会话
- `GET /api/sessions/{session_id}`：查看会话消息
- `POST /api/sessions/{session_id}/run`：在指定会话中等待输出
- `POST /api/sessions/{session_id}/stream`：在指定会话中流式输出
- `POST /admin/reload`：重载配置

## 管理页面

启动服务后打开：

```text
http://127.0.0.1:8008/admin
```

页面支持：

- 运行时切换 Agent、Skill、模型适配器和模型名
- 保存当前 Agent 的 Skill 白名单组合
- 控制是否启用 RAG，并选择已加载的向量库适配器
- 控制 Thinking 模式
- 切换等待输出或流式输出
- 上传最多 5 个文件；图片会转换为 base64 传给 Ollama `images` 字段，文本文件会附加到任务上下文

## 临时历史会话

启动服务后打开：

```text
http://127.0.0.1:8008/chat
```

会话页支持：

- SQLite 临时历史会话，默认文件为 `data/history.sqlite3`
- 左侧卡片式历史瀑布流
- 右侧当前会话消息流
- 底部固定输入框
- 模型适配器和模型名默认可见，高级设置面板用于调整 Agent、Skill、RAG、Thinking 和输出方式
- 每条 Assistant 消息内嵌 Thinking 折叠区
- 等待输出和 SSE 流式输出
- 文件上传、多模态图片 base64 传递和文本附件上下文注入

## 提交任务示例

默认走 `DefaultPlanner`，未指定 Skill 时优先使用 `OllamaSkill`：

```bash
curl -X POST http://127.0.0.1:8008/task/submit ^
  -H "Content-Type: application/json" ^
  -d "{\"task\":\"用三句话解释 Hermes-Lite 的价值\"}"
```

指定模型适配器：

```bash
curl -X POST http://127.0.0.1:8008/task/submit ^
  -H "Content-Type: application/json" ^
  -d "{\"task\":\"用三句话解释 Agent/Skill 可插拔架构\",\"params\":{\"skill\":\"OllamaSkill\",\"model_adapter\":\"Qwen3ChatAdapter\"}}"
```

指定本地 Skill：

```bash
curl -X POST http://127.0.0.1:8008/task/submit ^
  -H "Content-Type: application/json" ^
  -d "{\"task\":\"ping\",\"params\":{\"skill\":\"LocalSkill\"}}"
```

自定义多步 workflow：

```json
{
  "task": "生成一份执行摘要",
  "agent": "DefaultPlanner",
  "params": {
    "workflow": [
      {
        "id": "step-1",
        "name": "draft",
        "skill": "OllamaSkill",
        "prompt": "先生成摘要初稿"
      },
      {
        "id": "step-2",
        "name": "polish",
        "skill": "OllamaSkill",
        "prompt": "润色摘要，使其更清晰",
        "depends_on": ["step-1"]
      }
    ]
  }
}
```

## 配置说明

`config.yaml` 是控制面：

- `ollama.base_url`：Ollama 服务地址，通常是 `http://localhost:11434`
- `ollama.url`：Ollama Chat API 地址，通常是 `http://localhost:11434/api/chat`
- `ollama.default_adapter`：默认模型适配器，当前为 `Qwen3ChatAdapter`
- `ollama.default_model`：默认 Ollama 文本模型，当前为 `qwen3:14b`
- `model_adapters[]`：模型策略配置。当前启用 `Qwen3ChatAdapter` 和 `BgeM3EmbeddingAdapter`，`Qwen3VLAdapter` 作为多模态后续扩展预留。
- `rag_stores[]`：RAG 向量库策略配置。当前启用 `NullVectorStore`，Chroma/Milvus 默认关闭，安装依赖后可启用。
- `agents[].enabled_skills`：控制某个 Agent 能调用哪些 Skill
- `skills[].enabled`：控制启动时是否加载该 Skill
- `MCPSkill` 默认关闭，避免未部署 MCP 服务时影响健康检查；需要 MCP 时将其启用并加入 Agent 白名单。

## 适配器设计

项目采用接近 Java Adapter/Strategy 的设计方式：

- 模型适配器：`BaseModelAdapter` 定义统一模型接口，`Qwen3ChatAdapter`、`Qwen3VLAdapter`、`BgeM3EmbeddingAdapter` 负责具体 Ollama 模型差异。
- RAG 向量库适配器：`BaseVectorStore` 定义统一写入和检索接口，`NullVectorStore`、`ChromaVectorStore`、`MilvusVectorStore` 负责具体数据库差异。
- Skill 不直接绑定具体模型或数据库，只读取配置中的适配器名称。
- Agent 仍通过 `enabled_skills` 白名单控制可调用 Skill，保持 Agent/Skill 插拔边界清晰。

当前优先路径是 `DefaultPlanner -> OllamaSkill -> Qwen3ChatAdapter -> qwen3:14b`。
