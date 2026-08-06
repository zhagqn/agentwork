# 平台适配层说明（Codex / Claude / OpenCode / Antigravity / Cursor / VS Code Copilot）

> 目的：在保留 `.shared/` 统一规则的前提下，明确“平台能力边界 + 触发差异 + 回退策略”，确保跨平台协作的一致性。

## 适用范围

- 目录：`AGENTS.md`、`.claude/*`、`.agent/*`、`.codex/*`、`.opencode/*`、`.cursor/*`、`.github/*`、`.shared/*`
- 对象：Codex CLI、Claude Code、OpenCode、Antigravity、Cursor、VS Code Copilot（及同类代理平台）

## 核心原则（最佳实践）

1. 共享事实集中在 `.shared/`，平台入口只做入口说明。
2. 平台能力与默认行为（权限/触发/工具）必须与共享规则分离描述。
3. 社区资料只作线索，最终以官方文档与可复现实验为准。
4. 跨平台接力仅信任 `.shared/session/*.md`，不依赖工具内私有上下文。

## 边界定义（模板提供 vs 平台提供）

模板稳定提供：

- 规则入口与长期约束（`.shared/INDEX.md`、`.shared/project/*`）
- 命令正文与占位符规范（`.shared/commands/*`、`.shared/constraints/*`）
- session 工作流与固定检查脚本（`.shared/patterns/*`、`.shared/scripts/*`）
- Codex custom agent 边界（见本文“Codex custom agent 边界”小节）

平台运行时提供（需官方确认）：

- 命令触发机制（slash/workflow/command）
- skills 或类似扩展机制的发现、优先级与冲突处理
- 沙箱、审批、严格模式等默认值与权限边界
- 多代理调度、工具路由与升级权限策略
- 目标持续性、自动循环、定时轮询等 runtime-only 能力

## 能力分工（推荐）

- `.shared/commands/*`：跨平台共享的工作流语义、工件格式、回退路径
- Codex Goal：Codex 线程内的目标持续性、预算跟踪、完成审计
- 平台原生 loop：定时轮询外部状态或周期性重复 prompt

## 平台能力优先级（建议）

1. 先用平台原生 runtime 能力解决平台内问题
2. 需要跨平台接力、共享工件或规避平台漂移时，再退回 `.shared/*`

## 选择责任

- 是否启用某个平台的 goal / loop / hook / plugin，属于平台层决策，不应由 `.shared/commands/exec.md` 自动替用户做选择
- `.shared/*` 只定义共享语义、工件契约与回退路径；不承诺不同平台会以同样方式持续运行
- 若同一任务在不同平台采用不同 runtime 机制，允许结果路径不同，但应尽量回收到一致的 session / plan / review 工件

## 平台映射（建议）

| 平台 | 入口文件 | 平台差异（需官方确认） | 推荐优先能力 | 回退方式 |
| --- | --- | --- | --- | --- |
| Codex CLI | `AGENTS.md`、`.codex/skills/*`、`.codex/agents/*` | AGENTS 分层合并、审批与沙箱参数、生效优先级、custom agents 的发现与继承规则 | Goal + 原生多代理/工具能力；长任务优先 Goal，再配合 `/exec` | 直接执行 `.shared/commands/*` 文本流程，必要时把结论回收到 session / plan / review |
| Claude Code | `.claude/CLAUDE.md`、`.claude/commands/*`、`.claude/skills/*` | slash commands 与 skills 触发/优先级规则 | 自动迭代优先平台原生 loop；定时轮询优先官方 loop | 以 `.shared/commands/*` 为主入口，需跨平台共享语义时写入 session / plan / review |
| OpenCode | `AGENTS.md`、`.opencode/commands/*` | 项目规则首个匹配、`AGENTS.md` 普通文件引用不会自动展开、commands/agents/skills 发现与权限默认值 | 使用原生 command 薄 wrapper 注入共享定义；平台 agents/skills 仅按任务需要启用 | 直接读取 `.shared/commands/*` 手动执行，继续以 session / plan / review 工件接力 |
| Antigravity | `.agent/rules/*`、`.agent/workflows/*`、`.agent/skills/*` | rules/workflows/skills 触发语义、执行策略默认值 | 以平台原生 workflow 能力为先 | 退回 `.shared/INDEX.md` + `.shared/commands/*` 手动流程 |
| Cursor | `.cursor/rules/*` | rules 的触发范围、上下文注入时机和工具权限需按项目验证 | 优先使用 Cursor 原生编辑、检索与诊断能力 | 退回 `AGENTS.md` + `.shared/commands/*`，需要接力时写入 session |
| VS Code Copilot | `.github/copilot-instructions.md` | instructions 注入范围、chat / agent mode 能力边界和命令触发语义需按官方文档确认 | 优先使用 VS Code / Copilot 原生 workspace 能力 | 退回 `AGENTS.md` + `.shared/commands/*`，需要接力时写入 session |

## OpenCode 适配边界

- OpenCode 原生读取项目根 `AGENTS.md`；项目级 `AGENTS.md` 优先于兼容回退的 `CLAUDE.md`。它不会自动展开 `AGENTS.md` 中的普通文件引用，因此 bootstrap command 使用 `@file` 注入对应共享命令和占位符规则。
- `.opencode/commands/{brain,plan,exec,review,session,commit}.md` 是生成式薄入口：只转发 `$ARGUMENTS` 并引用 `.shared/*`，不复制共享工作流正文，也不固定 agent、model 或 subtask。
- OpenCode 默认多数权限为 `allow`；项目需要机械审批时应显式配置 `permission`。`--auto` 会自动批准非显式 `deny` 的询问，不能把文本中的“高风险操作前确认”描述成 runtime 强制拦截。
- `opencode.json*`、`.opencode/agents/*`、`.opencode/skills/*`、plugins、MCP、Provider 与认证属于项目或用户的运行时配置，不由核心 bootstrap 默认创建。
- OpenCode 项目级 skills 发现兼容 `.claude/skills/*` 与 `.agents/skills/*`；skill 类可选工具（如 browser）随工具安装落地 `.claude/skills/` 后即可被发现，无需重复包装到 `.opencode/skills/`。
- OpenCode 的 `/undo` / `/redo` 会改写工作树；agentwork 不自动触发这些命令，也不把它们当作 staged 区管理工具。
- command 解析或权限行为在平台升级后漂移时，按本文冲突处理流程回退。

## Codex custom agent 边界

- `.codex/agents/` 是 **Codex-only** 的项目级运行层，不是跨平台共享规则层。
- 不要为了“平台对齐”把 agent prompt 正文复制到 `.claude/`、`.agent/` 或 `.opencode/agents/`。
- 如果某条规则需要跨平台长期复用，应先写入 `.shared/*`；custom agent 只保留委派角色与输出契约。
- 如果 Codex custom agents 失效、未加载或行为漂移，主代理应直接退回 `.shared/*` 工作流，不阻塞交付。

## 冲突处理流程

触发条件：

- 平台行为与文档描述不一致
- 命令可读但不可执行（触发失败或参数失效）
- 平台升级后出现行为漂移

处理顺序（必须按序）：

1. 先查官方文档与 release/changelog，更新本地假设。
2. 做最小可复现验证，记录命令、配置、结果。
3. 临时回退到 `.shared/commands/*` 手动执行，保障交付。
4. 将高信号结论写入 session“审查记录”。
5. 结论稳定后再摘录到 `.shared/project/*`。

## 社区资料可信度分级

1. 官方文档、官方 changelog / release note
2. 官方仓库示例、测试、默认配置
3. 维护者在官方渠道的 FAQ / issue 回答
4. 社区博客与二手教程

## 落地检查清单

- 平台入口是否保持入口说明（不复制 `.shared/commands/*` 正文）
- 规则变更是否先更新 `.shared/*` 再更新平台入口
- 差异结论是否标注来源级别（官方/社区/待验证）
- 若项目中存在该脚本，文档变更后是否执行 `.shared/scripts/doc-health-check.sh`
