# 平台适配层说明（Codex / Claude / Antigravity）

> 目的：在保留 `.shared/` 统一规则的前提下，明确“平台能力边界 + 触发差异 + 回退策略”，确保跨平台协作的一致性。

## 适用范围

- 目录：`AGENTS.md`、`.claude/*`、`.agent/*`、`.shared/*`
- 对象：Codex CLI、Claude Code、Antigravity（及同类代理平台）

## 核心原则（最佳实践）

1. 共享事实集中在 `.shared/`，平台入口只做薄封装。
2. 平台能力与默认行为（权限/触发/工具）必须与共享规则分离描述。
3. 社区资料只作线索，最终以官方文档与可复现实验为准。
4. 跨平台接力仅信任 `.shared/session/*.md`，不依赖工具内私有上下文。

## 边界定义（模板提供 vs 平台提供）

模板稳定提供：

- 规则入口与长期约束（`.shared/INDEX.md`、`.shared/project/*`）
- 命令正文与占位符规范（`.shared/commands/*`、`.shared/constraints/*`）
- session 工作流与固定检查脚本（`.shared/patterns/*`、`.shared/scripts/*`）
- Codex custom agent 的编写规范（`.shared/patterns/agent-authoring.md`）

平台运行时提供（需官方确认）：

- 命令触发机制（slash/workflow/command）
- skills 或类似扩展机制的发现、优先级与冲突处理
- 沙箱、审批、严格模式等默认值与权限边界
- 多代理调度、工具路由与升级权限策略

## 平台映射（建议）

| 平台        | 入口文件                                                      | 平台差异（需官方确认）                          | 回退方式                                                |
| ----------- | ------------------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------------- |
| Codex CLI   | `AGENTS.md`、`.codex/skills/*`、`.codex/agents/*`             | AGENTS 分层合并、审批与沙箱参数、生效优先级、custom agents 的发现与继承规则 | 直接执行 `.shared/commands/*` 文本流程                  |
| Claude Code | `.claude/CLAUDE.md`、`.claude/commands/*`、`.claude/skills/*` | slash commands 与 skills 触发/优先级规则        | 以 `.shared/commands/*` 为主入口，commands 保持兼容     |
| Antigravity | `.agent/rules/*`、`.agent/workflows/*`、`.agent/skills/*`     | rules/workflows/skills 触发语义、执行策略默认值 | 退回 `.shared/INDEX.md` + `.shared/commands/*` 手动流程 |

## Codex custom agent 边界

- `.codex/agents/` 是 **Codex-only** 的项目级运行层，不是跨平台共享规则层。
- 不要为了“平台对齐”把 agent prompt 正文复制到 `.claude/` 或 `.agent/`。
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

- 平台入口是否保持薄封装（不复制 `.shared/commands/*` 正文）
- 规则变更是否先更新 `.shared/*` 再更新平台入口
- 差异结论是否标注来源级别（官方/社区/待验证）
- 若项目中存在该脚本，文档变更后是否执行 `.shared/scripts/doc-health-check.sh`
