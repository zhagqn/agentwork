# /review [review-source]

对当前任务做一次 **双层 review**：
1. review 当前工件本身是否与事实对齐；
2. review 当前工作产物是否符合目标、计划与质量要求。

> `review-source` 指的是**要审查的工件引用**，通常是 session 或 plan 文件路径，不是自然语言任务描述。

## 两种工作模式
### Session mode
- 来源：当前 session 或显式 session ref
- 结果：更新 session 的任务、结论、计划摘要、当前批次工作集、产出批次、风险 / 阻塞、审查记录
- 不默认写 `.tmp/agentwork/review/*.md`；只有用户明确要求导出 standalone review 时才额外写入

#### Session mode 必做流程
1. 读取当前 session：优先看任务列表、已确认结论、计划摘要、当前批次工作集、产出批次、风险 / 阻塞、最近审查记录。
2. 取证当前事实：至少检查 `git status --short`，按当前批次工作集和用户问题读取相关 diff / 文件；需要时运行 `.shared/scripts/session-review.sh <session-ref>` 辅助发现过期路径和未覆盖改动。
3. 审查工作产物：先列真实问题，再列无问题结论；不要只审查 session 文本，也要对照当前工作区事实。
4. 收敛 session 快照：更新任务状态、已确认结论、计划摘要、当前批次工作集、产出批次、风险 / 阻塞。
5. 压缩历史记录：把过程流水合并为阶段摘要，只保留最近 3-5 条仍有追踪价值的审查记录。
6. 完成前自检：确认 session 仍是可恢复任务快照，而不是命令日志、长篇过程记录或仅追加的 review note。

若本轮 review 计划或用户要求使用 subagent 做局部复核，先参考 `.shared/patterns/subagent-workflow.md`，再拆分审查范围、指定输出格式和验收方式。

#### Session 收敛维护检查清单
- 任务列表：完成状态只写在 checkbox；仍未完成的后续项必须保留。
- 已确认结论 / 计划摘要：必须反映当前真实决策；删除或改写已失效方案、旧路径、旧入口和旧目标。
- 当前批次工作集：必须保留 `## 当前批次工作集（可选）` 小节；条目格式必须是 `- 范围: `path` | 主题: ...`。不要写成 `- 已完成:`、命令流水或审查结论。
- 当前批次工作集压缩：小批次可列精确路径；跨目录或超过约 20 个路径时改写为主题/目录范围，精确路径以 `git status`、`git diff`、`.shared/scripts/session-review.sh` 取证，不长期堆入 session。
- 过期内容清理：移除已提交、已删除、已还原或不再属于当前批次的工作集路径；已解决风险不继续保留为当前风险。
- 产出批次压缩：只记录提交锚点与简要范围；过长时保留最近 3-5 条仍有追踪价值的明细，更早已闭环批次合并为阶段摘要或提交范围索引。
- 审查记录压缩：只写高信号结论、真实发现、修正和剩余风险；不记录命令流水、重复验证过程、临时判断或已被 project 文档吸收的长期事实。
- 可恢复性：session 顶部快照必须能让下一次 `/session load` 后恢复任务；保留目标、边界、关键入口、当前工作集、有效产出锚点、当前风险和后续项。
- session 文件自身提交不为了回填自身 hash 再追加提交；该批次允许保留 `提交: -`，并依赖 Git 历史追踪真实提交。

#### 禁止的 Session Review 结果
- 只追加一条审查记录，但不更新任务、结论、计划摘要、工作集、产出批次和风险。
- 让旧目标、旧入口、旧目录或已废弃方案留在顶部工作快照。
- 把长篇历史命令流水、逐次 run 结果、临时分析和重复验证长期堆在审查记录中。
- 把 `check_session_standard.py` 通过当作语义收敛完成；结构通过只代表格式合格，不代表快照已压缩。

### Standalone mode
- 来源优先级：
  1. 显式传入的 `review-source`
  2. 最新的 `.tmp/agentwork/plan/*.md`
- 结果：写入 `.tmp/agentwork/review/{YYYYMMDD-HHMM-slug}.md`
- 使用模板：`.shared/templates/review.md`

### 若当前执行策略是 `--ralph`
- 还应同步更新 `.tmp/agentwork/ralph/{slug}/progress.json`
- 保持目标、phase、进度摘要和阻塞可恢复，与 `/exec --ralph` 的主上下文约束一致
- 把本轮结论压缩成高信号摘要，避免把完整过程回灌进主上下文
- 若使用 subagent 做局部复核，仍按 `.shared/patterns/subagent-workflow.md` 约束委派契约、输出格式和验收责任
