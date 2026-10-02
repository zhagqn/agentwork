# `.shared` 入口

> 目标：保留 agentwork 的核心工作流层，使其可读、可同步、可在新项目中直接复用。

## 0) 约束

- `.shared/constraints/coding-style.md`
- `.shared/constraints/destructive-operations.md`
- `.shared/constraints/placeholder-naming.md`
- 新建、修改或审查用户界面时读取 `.shared/constraints/frontend-design.md`；需要选择设计基底或借鉴参考时再读 `.shared/patterns/design-reference.md`；纯需求讨论和非 UI 任务不加载。

## 1) 核心工作流
- Case 命令：`.shared/commands/case.md`
- Brain 命令：`.shared/commands/brain.md`
- Spec 命令：`.shared/commands/spec.md`
- Exec 命令：`.shared/commands/exec.md`
- Audit 命令：`.shared/commands/audit.md`
- Commit 流程：`.shared/commands/commit.md`
- Case 工作流：`.shared/patterns/case-workflow.md`
- Subagent 协作：`.shared/patterns/subagent-workflow.md`
- Case 模板：`.shared/templates/case.md`
- Case 目录说明：`.shared/case/README.md`
- Brain / Spec / Audit 模板：`.shared/templates/brain.md`、`.shared/templates/spec.md`、`.shared/templates/audit.md`
- Project 管理：`.shared/patterns/project-management.md`
- Project 索引：`.shared/project/index.md`
- 平台适配：`.shared/patterns/platform-adapter.md`
- 核心脚本说明：`.shared/scripts/README.md`
- 命令输出预览：`.shared/scripts/command-preview.sh`（未知或大输出命令优先使用）
- 命令自检脚本：`.shared/scripts/agentwork-check.py`（本地回归入口：`self-test`）

## 2) 命令栈
- `/brain`：设计收敛，输出 `.tmp/agentwork/brain/*.md`
- `/spec`：编号决策 + 任务切片的可执行规格，输出 `.tmp/agentwork/spec/*.md`
- `/exec`：任务执行
- `/audit`：工件 + 工作双层审查
- `/case spec`：把已确认 brain / spec 工件写入 Case
- `/case exec` / `/case audit`：围绕当前 Case 执行和审查

## 3) Temporary Artifacts
- `.tmp/agentwork/brain/*.md`
- `.tmp/agentwork/spec/*.md`
- `.tmp/agentwork/audit/*.md`
- 上述是核心 workflow 的临时工件；可选工具可使用各自 `.tmp/<domain>/`，默认不纳入提交

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
