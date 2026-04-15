# /brain <brain-topic>

围绕当前任务做一次 **设计收敛 + 方案选择 + 计划准备**。

> 定位：`/brain` 负责在动手前澄清目标、边界、约束和方案，不绑定任何特定 runtime。

## 何时使用
- 需求还不够清晰
- 需要比较 2-3 个方案
- 任务虽不大，但边界/成功标准还没锁定
- 准备进入 `/plan` 或 `/session brain`

## 两种工作模式
### Session mode
- 已有当前 session，或正在执行 `/session brain`
- 输出写回当前 session 的“已确认结论（当前版本）”

### Standalone mode
- 没有当前 session，或明确不想进 session
- 输出写到：`.tmp/agentwork/brain/{YYYYMMDD-HHMM-slug}.md`
- 使用模板：`.shared/templates/brain.md`

## 执行流程
1. 先看上下文（项目结构、相关代码、相关文档）
2. 一次只问一个关键问题（目标 / 约束 / 成功标准 / 非目标）
3. 提出 2-3 个可行方案并给出推荐
4. 拿到确认后再落文档，只沉淀最终态
5. 调用 `/plan`
