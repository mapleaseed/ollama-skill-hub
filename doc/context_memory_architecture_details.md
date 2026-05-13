# 上下文记忆与 /compact 架构详解

本文档是对 [context_memory_standard.md](./context_memory_standard.md) 的展开说明，解释 MemoryManager、ContextBuilder、SQLite compact boundary、`/compact` 流程和前端配置边界。

## 1. 设计背景

Ollama 本身不保存长期记忆。每次模型回答时，它只看到本次请求传入的 prompt/messages。当前项目虽然已经把会话全量消息保存到 SQLite，但下一轮请求并不会自动把这些历史注入模型。

上下文记忆能力要解决的问题是：

```text
从 SQLite 中保存的全量历史中，按当前配置构造一个适合本次模型调用的上下文窗口。
```

这个上下文窗口不是数据库里的永久字段，而是每次请求时动态构造的 `MemoryContext`。

## 2. 术语解释

### MemoryManager

MemoryManager 是后端上下文构造入口。它根据 `memory_enabled`、`memory_mode` 和 `memory_config` 选择具体策略，并输出 `MemoryContext`。

### MemoryContext

MemoryContext 是本次模型调用使用的上下文视图。

它通常包含：

- `prompt`：最终注入 Agent/Ollama 的文本。
- `summary_used`：是否使用了 `sessions.summary`。
- `message_ids_used`：使用了哪些消息。
- `mode`：使用的上下文模式。
- `warnings`：裁剪、缺少 boundary 等提示信息。

### ContextBuilder

ContextBuilder 是具体上下文构造策略。

一期至少包括：

- `RecentTurnContextBuilder`
- `CompactSummaryContextBuilder`

后续可以继续增加模式，但不能把 RAG、Thinking、top_k 等运行配置塞进 ContextBuilder。

### RecentTurnContext

最近对话模式。它只使用当前 session 内最近 N 轮对话和当前用户问题。

### CompactSummaryContext

摘要压缩模式。它使用 `sessions.summary`、compact boundary 之后最近 N 轮对话和当前用户问题。

### compact boundary

compact boundary 表示当前 `sessions.summary` 覆盖到哪条 message。

推荐字段：

```text
sessions.compacted_until_message_id
```

有了 boundary 后，系统就能避免把已经被 summary 覆盖的旧消息再次完整塞进上下文。

### sessions.summary

当前 session 的压缩摘要。它是模型上下文参考材料，不是原始历史的替代品。

### messages

当前 session 的全量原始消息。`/compact` 不得删除或覆盖它。

## 3. 后端策略模式

推荐结构：

```text
MemoryManager
  - RecentTurnContextBuilder
  - CompactSummaryContextBuilder
```

统一接口：

```python
class BaseContextBuilder:
    name: str

    def build(self, session, messages, current_input, config):
        raise NotImplementedError
```

MemoryManager 负责选择策略：

```python
builder = context_registry.get(memory_mode)
memory_context = builder.build(
    session=session,
    messages=messages,
    current_input=current_input,
    config=memory_config,
)
```

## 4. 后端输入输出边界

MemoryManager 输入：

```text
session_id
current_input
memory_enabled
memory_mode
memory_config
```

MemoryManager 输出：

```text
MemoryContext.prompt
使用到的 summary/messages 元信息
```

MemoryManager 不读取、不解释、不修改：

```text
rag_enabled
vector_store_name
top_k
think
stream
model_adapter
skill
```

这样可以保证上下文配置域独立，不和 RAG、输出、模型、Agent/Skill 配置耦合。

## 5. SQLite 设计建议

保留现有 `messages` 全量记录。

扩展 `sessions`：

```text
summary
compacted_until_message_id
compacted_at
```

可选新增审计表：

```text
session_compactions
  id
  session_id
  summary
  covered_until_message_id
  source_message_count
  model
  created_at
```

`sessions.summary` 保存当前生效摘要。`session_compactions` 保存历史 compact 版本，便于后续审计、回滚或调试压缩质量。

## 6. /compact 后端流程

`/compact` 应作为会话控制命令处理，不作为普通用户任务送给业务 Agent。

流程：

```text
识别 /compact
 -> 不作为普通用户问题送入业务 Agent
 -> 读取当前 session 全量 messages
 -> 调用 Ollama 生成压缩摘要
 -> 找到当前最后一条 message_id
 -> 写 sessions.summary
 -> 写 compact boundary
 -> 返回压缩结果
```

注意事项：

- `/compact` 不删除原始 messages。
- `/compact` 不改变当前会话标题，除非后续明确要求。
- `/compact` 可以写入一条系统提示或 assistant 消息，用于前端展示“已压缩上下文”。
- 如果当前 session 没有足够消息，可以返回“无需压缩”。

## 7. 请求执行流程

普通消息发送时：

```text
API 收到 session_id + task
 -> 读取 memory_enabled/memory_mode/memory_config
 -> 如果 memory_enabled=false，只使用当前 task
 -> 如果 memory_enabled=true，调用 MemoryManager.build_context
 -> 将 MemoryContext.prompt 写入 params["context"]
 -> TaskManager / Agent / OllamaSkill 使用 params["context"]
```

当前项目已有 `DefaultPlanner.build_skill_inputs()` 会把 `params["context"]` 拼进 `OllamaSkill` prompt。后续 MemoryManager 生成的 `context` 可以复用这个入口。

## 8. RecentTurnContextBuilder 细节

输入：

```text
session
messages
current_input
config.max_turns
config.max_context_chars
```

构造：

```text
[最近对话]
最近 N 轮 user/assistant 消息

[当前用户问题，优先级最高]
current_input
```

规则：

- 不使用 `sessions.summary`，除非配置显式增加 `include_summary`。
- 默认不包含 `thinking`。
- 附件内容仍由现有附件逻辑处理，不属于本模式配置。

## 9. CompactSummaryContextBuilder 细节

输入：

```text
session.summary
session.compacted_until_message_id
messages
current_input
config.max_turns_after_compact
config.max_context_chars
config.summary_max_chars
config.conflict_policy
```

构造：

```text
[历史摘要，仅供参考]
sessions.summary

[最近对话]
compact boundary 之后最近 N 轮消息

[当前用户问题，优先级最高]
current_input
```

规则：

- 如果没有 `sessions.summary`，可以退化为 `RecentTurnContext`。
- 如果没有 compact boundary，可以使用最近 N 轮消息，且在 `MemoryContext.warnings` 中标记。
- `sessions.summary` 超过 `summary_max_chars` 时应裁剪或提示重新 compact。
- `conflict_policy` 一期固定为 `current_input_wins`。

## 10. 前端配置页

`/chat` 配置面板新增“上下文”tab。

只包含：

- 开启记忆功能。
- 记忆模式。
- 当前模式参数。
- 压缩当前会话操作。

不包含：

- RAG 数据库。
- Top K。
- Thinking。
- Stream。
- Model Adapter。
- Agent。
- Skill。

推荐 UI 字段：

```text
开启记忆功能：checkbox
记忆模式：select
  - RecentTurnContext
  - CompactSummaryContext

RecentTurnContext:
  最近轮数 max_turns
  最大上下文长度 max_context_chars

CompactSummaryContext:
  compact 后保留最近轮数 max_turns_after_compact
  摘要最大长度 summary_max_chars
  最大上下文长度 max_context_chars
  冲突策略 conflict_policy=current_input_wins

操作：
  压缩当前会话
```

关闭记忆时，模式参数区域置灰即可。

## 11. 表单字段

请求表单新增字段：

```text
memory_enabled
memory_mode
memory_config
```

示例：

```json
{
  "memory_enabled": true,
  "memory_mode": "CompactSummaryContext",
  "memory_config": {
    "max_turns_after_compact": 5,
    "max_context_chars": 16000,
    "summary_max_chars": 3000,
    "conflict_policy": "current_input_wins"
  }
}
```

`memory_config` 可作为 JSON 字符串提交，由后端解析后放入 `params`。

## 12. 当前问题优先策略

构造 prompt 时必须显式声明：

```text
历史摘要仅供参考。
如果历史摘要或最近对话与当前用户问题冲突，以当前用户问题为准。
当前用户问题拥有最高优先级。
```

当前问题必须：

- 完整保留。
- 放在 prompt 最后。
- 不参与 summary 裁剪。
- 不参与最近对话截断。

## 13. 上下文字符预算

`max_context_chars` 是工程上的粗略预算，不等价于真实 token 数。

裁剪顺序建议：

```text
1. 保留当前用户问题
2. 保留模式规则和优先级说明
3. 保留最近对话
4. 保留历史摘要
5. 如仍超限，裁剪最旧的最近对话
```

不建议一开始做复杂 token 计算；一期可用字符长度控制，后续再接 tokenizer。

## 14. 和现有能力的关系

与 RAG 的关系：

- RAG 是否开启由 RAG 配置决定。
- RAG top_k 由 RAG 配置决定。
- MemoryManager 不处理 RAG 参数。

与 Thinking 的关系：

- Thinking 是否开启由输出配置决定。
- MemoryManager 默认不把 `thinking` 注入历史上下文。

与 Agent/Skill 的关系：

- Agent/Skill 由 Agent 配置决定。
- MemoryManager 只构造 `params["context"]`。
- Agent 如何使用 `context` 由 Agent 自己决定。

## 15. 验收场景

### 关闭记忆

配置：

```text
memory_enabled=false
```

期望：

- 后端不读取 session 历史作为模型上下文。
- 只使用当前输入。

### 最近对话模式

配置：

```text
memory_enabled=true
memory_mode=RecentTurnContext
max_turns=5
```

期望：

- prompt 包含最近 5 轮对话。
- prompt 包含当前问题。
- 不使用 `sessions.summary`。

### compact 摘要模式

配置：

```text
memory_enabled=true
memory_mode=CompactSummaryContext
max_turns_after_compact=5
```

期望：

- prompt 包含 `sessions.summary`。
- prompt 包含 compact boundary 之后最近 5 轮对话。
- 当前问题放在最后。

### /compact

操作：

```text
用户输入 /compact
```

期望：

- 生成摘要。
- 写入 `sessions.summary`。
- 写入 `compacted_until_message_id`。
- 不删除 `messages`。
- 不作为普通问题调用业务 Agent。

## 16. 实现底线

- 不删除原始消息。
- 不把 RAG/Thinking/top_k/stream 混入上下文配置。
- 不让 MemoryManager 依赖具体 Agent 或 Skill。
- 不把当前用户问题压缩进 summary。
- 不让历史摘要优先级高于当前问题。
- 不把 `thinking` 默认作为记忆上下文。
