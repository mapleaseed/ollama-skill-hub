# Web Experience Milestone

时间：2026-05-12

## 发布摘要

本里程碑记录 Ollama Skill Hub 从偏后端/API 和管理页工具，演进为具备 AI 会话工作台的 Web 体验。

这不是多次独立 UI 发布，而是同一项 Web 能力从无到有、反复打磨后的阶段性发布。后续可作为 GitHub release note 的基础。

## 发布前状态

发布前项目已经具备：

- FastAPI 服务。
- `/admin` 管理页。
- Agent、Skill、模型适配器、RAG store 的基础配置和注册。
- 任务提交、注册表、健康检查等后端接口。

但面向日常 AI 使用仍有明显缺口：

- 缺少独立会话工作台。
- 缺少历史会话持久化。
- 用户无法像聊天工具一样恢复上下文和查看历史。
- 模型输出还没有 Markdown、代码块复制、thinking 折叠等阅读体验。
- 文件上传和运行配置暴露方式偏工具化。

## 设计考量

本次 Web 体验围绕三个目标推进：

1. 让项目具备可日常使用的 AI 会话入口，而不只是 API 和管理页。
2. 保留配置驱动和 Agent/Skill 可插拔能力，但不要让普通会话界面显得像表单配置工具。
3. 让输出阅读、流式生成、附件和历史恢复更接近现代 AI 工作台体验。

因此最终选择：

- `/admin` 继续承担管理和调试用途。
- `/chat` 专注会话、历史、输入、输出和轻量运行配置。
- SQLite 作为最小可用历史存储。
- Markdown 和流式滚动在前端本地实现，不引入重依赖。
- 高级配置低噪声收纳，模型名称作为主要可见上下文。

## 发布内容

### 会话工作台

- 新增 `/chat` 页面。
- 左侧提供历史会话列表。
- 中间展示当前会话消息流。
- 底部提供固定输入区。
- 会话标题支持编辑。
- 首次回答后可基于内容生成摘要式标题。

### 历史会话

- 新增 `SQLiteHistoryStore`。
- 默认数据库为 `data/history.sqlite3`。
- 新增 sessions/messages 持久化。
- 支持会话创建、列表、详情、删除、运行和流式运行。
- 保存用户输入、助手输出、thinking、运行配置和附件元信息。

### 输出阅读体验

- Assistant 输出默认按 Markdown 渲染。
- 支持标题、段落、列表、引用、链接、行内代码和 fenced code block。
- fenced code block 支持复制。
- thinking 内容以内嵌折叠区展示。

### 流式体验

- 支持等待输出和 SSE 流式输出。
- 流式生成时避免每个 token 都强制重绘。
- 用户上滑查看历史时不强制拉回底部。
- 用户回到底部后继续跟随生成。
- 生成完成后不重建当前消息区，减少闪烁和跳动。

### 配置体验

- 将模型名称作为主要可见上下文。
- Agent、Skill、RAG、Top K、Thinking、stream 等配置收纳到低频设置入口。
- 配置仍由发送任务时读取，不改变后端任务 API 的核心结构。
- 技术性适配器信息只作为辅助信息或 hover 提示。

### 视觉与交互

- `/chat` 视觉调整为更接近 Codex 工作台风格。
- 降低卡片堆叠、阴影和表单噪声。
- 历史列表更紧凑。
- 消息流更偏文档式阅读。
- 输入区保留浮层 composer，但弱化边框和装饰。

### 附件能力

- 支持最多 5 个文件。
- 图片转换为 base64 传入模型参数。
- 文本文件内容可注入任务上下文。
- 支持多次选择累计文件。
- 已选文件以卡片形式展示。
- 每个附件可单独移除。
- 常见 Office、PDF、文本、Markdown、日志、配置、图片、音视频、代码、数据、压缩包、可执行文件、数据库、设计稿、字体和系统库文件都有类型化显示。

## 主要改动范围

- `api/server.py`
- `web/chat.html`
- `web/admin.html`
- `history/base_history_store.py`
- `history/sqlite_history_store.py`
- `config.yaml`
- `README.md`

## 发布后差异

发布后项目具备了一个可直接使用的 AI Web 工作台：

- 用户可以通过 `/chat` 创建和恢复会话。
- 会话记录持久化到 SQLite。
- 模型输出具备 Markdown 阅读体验。
- 流式生成不会破坏用户查看历史的操作。
- 附件和多模态入口具备基本可用性。
- 运行配置仍然保留，但不再喧宾夺主。
- `/admin` 与 `/chat` 职责分离。

## 验收方式

基础验证：

```powershell
python -m compileall -q api history adapters agents orchestrator rag skills utils
```

前端脚本验证：

```powershell
node -e "const fs=require('fs'); const html=fs.readFileSync('web/chat.html','utf8'); const script=html.match(/<script>([\s\S]*)<\/script>/)[1]; new Function(script); console.log('chat js syntax ok');"
```

服务验证：

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8011/chat -UseBasicParsing
Invoke-WebRequest -Uri http://127.0.0.1:8011/admin -UseBasicParsing
```

## 后续注意

- Web 体验后续再有发布级变化时，应更新或新增一个发布级里程碑，而不是按每次样式微调拆文件。
- 小修小改只记录在 `doc/process_log.md`。
- 如果某次改动可以作为 GitHub release note 独立说明，再新增里程碑文件。
