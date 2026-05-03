# /review [review-source]

对当前任务做一次 **双层 review**：
1. review 当前工件本身是否与事实对齐；
2. review 当前工作产物是否符合目标、计划与质量要求。

> `review-source` 指的是**要审查的工件引用**，通常是 session 或 plan 文件路径，不是自然语言任务描述。

## 两种工作模式
### Session mode
- 来源：当前 session 或显式 session ref
- 结果：更新 session 的任务、结论、当前批次工作集、产出批次、审查记录

#### Session 收敛维护
- 同步清理过期内容：移除已完成、已提交、已删除或不再属于当前批次的工作集路径；已解决风险不继续保留为当前风险。
- 同步压缩当前工作集：小批次可列精确路径；跨目录或超过约 20 个路径时，默认改写为主题/目录范围，精确路径以 `git status`、`git diff` 与 `.shared/scripts/session-review.sh` 取证，不长期堆入 session。
- 同步压缩历史产出：产出批次只记录提交锚点与简要范围；当记录过长时，默认保留最近 3-5 条仍有追踪价值的明细，更早已闭环批次合并为阶段摘要或提交范围索引。
- 删除过渡讨论和过程流水：reset / 暂存 / 提交边界整理、命令流水、临时判断、已失效方案和仅解释当时上下文的记录，不作为长期 session 内容保留。
- 审查记录只写高信号结论，不记录命令流水、重复验证过程或已被 project 文档吸收的长期事实。
- 保留可恢复任务的长期快照：目标、边界、已确认结论、关键入口、有效提交锚点、当前风险、仍未完成的后续项。
- session 文件自身提交不为了回填自身 hash 再追加提交；该批次允许保留 `提交: -`，并依赖 Git 历史追踪真实提交。

### Standalone mode
- 来源优先级：
  1. 显式传入的 `review-source`
  2. 最新的 `.tmp/agentwork/plan/*.md`
- 结果：写入 `.tmp/agentwork/review/{YYYYMMDD-HHMM-slug}.md`
- 使用模板：`.shared/templates/review.md`

### 若当前执行策略是 `--ralph`
- 还应同步更新 `.tmp/agentwork/ralph/{slug}/progress.json`
- 把本轮结论压缩成高信号摘要，避免把完整过程回灌进主上下文
