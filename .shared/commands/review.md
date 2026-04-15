# /review [review-source]

对当前任务做一次 **双层 review**：
1. review 当前工件本身是否与事实对齐；
2. review 当前工作产物是否符合目标、计划与质量要求。

> `review-source` 指的是**要审查的工件引用**，通常是 session 或 plan 文件路径，不是自然语言任务描述。

## 两种工作模式
### Session mode
- 来源：当前 session 或显式 session ref
- 结果：更新 session 的任务、结论、当前批次工作集、产出批次、审查记录

### Standalone mode
- 来源优先级：
  1. 显式传入的 `review-source`
  2. 最新的 `.tmp/agentwork/plan/*.md`
- 结果：写入 `.tmp/agentwork/review/{YYYYMMDD-HHMM-slug}.md`
- 使用模板：`.shared/templates/review.md`

### 若当前执行策略是 `--ralph`
- 还应同步更新 `.tmp/agentwork/ralph/{slug}/progress.json`
- 把本轮结论压缩成高信号摘要，避免把完整过程回灌进主上下文
