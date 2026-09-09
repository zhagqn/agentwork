# /plan [plan-source]

把已确认的设计整理成 **可执行、可验证、无占位** 的轻量计划。

> `plan-source` 指的是**输入来源 / 引用对象**，通常是 brain note 或现有文本工件路径，不是自然语言任务描述。若要把计划写入 Case，使用 `/case plan [plan-source]`。

## 输出

- `/plan` 不创建或更新 `.shared/case/*.md`
- 来源优先级：
  1. 显式传入的 `plan-source`
  2. 最新的 `.tmp/agentwork/brain/*.md`
- 输出：`.tmp/agentwork/plan/{YYYYMMDD-HHMM-slug}.md`
- 使用模板：`.shared/templates/plan.md`
- `/plan` 只把已确认设计拆成任务，不代表可以开始修改源码；真正执行需明确的当前执行意图，例如 `/exec`、`/case exec` 或“按已确认计划，现在开始修改”
- 需要写入 Case 时，后续显式调用 `/case plan [plan-source]`

## 必做流程

1. 复核输入来源：确认目标、边界、已选方案、非目标与约束；若只有“推荐方案（待确认）”或缺关键结论，回到 `/brain` 或先问用户。
2. 锁定本轮范围：列出会影响的文件 / 模块 / 文档边界，以及明确不做的范围。
3. 拆成 bite-sized 任务：每条任务应能被独立执行、审查和验证，避免把整轮工作写成一个大任务。
4. 补验证与完成标准：为本轮计划写清最小验证方式；复杂或多轮任务补完成标准、风险和阻塞条件。
5. 运行命令自检
   - 运行 `.shared/scripts/agentwork-check.py plan <plan-file>`；未显式路径时可用 `.shared/scripts/agentwork-check.py plan` 检查最新 plan
6. 给出下一步：计划可执行后，下一步进入 `/exec`，或先用 `/case plan [plan-source]` 写入 Case 后再 `/case exec`；若计划仍依赖确认，停下来等确认。

## 关键要求

- 任务 bite-sized
- 无占位符
- 先锁边界，再拆任务
- 每条任务都应有最小验证思路

## 禁止事项

- 不在 `/plan` 阶段修改项目源码、README、脚本、配置、测试或业务文档
- 不重做完整方案对比；方案差异未收敛时回到 `/brain`
- 不把 plan 写成执行日志、命令流水或 review 结论
- 不把模糊任务直接拆给 `/exec`；边界、成功标准或非目标缺失时先澄清
- 创建或更新 `.shared/case/*.md`
