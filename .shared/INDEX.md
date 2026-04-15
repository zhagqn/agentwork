# `.shared` 入口

> 目标：保留 agentwork 的核心工作流层，使其可读、可同步、可在新项目中直接复用。

## 0) 最小必读（所有助手）
1. 约束（Hard constraints）
   - `.shared/constraints/coding-style.md`
   - `.shared/constraints/placeholder-naming.md`
   - `.shared/constraints/destructive-operations.md`

## 1) 核心工作流
- Session 命令：`.shared/commands/session.md`
- Brain 命令：`.shared/commands/brain.md`
- Plan 命令：`.shared/commands/plan.md`
- Exec 命令：`.shared/commands/exec.md`
- Review 命令：`.shared/commands/review.md`
- Commit 流程：`.shared/commands/commit.md`
- Session 工作流：`.shared/patterns/session-workflow.md`
- Session 模板：`.shared/templates/session.md`
- Brain / Plan / Review 模板：`.shared/templates/brain.md`、`.shared/templates/plan.md`、`.shared/templates/review.md`
- Ralph 辅助模板：`.shared/templates/ralph-context.md`、`.shared/templates/ralph-progress.json.example`
- Project 管理：`.shared/patterns/project-management.md`
- Project 索引：`.shared/project/index.md`
- 平台适配：`.shared/patterns/platform-adapter.md`

## 2) 命令栈
- `/brain`：设计收敛（可 standalone）
- `/plan`：计划落地（可 standalone）
- `/exec`：任务执行（可 standalone；`--ralph` 可启用持久执行策略）
- `/review`：工件 + 工作双层审查（可 standalone）
- `/session`：围绕当前 session 串联这些命令

## 3) Standalone Temporary Artifacts
- `.tmp/agentwork/brain/*.md`
- `.tmp/agentwork/plan/*.md`
- `.tmp/agentwork/review/*.md`
- `.tmp/agentwork/ralph/{slug}/*`

## 4) Optional Tools (source-managed)
- 可选工具默认不预装
- 需要时通过项目自己的安装流程按需引入
- 当前已初始化：`figma`、`browser`、`android`、`godot`

## 5) Project（长期复用）
- 位置：`.shared/project/`
- 入口：`.shared/project/index.md`

## 6) 维护原则
- `.shared` 只承载项目内可直接使用的核心工作流契约
- 安装/生成/工具管理入口不应直接泄漏到项目内使用说明中
