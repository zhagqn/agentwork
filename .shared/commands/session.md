# /session [subcommand] [args]

Session 管理与推进命令。

> 定位：Session 是当前任务的**手动任务快照**，不承担 runtime state。其核心动作由独立命令实现：`/brain`、`/plan`、`/exec`、`/review`。`/session` 负责管理当前 session，并把这些动作串起来。

## 当前核心子命令
| 子命令 | 作用 | 等价流程 |
| --- | --- | --- |
| （无） | 同步当前 session | 更新当前 session 的结论 / 任务 / 当前批次工作集 / 产出批次 |
| `new <session-desc>` | 创建新 session | 仅建文件，不自动脑暴 |
| `brain <brain-topic>` | 新建 session，并按 `/brain` 收敛后进入计划 | `/session new` → `/brain` → `/plan`，结果直接写入 session |
| `load <session-id>` | 手动加载 session | 读取任务 / 结论 / 当前批次工作集 / 最近产出批次 / 最近审查记录 |
| `exec [--ralph]` | 按任务列表推进当前批次，或进入持久执行模式 | 调用 `/exec` 或 `/exec --ralph` |
| `review [session-id]` | 审查 session 与当前工作 | 调用 `/review` |

## 说明
- 独立命令 `/brain` `/plan` `/exec` `/review` 不要求必须处于 session 上下文
- 没有当前 session 时，它们可以直接使用 `.tmp/agentwork/*` 下的 standalone 工件
- session 模式默认不创建 `.tmp/agentwork/brain`、`.tmp/agentwork/plan`、`.tmp/agentwork/review` 工件；除非用户明确要求导出调试工件
- session 不使用固定阶段字段；当前处于什么状态，以任务列表、结论、当前批次工作集和审查记录表达

## /session（无参数）
把当前对话新增信息同步到当前 session。

## /session new <session-desc>
创建新的 session 文件并设为当前 session。

## /session brain <brain-topic>
等价于：`/session new <brain-topic>` → `/brain <brain-topic>` → `/plan`。

额外约束只有两条：
- `/brain` 的澄清、方案对比、推荐、默认假设规则，统一以 `.shared/commands/brain.md` 为准，`/session brain` 不再重复定义一套流程
- session 模式只把最终确认结论、任务列表和计划摘要写回 session；方案对比默认保留在当前回复，不默认落 `.tmp/agentwork/brain/*.md` 或 `.tmp/agentwork/plan/*.md`
- 若 brain 已能收敛到明确执行范围，应在 session 中写入“计划摘要”和“当前批次工作集”；当前批次工作集条目必须使用 `- 范围: `path` | 主题: ...` 格式

## /session load <session-id>
优先读取：任务列表、已确认结论、计划摘要、关联工件、当前批次工作集、最近产出批次、最近审查记录。
- `load` 只恢复任务快照，不替代实际仓库事实。
- 当需要确认具体实现、精确文件内容、真实 diff、提交边界时，必须继续读取相关文件，并按需使用 `git diff`、`git show`、`git log -- <path>` 等方式取证。

## /session exec [--ralph]
- 默认：调用 `/exec`
- 指定 `--ralph`：调用 `/exec --ralph`
- session 仍然是当前任务快照，持久执行辅助工件位于 `.tmp/agentwork/ralph/{slug}/`
- 执行后必须同步 session 的任务状态、当前批次工作集、产出批次和风险 / 阻塞
- 当前批次工作集必须保留 `## 当前批次工作集（可选）` 小节；条目格式必须是 `- 范围: `path` | 主题: ...`，不要写成 `- 已完成:` 或命令流水

## /session review [session-id]
- 调用 `/review [session-id]`
- 不仅整理 session 文本，也对当前工作产物做结构化审查
- session 模式默认只更新 session，不额外生成 `.tmp/agentwork/review/*.md`
- review 后必须保证 session 仍保留可恢复的当前批次工作集；即使任务已完成，也不要删除该小节，完成状态由任务列表 checkbox 与产出批次表达
