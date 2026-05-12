# Agent Handoff

时间：2026-05-12

项目：Ollama Skill Hub

## 当前目标

本项目是一个基于 FastAPI、Ollama、本地 Agent、Skill、模型适配器和 RAG 适配器的可插拔 AI 应用工程。

明天优先继续做 Agent 和 Skill 的可插拔开发，让 Agent、Skill、模型适配器、RAG 数据库都能通过统一接口、配置和注册机制组合替换。

## 环境信息

- 工作目录：`E:\WorkSpace\Agents\ollama_skill_hub`
- Python 环境：`conda env ollama_env`
- 本地 Ollama：`http://localhost:11434`
- 已安装模型：
  - `qwen3:14b`
  - `qwen3-vl:8b`
  - `bge-m3:latest`
- FastAPI 本地服务常用地址：
  - `/admin`
  - `/chat`
  - `/registry`
  - `/api/sessions`
- Git 分支：`main`
- Git remote：`https://github.com/mapleaseed/ollama-skill-hub.git`

注意：不要在项目文件中写入账号、密码、Token 等敏感信息。

## 今天完成的工作

### Git 与项目基础

- 初始化为 Git 工程。
- 增加 `.gitignore`，已排除 Python 缓存、虚拟环境、日志、IDE 文件、`.idea/`、本地数据库等。
- 绑定 GitHub remote：`origin -> https://github.com/mapleaseed/ollama-skill-hub.git`。

### Ollama 与模型适配

- `config.yaml` 中已配置模型适配器：
  - `Qwen3ChatAdapter`，默认模型 `qwen3:14b`
  - `BgeM3EmbeddingAdapter`，默认模型 `bge-m3:latest`
  - `Qwen3VLAdapter`，默认模型 `qwen3-vl:8b`
- 当前优先适配 `qwen3:14b` 的文本生成和流式输出。
- 已预留 `qwen3-vl:8b` 多模态入口，前端支持上传图片和文件，后端会把图片转为 base64 传入参数。
- 已预留 `bge-m3:latest` 作为 RAG embedding 模型。

### RAG 可插拔基础

- `config.yaml` 中已配置 RAG store：
  - `NullVectorStore` 已启用
  - `ChromaVectorStore` 已预留，默认未启用
  - `MilvusVectorStore` 已预留，默认未启用
- `RAGSkill` 当前通过 `embedding_adapter_name` 和 `vector_store_name` 动态选择向量模型和向量库。

### FastAPI 与页面

- 已有 `/admin` 管理页。
- 新增并持续优化 `/chat` 页面。
- `/chat` 支持：
  - 选择 Agent
  - 选择 Skill
  - 选择模型
  - 开启或关闭 RAG
  - 选择 RAG 数据库
  - 开启或关闭 Thinking
  - 流式输出或等待输出
  - 文件上传，最多 5 个文件

### 历史会话与 SQLite

- 新增 SQLite 历史会话存储，默认数据库：`./data/history.sqlite3`
- 支持创建、查询、删除、更新会话。
- 会话标题现在由 SQLite 持久化。
- `session_id` 是 SQLite 会话行的主键，只用于定位要更新哪一个会话。
- 标题支持在 `/chat` 顶部直接编辑。
- 手动编辑标题不会刷新 `updated_at`，避免会话被错误移动到最近对话顶部。
- 首次回答后会基于内容自动生成摘要式标题，之后不再反复覆盖用户编辑的标题。

### Chat 体验

- `/chat` 已改为接近 Codex 的工作台风格：
  - 左侧紧凑会话列表
  - 中间文档式消息流
  - 底部浮动输入框
  - 小字号、低噪声配置入口
- 配置入口收敛到 `+` 弹窗。
- 模型选择主体显示模型名称，适配器只作为灰色辅助信息和 hover 提示。
- 移除 `/chat` 到管理页的跳转入口。
- `file://` 打开 `web/chat.html` 时，前端会自动请求 `http://127.0.0.1:8011`。

### Markdown 与流式输出

- Assistant 输出默认按 Markdown 渲染。
- 支持标题、段落、列表、引用、链接、行内代码、fenced code block。
- fenced code block 有复制按钮。
- 流式输出时避免每个 token 都强制重绘。
- 用户上滑查看历史时不会被流式输出强制拉回底部。
- 用户回到底部后继续自动跟随输出。
- Thinking 内容以内嵌可展开区域展示。

### 附件体验

- 附件入口已统一为一个按钮。
- 支持多次选择并累计，最多 5 个文件。
- 已选文件在输入框上方可视化展示。
- 每个文件卡片支持单独移除。
- 附件卡片按 Codex 风格显示：
  - 文件名
  - 扩展名
  - 类型化图标标签
  - 右上角移除按钮
- 已覆盖常用文件类型：
  - Word：`doc`、`docx`、`wps`、`rtf`
  - Excel：`xls`、`xlsx`、`xlsm`、`ods`
  - PowerPoint：`ppt`、`pptx`、`ppsx`
  - PDF：`pdf`
  - 文本：`txt`、`rst`、`properties`
  - Markdown：`md`、`mdx`
  - 日志：`log`、`trace`、`out`
  - 配置：`conf`、`cfg`、`env`、`toml`、`gitignore`、`dockerignore`
  - 图片：`png`、`jpg`、`jpeg`、`gif`、`webp`、`svg`、`ico`
  - 视频：`mp4`、`mov`、`avi`、`mkv`、`webm`
  - 音频：`mp3`、`wav`、`flac`、`aac`
  - 代码：`py`、`js`、`ts`、`java`、`go`、`rs`、`html`、`css`、`sql` 等
  - 数据：`csv`、`tsv`、`json`、`jsonl`、`yaml`、`parquet`
  - 压缩包：`zip`、`rar`、`7z`、`tar`、`gz`
  - 可执行文件：`exe`、`msi`、`apk`
  - 数据库：`db`、`sqlite`、`duckdb`
  - 设计稿：`fig`、`sketch`、`ai`、`xd`
  - 字体：`ttf`、`otf`、`woff`
  - 系统库：`dll`、`so`、`dylib`
- 未识别类型显示扩展名，不再显示空白方块。

### 里程碑文档

- `doc/milestones/` 用于记录里程碑式改动。
- `doc/milestones/README.md` 维护总体摘要。
- 当前已有里程碑包括：
  - `2026-05-12-chat-history.md`
  - `2026-05-12-chat-markdown-scroll.md`
  - `2026-05-12-chat-config-ux.md`
  - `2026-05-12-chat-codex-ui.md`

## 今天验证过的内容

常用检查命令：

```powershell
conda run -n ollama_env python -m compileall -q api history adapters agents orchestrator rag skills utils
```

```powershell
node -e "const fs=require('fs'); const html=fs.readFileSync('web/chat.html','utf8'); const script=html.match(/<script>([\s\S]*)<\/script>/)[1]; new Function(script); console.log('chat js syntax ok');"
```

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8011/chat -UseBasicParsing
Invoke-WebRequest -Uri http://127.0.0.1:8011/admin -UseBasicParsing
```

已确认：

- `/chat` 返回 `200`
- `/admin` 返回 `200`
- `web/chat.html` JS 语法检查通过
- Python compileall 通过
- 标题 PATCH 写入 SQLite 正常。PowerShell 控制台直接输出中文时可能出现乱码，这属于命令行编码显示问题，不是 SQLite 存储问题。

## 当前架构要点

### 模型适配器

基类：`adapters/base_model_adapter.py`

当前思想接近适配器模式：

- `BaseModelAdapter` 定义统一模型能力入口。
- `Qwen3ChatAdapter`、`BgeM3EmbeddingAdapter`、`Qwen3VLAdapter` 这类实现负责屏蔽 Ollama 具体 API 和模型差异。
- 上层 Skill 不直接关心底层模型接口细节，只关心 `generate`、`stream_generate`、`embed` 等能力。

### RAG store

当前也接近适配器模式：

- 不同向量库应该实现统一的 `search`、`upsert`、`health_check`。
- `RAGSkill` 通过配置选择具体 store。

### Agent 和 Skill

当前更接近策略模式加注册表：

- `BaseAgent` 定义 `plan`、`dispatch`、`monitor`。
- `BaseSkill` 定义 `execute` 和 `health_check`。
- `TaskManager` 根据选择的 Agent 进行计划和调度。
- `DefaultPlanner` 当前是默认策略。
- Skill 是可组合能力单元，但元数据、输入输出 schema、权限、动态组合能力还需要继续补强。

## 明天优先任务：Agent 和 Skill 可插拔开发

建议先新增里程碑设计文件：

```text
doc/milestones/2026-05-13-agent-skill-plugin.md
```

并更新：

```text
doc/milestones/README.md
```

### 推荐落地顺序

1. 阅读现有加载链路：
   - `utils/plugin_loader.py`
   - `orchestrator/task_manager.py`
   - `agents/base_agent.py`
   - `agents/default_planner.py`
   - `skills/base_skill.py`
   - `skills/ollama_skill.py`
   - `skills/rag_skill.py`

2. 补齐 Skill 元数据协议：
   - `name`
   - `description`
   - `category`
   - `input_schema`
   - `output_schema`
   - `config_schema`
   - `capabilities`
   - `supports_stream`
   - `requires`

3. 补齐 Agent 元数据协议：
   - `name`
   - `description`
   - `strategy`
   - `enabled_skills`
   - `default_skill`
   - `skill_policy`
   - `config_schema`

4. 给 `BaseSkill` 增加 `as_dict()` 或 `describe()`，让 `/registry` 能直接给前端展示可配置项。

5. 给 `BaseAgent` 增加 `as_dict()` 或 `describe()`，并明确 Agent 如何声明可用 Skill。

6. 统一 `stream_execute` 协议：
   - 不是所有 Skill 都需要流式。
   - 基类可以提供默认 `supports_stream = False`。
   - `OllamaSkill` 覆盖为 `True`。

7. 优化 `TaskManager.stream()`：
   - 现在最后一步是 `OllamaSkill` 时有特殊判断。
   - 明天应改为 capability 判断，例如 `skill.supports_stream`。
   - 避免把 `OllamaSkill` 名称写死。

8. 优化 Agent 调度：
   - 当前 `DefaultPlanner` 可作为默认策略。
   - 后续新增不同 Agent 时，应该只替换规划策略，不影响 Skill 调用协议。

9. 更新 `/registry` 返回结构：
   - agents
   - skills
   - model_adapters
   - rag_stores
   - history_store
   - capabilities
   - config_schema

10. 前端只显示用户能理解的信息：
   - 模型主体显示模型名称。
   - Agent 显示角色或用途。
   - Skill 显示能力名称。
   - 适配器、类名、路径等技术信息只作为辅助信息或 hover 提示。

### 明天建议先做的代码改动

最小可交付版本：

- `skills/base_skill.py`
  - 增加 `category`、`capabilities`、`supports_stream`
  - 增加 `as_dict()`
- `agents/base_agent.py`
  - 增加 `strategy`、`as_dict()`
  - 保持 `plan`、`dispatch`、`monitor` 不破坏
- `utils/plugin_loader.py`
  - 注册后注入 model adapters、rag stores、skills
  - `PluginRegistry.as_dict()` 输出新元数据
- `orchestrator/task_manager.py`
  - 去掉对 `OllamaSkill` 名称的硬编码，改为 `supports_stream` 判断
- `web/chat.html`
  - 读取新的 registry 元数据
  - Agent 和 Skill 下拉显示面向用户的名称和描述

## 风险与注意事项

- 不要破坏现有 `/chat` 和 `/admin` API。
- 不要在 UI 中暴露太多“适配器、路径、类名”等实现细节。
- 多模态 `qwen3-vl:8b` 目前只是预留入口，真正要验证还需要确认 Ollama 当前接口对该模型图片输入的格式要求。
- Chroma 和 Milvus 目前是预留适配，不要默认启用，避免用户没有服务时启动失败。
- PowerShell 对中文 JSON 和控制台输出容易产生编码误判，验证中文接口时优先用浏览器或 Python 发送 UTF-8/Unicode escape。
- 每次里程碑式改动前先写 `doc/milestones/` 计划文件，开发过程中同步调整，完成后更新 `README.md` 摘要。

## 建议的明天第一句话

继续 Agent 和 Skill 可插拔开发。先读取 `Agent.md`、`config.yaml`、`utils/plugin_loader.py`、`agents/base_agent.py`、`skills/base_skill.py`、`orchestrator/task_manager.py`，然后新增 `doc/milestones/2026-05-13-agent-skill-plugin.md`，按元数据协议和 `supports_stream` 去掉 `OllamaSkill` 硬编码。
