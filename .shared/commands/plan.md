# /plan [plan-source]

把已确认的设计整理成 **可执行、可验证、无占位** 的轻量计划。

> `plan-source` 指的是**输入来源 / 引用对象**，通常是 session、brain note 或现有文本工件路径，不是自然语言任务描述。

## 两种工作模式
### Session mode
- 来源：当前 session
- 输出：更新 session 的任务列表与计划摘要

### Standalone mode
- 来源优先级：
  1. 显式传入的 `plan-source`
  2. 最新的 `.tmp/agentwork/brain/*.md`
- 输出：`.tmp/agentwork/plan/{YYYYMMDD-HHMM-slug}.md`
- 使用模板：`.shared/templates/plan.md`

## 关键要求
- 任务 bite-sized
- 无占位符
- 先锁边界，再拆任务
- 每条任务都应有最小验证思路
- 若预计进入 `/exec --ralph`，还应补齐完成标准、验证方式、blocker 条件、适合交给 subagent 的任务
