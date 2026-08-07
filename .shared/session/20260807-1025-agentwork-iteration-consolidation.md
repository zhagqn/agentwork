# Session: 20260807-1025-agentwork-iteration-consolidation

> 创建: 2026-08-07 10:25
> 简述: 收敛 agentwork 自承载、平台适配、可选工具与 GV 迁移迭代的当前有效工作快照

## 任务列表（按优先级）
- [x] 将 agentwork source 与 GV 迁移迭代收敛为单一 session，并删除 4 个已被吸收的旧快照
- [x] 从 source 与 GV 安装态退役 GitHub Copilot / Antigravity，确认 Figma desktop-first 和 GV 19/19 工具安装态
- [x] 完成 source 最终 review，修复退役清理所有权边界和 optional tool 文档语义，并通过全量自检
- [x] 提交 agentwork source 当前批次
- [ ] 对 GV 当前 staged 批次执行 cached-only review，并在用户明确要求后提交
- [ ] 在服务端轮换曾进入 Git 历史的 Brave Search / Context7 旧凭据

## 已确认结论（工作快照）
### 目标
- 用一个可恢复的 session 维护 agentwork source 与 GV 安装态的当前有效结论和提交边界。
- 以 agentwork source 为工作流事实源，以 GV worktree 为安装态验证目标，后续迭代默认从本 session 续接。

### 边界
- In Scope: 自承载 bootstrap、核心命令流、平台薄封装、optional tool 边界、Figma/CodeGraph/Ponytail 定位、GV 升级迁移与工具安装态、GitHub Copilot/Antigravity 退役。
- Out of Scope: GV 业务代码、Git 历史改写、自动 stage/commit、服务端凭据轮换、删除通用 GitHub 内容或用户自有退役平台配置。

### 约束
- 当前支持平台仅为 Codex、Claude、OpenCode、Cursor；共享正文保持平台无关，各平台只保留薄封装。
- 可选工具不进入 bootstrap；安装后必须与各自 `tool.json` 完整一致，不接受“部分安装”状态。
- Git index 是用户的提交和 review 边界；本 session 创建与校验不改变 source 或 GV 的 staged 区。
- source repo 是生成源和长期规范；GV 只同步 agentwork 管理的路径，业务源码和项目自有资产不得被覆盖。
- 退役 adapter 只在内容可识别为 agentwork 生成物时自动删除；同路径的项目自定义文件、符号链接、历史记录和无关 `.github` 内容保留。
- 本统一 session 使用 strict-flow；GV 34 个迁移 session 保持结构检查和 session-review gate，不追溯补写历史计划字段。

### 已选方案
- 核心工作流保持 `/brain -> /plan -> /session plan -> /exec -> /review -> /commit`；当前任务上下文写入显式引用的 session，不在启动时自动加载全部历史。
- bootstrap 只安装稳定核心；optional tool 继续通过 `install-tool.py` 和 manifest 管理，source 自承载只物化所需 shared 参考文档。
- Figma 默认使用 Desktop MCP；remote MCP 仅在 Desktop 不可用时作为 fallback。
- CodeGraph 作为可选语义导航/MCP 工具，适合跨文件调用图和复杂仓库；Ponytail 作为独立可选规则工具，不作为 CodeGraph 的替代基础。
- GV 最终安装集为 Android 6、Browser 5、Figma 7、CodeGraph 1，共 19/19 manifest entries；Arch 已由用户手动卸载，Godot/Ponytail 未安装。
- Apifox/PostgreSQL 已从 GV 活动工具入口移除；业务 PostgreSQL、Docker 和历史叙述不属于工具入口清理范围。
- GitHub Copilot/Antigravity 从当前 agentwork workflow、生成源、tool manifests 和 GV 安装态中退役；安装器仅精确清理 agentwork 拥有的旧路径。

### 核心定义 / 流程
- 事实源顺序：agentwork source 规范与 manifests -> 安装器生成/同步 -> GV 安装态与运行时 smoke。
- 状态判定：工具 manifest entries 全部存在且内容一致才算已安装；全部不存在才算未安装；missing/drifted 必须清理或补齐。
- 续作顺序：用户确认后提交 source -> cached-only 审查 GV staged 批次 -> 用户确认后提交 GV -> 重新执行跨仓库回归。

## 计划摘要
> 此处只保留继续推进所需的统一执行视图；过程讨论仍由关联工件提供证据。

### 关键文件 / 边界
- bootstrap：`install-bootstrap.py`、`.agentwork/bootstrap/**`、根目录 `AGENTS.md` 及平台入口。
- optional tools：`.agentwork/tools/**`、`install-tool.py`、shared MCP/tool 参考文档和语义导航约束。
- source 当前批次：退役 `.agent/**` 与 agentwork 生成的 Copilot 文件，收敛平台文档、tool manifests、Figma/Ponytail 说明和精确卸载逻辑。
- GV 当前批次：迁移后的 `.shared/**`、4 个保留平台入口、Android/Browser/Figma/CodeGraph 安装态和 34 个重构 session；业务目录始终在边界外。

### 执行批次 / 优先级
- 已完成：source 自承载与命令流、optional tool 边界、OpenCode 一等适配、Figma desktop-first 和退役平台清理。
- 已完成：GV 核心迁移、34 个 session 重构、工具清理、CodeGraph 接入、rebase 收敛和退役平台同步。
- 当前：source review 与提交已闭环；随后进入 GV cached-only review、显式提交和跨仓库回归。

### 执行策略
- `standard`：事实源先修正，再通过安装命令同步目标仓库；每轮对 manifest、引用、运行态、session 和 Git 边界分层验证。

### 验证策略
- source：bootstrap 自刷新幂等、`agentwork-check.py self-test`、JSON/Python 解析、7 个 tool manifest surface、退役 adapter 引用和 `git diff --check`。
- GV：34/34 session check 与 session-review、19/19 manifest exact、Figma Desktop endpoint、CodeGraph 查询/遥测、Apifox/PostgreSQL 活动引用、业务目录和 Git 冲突状态。
- 提交前：source 使用 working-tree review；GV 只审查 cached diff，且两边均重新确认 staged/unstaged 数量。

### 完成标准
- 本统一 session 通过 strict-flow 和 session-review，可独立说明当前目标、边界、决策、工作集、已产出批次和剩余风险。
- source 和 GV 的平台面仅保留 Codex/Claude/OpenCode/Cursor，退役 adapter 无活动入口或生成源残留。
- GV 保持 19/19 工具安装态、34/34 session 可解析、业务目录无改动；两仓库提交均需用户显式授权。

## 关联工件
- `.tmp/agentwork/plan/20260713-2204-ponytail-codegraph-optional-tools.md`
- `.tmp/agentwork/plan/20260806-0956-opencode-adaptation-gap-fix.md`
- `.tmp/agentwork/plan/20260806-1149-gv-agentwork-upgrade-migration.md`
- `.tmp/agentwork/plan/20260806-2152-gv-tool-cleanup-codegraph.md`
- `.tmp/agentwork/review/20260807-1018-gv-platform-removal-migration.md`

## 当前批次工作集
- 范围: `install-bootstrap.py` | 主题: 精确退役 agentwork 旧平台路径并保持安装幂等
- 范围: `.agentwork/bootstrap/**` | 主题: 生成面只保留 Codex、Claude、OpenCode、Cursor
- 范围: `.agentwork/tools/**` | 主题: 移除退役平台 surface，保持 manifest 完整安装语义并收敛 Figma/Ponytail 说明
- 范围: `.agent/**` | 主题: 删除 source repo 中已退役的 Antigravity 自承载输出
- 范围: `.github/**` | 主题: 删除 agentwork 生成的 Copilot 根入口和工具入口
- 范围: `.shared/mcp/figma.md` | 主题: 固化 Figma desktop-first 长期事实
- 范围: `.shared/patterns/platform-adapter.md` | 主题: 固化当前四平台适配边界
- 范围: `.shared/project/agentwork.md` | 主题: 更新 source repo 稳定事实
- 范围: `.shared/tools/ponytail.md` | 主题: 移除退役平台说明并保持可选工具边界
- 范围: `AGENTS.md` | 主题: 同步当前支持平台与启动约束
- 范围: `.shared/session/*.md` | 主题: 删除已被吸收的旧迭代快照，只保留统一续作 session 和目录说明

## 产出批次（提交锚点）
- 历史: `自承载、session 工作流、Arch、command preview 与 Ponytail/CodeGraph optional tool 边界已闭环` | 范围: `8b41c9e..1ad3eed`
- 提交: `24d51e8 feat(adapters): 完善 OpenCode 与 Codex 适配` | 范围: OpenCode 一等适配与 Codex 交互规则
- 提交: `70fb671 feat(figma): 默认使用 Desktop MCP` | 范围: Figma source 规范与自承载安装态
- 提交: `-` | 范围: `.shared/session/20260807-1025-agentwork-iteration-consolidation.md`（session 文件自身，等待后续提交）

## 风险 / 阻塞
- GV 当前有 127 个 staged 路径、0 unstaged；该 index 属用户边界，必须先做 cached-only review，不能由 source session 操作隐式改写。
- Brave Search/Context7 旧凭据曾进入 Git 历史；tracked 配置已清理，但只有服务端轮换才能使旧值失效。
- source gate 已覆盖 shared 载荷、manifest、生成链和隔离安装；真实 provider E2E 仍按工具需要单独 smoke，不作为默认合并 gate。

## 审查记录
### 2026-08-07 10:18
- 变更：完成 GV 平台退役同步、Android drift 修复、Figma/CodeGraph 最终态复查，并确认 rebase 后无冲突元数据。
- 验证：source self-test/manifest/幂等检查通过；GV 34/34 session、19/19 工具 entries、Figma Desktop、CodeGraph 查询与业务边界检查通过。
- 风险/待办：保留 source 未暂存和 GV 已暂存两套提交边界；外部凭据轮换仍未完成。

### 2026-08-07 10:30
- 变更：将有效迭代收敛到本 session，删除 4 个已被吸收的旧快照；提交锚点和当前结论保留。
- 验证：strict-flow/session-review、source self-test、bootstrap 幂等、四平台空项目 smoke 和 7 个 optional tools 安装/卸载往返通过。
- 风险/待办：旧快照仍可从 Git 历史恢复；source staged 区保持为空。

### 2026-08-07 13:36
- 变更：source 双层 review 发现并修复退役路径按路径无条件删除的问题；安装器改为验证 agentwork marker/旧 wrapper 签名，保留同路径自定义文件与符号链接。同步移除 tool 文档的“wrapper 可选安装”歧义，统一 Ponytail 默认 `full` 口径。
- 验证：安装器整链路正反 smoke 通过，旧 agentwork wrapper 被清理，同路径自定义文件和符号链接被保留；当前 manifests 只含 shared/Codex/Claude/Cursor/OpenCode，GV 仍为 127 staged、0 unstaged，两个仓库 staged 边界未被改动。
- 风险/待办：source 当前批次与本 session 同笔提交；下一步执行 GV cached-only review。

## 建议摘录到 Project（可选）
- 当前支持平台、Figma desktop-first、optional tool 完整安装语义和精确退役边界已写入长期 source 文档，无需重复摘录。
