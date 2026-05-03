# Session Workflow

Session 是 agentwork 的**任务快照与工作流外壳**：
- `new / load` 管理工件
- `brain / plan / exec / review` 负责真正的工作流推进
- `exec --ralph` 提供按需启用的持久执行策略
- `/session ...` 只是把这些动作串起来，围绕当前 session 运转

## 核心原则
1. 手动控制上下文：不自动加载旧 session
2. 设计先于动作：对含糊任务先 `/brain`
3. 计划先于执行：设计确认后先 `/plan`
4. 执行小步化：通过 `/exec` 小批次推进
5. 持久执行按需启用：默认先 `/exec`，只有在确实需要多轮持续推进时才进入 `/exec --ralph`
6. review 双层化：通过 `/review` 同时 review 工件与工作产物
7. standalone 可工作：没有 session 也能通过 `.tmp/agentwork/*` 跑通
8. 快照不替代事实：load session 后，若需要精确代码/差异/提交上下文，继续以仓库当前文件与 git 记录为准
9. 提交边界保守：session 记录只用于帮助判断归属，不自动扩大提交范围；具体提交确认规则以 `.shared/commands/commit.md` 为准

## Brain 约束
- 含糊任务先 `/brain`；澄清、方案对比、推荐、默认假设的细则统一以 `.shared/commands/brain.md` 为准
- session 正文只保留最终确认结论；方案对比默认保留在当前回复或 brain note

## 命令分层
| 命令 | 角色 | standalone 落点 |
| --- | --- | --- |
| `/brain` | 设计收敛 | `.tmp/agentwork/brain/*.md` |
| `/plan` | 轻量计划落地 | `.tmp/agentwork/plan/*.md` |
| `/exec` | 小步执行 / 可选持久执行 | 更新 `.tmp/agentwork/plan/*.md` |
| `/review` | 工件 + 工作双层审查 | `.tmp/agentwork/review/*.md` |
| `/session` | 当前 session 的入口壳层 | `.shared/session/*.md` |

## 执行策略选择
- 默认路径：`/brain` → `/plan` → `/exec` → `/review`
- 需要多轮持续推进、共享执行摘要或辅助工件时，显式使用 `/exec --ralph`
- 平台原生 goal / loop / hook 的选择责任见 `.shared/patterns/platform-adapter.md`

## 典型流程
### Session 模式
```text
/session brain 修复欢迎页焦点问题
/session exec
/session review
/commit
```

### Standalone 模式
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
