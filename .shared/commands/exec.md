# /exec [--ralph] [exec-source]

按当前任务的计划执行当前批次工作。

> `exec-source` 指的是**输入来源 / 引用对象**，通常是 session 或 plan 文件路径，不是自然语言任务描述。

## 两种工作模式
### Session mode
- 来源：当前 session
- 执行后：更新 session 中的任务状态、当前批次工作集、风险

### Standalone mode
- 来源优先级：
  1. 显式传入的 `exec-source`
  2. 最新的 `.tmp/agentwork/plan/*.md`
- 执行后：更新 plan 文件中的任务状态与执行记录

## 两种执行策略
### Standard mode
- 推进当前批次 1-3 个任务
- 一轮后停下来，等待下一次 `/exec` 或 `/review`

### Ralph mode (`--ralph`)
- 让 `/exec` 进入可选的持久执行策略，而不是默认主路径
- 每轮执行后自动进入 review / fix / verify 循环
- 尽量使用 **subagent** 承担独立实现、局部分析、局部 review，减少主上下文消耗
- 主上下文只保留目标、phase、进度摘要、blocker
- 辅助工件位于 `.tmp/agentwork/ralph/{slug}/`

## `--ralph` 辅助工件
- `.tmp/agentwork/ralph/{slug}/context.md`
- `.tmp/agentwork/ralph/{slug}/progress.json`
- `.tmp/agentwork/ralph/{slug}/review.md`

## 关键纪律
- 先复核计划，再执行
- 遇 blocker 停，不猜
- 不跳过验证
- completion 必须基于 fresh evidence
- cancel 是 terminalization，不是静默丢状态
