# /plan [plan-source]

把已确认的设计整理成 **可执行、可验证、无占位** 的轻量计划。

> `plan-source` 指的是**输入来源 / 引用对象**，通常是 session、brain note 或现有文本工件路径，不是自然语言任务描述。

## 两种工作模式
### Session mode
- 来源：当前 session
- 输出：更新 session 的任务列表与计划摘要；范围已明确时同步更新当前批次工作集
- 被 `/session brain` 内联使用时，采用同一套产出规则，但不额外创建 standalone plan 文件
- 不默认写 `.tmp/agentwork/plan/*.md`；只有用户明确要求导出 standalone plan 时才额外写入

### Standalone mode
- 来源优先级：
  1. 显式传入的 `plan-source`
  2. 最新的 `.tmp/agentwork/brain/*.md`
- 输出：`.tmp/agentwork/plan/{YYYYMMDD-HHMM-slug}.md`
- 使用模板：`.shared/templates/plan.md`

## 必做流程
1. 复核输入来源：确认目标、边界、已选方案、非目标与约束；缺关键结论时回到 `/brain` 或先问用户。
2. 锁定本轮范围：列出会影响的文件 / 模块 / 文档边界，以及明确不做的范围。
3. 拆成 bite-sized 任务：每条任务应能被独立执行、审查和验证，避免把整轮工作写成一个大任务。
4. 补验证与完成标准：为本轮计划写清最小验证方式；复杂或多轮任务补完成标准、风险和阻塞条件。
5. 给出下一步：计划可执行后，下一步进入 `/exec` 或 `/session exec`；若计划仍依赖确认，停下来等确认。

## 关键要求
- 任务 bite-sized
- 无占位符
- 先锁边界，再拆任务
- 每条任务都应有最小验证思路
- 若预计进入 `/exec --ralph`，还应补齐完成标准、验证方式、阻塞条件、适合交给 subagent 的任务

## 禁止事项
- 不在 `/plan` 阶段修改项目源码、README、脚本、配置、测试或业务文档
- 不重做完整方案对比；方案差异未收敛时回到 `/brain`
- 不把 plan 写成执行日志、命令流水或 review 结论
- 不把模糊任务直接拆给 `/exec`；边界、成功标准或非目标缺失时先澄清
