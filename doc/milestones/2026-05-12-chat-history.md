# Chat History Milestone

时间：2026-05-12

## 设计目标

为 Ollama Skill Hub 增加临时历史会话能力，新增独立 `/chat` 页面，保留 `/admin` 管理页。页面参考 Kimi 的会话结构：左侧卡片式历史，右侧当前会话，底部固定输入框。Thinking 展示参考 Codex，内嵌在 Assistant 消息中，可展开查看。

## 计划内容

- 新增历史存储适配器，默认使用 SQLite，后续可替换 MongoDB。
- 新增会话 API：创建、列表、详情、删除、等待输出和流式输出。
- 新增 `/chat` 页面：历史卡片、会话消息、底部输入、配置折叠。
- 保存完整运行记录：用户输入、模型输出、Thinking、运行配置和附件元信息。
- 文件上传沿用最多 5 个文件限制，图片转换为 base64，文本注入上下文。

## 实施调整

- 历史存储适配器命名为 `SQLiteHistoryStore`，配置项为 `history_store`。
- SQLite 文件默认放在 `data/history.sqlite3`，该文件被现有 `.gitignore` 的 `*.sqlite3` 排除。
- Thinking 不再放在独立面板，而是在每条 Assistant 消息中以折叠区显示。
- `/admin` 保持管理用途，`/chat` 专注历史会话体验。

## 验收标准

- `/chat` 可以打开。
- 可以创建、查看、删除会话。
- 左侧历史卡片可以恢复会话。
- 等待输出和流式输出都能写入历史。
- Assistant 消息中的 Thinking 默认收起，可展开。
- SQLite 自动初始化。
