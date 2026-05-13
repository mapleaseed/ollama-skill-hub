# Working Rules

## 基本工作方式

- 先读 `Agent.md`，再按任务类型读 `doc/agent_index/` 下的索引。
- 开发前读相关源码，不凭设计文档直接改代码。
- 优先做最小可交付切片，不一次性引入大框架。
- 保持配置优先，尊重当前代码风格和模块边界。
- 不要破坏现有 `/chat`、`/admin`、`/registry`、`/api/sessions`。

## 设计不是圣经

已有设计文档是当前上下文，不是唯一答案。

遇到以下情况时应主动提问或建议：

- 设计方案明显过重。
- 设计与当前代码冲突。
- 设计与 `doc/arrangement.md` 冲突，但有更好的实现路径。
- 用户目标和历史目标不一致。
- 继续执行会引入安全、权限或维护风险。
- 某项实现会改变项目核心边界。

提问时应说明：

```text
当前设计是什么
发现的问题是什么
可选方案是什么
推荐方案和原因
需要用户确认的点
```

## 文档维护规则

- `doc/process_log.md` 必须实时更新。
- 阶段性任务完成后必须检查 `doc/project_goal.md` 是否需要更新。
- 目标偏移必须先问用户，再更新 `doc/project_goal.md`。
- 受保护约定变更必须先问用户，再更新 `doc/arrangement.md`。
- 里程碑只记录发布级成果，不按每次 UI 或代码微调拆文件。
- 完成里程碑级任务时，更新 `doc/milestones/README.md` 和对应里程碑文件，使其可作为 GitHub release note。
- 任何里程碑文件新增、合并、重命名、废弃或粒度调整时，必须同轮更新 `doc/milestones/README.md`，不能只改具体里程碑文件。
- 下一步待办必须写入 `doc/agent_index/next_steps.md`。
- 如果索引结构或接续规则变化，更新 `Agent.md`。

## 里程碑写法

里程碑文件应像发布说明，而不是开发流水账。

必须说明：

- 发布前状态。
- 为什么要做。
- 经过什么设计考量。
- 修改了什么。
- 发布后对比以前有什么区别。
- 主要改动范围。
- 验证方式。

同一发布目标只保留一个里程碑文件。例如 Web 会话工作台从无到有包含历史、Markdown、滚动、配置 UX、视觉风格和附件体验，这些应合并到一个 Web 里程碑，而不是拆成多个 UI 调整里程碑。

如果同一发布目标在开发过程中经历多版调整，应更新同一个里程碑文件和 `doc/milestones/README.md` 的摘要或整理说明，保证后来者能从 README 看出当前里程碑文件结构和历史整理结果。

## 编码规则

- 手动改文件使用 `apply_patch`。
- 搜索优先用 `rg`。
- 不要删除用户未要求删除的文件。
- 不要执行破坏性 Git 命令。
- 遇到未提交改动时，先确认是否相关，再决定如何避开或协同。

## 验证规则

基础 Python 验证：

```powershell
python -m compileall -q api history adapters agents orchestrator rag skills utils
```

前端脚本验证按需执行：

```powershell
node -e "const fs=require('fs'); const html=fs.readFileSync('web/chat.html','utf8'); const script=html.match(/<script>([\s\S]*)<\/script>/)[1]; new Function(script); console.log('chat js syntax ok');"
```

涉及服务接口时，启动或复用本地 FastAPI 服务后验证相关接口。

## 下一次会话交接规则

完成任务后，至少留下：

- 已完成什么。
- 验证了什么。
- 未完成什么。
- 下一步从哪个文件开始读。
- 如果有决策点，写明需要用户确认什么。
