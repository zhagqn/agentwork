# /session [subcommand] [args]

Session 管理与推进命令。

> 定位：Session 是当前任务的**手动任务快照**，不承担 runtime state。其核心动作由独立命令实现：`/brain`、`/plan`、`/exec`、`/review`。`/session` 负责管理当前 session，并把这些动作串起来。

## 当前核心子命令

| 子命令                 | 作用                                                                             | 等价流程                                                                         |
| ---------------------- | -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| （无）                 | 同步当前 session                                                                 | 更新当前 session 的结论 / 任务 / 计划摘要 / 当前批次工作集 / 产出批次 / 风险     |
| `new <session-desc>`   | 创建新 session                                                                   | 仅建文件，不自动脑暴                                                             |
| `plan [plan-source]`   | 把已确认 brain / plan / 当前结论写入 session                                     | `/brain` / `/plan` → `/session plan`                                             |
| `load <session-ref>`   | 手动加载 session                                                                 | 读取任务 / 结论 / 计划摘要 / 当前批次工作集 / 最近产出批次 / 风险 / 最近审查记录 |
| `exec [--ralph]`       | 按任务列表推进当前批次，或进入持久执行策略                                       | 调用 `/exec` 或 `/exec --ralph`                                                  |
| `review [session-ref]` | 审查 session 与当前工作                                                          | 调用 `/review [review-source]`                                                   |

## 说明

- 独立命令 `/brain` `/plan` `/exec` `/review` 不要求必须处于 session 上下文
- 没有当前 session 时，它们可以直接使用 `.tmp/agentwork/*` 下的临时工件
- `/brain` 和 `/plan` 默认只写 `.tmp/agentwork/*`，不创建或更新 `.shared/session/*.md`
- `/session plan [plan-source]` 是把已确认 brain / plan 结果写入 session 的入口
- session 不使用固定阶段字段；当前处于什么状态，以任务列表、已确认结论、计划摘要、当前批次工作集、产出批次、风险和审查记录表达
- session 文件完成一次创建或同步后，运行 `.shared/scripts/agentwork-check.py session <session-ref>`；已经进入 plan / exec / review 完整流时使用 `--strict-flow`

## /session（无参数）

把当前对话新增信息同步到当前 session。

- 只同步当前对话中已经明确的新信息，不替代 `/exec` 的执行状态同步，也不替代 `/review` 的取证审查、历史压缩和语义收敛。

## /session new <session-desc>

创建新的 session 文件并设为当前 session。

- 创建后运行 `.shared/scripts/agentwork-check.py session <session-ref>`，确认没有模板占位符或临时工件章节泄漏。

## /session plan [plan-source]

把已确认的 brain / plan / 当前结论写入 session。

### 输入来源

优先级：
1. 显式传入的 `[plan-source]`
2. 最新的 `.tmp/agentwork/plan/*.md`
3. 最新的 `.tmp/agentwork/brain/*.md`

`[plan-source]` 可为 brain note、plan note 或其他明确文本工件；不要自动读取旧 session，也不要从未确认讨论中推断已选方案。

### 写入内容

- 创建或更新 `.shared/session/*.md`
- 把已确认目标、边界、约束、已选方案写入“已确认结论（工作快照）”
- 把执行拆解写入任务列表、计划摘要和当前批次工作集
- 记录关联工件，保留 `.tmp/agentwork/brain/*.md` / `.tmp/agentwork/plan/*.md` 的可追溯路径
- 不修改项目源码、README、脚本、配置、测试或业务文档

### 必做检查

- 若来源只有“推荐方案（待确认）”或缺少目标 / 边界 / 非目标 / 验证策略，回到 `/brain` 或 `/plan`，不要写成 session 已选方案
- 当前批次工作集条目必须使用 `- 范围: `path` | 主题: ...` 格式
- 写入后运行 `.shared/scripts/agentwork-check.py session <session-ref> --strict-flow`

## /session load <session-ref>

优先读取：任务列表、已确认结论、计划摘要、关联工件、当前批次工作集、最近产出批次、风险 / 阻塞、最近审查记录。

- `load` 只恢复任务快照，不替代实际仓库事实。
- 当需要确认具体实现、精确文件内容、真实 diff、提交边界时，必须继续读取相关文件，并按需使用 `git diff`、`git show`、`git log -- <path>` 等方式取证。

## /session exec [--ralph]

- 默认：调用 `/exec`
- 指定 `--ralph`：调用 `/exec --ralph`
- session 仍然是当前任务快照，持久执行辅助工件位于 `.tmp/agentwork/ralph/{slug}/`
- 执行后必须同步 session 的任务状态、当前批次工作集、产出批次和风险 / 阻塞
- 当前批次工作集必须保留 `## 当前批次工作集（可选）` 小节；条目格式必须是 `- 范围: `path` | 主题: ...`，不要写成 `- 已完成:` 或命令流水
- 同步后运行 `.shared/scripts/agentwork-check.py session <session-ref> --strict-flow`

## /session review [session-ref]

- 调用 `/review [review-source]`；未传入 `[session-ref]` 时使用当前 session，传入时把该 session ref 作为 `review-source`
- 不仅整理 session 文本，也对当前工作产物做结构化审查
- `/session review` 默认只更新 session，不额外生成 `.tmp/agentwork/review/*.md`
- review 后必须保证 session 仍保留可恢复的当前批次工作集；即使任务已完成，也不要删除该小节，完成状态由任务列表 checkbox 与产出批次表达
- 完成 `.shared/scripts/session-review.sh <session-ref>` 取证和 session 收敛后，运行 `.shared/scripts/agentwork-check.py session <session-ref> --strict-flow`
