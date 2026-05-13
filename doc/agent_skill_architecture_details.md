# Agent/Skill 插件化与编排架构详解

本文档是对 [agent_skill_plugin_standard.md](./agent_skill_plugin_standard.md) 的展开说明。原文标准文档保持为设计基线，不在本文中改写；本文只解释为什么这样设计、各模块如何协作、实现时应注意哪些边界。

## 1. 文档关系

当前 `/doc` 下与 Agent/Skill 插件化相关的文档分工如下：

- `agent_skill_plugin_standard.md`：原文基线，作为范式标准和开发约束。
- `agent_skill_architecture_details.md`：对原文逐节扩展，解释设计思想和实现方向。
- `context_memory_standard.md`：上下文记忆与 `/compact` 标准，定义记忆开关、上下文模式、compact 标准和配置边界。
- `context_memory_architecture_details.md`：上下文记忆架构详解，解释 MemoryManager、ContextBuilder、SQLite compact boundary 和前端配置边界。

后续开发时应优先遵循 `agent_skill_plugin_standard.md`；上下文记忆、`/compact`、MemoryManager 和前端上下文配置边界详见 `context_memory_standard.md` 与 `context_memory_architecture_details.md`。

## 2. 项目根本定位

原文定义项目根本定位为：

```text
可定制 Agent + 可插拔 Skill + 配置驱动组合
```

这个定位决定了项目不是一个单纯的聊天页面，也不是只封装 Ollama HTTP API 的薄壳。它的核心价值是形成一套应用层运行时，让不同 Agent 与不同 Skill 可以自由组合。

Ollama 在这里扮演的是推理底座：

- 它负责根据上下文生成文本。
- 它可以支持 tool calling。
- 它可以输出 thinking/content 流。
- 它不负责长期记忆。
- 它不负责后台任务编排。
- 它不负责权限、安全和命令执行治理。

应用层需要承担：

- 会话历史和记忆组装。
- Agent 选择和调度。
- Skill 注册和权限控制。
- RAG 检索。
- MCP/内部接口调用。
- 白名单命令执行。
- 后台任务持久化。
- 事件流恢复。

如果把这些职责直接交给模型，系统会变得不可审计、不可恢复，也无法稳定控制高风险操作。因此本项目必须保持“模型建议、系统裁决、工具执行、事件记录”的架构边界。

## 3. 设计原则详解

### 3.1 Agent 是决策者

Agent 的职责是“决定怎么做”，不是“亲自做所有事”。

一个合格 Agent 至少应能回答：

- 当前任务是否需要工具？
- 如果需要工具，先调用哪个 Skill？
- Skill 返回结果后，是否需要继续下一步？
- 是否需要基于观察结果修正计划？
- 什么时候应该停止并给出最终回答？

因此 Agent 应关心流程控制、计划生成、步骤校验、结果汇总，而不应该直接写死某个具体工具的实现细节。

### 3.2 Skill 是能力单元

Skill 是可调用能力。它应该像一个受平台治理的函数：

- 有清晰名称。
- 有明确描述。
- 有输入 schema。
- 有输出 schema。
- 有权限声明。
- 有健康检查。
- 可被 Agent 白名单控制。

例如 `RAGSkill` 只做检索，不负责生成最终回答；`CommandSkill` 只执行白名单命令，不负责判断业务含义；`OllamaSkill` 只负责调用模型生成，不负责决定整个任务流程。

这种拆分能让能力可复用、可替换、可组合。

### 3.3 Registry 是核心

Registry 是整个插件系统的事实源。

任何 Agent 或 Skill 如果没有注册，就不应该被调用。这样做的原因是：

- 避免模型凭空编造工具。
- 避免代码里出现绕过权限的直接调用。
- 让 `/registry` 能完整展示系统能力。
- 让 UI 可以根据 registry 渲染可选 Agent/Skill。
- 让健康检查能定位插件加载失败。

未来所有外部开源 Skill、内部 MCP 过程、UI 风格插件，都必须先适配成 `BaseSkill` 并进入 Registry。

### 3.4 配置优先

Agent/Skill 的组合必须通过配置完成，而不是在代码里硬编码。

例如同一个 `HermesOrchestratorAgent` 在运维场景中可启用：

```yaml
enabled_skills:
  - OllamaSkill
  - RAGSkill
  - CommandSkill
```

在知识问答场景中则可启用：

```yaml
enabled_skills:
  - OllamaSkill
  - RAGSkill
```

这样可以通过配置改变 Agent 能力边界，而不是修改 Agent 代码。

### 3.5 权限优先

权限不是附加功能，而是系统基本约束。

Agent 不能因为模型要求就调用任意 Skill。命令执行更不能因为模型输出了一段 shell 就执行。所有调用必须满足：

- Skill 已加载。
- Skill 在 Agent 白名单内。
- Skill 权限允许当前操作。
- 参数通过 schema 校验。
- 命令在白名单中。

对于运维场景，权限治理比模型自主性更重要。

### 3.6 事件优先

复杂任务不是一次请求一次响应，而是一段可观察的执行过程。

因此系统要把过程拆成事件：

```text
planning
plan_step
step_start
tool_call
tool_result
command_log
reflection
content
done
error
```

事件的价值：

- 前端可展示进度。
- 刷新页面后可恢复内容。
- 运维操作可审计。
- 失败时能定位在哪一步失败。
- 后续可接多机器和后台任务。

### 3.7 框架可替换

一期使用 Native engine，不把核心绑定到 LangChain/LangGraph。

这样做是为了保护项目自己的核心标准：

- Agent manifest。
- Skill manifest。
- Skill schema。
- 权限治理。
- RunEvent。
- MemoryContext。

二期引入 LangGraph 时，它应该实现 `OrchestrationEngine` 接口，而不是替代 Registry、Skill、权限和事件标准。

## 4. 插件标准详解

### 4.1 为什么采用包目录 + manifest

单文件 path 方式适合早期快速开发，但不适合长期插件生态。

包目录的优势：

- 一个插件可以包含实现文件、提示词、README、assets、测试样例。
- manifest 可以独立描述元数据，不需要 import Python 类才能知道插件能力。
- 便于上传、复制、下载和版本管理。
- 便于未来做插件市场或插件扫描。

典型插件目录：

```text
skills/ui_style_skill/
  manifest.yaml
  skill.py
  prompts/
    frontend_style.md
  assets/
    tokens.json
  README.md
```

### 4.2 为什么保留旧 path 兼容

项目当前已经有：

```yaml
path: ./skills/ollama_skill.py
```

直接废弃会破坏现有功能和配置。因此新机制必须增量接入：

- 如果配置里有 `package`，按新插件目录加载。
- 如果配置里有 `path`，按旧单文件方式加载。
- 两者进入同一个 Registry。

这样可以逐步迁移，不影响 `/chat` 和 `/admin`。

### 4.3 manifest 字段解释

`schema_version` 用于处理未来字段升级。例如第一版使用 `input_schema`，第二版可能增加 `security`、`dependencies`、`ui_schema` 等。

`kind` 决定插件类型。当前至少支持：

```text
agent
skill
```

未来可扩展：

```text
model_adapter
rag_store
history_store
```

`id` 是稳定标识，适合配置、日志和插件市场使用。`name` 可以对应 Python 类名，也可以作为展示名，但不应承担唯一标识职责。

`entry` 用于加载 Python 类：

```text
agent.py:HermesOrchestratorAgent
```

`permissions` 表示插件申请哪些能力。系统后续可根据权限决定是否允许启用，例如：

```text
rag.search
mcp.call_internal
command.execute.whitelist
filesystem.read
network.request
```

`input_schema` 和 `output_schema` 使用 JSON Schema 思想，方便：

- 校验参数。
- 转成 Ollama tool schema。
- 转成 LangChain Tool。
- 给前端生成表单。
- 给模型理解工具用途。

## 5. 两类 Agent 详解

### 5.1 HermesOrchestratorAgent

这个 Agent 是项目复杂任务能力的代表。它的目标是让 Ollama 具备类似 Hermes 的执行效果：

```text
先理解任务
再制定计划
然后分步执行
每步观察结果
必要时反思调整
最后统一答复
```

它适合：

- 运维诊断。
- 日志分批分析。
- 知识库检索。
- 多步骤修复。
- 长时间任务。
- 需要审计的操作。

它不适合：

- 普通闲聊。
- 低延迟问答。
- 只需要一个工具结果的查询。

HermesOrchestratorAgent 的关键不是让模型“随便行动”，而是让模型生成计划，然后由系统进行裁决。

模型输出 JSON 计划后，系统必须校验：

- JSON 是否可解析。
- step 数量是否超过上限。
- 每个 Skill 是否存在。
- 每个 Skill 是否在 Agent 白名单内。
- 参数是否符合 Skill schema。
- 命令是否在白名单内。
- 是否存在循环依赖。
- 是否超过最大运行时间。

只有通过校验的计划才允许执行。

### 5.2 SkillRouterAgent

这个 Agent 是项目快速工具增强能力的代表。它的目标是让 Ollama 在普通问答中可以自主判断是否需要 Skill。

例如用户问：

```text
查一下知识库里 Spark 进程终止怎么处理
```

SkillRouterAgent 可以调用 `RAGSkill`。

用户问：

```text
按照公司 UI 风格帮我生成一个管理页面
```

SkillRouterAgent 可以调用 `UIStyleSkill` 获取 UI 规范，再让 Ollama 生成代码。

SkillRouterAgent 的原则：

- 少步骤。
- 低延迟。
- 工具调用数量受限。
- 不执行高风险长任务。
- 不做复杂 Plan-Act-Observe 循环。

它可以优先依赖 Ollama tool calling，因为 tool calling 更适合“模型自己判断是否调用一个工具”。

## 6. YAML / JSON / Tool Calling 深入解释

### 6.1 YAML 是配置层

YAML 是人写的稳定配置。它适合描述：

- 插件 manifest。
- Agent 启用哪些 Skill。
- Skill 默认参数。
- 命令白名单。
- MCP profile。
- 模型适配器配置。

YAML 不适合作为模型每次动态输出的计划格式，因为它解析宽松，结构错误不如 JSON 容易严格校验。

### 6.2 JSON 是计划层

JSON 适合模型输出结构化计划，因为：

- 可严格解析。
- 可用 JSON Schema 校验。
- 易于记录到数据库。
- 易于在前端展示。
- 易于回放和审计。

HermesOrchestratorAgent 应让模型输出 JSON 计划，而不是自由文本计划。

计划不能直接执行，必须系统校验后执行。

### 6.3 Tool calling 是快速工具选择层

Tool calling 的本质是：应用把工具 schema 提供给模型，模型返回需要调用哪个工具和参数。

它适合：

- 调用一个 RAG 工具。
- 调用一个 MCP 查询接口。
- 调用一个 UI 风格辅助 Skill。
- 简单 API 查询。

它不适合完全承担复杂运维编排，因为复杂任务需要全局计划、权限校验、事件持久化和多步观察。

## 7. 编排内核详解

一期 Native engine 的正式流程采用轻量 PAOR：

```text
Plan -> Act -> Observe -> Reflect -> Answer
```

当前 `TaskManager + DefaultPlanner` 已经具备 `Plan -> Act -> Monitor` 雏形：

- `TaskManager.submit()` 创建任务、调用 `agent.plan()`、解析依赖、逐步 dispatch。
- `DefaultPlanner.plan()` 支持单步、RAG 两步和用户传入 workflow。
- `resolve_steps()` 已经具备依赖排序和循环依赖检测。
- `BaseAgent.get_skill()` 已经通过 `enabled_skills` 做 Agent 白名单校验。
- `_params_with_context()` 已经把前序 step 的 `content` 汇入后续上下文。

PAOR 不应推翻现有链路，而应在现有链路上增加结构化 observation、reflection 和可选 replan。

### 7.1 编排引擎分层

推荐新增轻量接口：

```python
class OrchestrationEngine:
    def run(self, context):
        raise NotImplementedError

    def stream(self, context):
        raise NotImplementedError
```

一期实现：

```text
NativePlanActEngine
NativePAOREngine
```

二期可选实现：

```text
LangGraphEngine
```

职责边界：

- `TaskManager`：选择 Agent、创建 run、选择 engine、写最终结果。
- `NativePlanActEngine`：承载当前简单任务流程，兼容 `DefaultPlanner`。
- `NativePAOREngine`：承载复杂任务 PAOR 循环，面向 `HermesOrchestratorAgent`。
- `RunEventStore`：持久化 run events，不理解业务语义。
- `Agent`：负责 plan、observe、reflect、answer，不直接调用底层高风险能力。
- `Skill`：只执行单一能力。

这样二期迁移 LangGraph 时不需要重写 Skill，只需要让 `LangGraphEngine` 实现同样的 engine 接口。

### 7.2 RunContext

PAOR 引擎的输入统一为 `RunContext`。

建议字段：

```text
run_id
session_id
task
agent_name
params
memory_context
registry
max_steps
max_reflect_rounds
started_at
```

其中 `memory_context` 由 MemoryManager 构造，PAOR 只消费，不负责读取历史消息。

`params` 可以包含：

```text
skill
workflow
rag_enabled
model_adapter
model
think
vector_store_name
top_k
stream
engine
```

PAOR 引擎不得直接解释所有业务参数，只把需要的参数传给 Agent 或 Skill。

### 7.3 Plan

Plan 阶段由 Agent 生成结构化计划。

计划格式建议：

```json
{
  "goal": "用户目标",
  "steps": [
    {
      "id": "step-1",
      "name": "retrieve_context",
      "skill": "RAGSkill",
      "action": "search",
      "prompt": "检索 Spark 进程终止原因",
      "params": {
        "mode": "search",
        "top_k": 5
      },
      "depends_on": []
    }
  ]
}
```

兼容规则：

- 现有 `workflow` 仍可作为用户显式计划输入。
- 单步任务仍可由 `DefaultPlanner` 生成单个 step。
- PAOR 中模型生成的计划必须是 JSON，不接受自由文本计划直接执行。

Plan 阶段事件：

```text
planning
plan_step
```

### 7.4 Validate Plan

计划不能直接执行，必须由系统校验。

校验项：

- JSON 可解析。
- `steps` 非空。
- step 数量不超过 `max_steps`。
- step id 唯一。
- `depends_on` 不存在缺失或循环。
- 每个 Skill 已注册。
- 每个 Skill 在当前 Agent `enabled_skills` 内。
- 输入参数符合 Skill `input_schema`。
- 高风险权限在 Skill `permissions` 和系统配置中允许。
- CommandSkill 的 `command_id` 在白名单内。

校验失败直接写 `error` event，run 进入 failed。

### 7.5 Act

Act 阶段由系统调用 Skill。

固定规则：

- Agent 只决定调用哪个 Skill 和传什么结构化参数。
- 真正调用必须经过 `agent.get_skill()`。
- Skill 执行前必须完成白名单和 schema 校验。
- Skill 执行期间产出的日志应写入事件。
- 最后一跳是否流式输出由 `skill.supports_stream` 判断，不依赖类名。

Act 阶段事件：

```text
step_start
tool_call
command_log
tool_result
```

### 7.6 Observe

Observe 阶段把 Skill 返回结果规范化为 observation。

建议 observation 格式：

```json
{
  "step_id": "step-1",
  "skill": "RAGSkill",
  "ok": true,
  "content": "检索到的文本",
  "data": {},
  "error": "",
  "summary": "面向后续反思的短摘要"
}
```

规则：

- observation 应保留原始结果中的关键字段。
- observation 的 `summary` 用于给 reflect 和 answer 降低上下文体积。
- 大体积原始输出可以保留在 run_step output 或附件引用中，不必全部塞入下一次模型 prompt。
- `thinking` 默认不进入 observation。

Observe 阶段事件：

```text
observation
```

### 7.7 Reflect

Reflect 阶段由 Agent 基于当前计划和 observations 判断下一步。

返回值必须是结构化 JSON：

```json
{
  "decision": "continue",
  "reason": "已经获得手册片段，继续执行诊断命令",
  "next_steps": []
}
```

允许的 decision：

| decision | 含义 |
| --- | --- |
| `continue` | 继续执行当前计划中的后续步骤 |
| `replan` | 基于 observation 生成新步骤或替换后续步骤 |
| `finish` | 信息已足够，进入 Answer |
| `fail` | 无法继续，run 失败 |

Reflect 限制：

- `reflect` 不能直接执行 Skill。
- `replan` 产生的新步骤必须重新走 Validate Plan。
- `max_reflect_rounds` 到达上限后只能 `finish` 或 `fail`。
- `finish` 后不得再调用 Skill。
- `fail` 必须记录 reason。

Reflect 阶段事件：

```text
reflection
```

### 7.8 Replan

Replan 是 Reflect 的一种结果，不是独立权限。

Replan 只允许修改尚未执行的步骤。已执行步骤只作为 observation 保留，不允许被删除或覆盖。

推荐策略：

```text
已执行 steps 保留
未执行 steps 可替换
新增 steps 追加到计划
整份计划重新做依赖和权限校验
```

这样可以避免审计链路断裂。

### 7.9 Answer

Answer 阶段由 Agent 汇总最终答复。

输入：

- 用户原始任务。
- MemoryManager 输出的上下文。
- 已执行 steps。
- observations。
- reflection reason。

输出：

```json
{
  "content": "最终答复",
  "thinking": "",
  "citations": [],
  "used_skills": ["RAGSkill", "CommandSkill", "OllamaSkill"]
}
```

Answer 可以调用 `OllamaSkill`，但仍必须经过 Agent 白名单和 Registry。Answer 阶段不得虚构未调用的工具结果。

Answer 阶段事件：

```text
content
done
```

### 7.10 NativePAOREngine 伪代码

推荐第一版实现保持简单：

```python
def run(context):
    agent = registry.agents[context.agent_name]
    emit("planning")
    plan = agent.plan(context.task, context.params)
    steps = validate_and_resolve(plan)
    observations = []
    reflect_rounds = 0

    while has_next_step(steps):
        step = next_ready_step(steps)
        emit("step_start", step)
        result = agent.dispatch(step, params_with_observations(context.params, observations))
        emit("tool_result", result)

        observation = agent.observe(step, result)
        observations.append(observation)
        emit("observation", observation)

        reflection = agent.reflect(context.task, steps, observations, context.params)
        emit("reflection", reflection)

        if reflection["decision"] == "continue":
            continue
        if reflection["decision"] == "replan":
            reflect_rounds += 1
            ensure_reflect_limit(reflect_rounds)
            steps = merge_and_validate_replan(steps, reflection["next_steps"])
            continue
        if reflection["decision"] == "finish":
            break
        if reflection["decision"] == "fail":
            raise RuntimeError(reflection["reason"])

    answer = agent.answer(context.task, observations, context.params)
    emit("content", answer["content"])
    emit("done")
    return answer
```

第一版可以先让 `observe()` 默认包装 `dispatch()` 结果，让 `reflect()` 默认根据 `monitor()` 返回 `continue/finish/fail`，这样不破坏现有 Agent。

### 7.11 BaseAgent 增量接口

为了兼容现有实现，`BaseAgent` 推荐增量增加默认方法，而不是改成全新抽象。

```python
class BaseAgent:
    strategy = "plan_act"
    max_steps = 8
    max_reflect_rounds = 2

    def observe(self, step, result, params=None):
        return {
            "step_id": step["id"],
            "skill": step["skill"],
            "ok": not result.get("error"),
            "content": result.get("content", ""),
            "data": result,
            "error": result.get("error", ""),
        }

    def reflect(self, task, steps, observations, params=None):
        last = observations[-1] if observations else {}
        if not last.get("ok", True):
            return {"decision": "fail", "reason": last.get("error", "步骤失败"), "next_steps": []}
        return {"decision": "continue", "reason": "继续执行计划", "next_steps": []}

    def answer(self, task, observations, params=None):
        return {"content": observations[-1].get("content", "") if observations else ""}
```

`HermesOrchestratorAgent` 再覆盖 `plan()`、`reflect()` 和 `answer()`，实现真正 PAOR。

### 7.12 配置开关

配置层保持项目核心思想。

推荐 Agent 配置：

```yaml
agents:
  - name: HermesOrchestratorAgent
    path: './agents/hermes_orchestrator_agent.py'
    enabled: true
    strategy: paor
    max_steps: 8
    max_reflect_rounds: 2
    enabled_skills:
      - OllamaSkill
      - RAGSkill
      - CommandSkill
```

运行时也可以通过参数显式选择：

```json
{
  "agent": "HermesOrchestratorAgent",
  "params": {
    "engine": "paor"
  }
}
```

默认 `DefaultPlanner` 继续使用 `plan_act`，避免影响 `/chat` 的快速问答体验。

## 8. 持久化与恢复详解

当前请求绑定式 SSE 的问题是：浏览器连接断开后，用户无法可靠恢复正在执行的内容。

事件日志恢复方案把执行和展示拆开。

后台执行：

```text
RunScheduler 创建 run
后台线程选择 OrchestrationEngine
NativePAOREngine 执行 Plan/Act/Observe/Reflect/Answer
每个阶段写 run_events
完成后写 final message
```

前端展示：

```text
打开页面
读取当前 session active run
读取 run_events
按 seq 重放事件
如果 run 还在 running，继续订阅 after_seq
```

这个方案的关键是 `run_events` 必须持久化，不只是内存队列。

推荐字段：

```text
id
run_id
seq
event_type
payload_json
created_at
```

其中 `seq` 用于保证重放顺序。

PAOR 恢复时不要求重新执行 Agent。前端只按事件恢复已产生内容：

```text
planning/plan_step       -> 展示计划
step_start/tool_call     -> 展示当前执行到哪一步
tool_result/observation  -> 展示工具结果摘要
reflection               -> 展示 Agent 判断
content                  -> 追加最终或阶段性文本
done/error               -> 结束当前 run
```

如果浏览器断开，后台 run 继续执行；如果服务进程重启，一期只要求恢复已写入事件，不要求自动接管未完成线程。

## 9. 并发模型详解

项目当前没有明确并发控制。未来要在应用层控制。

推荐规则：

```text
同一 session 串行
不同 session 并行
模型调用限流
命令执行限流
```

同一 session 串行的原因：

- 同一会话上下文共享。
- 两个 run 同时写 message 会造成顺序混乱。
- MemoryManager 很难判断哪个 run 的 observation 应进入上下文。

不同 session 并行的原因：

- 不同用户或不同任务互不干扰。
- 可以提升吞吐。

Ollama semaphore 的原因：

- 本地模型资源有限。
- 不限制并发容易导致响应极慢或显存压力。

## 10. CommandSkill 深入说明

CommandSkill 是验证整个编排体系是否可用的关键 Skill。

它必须做到：

- 模型不能直接传 shell。
- Agent 只能传 command_id。
- CommandSkill 根据 command_id 查白名单。
- 参数按 schema 校验。
- 执行时使用参数数组，不走 shell 拼接。
- stdout/stderr 逐行采集。
- 采集到的日志写入 run_events。
- 脚本结束后返回 exit_code。

执行期间模型不干预，这一点很重要。否则模型可能在日志中途做出错误判断并继续追加危险动作。

正确做法是：

```text
命令完整执行
收集日志
再交给 Ollama 汇总解释
```

## 11. Spark 验收场景详解

这个场景用于验收：

- HermesOrchestratorAgent 是否能规划。
- RAGSkill 是否能检索手册。
- CommandSkill 是否能执行白名单脚本。
- RunEvent 是否能记录日志。
- Ollama 是否能基于工具结果最终回答。

完整输入：

```text
为什么我的 Spark 进程终止了？
```

期望执行过程：

```text
planning: 判断为 Spark 运维诊断任务
plan_step: 使用 RAGSkill 查询修复手册
tool_call: RAGSkill.search
tool_result: 返回 Spark 进程终止相关手册
plan_step: 使用 CommandSkill 执行修复脚本
tool_call: CommandSkill.execute repair_spark_process
command_log: checking spark driver status...
command_log: found executor lost caused by memory overhead
command_log: restarting spark service...
tool_result: exit_code=0
content: 汇总原因、修复动作、执行结果和建议
done
```

这个场景不要求一开始连接真实集群，可以先用 mock 脚本。

## 12. MCPSkill 深入说明

MCPSkill 是公司内部资产的 MCP/接口网关，不是所有第三方 Skill 的统一入口。

它未来可以读取多个 profile 文件：

```text
mcp_profiles/bigdata_platform.yaml
mcp_profiles/cmdb.yaml
mcp_profiles/monitor_platform.yaml
```

每个 profile 可描述：

- 项目名称。
- 服务地址。
- 端口。
- 接口列表。
- 入参出参。
- 认证方式。
- 调用准则。
- 风险等级。

这种设计适合公司内部平台，因为内部资产需要统一治理。

第三方开源 Skill 则应该独立接入，不强制放进 MCPSkill。

## 13. 第三方 Skill 接入说明

项目长期目标是支持：

```text
上传 Skill 目录
配置 package
重载配置
Skill 可用
Agent 可调用
```

对于符合本项目 manifest 标准的 Skill，可以直接加载。

对于不符合标准的开源工具，需要适配：

```text
开源工具
 -> wrapper
 -> BaseSkill
 -> manifest.yaml
 -> Registry
```

例如 UI 风格 Skill：

```text
skills/ui_style_skill/
  manifest.yaml
  skill.py
  prompts/company_ui.md
```

它可以提供：

- UI 设计原则。
- 组件使用建议。
- 颜色和间距 token。
- 前端代码生成约束。
- 示例代码片段。

当用户让 Ollama 写前端时，SkillRouterAgent 可以调用它获取风格约束。

## 14. LangChain/LangGraph 兼容说明

LangChain 支持 Ollama，但本地模型 tool calling 的稳定性取决于具体模型能力。

API Key 大模型通常在以下方面更强：

- tool calling。
- 结构化输出。
- 长上下文。
- 复杂指令遵循。

但本项目不能因此绑定 API Key 大模型，因为项目目标是以 Ollama 为底座。

因此一期策略是：

```text
复杂编排：Native PAOR + JSON 计划 + 系统校验
快速路由：Ollama tool calling
框架兼容：预留 LangGraphEngine
```

二期接入 LangGraph 的难度取决于一期是否做好抽象。

必须预留：

- `OrchestrationEngine`
- `RunState`
- `RunEvent`
- `MemoryContext`
- `BaseSkill.to_tool_schema()`
- `BaseSkill.to_langchain_tool()`

如果这些边界清晰，二期接入 LangGraph 是中等偏低难度；如果一期把所有逻辑写死在 `TaskManager.stream()`，迁移难度会显著升高。

## 15. 实施顺序建议

第一阶段：

- 增加 Agent/Skill manifest 标准。
- 保留旧 path 加载。
- 增强 `BaseSkill` 元数据。
- 增强 `BaseAgent` 元数据。
- 为 `BaseAgent` 增加默认 `observe/reflect/answer`。
- `/registry` 返回完整元数据。

第二阶段：

- 将当前 `TaskManager` 简单流程抽象为 `NativePlanActEngine`。
- 新增 `NativePAOREngine`，先使用默认 observe/reflect/answer 兼容现有 Agent。
- 去掉 `TaskManager.stream()` 中对 `OllamaSkill` 类名的流式硬编码，改为 `supports_stream`。

第三阶段：

- 实现 `RunScheduler`。
- 实现 `runs/run_steps/run_events`。
- 改造前端按 run events 恢复显示。

第四阶段：

- 实现 `HermesOrchestratorAgent`。
- 接入 JSON 计划、Reflect JSON 和 replan 校验。

第五阶段：

- 实现 `CommandSkill`。
- 实现 Spark mock 修复脚本。
- 跑通 Spark 验收链路。

第六阶段：

- 实现 `SkillRouterAgent`。
- 接入 tool calling 快速路由。

第七阶段：

- 优化 MCPSkill 内部 profile。
- 接入第三方 Skill 示例。
- 预留 LangGraphEngine。

## 16. 设计底线

后续无论实现如何演进，都不应破坏以下底线：

- Agent/Skill 必须可配置组合。
- Skill 必须通过 Registry 注册。
- Agent 只能调用白名单 Skill。
- 命令执行必须走 CommandSkill 白名单。
- 复杂任务必须写事件。
- Ollama 不承担权限和任务状态治理。
- LangGraph/LangChain 不能替代项目自己的插件标准。

## 17. 节点职责速查

| 节点 | 职责 | 不应承担的职责 |
| --- | --- | --- |
| Web UI | 展示会话、配置、事件流、最终结果 | 不直接执行 Agent 或 Skill |
| API | 接收请求、创建 run、返回状态和事件 | 不硬编码具体任务流程 |
| RunScheduler | 后台任务调度、并发控制、session lock | 不理解业务语义 |
| TaskManager | 协调 Agent 执行、记录状态 | 不直接绕过 Agent 调用高风险 Skill |
| Agent | 决策、规划、路由、反思、汇总 | 不直接执行 shell 或访问数据库底层 |
| OrchestrationEngine | 执行 Agent 策略和状态流转 | 不定义插件标准 |
| SkillRegistry | 加载、注册、发现、授权 Skill | 不实现具体业务能力 |
| Skill | 执行单一能力 | 不决定全局任务流程 |
| ModelAdapter | 屏蔽模型 API 差异 | 不管理 Agent 权限 |
| RAGStore | 向量写入和检索 | 不生成最终回答 |
| HistoryStore | 保存会话和消息 | 不负责任务调度 |
| RunEventStore | 保存运行事件 | 不替代技术日志系统 |
| CommandSkill | 执行白名单命令 | 不执行任意 shell |
| MCPSkill | 管理内部 MCP/接口资产 | 不统一管理所有第三方 Skill |

## 18. 关键链路速查

### 插件加载链路

```text
读取 config.yaml
 -> 遍历 agents / skills
 -> 判断 package 或 path
 -> package: 读取 manifest.yaml
 -> 校验 schema_version/kind/id/name/entry
 -> 加载 Python class
 -> 检查是否继承 BaseAgent/BaseSkill
 -> 注入 config、model_adapters、rag_stores
 -> 注册到 PluginRegistry
 -> 输出 /registry 元数据
```

关键约束：

- `package` 是长期标准。
- `path` 是兼容旧配置。
- 加载失败的插件应记录错误，不应拖垮整个系统。
- `/registry` 应能展示加载成功和失败原因。
- Agent 的 `enabled_skills` 必须在 Registry 中存在。

### Skill 启用链路

```text
Skill 目录存在
 -> manifest.yaml 合法
 -> config.yaml enabled=true
 -> PluginRegistry 加载
 -> Agent enabled_skills 包含该 Skill
 -> Agent 可调用
```

只把 Skill 放到目录里还不等于可用。必须满足插件格式正确、配置启用、依赖满足、Agent 白名单启用，避免上传了高风险 Skill 后被模型自动调用。

### RunEvent 恢复链路

```text
读取当前 session
 -> 查询 active run
 -> GET /api/runs/{run_id}/events?after_seq=0
 -> 按 seq 重放事件
 -> 恢复已输出内容
 -> 如果 run 还在 running，继续订阅 after_seq
```

`seq` 用于保证事件顺序、避免重复渲染并支持断点续拉。只保存最终 message 无法恢复正在执行的长任务过程，也不利于失败定位。

### 并发控制链路

```text
POST run
 -> 获取 session lock
 -> 如果同 session 有 active run，拒绝或排队
 -> 提交 ThreadPoolExecutor
 -> 获取 ollama semaphore
 -> 调用模型
 -> 释放 semaphore
 -> run 完成释放 session lock
```

建议默认值：

```text
session_serial: true
max_workers: 2 或 4
max_ollama_concurrent: 1 或 2
```

## 19. 事件类型速查

| 事件 | 含义 |
| --- | --- |
| `planning` | Agent 开始理解任务和生成计划 |
| `plan_step` | 产生或确认某个计划步骤 |
| `plan_validated` | 系统完成计划校验 |
| `step_start` | 某一步开始执行 |
| `tool_call` | Agent 准备调用某个 Skill |
| `tool_result` | Skill 返回执行结果 |
| `observation` | 系统把 Skill 结果规范化为 observation |
| `command_log` | CommandSkill 输出过程日志 |
| `reflection` | Agent 基于 observation 判断是否继续 |
| `replan` | Agent 触发重规划且系统接受新计划 |
| `content` | 面向用户的最终或阶段性回答内容 |
| `done` | Run 成功结束 |
| `error` | Run 或某一步失败 |

`CommandSkill` 推荐事件 payload：

```json
{
  "event_type": "command_log",
  "payload": {
    "command_id": "repair_spark_process",
    "stream": "stdout",
    "line": "checking spark driver status..."
  }
}
```

## 20. 数据结构建议

### runs

```text
id
session_id
agent
engine
status
task
max_steps
max_reflect_rounds
reflect_rounds
created_at
updated_at
started_at
finished_at
error
```

### run_steps

```text
id
run_id
step_id
name
skill
action
status
input_json
output_json
observation_json
started_at
finished_at
error
```

### run_events

```text
id
run_id
seq
event_type
payload_json
created_at
```

### command_invocations

```text
id
run_id
step_id
command_id
args_json
status
exit_code
started_at
finished_at
stdout_summary
stderr_summary
error
```

## 21. Spark 验收链路详表

| 阶段 | 节点 | 输入 | 输出 |
| --- | --- | --- | --- |
| 1 | 用户 | 为什么 Spark 进程终止了 | 用户问题 |
| 2 | RunScheduler | session_id + 用户问题 | active run |
| 3 | NativePAOREngine | RunContext | PAOR 循环 |
| 4 | HermesOrchestratorAgent | 用户问题 + 记忆 + Registry 元数据 | JSON 计划 |
| 5 | PlanValidator | JSON 计划 | 可执行 steps |
| 6 | RAGSkill | Spark 终止问题查询 | 修复手册片段 |
| 7 | Agent.observe | RAG 返回结果 | observation |
| 8 | Agent.reflect | observation | continue 或 replan |
| 9 | CommandSkill | command_id + args | 过程日志 |
| 10 | RunEventStore | 日志行 | command_log events |
| 11 | Agent.reflect | 手册 + 命令结果 | finish |
| 12 | OllamaSkill | 用户问题 + 手册 + 日志 + observations | 最终回答 |
| 13 | HistoryStore | 最终回答 | assistant message |

成功条件：

- RAG 命中 Spark 修复手册。
- CommandSkill 命中白名单命令。
- 日志进入事件流。
- 每个 Skill 结果都有 observation。
- 至少一次 reflection 进入 `finish`。
- 无自动重试。
- 最终答案解释原因、动作和结果。

## 22. 关键实现约束速查

- 不允许 Agent 直接执行命令。
- 不允许模型生成 shell 后直接运行。
- 不允许绕过 Registry 调用 Skill。
- 不允许没有 schema 的高风险 Skill 自动启用。
- 不允许同一 session 多个 active run 并发写入上下文。
- 不允许 LangGraph 替换项目自己的 Skill 标准。
- 不允许第三方 Skill 未适配就直接暴露给模型。
