# `.shared` 入口

> 目标：保留 agentwork 的核心工作流层，使其可读、可同步、可在新项目中直接复用。

## 0) 约束

- `.shared/constraints/coding-style.md`
- `.shared/constraints/destructive-operations.md`
- `.shared/constraints/placeholder-naming.md`

## 1) 核心工作流
- Session 命令：`.shared/commands/session.md`
- Brain 命令：`.shared/commands/brain.md`
- Plan 命令：`.shared/commands/plan.md`
- Exec 命令：`.shared/commands/exec.md`
- Review 命令：`.shared/commands/review.md`
- Commit 流程：`.shared/commands/commit.md`
- Session 工作流：`.shared/patterns/session-workflow.md`
- Subagent 协作：`.shared/patterns/subagent-workflow.md`
- Session 模板：`.shared/templates/session.md`
- Session 目录说明：`.shared/session/README.md`
- Brain / Plan / Review 模板：`.shared/templates/brain.md`、`.shared/templates/plan.md`、`.shared/templates/review.md`
- Project 管理：`.shared/patterns/project-management.md`
- Project 索引：`.shared/project/index.md`
- 平台适配：`.shared/patterns/platform-adapter.md`
- 核心脚本说明：`.shared/scripts/README.md`
- 命令输出预览：`.shared/scripts/command-preview.sh`（未知或大输出命令优先使用）
- 命令自检脚本：`.shared/scripts/agentwork-check.py`（本地回归入口：`self-test`）

## 2) 命令栈
- `/brain`：设计收敛，输出 `.tmp/agentwork/brain/*.md`
- `/plan`：计划落地，输出 `.tmp/agentwork/plan/*.md`
- `/exec`：任务执行
- `/review`：工件 + 工作双层审查
- `/session plan`：把已确认 brain / plan 工件写入 session
- `/session exec` / `/session review`：围绕当前 session 执行和审查

## 3) Temporary Artifacts
- `.tmp/agentwork/brain/*.md`
- `.tmp/agentwork/plan/*.md`
- `.tmp/agentwork/review/*.md`
- 上述是核心 workflow 的临时工件；可选工具或上游镜像可使用各自 `.tmp/<domain>/`，默认不纳入提交

## 4) Optional Tools
- 可选工具默认不预装
- 需要时通过项目安装入口按需引入
- `.shared` 不枚举可选工具清单；可用工具以安装入口或工具注册表的实际输出为准

## 5) Project（长期复用）
- 位置：`.shared/project/`
- 入口：`.shared/project/index.md`

## 6) 维护原则
- `.shared` 只承载项目内可直接使用的核心工作流契约
- 安装/生成/工具管理入口不应直接泄漏到项目内使用说明中
