# /case [subcommand] [args]

Case 管理与推进命令。

> 定位：Case 是当前任务的**手动任务快照**，不承担 runtime state。其核心动作由独立命令实现：`/brain`、`/plan`、`/exec`、`/review`。`/case` 负责管理当前 Case，并把这些动作串起来。

## 当前核心子命令

| 子命令              | 作用                                                                          | 等价流程                                                                      |
| ------------------- | ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| （无）              | 同步当前 Case                                                                 | 更新当前 Case 的结论 / 任务 / 计划摘要 / 当前批次工作集 / 产出批次 / 风险     |
| `new <case-desc>`   | 创建新 Case                                                                   | 仅建文件，不自动脑暴                                                          |
| `plan [plan-source]`| 把已确认 brain / plan / 当前结论写入 Case                                     | `/brain` / `/plan` → `/case plan`                                             |
| `load <case-ref>`   | 手动加载 Case                                                                 | 读取任务 / 结论 / 计划摘要 / 当前批次工作集 / 最近产出批次 / 风险 / 最近审查记录 |
| `exec`              | 按任务列表推进当前批次                                                        | 调用 `/exec`                                                                  |
| `review [case-ref]` | 审查 Case 与当前工作                                                          | 调用 `/review [review-source]`                                                |

## 说明

- 独立命令 `/brain` `/plan` `/exec` `/review` 不要求必须处于 Case 上下文
- 没有当前 Case 时，它们可以直接使用 `.tmp/agentwork/*` 下的临时工件
- `/brain` 和 `/plan` 默认只写 `.tmp/agentwork/*`，不创建或更新 `.shared/case/*.md`
- `/case plan [plan-source]` 是把已确认 brain / plan 结果写入 Case 的入口
- Case 不使用固定阶段字段；当前处于什么状态，以任务列表、已确认结论、计划摘要、当前批次工作集、产出批次、风险和审查记录表达
- Case 文件完成一次创建或同步后，运行 `.shared/scripts/agentwork-check.py case <case-ref>`；已经进入 plan / exec / review 完整流时使用 `--strict-flow`

## /case（无参数）

把当前对话新增信息同步到当前 Case。

- 只同步当前对话中已经明确的新信息，不替代 `/exec` 的执行状态同步，也不替代 `/review` 的取证审查、历史压缩和信息保留检查。

## /case new <case-desc>

创建新的 Case 文件并设为当前 Case。

- 创建后运行 `.shared/scripts/agentwork-check.py case <case-ref>`，确认没有模板占位符或临时工件章节泄漏。

## /case plan [plan-source]

把已确认的 brain / plan / 当前结论写入 Case。

### 输入来源

优先级：
1. 显式传入的 `[plan-source]`
2. 最新的 `.tmp/agentwork/plan/*.md`
3. 最新的 `.tmp/agentwork/brain/*.md`

上述两项的「最新」由 `.shared/scripts/agentwork-check.py latest plan|brain` 判定，不按修改时间手选：只有符合 `YYYYMMDD-HHMM-slug.md` 的工件参与，最新时间戳存在多个候选时报 `ambiguous_latest` 并要求显式指定。完整规则见 `.shared/scripts/README.md`。

`[plan-source]` 可为 brain note、plan note 或其他明确文本工件；不要自动读取旧 Case，也不要从未确认讨论中推断已选方案。

### 写入内容

- 创建或更新 `.shared/case/*.md`
- 把已确认目标、边界、约束、已选方案写入“已确认结论（工作快照）”
- 把执行拆解写入任务列表、计划摘要和当前批次工作集
- 记录关联工件，保留 `.tmp/agentwork/brain/*.md` / `.tmp/agentwork/plan/*.md` 的可追溯路径
- 不修改项目源码、README、脚本、配置、测试或业务文档

### 必做检查

- 若来源只有“推荐方案（待确认）”或缺少目标 / 边界 / 非目标 / 验证策略，回到 `/brain` 或 `/plan`，不要写成 Case 已选方案
- 当前批次工作集条目必须使用 `- 范围: `path` | 主题: ...` 格式
- 写入后运行 `.shared/scripts/agentwork-check.py case <case-ref> --strict-flow`

## /case load <case-ref>

优先读取：任务列表、已确认结论、计划摘要、关联工件、当前批次工作集、最近产出批次、风险 / 阻塞、最近审查记录。

- `load` 只恢复任务快照，不替代实际仓库事实。
- 当需要确认具体实现、精确文件内容、真实 diff、提交边界时，必须继续读取相关文件，并按需使用 `git diff`、`git show`、`git log -- <path>` 等方式取证。

## /case exec

- 调用 `/exec`
- 执行后必须同步 Case 的任务状态、当前批次工作集、产出批次和风险 / 阻塞
- 当前批次工作集必须保留 `## 当前批次工作集（可选）` 小节；条目格式必须是 `- 范围: `path` | 主题: ...`，不要写成 `- 已完成:` 或命令流水
- 产出批次按提交、行为和决策归类；保留有独立语义的提交锚点，可把相关提交合并到一条并用目录/主题范围代替逐文件清单。同一 hash 默认只出现一次
- 同步后运行 `.shared/scripts/agentwork-check.py case <case-ref> --strict-flow`

## /case review [case-ref]

- 调用 `/review [review-source]`；未传入 `[case-ref]` 时使用当前 Case，传入时把该 Case ref 作为 `review-source`
- 不仅整理 Case 文本，也对当前工作产物做结构化审查
- `/case review` 默认只更新 Case，不额外生成 `.tmp/agentwork/review/*.md`
- `/case review` 不按固定条数截断产出锚点；只压缩重复路径、命令流水和无新增语义的 Case/格式提交。未解决风险、兼容/迁移前提、关键取舍和仍影响接力的旧结论必须保留或指向可追溯来源
- `/case review` 的审查记录先按标题中的实际日期识别新旧并按时间倒序整理，不按原文位置推断时间；最近 3 个有独立结论/验证的审查事件保留变更、验证和风险/待办详情，历史审查摘要不计入名额；更早记录按里程碑或时间段压缩为一句话/简述。已关闭或归档指针 Case 可主要保留历史摘要，但未解决风险、兼容/迁移前提、关键取舍和接力所需旧结论不压缩掉
- review 后必须保证 Case 仍保留可恢复的当前批次工作集；即使任务已完成，也不要删除该小节，完成状态由任务列表 checkbox 与产出批次表达
- 完成 `.shared/scripts/case-review.sh <case-ref>` 取证和 Case 收敛后，运行 `.shared/scripts/agentwork-check.py case <case-ref> --strict-flow`
