# /exec [exec-source]

按当前任务的 spec 执行当前批次工作。

> `exec-source` 指的是**输入来源 / 引用对象**，通常是 Case 或 spec 文件路径，不是自然语言任务描述。

## 输入来源
### 当前 Case
- 来源：当前 Case
- 任务状态的唯一事实源是 Case：spec 工件经 `/case spec` 写入 Case 后冻结为决策追溯来源，不回写其 checkbox
- 执行后：更新 Case 中的任务状态、当前批次工作集、产出批次、风险 / 阻塞
- 当前批次工作集必须保留 `## 当前批次工作集（可选）` 小节；每条使用 `- 范围: `path` | 主题: ...`，不要用 `- 已完成:`、命令流水或临时过程记录替代
- 完成状态写在任务列表 checkbox；本轮产出写在产出批次；当前批次工作集表达本轮可恢复的范围和主题
- 最小同步顺序：更新任务 checkbox → 收敛当前批次工作集到本轮仍需恢复的范围 → 记录本轮产出批次摘要 → 记录新增风险 / 阻塞
- `/exec` 只做本轮执行同步；过期结论压缩、审查记录收敛和历史产出归并属于 `/audit` 职责

### Spec 工件
- 来源优先级：
  1. 显式传入的 `exec-source`
  2. 最新的 `.tmp/agentwork/spec/*.md`

「最新」由 `.shared/scripts/agentwork-check.py latest spec` 判定，不按修改时间手选：只有符合 `YYYYMMDD-HHMM-slug.md` 的工件参与，最新时间戳存在多个候选时报 `ambiguous_latest` 并要求显式指定。完整规则见 `.shared/scripts/README.md`。

- 执行后：更新 spec 文件中的任务状态与执行记录

## 执行策略
### 标准策略
- 选择任务：只从 `依赖` 已全部完成的未完成任务中，按优先级选 1-3 个作为当前批次；依赖未就绪的任务不提前开工
- 一轮后停下来，等待下一次 `/exec` 或 `/audit`
- 审查时机按实际情况决定：可在单个批次后、风险变化时或多个批次完成后统一 `/audit`；准备提交前至少完成一次审查
- 若本轮 spec 或用户要求使用 subagent，先参考 `.shared/patterns/subagent-workflow.md`，再拆分任务、指定输出格式和验收方式

### 完成判定
- 任务只有在其 `完成` 条件成立、且本轮新鲜运行的 `验证` 通过后才勾选；没有写 `完成` 时以 `验证` 通过为准
- 验证无法运行或未通过时保持未完成，在风险 / 阻塞中写明原因，不以“代码已写完”代替完成

### 范围外发现
- 执行中发现 spec 未覆盖的问题或改进时，不在本轮扩展实现：能归入现有决策的记为新任务，并在 `覆盖` 中写明该决策；不能归入的记为风险或待决策，需要新增决策时回到 `/brain`
- 发现会改变已确认决策的事实时停下，回到 `/brain` 或先问用户，不在执行中改写决策

## 关键纪律
- 先复核 spec，再执行
- 遇阻塞停，不猜
- 不跳过验证
- completion 必须基于 fresh evidence
- cancel 是 terminalization，不是静默丢状态

## 命令自检
- Spec 工件（未写入 Case 时）：更新 spec 后运行 `.shared/scripts/agentwork-check.py exec <spec-file>`；未显式路径时可用 `.shared/scripts/agentwork-check.py exec` 检查最新 spec
- 当前 Case：同步 Case 后只运行 `.shared/scripts/agentwork-check.py case <case-ref> --strict-flow`，使用 Case 中的完整任务行校验依赖与完成顺序；不运行 `exec` 检查，已冻结的 spec 工件任务仍为未勾选，不代表执行状态
- 自检通过只代表 workflow 工件形态合格；业务正确性仍以本轮实际验证、测试、构建或人工取证为准
