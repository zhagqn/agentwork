# /exec [--ralph] [exec-source]

按当前任务的计划执行当前批次工作。

> `exec-source` 指的是**输入来源 / 引用对象**，通常是 session 或 plan 文件路径，不是自然语言任务描述。

## 输入来源
### 当前 session
- 来源：当前 session
- 执行后：更新 session 中的任务状态、当前批次工作集、产出批次、风险 / 阻塞
- 当前批次工作集必须保留 `## 当前批次工作集（可选）` 小节；每条使用 `- 范围: `path` | 主题: ...`，不要用 `- 已完成:`、命令流水或临时过程记录替代
- 完成状态写在任务列表 checkbox；本轮产出写在产出批次；当前批次工作集表达本轮可恢复的范围和主题
- 最小同步顺序：更新任务 checkbox → 收敛当前批次工作集到本轮仍需恢复的范围 → 记录本轮产出批次摘要 → 记录新增风险 / 阻塞
- `/exec` 只做本轮执行同步；过期结论压缩、审查记录收敛和历史产出归并属于 `/review` 职责

### Plan 工件
- 来源优先级：
  1. 显式传入的 `exec-source`
  2. 最新的 `.tmp/agentwork/plan/*.md`
- 执行后：更新 plan 文件中的任务状态与执行记录

## 执行策略
### 标准策略
- 推进当前批次 1-3 个任务
- 一轮后停下来，等待下一次 `/exec` 或 `/review`
- 当前批次完成、风险变化或准备提交前，优先进入 `/review`
- 若本轮计划或用户要求使用 subagent，先参考 `.shared/patterns/subagent-workflow.md`，再拆分任务、指定输出格式和验收方式

### Ralph 策略（`--ralph`）
- 让 `/exec` 进入可选的持久执行策略，而不是默认主路径
- 每轮执行后自动进入 review / fix / verify 循环
- 尽量使用 **subagent** 承担独立实现、局部分析、局部 review；使用前参考 `.shared/patterns/subagent-workflow.md`
- 主上下文只保留目标、phase、进度摘要、阻塞
- 辅助工件位于 `.tmp/agentwork/ralph/{slug}/`

## `--ralph` 辅助工件
- `.tmp/agentwork/ralph/{slug}/context.md`
- `.tmp/agentwork/ralph/{slug}/progress.json`
- `.tmp/agentwork/ralph/{slug}/review.md`

## 关键纪律
- 先复核计划，再执行
- 遇阻塞停，不猜
- 不跳过验证
- completion 必须基于 fresh evidence
- cancel 是 terminalization，不是静默丢状态

## 命令自检
- Plan 工件：更新 plan 后运行 `.shared/scripts/agentwork-check.py exec <plan-file>`；未显式路径时可用 `.shared/scripts/agentwork-check.py exec` 检查最新 plan
- 当前 session：同步 session 后运行 `.shared/scripts/agentwork-check.py session <session-ref> --strict-flow`
- 自检通过只代表 workflow 工件形态合格；业务正确性仍以本轮实际验证、测试、构建或人工取证为准
