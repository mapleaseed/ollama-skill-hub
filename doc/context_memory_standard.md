# 上下文记忆与 /compact 标准

本文档定义 Ollama Skill Hub 的会话记忆、上下文构造和 `/compact` 压缩标准。该标准只处理“当前会话如何从 SQLite 历史中构造模型上下文”，不处理 RAG、Thinking、top_k、stream、模型、Agent 或 Skill 的运行配置。

## 1. 当前系统事实

当前 SQLite 历史存储已经保存：

```text
sessions
  id
  title
  summary
  status
  last_model
  last_skill
  created_at
  updated_at

messages
  id
  session_id
  role
  content
  thinking
  run_config
  attachments
  created_at
```

当前事实：

- SQLite 已经按 `session_id` 保存全量 `messages`。
- `sessions.summary` 字段已经存在。
- 当前还没有真正的 `MemoryManager`。
- 当前还没有 compact boundary。
- 当前会话历史主要用于前端展示，不会自动作为下一轮 Ollama 请求的上下文。

## 2. 核心目标

上下文记忆能力的目标是让系统在不删除原始历史的前提下，为每次模型调用构造一个可控、可压缩、可解释的上下文视图。

关键原则：

- 原始 `messages` 永久保留。
- `/compact` 只生成摘要，不删除历史。
- 每次模型请求前动态构造 `MemoryContext`。
- 当前用户问题始终完整保留。
- 当前用户问题始终放在 prompt 最后。
- 历史摘要仅作为参考。
- 如果历史摘要与当前问题冲突，以当前问题为准。

## 3. /compact 固定标准

`/compact` 的行为必须固定为以下标准：

```text
1. SQLite 继续保存全量 messages
2. /compact 生成当前 session 的压缩摘要
3. 摘要写入 sessions.summary
4. 增加 compact boundary，记录摘要覆盖到哪条 message
5. 后续请求由 MemoryManager 构造：
   sessions.summary
   + boundary 之后的最近消息
   + 当前用户问题
6. 当前问题始终放最后，并声明优先级最高
```

`/compact` 不得删除、覆盖、截断原始 `messages`。

## 4. 记忆开关

系统必须支持是否开启记忆功能。

```text
memory_enabled=false
 -> 不读取历史上下文
 -> 不读取 sessions.summary
 -> 不读取最近 messages
 -> 只使用当前用户问题

memory_enabled=true
 -> 根据 memory_mode 选择上下文策略
 -> 根据 memory_config 构造 MemoryContext
 -> 将 MemoryContext 注入 Agent/Ollama
```

关闭记忆不影响 SQLite 继续保存用户和助手消息。

## 5. 可插拔上下文模式

一期支持两种模式。

### 5.1 RecentTurnContext

最近对话模式。

构造方式：

```text
当前 session 内最近 N 轮对话
+ 当前用户问题
```

适用场景：

- 简单聊天。
- 不需要 `/compact` 的短会话。
- 希望行为直观、低复杂度的场景。

推荐参数：

```yaml
RecentTurnContext:
  max_turns: 5
  max_context_chars: 12000
```

### 5.2 CompactSummaryContext

摘要压缩模式。

构造方式：

```text
sessions.summary
+ compact boundary 之后最近 N 轮对话
+ 当前用户问题
```

适用场景：

- 长会话。
- 已执行 `/compact` 的会话。
- 需要保留长期上下文但避免把全部历史塞给模型的场景。

推荐参数：

```yaml
CompactSummaryContext:
  max_turns_after_compact: 5
  max_context_chars: 16000
  summary_max_chars: 3000
  conflict_policy: current_input_wins
```

## 6. 推荐配置

推荐配置结构：

```yaml
memory:
  enabled: true
  mode: CompactSummaryContext
  modes:
    RecentTurnContext:
      max_turns: 5
      max_context_chars: 12000
    CompactSummaryContext:
      max_turns_after_compact: 5
      max_context_chars: 16000
      summary_max_chars: 3000
      conflict_policy: current_input_wins
```

字段含义：

- `enabled`：是否开启记忆功能。
- `mode`：当前会话上下文构造模式。
- `max_turns`：最近对话模式保留的最大轮数。
- `max_turns_after_compact`：摘要压缩模式中 compact boundary 之后保留的最近轮数。
- `max_context_chars`：上下文构造结果的最大字符预算。
- `summary_max_chars`：`/compact` 生成摘要的目标最大字符数。
- `conflict_policy`：冲突处理策略，一期固定为 `current_input_wins`。

## 7. 配置边界规范

上下文/记忆配置只负责回答一个问题：

```text
本次请求如何从当前 session 的 messages、sessions.summary 和 compact boundary 中构造模型上下文？
```

上下文/记忆配置不负责：

- 是否开启 RAG。
- 使用哪个 RAG store。
- RAG top_k。
- 是否开启 Thinking。
- 是否流式输出。
- 使用哪个模型。
- 使用哪个 Agent。
- 使用哪个 Skill。

这些配置已经分别属于 RAG、输出、模型、Agent/Skill 配置域，不允许混入上下文模式配置。

## 8. 前端配置边界

`/chat` 配置面板新增“上下文”tab。

该 tab 只包含：

- 开启记忆功能。
- 记忆模式。
- 当前模式参数。
- 压缩当前会话操作。

该 tab 不得包含：

- RAG 数据库。
- Top K。
- Thinking。
- Stream。
- Model Adapter。
- Agent。
- Skill。

关闭记忆时，模式参数区域可以置灰，但不需要深度隐藏，方便用户理解当前配置。

## 9. 后端边界

`MemoryManager` 只接收：

```text
session_id
current_input
memory_enabled
memory_mode
memory_config
```

`MemoryManager` 只输出：

```text
MemoryContext.prompt
使用到的 summary/messages 元信息
```

`MemoryManager` 不读取、不解释、不修改：

```text
rag_enabled
vector_store_name
top_k
think
stream
model_adapter
skill
```

## 10. Prompt 优先级标准

构造给模型的上下文必须明确分区：

```text
[历史摘要，仅供参考]
...

[最近对话]
...

[当前用户问题，优先级最高]
...
```

固定规则：

- 当前问题完整保留。
- 当前问题放在最后。
- 历史摘要只作为参考。
- 当前问题与历史摘要冲突时，以当前问题为准。
- `thinking` 不作为记忆上下文默认输入。

## 11. 验收标准

- `memory_enabled=false` 时不注入历史摘要或最近消息。
- `RecentTurnContext` 只注入当前 session 最近 N 轮对话和当前问题。
- `CompactSummaryContext` 注入 `sessions.summary`、compact boundary 之后最近 N 轮和当前问题。
- `/compact` 写入 `sessions.summary` 和 compact boundary，不删除 `messages`。
- 当前问题位于 prompt 最后，并声明优先级最高。
- 前端“上下文”tab 不包含 RAG、Thinking、top_k、stream、模型、Agent、Skill 配置。
- 后端 `MemoryManager` 不依赖 RAG、Thinking、top_k 等参数。
