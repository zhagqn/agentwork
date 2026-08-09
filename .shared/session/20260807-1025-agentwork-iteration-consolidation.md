# Session: 20260807-1025-agentwork-iteration-consolidation

> 创建: 2026-08-07 10:25
> 简述: 收敛 agentwork 自承载、平台适配、可选工具与 Research 迭代的当前有效工作快照

## 任务列表（按优先级）
- [x] 将 agentwork source 迭代收敛为单一 session，并删除 4 个已被吸收的旧快照
- [x] 从 agentwork workflow 退役 GitHub Copilot / Antigravity，并确认 Figma desktop-first
- [x] 完成 source 最终 review，修复退役清理所有权边界和 optional tool 文档语义，并通过全量自检
- [x] 提交 agentwork source 平台收敛批次：`152eadc refactor(agentwork): 收敛平台适配与迭代快照`
- [x] 完成 research 单一入口、provider 分层、真实 E2E 和官方文档扩展评测，退役未达 gate 的文档聚合 provider
- [x] 修复 research review 发现的安装事务、provider readiness、项目级 MCP 接入和过期评测工件问题
- [x] 复审当前 Research 批次，补齐 manifest 根目标/空 entries/父子目标冲突 preflight 与 `Ctrl-C` 回滚，删除无现存工件支撑的历史分数
- [ ] 为现行 8-case 内容套件与 12-case 路由套件生成可审计执行结果，通过 gate 后再决定 Research/Exa stable 状态
- [ ] 在服务端轮换曾进入 Git 历史的 research provider 旧凭据（包含 Brave Search）

## 已确认结论（工作快照）
### 目标
- 用一个可恢复的 session 维护 agentwork source 的当前有效结论和提交边界。
- 以 agentwork source 为工作流事实源，后续迭代默认从本 session 续接。

### 边界
- In Scope: 自承载 bootstrap、核心命令流、平台薄封装、optional tool 边界、Figma/CodeGraph/Ponytail 定位、research 单一入口与 provider 评测、GitHub Copilot/Antigravity 退役。
- Out of Scope: Git 历史改写、自动 stage/commit、服务端凭据轮换、删除通用 GitHub 内容或用户自有平台配置。

### 约束
- 当前支持平台仅为 Codex、Claude、OpenCode、Cursor；共享正文保持平台无关，各平台只保留薄封装。
- 可选工具不进入 bootstrap；安装后必须与各自 `tool.json` 完整一致，不接受“部分安装”状态。
- Git index 是用户的提交和 review 边界；本 session 创建与校验不改变 staged 区。
- source repo 是生成源和长期规范；安装器只操作 agentwork 管理的路径，项目自有资产不得被覆盖。
- 退役 adapter 只在内容可识别为 agentwork 生成物时自动删除；同路径的项目自定义文件、符号链接、历史记录和无关 `.github` 内容保留。
- 本统一 session 使用 strict-flow。

### 已选方案
- 核心工作流保持 `/brain -> /plan -> /session plan -> /exec -> /review -> /commit`；当前任务上下文写入显式引用的 session，不在启动时自动加载全部历史。
- bootstrap 只安装稳定核心；optional tool 继续通过 `install-tool.py` 和 manifest 管理，source 自承载只物化所需 shared 参考文档。
- Figma 默认使用 Desktop MCP；remote MCP 仅在 Desktop 不可用时作为 fallback。
- CodeGraph 作为可选语义导航/MCP 工具，适合跨文件调用图和复杂仓库；Ponytail 作为独立可选规则工具，不作为 CodeGraph 的替代基础。
- GitHub Copilot/Antigravity 从当前 agentwork workflow、生成源和 tool manifests 中退役；安装器仅精确清理 agentwork 拥有的旧路径。
- Research 保持 provider-neutral 单一入口：本地资料和直接官方来源优先，已知 GitHub 事实用 `gh`，未知公开 Web 发现/批量 fetch 用 Exa，跨仓库实现证据按需升级 Octocode，可视或登录态才使用 Browser。
- 旧架构的评测观察不作为当前 promotion 证据；Research/Exa 保持 provisional，Octocode 保持 experimental，只有现行套件和可审计结果工件可以改变状态。
- 版本、迁移、兼容、弃用和安全问题直接读取 package metadata、官方文档、release 或源码，不经过文档聚合层。

### 核心定义 / 流程
- 事实源顺序：agentwork source 规范与 manifests -> 安装器生成/同步 -> 隔离安装态与运行时 smoke。
- 状态判定：工具 manifest entries 全部存在且内容一致才算已安装；全部不存在才算未安装；missing/drifted 必须清理或补齐。
- 续作顺序：用户确认后提交当前 source Research 批次 -> 生成现行评测结果 -> 根据 gate 决定 Research/Exa 状态。

## 计划摘要
> 此处只保留继续推进所需的统一执行视图；过程讨论仍由关联工件提供证据。

### 关键文件 / 边界
- bootstrap：`install-bootstrap.py`、`.agentwork/bootstrap/**`、根目录 `AGENTS.md` 及平台入口。
- optional tools：`.agentwork/tools/**`、`install-tool.py`、shared MCP/tool 参考文档、research 路由/评测契约和语义导航约束。
- source 当前批次：Research 单一入口、Exa/Octocode 受限 provider、optional tool 凭据与事务生命周期、现行评测契约及确定性测试。

### 执行批次 / 优先级
- 已完成：source 自承载与命令流、optional tool 边界、OpenCode 一等适配、Figma desktop-first 和退役平台清理。
- 已完成：research 单一入口、Exa 受限路由、Octocode experimental 边界、直接官方文档扩展评测和低收益 provider 退役。
- 当前：source Research 批次已通过确定性回归，等待提交与现行 8-case/12-case 行为评测。

### 执行策略
- `standard`：事实源先修正，再通过安装命令同步目标仓库；每轮对 manifest、引用、运行态、session 和 Git 边界分层验证。

### 验证策略
- source：`agentwork-check.py self-test`、JSON/Python 解析、tool catalog 安装/重装/卸载往返、故障与用户中断回滚、manifest 路径冲突 preflight、research 结构路由契约和 `git diff --check`。
- research：冻结公开问题和一手真值；provider 每例固定调用预算；逐事实人工复核、引用可访问性检查，并与本地/直接官方 baseline 比较调用、耗时和返回字符。
- 提交前：source 使用 working-tree review，重新确认 staged/unstaged 边界。

### 完成标准
- 本统一 session 通过 strict-flow 和 session-review，可独立说明当前目标、边界、决策、工作集、已产出批次和剩余风险。
- source 平台面仅保留 Codex/Claude/OpenCode/Cursor，退役 adapter 无活动入口或生成源残留。
- Research 现行 8-case 内容套件和 12-case 路由套件通过各自 gate，且安装/卸载在写入失败时不会留下部分状态；provider readiness 与项目级 MCP 接入可按文档复现。

## 关联工件
- `.tmp/agentwork/plan/20260713-2204-ponytail-codegraph-optional-tools.md`
- `.tmp/agentwork/plan/20260806-0956-opencode-adaptation-gap-fix.md`

## 当前批次工作集
- 范围: `.agentwork/tools/**` | 主题: Research 单一入口、provider 分层、凭据契约、安装说明与评测 gate
- 范围: `.agentwork/tests/**` | 主题: 覆盖凭据管理、provider wrapper、路由契约与完整 tool catalog 往返
- 范围: `.shared/skills/**` | 主题: 同步安装后的 research 共享正文
- 范围: `.codex/skills/research/**` | 主题: 同步 Codex research 薄入口
- 范围: `.claude/skills/**` | 主题: 同步 Claude/OpenCode research 薄入口
- 范围: `.cursor/rules/research.mdc` | 主题: 同步 Cursor research 薄入口
- 范围: `.codex/agents/**` | 主题: 保持当前 Codex agent 定义安装态
- 范围: `install-tool.py` | 主题: 管理 optional tool 凭据占位与安全安装/卸载生命周期
- 范围: `.gitignore` | 主题: 忽略项目级 `.env` 凭据文件
- 范围: `.shared/project/agentwork.md` | 主题: 维护 research 与 optional provider 的长期边界
- 范围: `.shared/session/*.md` | 主题: 收敛当前 review 事实、风险和后续任务

## 产出批次（提交锚点）
- 历史: `自承载、session 工作流、Arch、command preview 与 Ponytail/CodeGraph optional tool 边界已闭环` | 范围: `8b41c9e..1ad3eed`
- 提交: `24d51e8 feat(adapters): 完善 OpenCode 与 Codex 适配` | 范围: OpenCode 一等适配与 Codex 交互规则
- 提交: `70fb671 feat(figma): 默认使用 Desktop MCP` | 范围: Figma source 规范与自承载安装态
- 提交: `152eadc refactor(agentwork): 收敛平台适配与迭代快照` | 范围: 退役平台、精确清理边界与本统一 session 基线
- 提交: `-` | 范围: 当前 Research/Exa/Octocode、optional tool 安装事务、确定性测试与 session 收敛批次

## 风险 / 阻塞
- research provider 旧凭据曾进入 Git 历史；tracked 配置已清理，但只有服务端轮换才能使旧值失效。
- Research/Exa 仍为 provisional，现行 8-case/12-case 套件尚未执行，不能标记 stable。
- 安装器已对普通运行异常和 `Ctrl-C` 提供 tool entries、`.env` 和 `.gitignore` 回滚；进程被强制终止、系统掉电或底层文件系统故障仍需通过重复命令恢复 manifest 完整状态。
- 真实 provider E2E 仍按工具需要单独 smoke，不作为默认合并 gate；结构测试通过不能替代路由行为评测。

## 审查记录
### 2026-08-07 平台收敛
- 变更：统一有效 session，修复退役路径无条件删除问题，保留同路径项目自定义文件和符号链接；Figma desktop-first、optional tool 完整安装与四平台边界收敛。
- 验证：source 回归通过，结果提交为 `152eadc`。

### 2026-08-09 Research 架构收敛
- 变更：建立 provider-neutral `research` skill、项目级凭据占位管理、Exa/Octocode 受限 wrapper 和 provider 独立生命周期；退役未达 gate 的文档聚合路径。
- 边界：真实 provider E2E 只作人工 smoke；远程 provider 只接收公开输入，最终引用必须打开核对。旧架构分数因无现存结果工件不作为当前 gate。

### 2026-08-09 13:23 当前批次复审
- 发现/修正：manifest 可将 target 指向项目根、允许空 entries 或声明父子重叠目标，会破坏安装与回滚边界；`Ctrl-C` 原本不触发回滚。现已全部 preflight/回滚并补故障注入。
- 清理：删除路由套件中已退出当前路由的 provider 名单、无结果工件支撑的历史分数和 Exa 不合同的 Browser fallback；Session 移除已提交批次的“当前”描述。
- 验证：36/36 工具测试、10-tool catalog 安装/重装/卸载、核心 self-test、Python 编译、source/installed Research 一致、退役文档 provider 扫描和 `git diff --check` 通过；现行 8-case/12-case 行为评测未执行。

## 建议摘录到 Project（可选）
- 当前支持平台、Figma desktop-first、optional tool 完整安装语义和精确退役边界已写入长期 source 文档，无需重复摘录。
