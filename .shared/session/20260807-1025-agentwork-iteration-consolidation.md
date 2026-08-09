# Session: 20260807-1025-agentwork-iteration-consolidation

> 创建: 2026-08-07 10:25
> 简述: 收敛 agentwork 自承载、平台适配、可选工具与 Research 迭代的当前有效工作快照

## 任务列表（按优先级）
- [x] 收敛 agentwork source 的 bootstrap、四平台适配、optional tool 边界与统一 session，结果提交至 `152eadc`
- [x] 完成 Research 单一入口、provider 分层、安装事务与确定性测试，结果提交至 `d4995af`
- [x] 将 `luna_worker` 纳入 spec 驱动的 bootstrap 初始化并完成双层 review
- [ ] 为现行 8-case 内容套件与 12-case 路由套件生成可审计执行结果，通过 gate 后再决定 Research/Exa stable 状态
- [ ] 在服务端轮换曾进入 Git 历史的 research provider 旧凭据（包含 Brave Search）

## 已确认结论（工作快照）
### 目标
- 用一个可恢复的 session 维护 agentwork source 的当前有效结论和提交边界。
- 以 agentwork source 为工作流事实源，后续迭代默认从本 session 续接。

### 边界
- In Scope: 当前 Codex 子代理 bootstrap 批次、Research 现行评测与凭据轮换待办、已提交批次锚点。
- Out of Scope: 其他项目工作树、Git 历史改写、自动 stage/commit、删除用户自有平台配置。

### 约束
- 当前支持平台仅为 Codex、Claude、OpenCode、Cursor；共享正文保持平台无关，各平台只保留薄封装。
- 可选工具不进入 bootstrap；安装后必须与各自 `tool.json` 完整一致，不接受“部分安装”状态。
- Git index 是用户的提交和 review 边界；本 session 创建与校验不改变 staged 区。
- source repo 是生成源和长期规范；安装器只操作 agentwork 管理的路径，项目自有资产不得被覆盖。
- 本统一 session 使用 strict-flow。

### 已选方案
- 核心工作流保持 `/brain -> /plan -> /session plan -> /exec -> /review -> /commit`；当前任务上下文写入显式引用的 session，不在启动时自动加载全部历史。
- bootstrap 只安装稳定核心；optional tool 继续通过 `install-tool.py` 和 manifest 管理，source 自承载只物化所需 shared 参考文档。
- Codex bootstrap 默认通过 `.codex/config.toml` 受管块注册 `luna_worker`；其角色配置逐文件生成和安装，同名项目自定义定义不覆盖。
- Research 保持 provider-neutral 单一入口：本地资料和直接官方来源优先，已知 GitHub 事实用 `gh`，未知公开 Web 发现/批量 fetch 用 Exa，跨仓库实现证据按需升级 Octocode，可视或登录态才使用 Browser。
- 旧架构的评测观察不作为当前 promotion 证据；Research/Exa 保持 provisional，Octocode 保持 experimental，只有现行套件和可审计结果工件可以改变状态。

### 核心定义 / 流程
- 事实源顺序：agentwork source 规范与 manifests -> 安装器生成/同步 -> 隔离安装态与运行时 smoke。
- 状态判定：工具 manifest entries 全部存在且内容一致才算已安装；全部不存在才算未安装；missing/drifted 必须清理或补齐。
- 续作顺序：用户确认后提交 Codex 子代理 bootstrap 批次 -> 生成现行 Research 评测结果 -> 根据 gate 决定 Research/Exa 状态。

## 计划摘要
> 此处只保留继续推进所需的统一执行视图；过程讨论仍由关联工件提供证据。

### 关键文件 / 边界
- bootstrap：`install-bootstrap.py`、`.agentwork/bootstrap/**`、根目录 `AGENTS.md`、`.codex/config.toml` 受管块及平台入口。
- Research 后续：`.agentwork/tools/research/evals/**` 及 provider readiness。
- source 当前批次：Codex `luna_worker` 的 spec 定义、生成产物、项目注册、保守安装边界及确定性测试。

### 执行批次 / 优先级
- 已完成：平台与 Research source 批次分别提交为 `152eadc`、`d4995af`。
- 当前：Codex 执行子代理 bootstrap 已通过双层 review 与确定性回归，等待 commit。
- 后续：执行 Research 现行 8-case/12-case 行为评测和服务端旧凭据轮换。

### 执行策略
- `standard`：事实源先修正，再通过安装命令同步目标仓库；每轮对 manifest、引用、运行态、session 和 Git 边界分层验证。

### 验证策略
- source：`agentwork-check.py self-test`、JSON/Python/TOML 解析、bootstrap 隔离安装/重装/冲突/symlink 测试、全量确定性测试和 `git diff --check`。
- research：冻结公开问题和一手真值；provider 每例固定调用预算；逐事实人工复核、引用可访问性检查，并与本地/直接官方 baseline 比较调用、耗时和返回字符。
- 提交前：source 使用 working-tree review，重新确认 staged/unstaged 边界。

### 完成标准
- 本统一 session 通过 strict-flow 和 session-review，可独立说明当前目标、边界、决策、工作集、已产出批次和剩余风险。
- source 平台面仅保留 Codex/Claude/OpenCode/Cursor，退役 adapter 无活动入口或生成源残留。
- 新项目初始化后存在已注册且配置可加载的 `luna_worker`，并保留项目已有 Codex 配置与其他 agent。
- Research 现行 8-case 内容套件和 12-case 路由套件通过各自 gate，且安装/卸载在写入失败时不会留下部分状态；provider readiness 与项目级 MCP 接入可按文档复现。

## 当前批次工作集
- 范围: `.agentwork/bootstrap/**` | 主题: 以 spec 生成 Codex agent 角色配置和项目注册块
- 范围: `install-bootstrap.py` | 主题: 保守安装 Codex agent、合并受管注册块并执行冲突/symlink 预检
- 范围: `.codex/agents/**` | 主题: source repo 自承载的 Codex agent 角色配置
- 范围: `.codex/config.toml` | 主题: source repo 自承载的 Codex agent 受管注册块
- 范围: `.agentwork/tests/test_install_bootstrap.py` | 主题: 覆盖 fresh install、幂等、项目配置保留和冲突边界
- 范围: `.shared/patterns/platform-adapter.md` | 主题: 固化跨平台 Codex custom agent 注册边界
- 范围: `.shared/project/agentwork.md` | 主题: 固化 source repo 的 Codex agent 生成与维护边界
- 范围: `.shared/session/*.md` | 主题: 回填 Research 提交锚点并记录当前 bootstrap 批次

## 产出批次（提交锚点）
- 历史: `自承载、核心命令流、OpenCode/Codex 适配、Figma 与 optional tool 基础已闭环` | 范围: `8b41c9e..70fb671`
- 提交: `152eadc refactor(agentwork): 收敛平台适配与迭代快照` | 范围: 退役平台、精确清理边界与本统一 session 基线
- 提交: `d4995af feat(research): 完善研究入口与可选 provider 工具链` | 范围: Research/Exa/Octocode、optional tool 安装事务、确定性测试与 session 收敛
- 提交: `-` | 范围: 当前 Codex 子代理 bootstrap、项目级注册、保守安装与回归测试批次

## 风险 / 阻塞
- research provider 旧凭据曾进入 Git 历史；tracked 配置已清理，但只有服务端轮换才能使旧值失效。
- Research/Exa 仍为 provisional；现行 8-case/12-case 套件及真实 provider smoke 尚未执行，结构测试不能替代 promotion gate。
- 安装器已对普通运行异常和 `Ctrl-C` 提供 tool entries、`.env` 和 `.gitignore` 回滚；进程被强制终止、系统掉电或底层文件系统故障仍需通过重复命令恢复 manifest 完整状态。

## 审查记录
### 2026-08-07 平台收敛
- 变更：统一有效 session，修复退役路径无条件删除问题，保留同路径项目自定义文件和符号链接；Figma desktop-first、optional tool 完整安装与四平台边界收敛。
- 验证：source 回归通过，结果提交为 `152eadc`。

### 2026-08-09 Research 架构与安装边界
- 变更：建立 provider-neutral `research`、Exa/Octocode 受限 provider 和项目级凭据管理；补齐 manifest 目标冲突 preflight、失败/中断回滚与现行评测契约，结果提交为 `d4995af`。
- 边界：远程 provider 只接收公开输入，最终引用必须打开核对；旧架构分数不作为当前 gate，现行行为评测仍待执行。

### 2026-08-09 Codex 子代理初始化
- 变更：将 `luna_worker` 纳入 bootstrap spec；生成角色配置与 `.codex/config.toml` 受管注册块，安装时逐文件维护并保留其他 Codex 配置和 agent。
- 边界：同名项目角色或非 agentwork 文件、Codex 路径符号链接会在任何目标写入前终止；仅受信任项目会加载项目级 Codex 配置。
- 审查：无阻塞代码问题；spec、renderer、installer 与测试职责清晰，受管配置合并没有覆盖项目自定义内容。
- 验证：bootstrap 隔离场景 5/5、全量测试 41/41、核心 self-test、Python/JSON/TOML 解析、source 原地刷新、Codex `--strict-config doctor`、模型目录检查和 `git diff --check` 通过。
