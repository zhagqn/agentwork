# Session: 20260807-1025-agentwork-iteration-consolidation

> 创建: 2026-08-07 10:25
> 简述: 收敛 agentwork 自承载、平台适配、可选工具与 Research 迭代的当前有效工作快照

## 任务列表（按优先级）
- [x] 收敛 agentwork source 的 bootstrap、四平台适配、optional tool 边界与统一 session，结果提交至 `152eadc`
- [x] 完成 Research 单一入口、provider 分层、安装事务与确定性测试，结果提交至 `d4995af`
- [x] 将 `luna_worker` 纳入 spec 驱动的 bootstrap 初始化并完成双层 review，结果提交至 `d6387db`
- [x] 修正 session/review 保真策略的无日期/无效日期审查漏检，刷新 source receipt 并完成当前批次验证
- [x] 将 `.agentwork/bootstrap-install-state.json` 与 session/review 当前批次一并提交至 `798dded`
- [ ] 为现行 8-case 内容套件与 12-case 路由套件生成可审计执行结果，通过 gate 后再决定 Research/Exa stable 状态
- [ ] 在服务端轮换曾进入 Git 历史的 research provider 旧凭据（包含 Brave Search）

## 已确认结论（工作快照）
### 目标
- 用一个可恢复的 session 维护 agentwork source 的当前有效结论和提交边界。
- 以 agentwork source 为工作流事实源，后续迭代默认从本 session 续接。

### 边界
- In Scope: session/review 保真策略与检查器当前批次、Research 现行评测与凭据轮换待办、已提交批次锚点。
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
- agentwork 只校验当前版本的 session 契约，不为 `gv` 等旧项目增加全局兼容模式；旧 session 在实际续作且存在可验证提交时按 Git 事实重整，没有历史提交或可靠证据时忽略，不补造历史。
- `.agentwork/bootstrap-install-state.json` 是安装器跨克隆、跨机器重复同步时识别旧版受管文件的仓库级所有权账本，不作为本地缓存忽略；source 实现收敛后刷新并纳入版本控制。

### 核心定义 / 流程
- 事实源顺序：agentwork source 规范与 manifests -> 安装器生成/同步 -> 隔离安装态与运行时 smoke。
- 状态判定：工具 manifest entries 全部存在且内容一致才算已安装；全部不存在才算未安装；missing/drifted 必须清理或补齐。
- 续作顺序：生成现行 Research 评测结果 -> 根据 gate 决定 Research/Exa 状态 -> 轮换服务端旧凭据。

## 计划摘要
> 此处只保留继续推进所需的统一执行视图；过程讨论仍由关联工件提供证据。

### 关键文件 / 边界
- session/review 当前批次：`.shared/commands/{session,review}.md`、`.shared/patterns/session-workflow.md`、session 模板/README、`.shared/scripts/{agentwork-check.py,session-review.sh}` 及 bootstrap managed block。
- Research 后续：`.agentwork/tools/research/evals/**` 及 provider readiness。
- 已提交 bootstrap 基线：`install-bootstrap.py`、`.agentwork/bootstrap/**`、根目录 `AGENTS.md`、`.codex/config.toml` 受管块及平台入口。

### 执行批次 / 优先级
- 已完成：平台与 Research source 批次分别提交为 `152eadc`、`d4995af`。
- 已完成：Codex 执行子代理 bootstrap 已提交为 `d6387db`。
- 已完成：session/review 按主题归类产出、保留独立提交锚点，并将审查记录分为最近 3 次详情和更早摘要；无日期与无效日期标题均会明确失败，legacy session 不属于 agentwork 当前契约的兼容与回归范围；source receipt 以 47 项零缺失、零漂移纳入 `798dded`。
- 后续：执行 Research 现行 8-case/12-case 行为评测和服务端旧凭据轮换。

### 执行策略
- `standard`：事实源先修正，再通过安装命令同步目标仓库；每轮对 manifest、引用、运行态、session 和 Git 边界分层验证。

### 验证策略
- source：`agentwork-check.py self-test`、JSON/Python/TOML 解析、bootstrap 隔离安装/重装/冲突/symlink 测试、全量确定性测试和 `git diff --check`。
- research：冻结公开问题和一手真值；provider 每例固定调用预算；逐事实人工复核、引用可访问性检查，并与本地/直接官方 baseline 比较调用、耗时和返回字符。
- 提交前：source 使用 working-tree review，重新确认 staged/unstaged 边界。

### 完成标准
- 本统一 session 通过 strict-flow 和 session-review，可独立说明当前目标、边界、决策、工作集、已产出批次和剩余风险。
- session review 不按固定条数截断独立提交、关键取舍、迁移前提或未闭环风险；自动检查可识别重复锚点、近期审查字段、日期倒序和历史摘要位置。
- source 平台面仅保留 Codex/Claude/OpenCode/Cursor，退役 adapter 无活动入口或生成源残留。
- 新项目初始化后存在已注册且配置可加载的 `luna_worker`，并保留项目已有 Codex 配置与其他 agent。
- Research 现行 8-case 内容套件和 12-case 路由套件通过各自 gate，且安装/卸载在写入失败时不会留下部分状态；provider readiness 与项目级 MCP 接入可按文档复现。

## 当前批次工作集
- 范围: `.shared/session/20260807-1025-agentwork-iteration-consolidation.md` | 主题: 回填 `798dded` 提交锚点并收敛 session/review 当前批次状态

## 产出批次（提交锚点）
- 历史: `自承载、核心命令流、OpenCode/Codex 适配、Figma 与 optional tool 基础已闭环` | 提交: `8b41c9e`, `70fb671` | 范围: 核心工作流与早期平台/工具基础
- 提交: `152eadc refactor(agentwork): 收敛平台适配与迭代快照` | 范围: 退役平台、精确清理边界与本统一 session 基线 | 验证: source 回归通过，项目自定义文件和符号链接保留边界已覆盖
- 提交: `d4995af feat(research): 完善研究入口与可选 provider 工具链` | 范围: Research/Exa/Octocode、optional tool 安装事务、确定性测试与 session 收敛 | 验证: 安装事务与现行评测契约通过确定性测试，provider promotion gate 仍保持未完成
- 提交: `d6387db feat(bootstrap): 初始化 Codex 执行子代理` | 范围: `.agentwork/bootstrap/{spec.json,render_bootstrap.py,codex}/`、`.codex/{agents/luna-worker.toml,config.toml}`、本 session | 验证: bootstrap 隔离场景、全量测试、核心 self-test、配置解析与 source 原地刷新通过
- 提交: `798dded feat(session): 完善审查信息保真` | 范围: session/review 策略、模板、检查器、取证脚本与 source receipt | 验证: checker self-test 覆盖无日期/无效日期负例，74 项 source unittest、脚本语法、差异检查与 source 自刷新通过；receipt 47 项零缺失、零漂移，legacy session 已排除在当前契约兼容与回归范围之外
- 提交: `-` | 范围: `.shared/session/20260807-1025-agentwork-iteration-consolidation.md` | 验证: 回填 `798dded` 并同步当前工作集、任务状态与剩余风险

## 风险 / 阻塞
- research provider 旧凭据曾进入 Git 历史；tracked 配置已清理，但只有服务端轮换才能使旧值失效。
- Research/Exa 仍为 provisional；现行 8-case/12-case 套件及真实 provider smoke 尚未执行，结构测试不能替代 promotion gate。
- 安装器已对普通运行异常和 `Ctrl-C` 提供 tool entries、`.env` 和 `.gitignore` 回滚；进程被强制终止、系统掉电或底层文件系统故障仍需通过重复命令恢复 manifest 完整状态。
- 自动检查只能校验锚点重复、记录顺序和最低信息字段，不能替代 review 对关键决策、迁移前提和风险是否仍有语义价值的判断。

## 审查记录
### 2026-08-21 22:11 session/review 当前批次 fresh review
- 变更：完成工作快照与实现双层复审；确认日期校验仍位于显式 session checker 边界，shell 取证与 Python 结构检查职责分离，receipt 作为仓库级所有权账本随批次交付，未引入运行时状态、隐式 session 加载或平台私有核心逻辑。
- 验证：checker self-test、74 项 source unittest、Shell/Python/JSON 检查、session-review、strict-flow、`git diff --check` 和 source 重复安装均通过；receipt 重复刷新内容稳定，47 项零缺失、零漂移。
- 风险/待办：未发现 Critical/Important 问题；receipt 已由 `798dded` 纳入，继续保留 Research 真实评测与服务端旧凭据轮换待办。

### 2026-08-21 当前 session/review 保真批次复审
- 变更：复核 session/review 契约、检查器、取证脚本、bootstrap managed block、本 session 与 source receipt；工作流方向仍保持显式任务快照和 provider-neutral 核心层。
- 验证：checker self-test、74 项 source unittest、脚本语法、managed block 对齐和 `git diff --check` 通过；当前 session 的 brace 范围曾被 `session-review.sh` 判为未覆盖，无日期审查标题实测不会产生失败。gv legacy session 仅作为旧格式事实记录，不作为 agentwork 当前契约的回归样本。
- 风险/待办：修正无日期漏检，刷新并跟踪 source receipt；完成后重新运行 session-review、strict-flow 和 fresh review。

### 2026-08-09 Codex 子代理初始化
- 变更：将 `luna_worker` 纳入 bootstrap spec；生成角色配置与 `.codex/config.toml` 受管注册块，安装时逐文件维护并保留其他 Codex 配置和 agent。
- 边界：同名项目角色或非 agentwork 文件、Codex 路径符号链接会在任何目标写入前终止；仅受信任项目会加载项目级 Codex 配置。
- 审查：无阻塞代码问题；spec、renderer、installer 与测试职责清晰，受管配置合并没有覆盖项目自定义内容。
- 验证：bootstrap 隔离场景 5/5、全量测试 41/41、核心 self-test、Python/JSON/TOML 解析、source 原地刷新、Codex `--strict-config doctor`、模型目录检查和 `git diff --check` 通过。
- 风险/待办：后续 Codex 配置契约变化仍需用安装器测试和真实 `doctor` smoke 复核。

### 2026-08-09 Research 架构与安装边界
- 变更：建立 provider-neutral `research`、Exa/Octocode 受限 provider 和项目级凭据管理；补齐 manifest 目标冲突 preflight、失败/中断回滚与现行评测契约，结果提交为 `d4995af`。
- 边界：远程 provider 只接收公开输入，最终引用必须打开核对；旧架构分数不作为当前 gate，现行行为评测仍待执行。
- 验证：安装事务与评测契约的确定性测试通过；真实 provider 的现行 8-case/12-case 行为评测尚未执行。
- 风险/待办：Research/Exa 保持 provisional、Octocode 保持 experimental；旧凭据仍需服务端轮换。

### 历史审查摘要（2026-08-07）
- 2026-08-07 平台收敛：统一有效 session，修复退役路径精确清理边界并收敛四平台与 optional tool；source 回归通过（`152eadc`），平台能力变化风险继续由 platform-adapter 契约和实际 smoke 跟踪。
