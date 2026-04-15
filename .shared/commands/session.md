# /session [subcommand] [args]

Session 管理与推进命令。

> 定位：Session 是当前任务的**手动任务快照**，不承担 runtime state。其核心动作由独立命令实现：`/brain`、`/plan`、`/exec`、`/review`。`/session` 负责管理当前 session，并把这些动作串起来。

## 当前核心子命令
| 子命令 | 作用 | 等价流程 |
| --- | --- | --- |
| （无） | 同步当前 session | 更新当前 session 的结论 / 任务 / 当前批次工作集 / 产出批次 |
| `new <session-desc>` | 创建新 session | 仅建文件，不自动脑暴 |
| `brain <brain-topic>` | 新建 session 并完成设计+计划收敛 | `/session new` → `/brain` → `/plan` |
| `load <session-id>` | 手动加载 session | 读取任务 / 结论 / 当前批次工作集 / 最近产出批次 / 最近审查记录 |
| `exec [--ralph]` | 按任务列表推进当前批次，或进入持久执行模式 | 调用 `/exec` 或 `/exec --ralph` |
| `review [session-id]` | 审查 session 与当前工作 | 调用 `/review` |

## 说明
- 独立命令 `/brain` `/plan` `/exec` `/review` 不要求必须处于 session 上下文
- 没有当前 session 时，它们可以直接使用 `.tmp/agentwork/*` 下的 standalone 工件

## /session（无参数）
把当前对话新增信息同步到当前 session。

## /session new <session-desc>
创建新的 session 文件并设为当前 session。

## /session brain <brain-topic>
等价于：`/session new <brain-topic>` → `/brain <brain-topic>` → `/plan`

## /session load <session-id>
优先读取：任务列表、已确认结论、计划摘要、关联工件、当前批次工作集、最近产出批次、最近审查记录。

## /session exec [--ralph]
- 默认：调用 `/exec`
- 指定 `--ralph`：调用 `/exec --ralph`
- session 仍然是当前任务快照，持久执行辅助工件位于 `.tmp/agentwork/ralph/{slug}/`

## /session review [session-id]
- 调用 `/review [session-id]`
- 不仅整理 session 文本，也对当前工作产物做结构化审查
