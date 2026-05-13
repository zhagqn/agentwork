# Session Workflow

Session 是 agentwork 的**任务快照与工作流外壳**：

- `new / load` 管理工件
- `brain / plan / exec / review` 负责 `.tmp/agentwork/*` 工作流工件
- `/session plan` 负责把已确认 `.tmp/agentwork/*` 结果写入 session
- `exec --ralph` 提供按需启用的持久执行策略
- `/session ...` 只是把这些动作串起来，围绕当前 session 运转

> 具体命令规则以 `.shared/commands/*.md` 为准；本文档只描述命令协作模型、阶段裁剪和工件关系。

## 核心原则

1. 手动控制上下文：不自动加载旧 session
2. 工件先于快照：对含糊任务先 `/brain`，再 `/plan`，不要先建 session 再反复改写
3. Session 写入显式化：只有 `/session plan [plan-source]` 把已确认 brain / plan 结果写入 session
4. 计划先于执行：设计确认且计划明确后才进入 `/exec` 或 `/session exec`
5. 执行许可显式化：确认推荐方案只表示可以进入 `/plan` 或 `/session plan`，不等于可以修改源码；真正开始动手仍需明确 `/exec` 或 `/session exec`
6. 执行小步化：通过 `/exec` 小批次推进
7. 持久执行按需启用：默认先 `/exec`，只有在确实需要多轮持续推进时才进入 `/exec --ralph`
8. review 双层化：通过 `/review` 同时 review 工件与工作产物
9. 无 session 也可工作：没有 session 也能通过 `.tmp/agentwork/*` 跑通
10. 快照不替代事实：load session 后，若需要精确代码/差异/提交上下文，继续以仓库当前文件与 git 记录为准
11. 提交边界保守：session 记录只用于帮助判断归属，不自动扩大提交范围；具体提交确认规则以 `.shared/commands/commit.md` 为准

## Brain 约束

- 含糊任务先 `/brain`；澄清、方案对比、推荐、默认假设的细则统一以 `.shared/commands/brain.md` 为准
- `/brain` 只写 `.tmp/agentwork/brain/*.md`，不直接创建或更新 `.shared/session/*.md`
- session 正文只保留经 `/session plan [plan-source]` 写入后的最终态；方案对比默认保留在当前回复或 brain note

## 工件流转

- Brain 阶段：用 `/brain` 反复澄清需求、比较方案、形成推荐和确认问题；输出 brain note
- Plan 阶段：用 `/plan [plan-source]` 把已确认设计拆成可执行、可验证的 plan note
- Session 写入阶段：用 `/session plan [plan-source]` 创建或更新 `.shared/session/*.md`，只沉淀已确认目标、边界、方案、任务、计划摘要和当前批次工作集
- Exec 阶段：不使用 session 时调用 `/exec [plan-file]`；使用 session 时调用 `/session exec`
- 草稿例外：用户明确要求跨轮保存未确认讨论时，可以保留 brain note；不要写成 session 已选方案或当前批次工作集

## 命令分层

| 命令            | 角色                                  | 落点                            |
| --------------- | ------------------------------------- | ------------------------------- |
| `/brain`        | 设计收敛                              | `.tmp/agentwork/brain/*.md`     |
| `/plan`         | 轻量计划落地                          | `.tmp/agentwork/plan/*.md`      |
| `/exec`         | 小步执行 / 可选持久执行               | 更新 `.tmp/agentwork/plan/*.md` |
| `/review`       | 工件 + 工作双层审查                   | `.tmp/agentwork/review/*.md`    |
| `/session plan` | 已确认工件写入 session                | `.shared/session/*.md`          |
| `/session exec` | 按 session 快照执行当前批次           | `.shared/session/*.md`          |
| `/session review` | 审查 session 与当前工作产物         | `.shared/session/*.md`          |

## 执行策略选择

- 不写入 session：`/brain` → `/plan` → `/exec` → `/review`
- 写入 session：`/brain` → `/plan` → `/session plan [plan-source]` → `/session exec` → `/session review`
- 用户对推荐方案的确认只代表可以进入 `/plan` 或 `/session plan`，不代表可以直接改源码；如果没有明确 `/exec`，就停在 plan 边界
- 需要多轮持续推进、共享执行摘要或辅助工件时，显式使用 `/exec --ralph`
- 当用户或计划明确采用 subagent 分工或局部复核时，任务拆解、输出契约与验收责任参考 `.shared/patterns/subagent-workflow.md`
- 平台原生 goal / loop / hook 的选择责任见 `.shared/patterns/platform-adapter.md`

## 阶段裁剪

| 场景                                 | 可裁剪阶段                  | 最小要求                                        |
| ------------------------------------ | --------------------------- | ----------------------------------------------- |
| 需求含糊、边界未锁定、需要方案取舍   | 不裁剪 `/brain`             | 先产出澄清结果、方案对比和推荐决策              |
| 已有明确方向，但任务跨文件 / 多步骤  | 可跳过 `/brain`，先 `/plan` | 计划中写清范围、任务、验证和非目标              |
| 单文件或小范围修复，目标与验证都明确 | 可直接 `/exec`              | 执行前仍要复核边界，完成后按需 `/review`        |
| 当前批次已完成、风险变化或准备提交   | 不跳过 `/review`            | 以当前文件、diff、测试和 session 为事实重新审查 |
| 需要多轮持续推进或共享辅助工件       | 使用 `/exec --ralph`        | 保持目标、phase、进度摘要和阻塞可恢复           |

## 典型流程

### 写入 session

```text
/brain 修复欢迎页焦点问题
# 方案确认后生成计划
/plan .tmp/agentwork/brain/20260120-1030-focus.md
# 写入 session
/session plan .tmp/agentwork/plan/20260120-1045-focus.md
# 再显式进入执行
/session exec
/session review
/commit
```

### 不写入 session

```text
/brain 欢迎页焦点问题
/plan
/exec
/review
```

## 工件分层

- `.shared/session/*.md`：当前任务快照
- `.tmp/agentwork/brain/*.md`：设计 note
- `.tmp/agentwork/plan/*.md`：轻量计划
- `.tmp/agentwork/review/*.md`：review note
- `.tmp/agentwork/ralph/{slug}/*`：持久执行辅助工件

## 命令内建 Harness

- `.shared/scripts/agentwork-check.py` 是核心命令自检入口，用于检查 brain / plan / exec / review / session 工件形态、模板占位符泄漏和关键 workflow 约束。
- `.shared/scripts/session-review.sh` 专注 session 与当前 git 工作区事实对照；`agentwork-check.py session` 专注 session 文本形态和可恢复性骨架。
- `/brain`、`/plan`、`/exec`、`/review`、`/session` 完成落盘或同步后，应运行对应的 `agentwork-check.py` 子命令，把原本只在集成测试里发现的问题前移到命令执行现场。
- 本地确定性回归入口是 `.shared/scripts/agentwork-check.py self-test`，不依赖 source repo 的 `test/` 目录或真实 provider。
- 自检脚本只验证 workflow 工件契约，不替代业务测试、构建、lint、人工审查或真实 provider smoke。
