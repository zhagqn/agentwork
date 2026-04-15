# Session 目录说明

## 本项目补充说明

<!-- AGENTWORK:SESSION-README:START -->
> 这里存放当前项目的 session 快照文件。
>
> - ✅ 写：当前任务的最小快照、任务列表、最终结论、当前批次工作集、产出批次、审查记录
> - ❌ 不写：长期稳定项目事实（应摘录到 `.shared/project/*`）

## 使用约定
- 不自动加载旧 session
- 只在需要时显式 `/session load <session-id>`
- 审查前优先运行 `.shared/scripts/session-review.sh`
- 当前未提交或正在处理的精确文件写到“当前批次工作集”
- 已提交结果按“产出批次（提交锚点）”记录，不再逐文件展开
- 临时思考过程不要直接沉淀为 session 结论
<!-- AGENTWORK:SESSION-README:END -->
