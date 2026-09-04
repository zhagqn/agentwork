# Session: 20260807-1025-agentwork-iteration-consolidation

> 创建: 2026-08-07 10:25
> 简述: 收敛 agentwork 自承载、平台适配、可选工具与 Research 迭代的当前有效工作快照

## 任务列表（按优先级）
- [x] 收敛 agentwork source 的 bootstrap、四平台适配、optional tool 边界与统一 session，结果提交至 `152eadc`
- [x] 完成 Research 单一入口、provider 分层、安装事务与确定性测试，结果提交至 `d4995af`
- [x] 将 `luna_worker` 纳入 spec 驱动的 bootstrap 初始化并完成双层 review，结果提交至 `d6387db`
- [x] 修正 session/review 保真策略的无日期/无效日期审查漏检，刷新 source receipt 并完成当前批次验证
- [x] 将 `.agentwork/bootstrap-install-state.json` 与 session/review 当前批次一并提交至 `798dded`
- [x] 完成 Pi `v0.84.4` 深度调研、六个核心薄入口适配、真实 RPC/TUI 发现验证与 bootstrap 安全修正
- [x] 确认 Pi 后续作为可替换 Agent runtime 时采用“项目文件为事实源、全局环境仅提供最小运行时”的迁移原则
- [x] 对 Pi 核心与 optional-tool 待提交批次执行 fresh `/review`，确认 2026-08-29 两项 Important 已闭环且无新增 Critical/Important
- [x] 设计 Pi 文件优先迁移契约：首批使用自动发现目录和项目文件，不纳管 `.pi/settings.json`，只对外部依赖提供显式 restore/doctor
- [x] 按迁移契约完成首批 Pi optional-tool surface：Browser / Research / CodeGraph 通过项目级 Skill 显式安装，未引入 `.pi/settings.json`、package 或隐式 MCP 接线
- [x] 修正 `install-tool.py` 对既有文件、`.env` 与 `.gitignore` 的硬链接外写风险，并补齐成功写入和失败回滚回归
- [x] 对 optional-tool 原子替换修正执行 fresh `/review`，确认硬链接外写已闭环，但发现重装可执行文件未恢复 source 权限的新 Important
- [x] 修正 `atomic_write_bytes` 在 tool entry / rollback 场景的权限来源优先级，并补齐 executable entry 重装权限回归
- [x] 对 optional-tool 权限修正再次执行 fresh `/review`，未发现新的 Critical/Important，当前安全提交门槛已关闭
- [x] 将 optional-tool 原子写入与权限安全修正提交至 `a946ba2`
- [x] 将 Pi 核心工作流、首批 optional-tool surface 与平台文档提交至 `a590257`
- [ ] 在隔离的新环境模型中验证 clone -> bootstrap -> optional restore -> 凭据补充 -> project trust 的完整恢复链，不依赖既有用户级 Pi 配置
- [ ] 将 Case 作为独立后续议题调研；在契约成熟前继续以 `/aw-session` 封装共享 session，不自动转换 Pi JSONL 或自动双写 Case
- [ ] 为现行 8-case 内容套件与 12-case 路由套件生成可审计执行结果，通过 gate 后再决定 Research/Exa stable 状态
- [ ] 在服务端轮换曾进入 Git 历史的 research provider 旧凭据（包含 Brave Search）

## 已确认结论（工作快照）
### 目标
- 用一个可恢复的 session 维护 agentwork source 的当前有效结论和提交边界。
- 以 agentwork source 为工作流事实源，后续迭代默认从本 session 续接。
- 让 Pi 可以作为项目可选择的 Agent runtime 随 agentwork 同步到其他环境；确定性工作流能力优先由仓库文件或可锁定声明恢复。

### 边界
- In Scope: Pi 核心薄适配及其 bootstrap 安全修正、Pi 文件优先迁移契约与后续 optional-tool 恢复路径、session/review 保真策略、Research 现行评测与凭据轮换待办、已提交批次锚点。
- Out of Scope: 其他项目工作树、Git 历史改写、自动 stage/commit、打包或提交 Pi/Node runtime、下载缓存、真实凭据、trust/browser profile、Case 实现或自动迁移、静默修改用户级 Pi 配置。

### 约束
- 当前支持平台为 Codex、Claude、OpenCode、Cursor、Pi；共享正文保持平台无关，各平台只保留薄封装。
- 可选工具不进入 bootstrap；安装后必须与各自 `tool.json` 完整一致，不接受“部分安装”状态。
- Git index 是用户的提交和 review 边界；本 session 创建与校验不改变 staged 区。
- source repo 是生成源和长期规范；安装器只操作 agentwork 管理的路径，项目自有资产不得被覆盖。
- Pi 的全局安装状态只能视为机器级运行时缓存，不能成为项目迁移的隐式事实源；bootstrap/restore 默认不静默修改全局环境。
- 能以 `.pi/settings.json`、`.pi/prompts/**`、`.pi/skills/**`、`.pi/extensions/**`、本地 package 或版本锁定声明表达的能力，优先保留为项目文件；下载缓存和 `node_modules` 由声明重建，不纳入版本控制。
- API key、OAuth、SSH key、Pi trust、浏览器登录状态和用户级原生 session 属于私有或机器状态，只提供无敏感值的配置说明/占位，不随仓库分发。
- 本统一 session 使用 strict-flow。

### 已选方案
- 核心工作流保持 `/brain -> /plan -> /session plan -> /exec -> /review -> /commit`；当前任务上下文写入显式引用的 session，不在启动时自动加载全部历史。
- bootstrap 只安装稳定核心；optional tool 继续通过 `install-tool.py` 和 manifest 管理，source 自承载只物化所需 shared 参考文档。
- Codex bootstrap 默认通过 `.codex/config.toml` 受管块注册 `luna_worker`；其角色配置逐文件生成和安装，同名项目自定义定义不覆盖。
- Pi 核心适配固定在已验证的 `v0.84.4` 结构基线，仅安装 `/brain`、`/plan`、`/exec`、`/review`、`/commit`、`/aw-session` 六个项目 prompt；`/aw-session` 映射共享 `/session`，Pi 原生 `/session` 与用户目录 JSONL 继续只服务 Pi 内部对话。
- Pi adapter 保持薄层：核心 bootstrap 不安装 Pi runtime、settings、provider/model、package、extension、plan-mode、subagent 或 Pi 专属 optional tools；项目 prompt 需从仓库根 cwd 启动并通过 project trust 才能发现，trust/`--approve` 不是 sandbox 或工具审批。
- Pi 是多 provider runtime；来源任务确认当前本机实测为 `openai-codex/gpt-5.6-sol`，并确认 GLM/Kimi 等可走 Pi 内建 provider，但未执行付费模型质量对比。共享 workflow 因此保持 provider-neutral，不把任何模型配置或未经实测的排名写进项目基线。
- Pi `v0.84.4` 没有独立的可见思考语言设置；本轮不生成 `.pi/APPEND_SYSTEM.md`、不替用户关闭 thinking 或写入 `hideThinkingBlock`，语言/显示偏好继续属于用户运行时配置。
- Pi JSONL、tree/fork/compaction 用于平台内探索；跨平台交接只在显式 `/aw-session` 时写仓库 session。暂不在自动 compaction 时写共享状态，Case 也不进入当前 adapter 契约。
- Pi optional tools 按 transport 分层：Browser、Research、CodeGraph 等 CLI/Skill 路径可独立设计 Pi surface；Figma、Exa 等 MCP 优先能力在没有明确 transport 前不生成“看似可用”的 Pi 入口。
- Pi 后续迁移采用 file-first / declarative / version-pinned / rebuildable / secret-free：agentwork 自有适配优先使用仓库相对路径，本地依赖提交 manifest 与 lockfile，外部 package 固定 npm 版本或 Git ref；`.pi/npm`、`.pi/git` 和 `node_modules` 只作为可重建产物。
- 核心 bootstrap 继续只同步稳定、确定性的 Pi 薄入口；Search/MCP/Browser 等扩展能力先通过项目级 optional profile 显式安装。未来是否纳入核心必须另行通过稳定性、安全和跨环境 gate，不因其可文件化就自动扩入 bootstrap。
- 迁移恢复入口按职责拆分：bootstrap 同步核心文件，optional restore 根据项目声明恢复依赖，doctor 只读报告缺失 runtime/版本，用户最后补充凭据并显式信任项目。
- Pi 首批 optional surface 采用 settings-last：Browser、Research、CodeGraph 优先安装为 `.pi/skills/<name>/SKILL.md` 薄入口并复用 `.shared` 正文，依赖 Pi 的项目自动发现，不为它们生成 `.pi/settings.json` 或安装 Pi package。
- Browser / Research / CodeGraph 的首批 Pi surface 已按上述契约实现：tool manifest 精确同步项目 Skill；Browser 外部 CLI 仍单独安装且要求显式任务级 `AGENT_BROWSER_SESSION`，默认不自动探测 CDP；CodeGraph 只使用已有 CLI 与 `.codegraph/` 索引，不假设 Pi MCP 已连接。
- 2026-09-02 fresh review 确认 Pi 核心 bootstrap 与三个 Skill surface 本身没有新的 Critical/Important，但共用的 `install-tool.py` 文件写入会跟随目标硬链接改写项目外 inode；optional-tool 批次在改为原子替换并补回归前不可作为安全完整批次提交。
- 2026-09-02 `/session exec` 已将 optional-tool 的单文件 entry、`.env`、`.gitignore` 和文件快照回滚统一改为同目录临时文件加 `os.replace`；定向 26 项与全量 104 项测试通过，外部硬链接内容保持不变。随后 fresh review 发现 helper 在目标已存在时错误保留目标 mode，导致重装已漂移为 `0644` 的可执行 entry 后仍不可执行；提交资格继续阻塞至权限语义修正及复审完成。
- 2026-09-03 `/session exec` 已将 `atomic_write_bytes` 的权限选择调整为有效 `mode_source` 优先、无 source 时才沿用既有目标 mode；新增回归覆盖 executable entry 从 `0755` 漂移为 `0644` 后重装恢复为 `0755`。随后 fresh review 以真实 Browser 重装、3 项定向测试、全量 105 项 unittest、workflow self-test、Python/Shell/JSON、source self-host 与差异检查确认无新的 Critical/Important，当前安全提交门槛已关闭。
- 纯文件能力随 Git clone 已完成恢复，不额外执行 restore；restore 只处理不能提交的外部 CLI、package dependencies 或其他可重建产物。Search/MCP 需要 extension/adapter 时使用独立显式 profile，并在其自身目录提交源码、manifest 与 lockfile。
- `.pi/settings.json` 保持项目所有：只有未来出现无法由自动发现目录、相对路径或本地 package 表达的必要能力时才单独设计逐字段所有权、冲突停止和事务回滚；本轮不复制用户级 settings，也不整文件覆盖项目 settings。
- Research 保持 provider-neutral 单一入口：本地资料和直接官方来源优先，已知 GitHub 事实用 `gh`，未知公开 Web 发现/批量 fetch 用 Exa，跨仓库实现证据按需升级 Octocode，可视或登录态才使用 Browser。
- 旧架构的评测观察不作为当前 promotion 证据；Research/Exa 保持 provisional，Octocode 保持 experimental，只有现行套件和可审计结果工件可以改变状态。
- agentwork 只校验当前版本的 session 契约，不为 `gv` 等旧项目增加全局兼容模式；旧 session 在实际续作且存在可验证提交时按 Git 事实重整，没有历史提交或可靠证据时忽略，不补造历史。
- `.agentwork/bootstrap-install-state.json` 是安装器跨克隆、跨机器重复同步时识别旧版受管文件的仓库级所有权账本，不作为本地缓存忽略；source 实现收敛后刷新并纳入版本控制。

### 核心定义 / 流程
- 事实源顺序：agentwork source 规范与 manifests -> 安装器生成/同步 -> 隔离安装态与运行时 smoke。
- 状态判定：工具 manifest entries 全部存在且内容一致才算已安装；全部不存在才算未安装；missing/drifted 必须清理或补齐。
- Pi 验证顺序：确定性 renderer/installer gate -> source self-host 幂等 -> 隔离 Pi RPC/TUI 发现 smoke -> fresh review；真实 runtime smoke 不替代安装事务与路径边界测试。
- Pi 迁移顺序：安装最小 runtime -> clone 项目 -> bootstrap 核心文件 -> 按项目声明 restore optional profiles -> 用户补充凭据 -> 显式 project trust -> 隔离 smoke。
- Pi 文件分类：`prompts/skills/extensions/themes` 与本地 package 源码/manifest/lockfile属于 tracked capability；外部 CLI 和下载依赖属于 declared + rebuildable；凭据、trust、browser profile 与原生 Pi session 属于 user-private。
- Pi 恢复语义：clone 直接恢复 tracked capability；doctor 只读检查 runtime 和版本；restore 只恢复声明的外部依赖，不重新复制已随仓库存在的资源，也不写用户目录或真实凭据。
- 续作顺序：验证 clean clone 恢复链 -> 独立设计并验证 Search/MCP 显式 profile -> 独立调研 Case -> 生成现行 Research 评测结果 -> 根据 gate 决定 Research/Exa 状态 -> 轮换服务端旧凭据。

## 计划摘要
> 此处只保留继续推进所需的统一执行视图；过程讨论仍由关联工件提供证据。

### 关键文件 / 边界
- session/review 当前批次：`.shared/commands/{session,review}.md`、`.shared/patterns/session-workflow.md`、session 模板/README、`.shared/scripts/{agentwork-check.py,session-review.sh}` 及 bootstrap managed block。
- Pi 当前批次：`.agentwork/bootstrap/{spec.json,render_bootstrap.py,pi/**}`、`install-bootstrap.py`、`.agentwork/tests/test_{install_bootstrap,pi_adapter}.py`、根 `.pi/prompts/**` 与平台说明/生成式入口；不接管 `.pi/` 其他内容。
- Pi 文件优先后续边界：首批只为 Browser / Research / CodeGraph 增加 `.pi/skills/**` 项目入口及对应 `tool.json` entries；暂不生成 `.pi/settings.json`、安装 package、修改用户目录或引入新的中心 profile 文件。共用 `install-tool.py` 的 hardlink-safe 与 executable source mode 修正均已通过 fresh review，并分别随 `a946ba2`、`a590257` 提交。
- Research 后续：`.agentwork/tools/research/evals/**` 及 provider readiness。
- 已提交 bootstrap 基线：`install-bootstrap.py`、`.agentwork/bootstrap/**`、根目录 `AGENTS.md`、`.codex/config.toml` 受管块及平台入口。

### 执行批次 / 优先级
- 已完成：平台与 Research source 批次分别提交为 `152eadc`、`d4995af`。
- 已完成：Codex 执行子代理 bootstrap 已提交为 `d6387db`。
- 已完成：session/review 按主题归类产出、保留独立提交锚点，并将审查记录分为最近 3 次详情和更早摘要；无日期与无效日期标题均会明确失败，legacy session 不属于 agentwork 当前契约的兼容与回归范围；source receipt 以 47 项零缺失、零漂移纳入 `798dded`。
- 已完成：Pi 六个核心 prompt、`v0.84.4` 基线、source self-host、renderer canonical path 校验、首批 optional-tool surface 与平台文档已提交至 `a590257`；共用安装器的硬链接安全原子替换与 source mode 修正已先提交至 `a946ba2`。
- 下游历史证据：来源任务在 2026-08-29 将当时的六个 Pi prompt 随核心 bootstrap 同步至 `roguelike-match`，重复同步与目标 self-test 通过；该同步早于 `v0.84.4` 基线和 2026-08-31 安全修正，只作为安装路径历史证据，不代表目标已包含当前 source 工作树。
- 已完成第一批：Pi fresh review 保持核心提交边界，没有把文件优先迁移实现混入当前 Pi 核心 diff。
- 已完成第二批：文件优先契约采用自动发现目录优先、settings-last、纯文件无需 restore、外部依赖显式 restore/doctor；首批不新增中心 profile schema。
- 安全复审完成：Browser / Research / CodeGraph 的 `.pi/skills/**` entries、定向测试和 trust/RPC smoke 已完成；`install-tool.py` 的原子替换已闭环项目外硬链接风险，且 executable entry 重装会恢复 source mode。fresh review 未发现新的 Critical/Important，修正与集成已分别随 `a946ba2`、`a590257` 提交；纯文件恢复链仍为下一批，Search/MCP 继续要求独立显式 profile。
- 后续独立议题：Case 调研、Research 现行 8-case/12-case 行为评测和服务端旧凭据轮换。

### 执行策略
- `standard`：事实源先修正，再通过安装命令同步目标仓库；每轮对 manifest、引用、运行态、session 和 Git 边界分层验证。
- Pi 迁移使用 `project-local first`：可迁移能力写入仓库或项目声明，全局 runtime 仅做只读检测；涉及网络安装、任意代码 extension 或凭据时必须走显式 optional restore。

### 验证策略
- source：`agentwork-check.py self-test`、JSON/Python/TOML 解析、bootstrap 隔离安装/重装/冲突/symlink 测试、全量确定性测试和 `git diff --check`。
- Pi：验证 canonical/root 六个 prompt 精确一致，receipt 精确纳管，重复同步幂等；用隔离 `PI_CODING_AGENT_DIR`、`PI_OFFLINE=1`、禁用 tools/extensions/skills 的 RPC/TUI smoke 核对根目录 trust、命令 provenance、子目录不发现与 `/session`/`/aw-session` 分离，全程不发送模型 prompt。
- Pi 文件迁移：在临时 Git 项目和隔离用户目录中模拟 clean clone，验证 tracked 文件足以恢复 prompts/skills/extensions/package 声明；缺失 runtime 时 doctor 只报告，restore 不接触真实 `~/.pi`，重复执行幂等，项目自有 settings/resources 不被覆盖，缓存与敏感值不进入 Git。
- research：冻结公开问题和一手真值；provider 每例固定调用预算；逐事实人工复核、引用可访问性检查，并与本地/直接官方 baseline 比较调用、耗时和返回字符。
- 提交前：source 使用 working-tree review，重新确认 staged/unstaged 边界。

### 完成标准
- 本统一 session 通过 strict-flow 和 session-review，可独立说明当前目标、边界、决策、工作集、已产出批次和剩余风险。
- session review 不按固定条数截断独立提交、关键取舍、迁移前提或未闭环风险；自动检查可识别重复锚点、近期审查字段、日期倒序和历史摘要位置。
- source 平台面仅保留 Codex/Claude/OpenCode/Cursor/Pi，退役 adapter 无活动入口或生成源残留；Pi adapter 仍只包含六个薄 prompt，不隐式扩装 runtime、配置、extension、subagent 或 optional tools。
- 新项目初始化后存在已注册且配置可加载的 `luna_worker`，并保留项目已有 Codex 配置与其他 agent。
- Pi 当前批次经 fresh review 确认无 Critical/Important，`v0.84.4` RPC 发现、原子写入和路径/所有权回归证据保持有效，staged 区未改变。
- optional-tool 安装、重装和环境占位写入不跟随目标硬链接修改项目外 inode；成功写入与失败回滚均由隔离回归覆盖，修正后 fresh review 无 Critical/Important。
- Pi 文件优先迁移契约完成后，新环境除最小 runtime 与用户凭据外，不依赖预先存在的全局 Pi settings/package/extension；项目能力可由 tracked 文件和固定版本声明重建，且 restore 失败不会留下部分安装状态。
- Research 现行 8-case 内容套件和 12-case 路由套件通过各自 gate，且安装/卸载在写入失败时不会留下部分状态；provider readiness 与项目级 MCP 接入可按文档复现。

## 关联工件（可选）
- `codex://threads/019ff5cf-a688-7611-acd5-6f26d0e6b388`（来源任务：`Roguelike Agentwork 同步`；Pi 调研、基线同步、runtime/optional-tool 分析与下游同步证据）
- `.tmp/agentwork/brain/20260828-1214-pi-agent-adapter.md`
- `.tmp/agentwork/plan/20260828-1332-pi-core-workflow-adapter.md`
- `.tmp/agentwork/review/20260829-1702-pi-core-workflow-adapter.md`

## 当前批次工作集
- 范围: `.agentwork/bootstrap/**` | 主题: Pi `v0.84.4` 生成规格、六个 canonical prompt 与 renderer 安全边界
- 范围: `install-bootstrap.py`, `.agentwork/tests/test_install_bootstrap.py`, `.agentwork/tests/test_pi_adapter.py` | 主题: Pi 安装事务、原子写入、路径/所有权回归与 runtime 结构测试
- 范围: `.pi/**`, `AGENTS.md`, `.agentwork/bootstrap-install-state.json` | 主题: source self-host 生成物与受管 receipt
- 范围: `.agentwork/tools/browser/**`, `.agentwork/tools/research/**`, `.agentwork/tools/codegraph/**`, `.agentwork/tools/registry.json` | 主题: Pi 项目 Skill 薄入口、Browser 任务会话/CDP 安全默认与 CodeGraph CLI 回退边界
- 范围: `.agentwork/tests/test_tool_catalog.py`, `.agentwork/tests/test_research_routing_contract.py`, `.agentwork/tests/test_pi_optional_tools.py` | 主题: optional-tool 精确同步、settings 保留、Pi trust discovery 与 Browser wrapper 回归
- 范围: `install-tool.py`, `.agentwork/tests/test_install_tool.py` | 主题: optional-tool 硬链接安全原子替换、source mode 恢复与事务回滚
- 范围: `README.md`, `.shared/patterns/platform-adapter.md`, `.shared/project/agentwork.md` | 主题: Pi 平台边界、兼容基线与长期事实
- 范围: `.shared/session/20260807-1025-agentwork-iteration-consolidation.md` | 主题: Pi 核心 fresh review、文件优先迁移契约与首批 optional surface 执行状态

## 产出批次（提交锚点）
- 历史: `自承载、核心命令流、OpenCode/Codex 适配、Figma 与 optional tool 基础已闭环` | 提交: `8b41c9e`, `70fb671` | 范围: 核心工作流与早期平台/工具基础
- 提交: `152eadc refactor(agentwork): 收敛平台适配与迭代快照` | 范围: 退役平台、精确清理边界与本统一 session 基线 | 验证: source 回归通过，项目自定义文件和符号链接保留边界已覆盖
- 提交: `d4995af feat(research): 完善研究入口与可选 provider 工具链` | 范围: Research/Exa/Octocode、optional tool 安装事务、确定性测试与 session 收敛 | 验证: 安装事务与现行评测契约通过确定性测试，provider promotion gate 仍保持未完成
- 提交: `d6387db feat(bootstrap): 初始化 Codex 执行子代理` | 范围: `.agentwork/bootstrap/{spec.json,render_bootstrap.py,codex}/`、`.codex/{agents/luna-worker.toml,config.toml}`、本 session | 验证: bootstrap 隔离场景、全量测试、核心 self-test、配置解析与 source 原地刷新通过
- 提交: `798dded feat(session): 完善审查信息保真` | 范围: session/review 策略、模板、检查器、取证脚本与 source receipt | 验证: checker self-test 覆盖无日期/无效日期负例，74 项 source unittest、脚本语法、差异检查与 source 自刷新通过；receipt 47 项零缺失、零漂移，legacy session 已排除在当前契约兼容与回归范围之外
- 提交: `a946ba2 fix(tools): 强化可选工具原子写入边界` | 范围: `install-tool.py`, `.agentwork/tests/test_install_tool.py` | 验证: 同目录临时文件加 `os.replace` 覆盖普通 entry、`.env`、`.gitignore` 和文件回滚；有效 `mode_source` 优先恢复 tool source / snapshot 权限，无 source 时保留环境文件权限；真实 Browser `0755 -> 0644 -> reinstall -> 0755`、3 项定向测试、105 项全量 `.agentwork` unittest、workflow self-test、Python/Shell/JSON、source self-host 和 `git diff --check` 通过，fresh review 未发现新的 Critical/Important
- 提交: `a590257 feat(pi): 接入核心工作流与可选工具入口` | 范围: Pi bootstrap 与六个核心 prompts、Browser / Research / CodeGraph optional-tool surfaces、对应安装与适配测试、source self-host 生成物、README 与平台文档 | 验证: 102 项 `.agentwork` unittest、workflow self-test、Python 编译、Shell/JSON、`git diff --check`、source self-host 与根仓库 optional-tool 同步通过；Pi `0.84.4` 隔离 RPC 仅在 `--approve` 下发现三个测试 Skill，`--no-approve` 不加载，source 根目录精确发现六个核心 prompt 与已安装的 Research/CodeGraph；真实 `agent-browser 0.34.0` 动态 skill 读取通过；安装器安全问题已由前置提交 `a946ba2` 闭环
- 提交: `-` | 范围: `.shared/session/20260807-1025-agentwork-iteration-consolidation.md` | 验证: 回填 Pi 集成与安装器安全修正的真实提交锚点，并同步后续 clean-clone、Search/MCP、Case、Research gate 与凭据轮换顺序

## 风险 / 阻塞
- research provider 旧凭据曾进入 Git 历史；tracked 配置已清理，但只有服务端轮换才能使旧值失效。
- Research/Exa 仍为 provisional；现行 8-case/12-case 套件及真实 provider smoke 尚未执行，结构测试不能替代 promotion gate。
- Pi 只在 `v0.84.4` 做过真实命令发现 smoke；未来版本升级必须重新核对保留命令、prompt/trust/RPC 契约，不能把当前 tag 自动外推为长期兼容范围。
- Pi 项目 prompt 从启动 cwd 发现：从子目录启动可能加载根 `AGENTS.md` 却缺少六个项目命令；project trust 与 `--approve` 不是 sandbox，当前高风险确认仍主要是文本契约。
- 首批 Browser / Research / CodeGraph Pi Skill 已闭环；外部 CLI、凭据、索引与 MCP 仍不是 Skill 文件本身可恢复的状态。Browser 需要目标环境单独安装 `agent-browser >= 0.26.0` 并显式选择任务 session；CodeGraph 需要单独安装 CLI 和按项目初始化索引。Figma、Exa 等 MCP 路径在 transport 明确前仍不应宣称 Pi 支持。
- `.pi/settings.json` 是普通 JSON 且可能已由项目维护；首批文件迁移明确不纳管它。若未来确有必要，必须另行设计逐字段所有权、冲突停止和可回滚合并，不能整文件覆盖或把用户全局 settings 当模板复制。
- Pi 项目 package 在获得 trust 后可联网安装并执行 extension 代码；“声明可迁移”不等于“安全自动执行”，版本固定、源码审查、显式 restore 和隔离验证仍是必要 gate。
- 外部 CLI、系统权限和平台相关动态库无法仅靠仓库文件移植；doctor 必须把它们列为明确前置条件，不能用下载缓存或绝对路径伪装成可移植能力。
- Pi 原生 session、tree/fork/compaction 不等于 agentwork 跨平台状态；Case 尚无已确认契约，当前不得自动转换 JSONL、自动双写或用自动 compaction 修改仓库 session。
- `roguelike-match` 的 2026-08-29 同步早于当前 `v0.84.4`/安全修正；当前 source 已提交至 `a590257`，若交付到 `roguelike-match`，仍需另行同步并验证目标项目。
- optional-tool 安装器的硬链接安全写入、source mode 恢复与普通异常/`Ctrl-C` 回滚已通过 fresh review；进程被强制终止、系统掉电或底层文件系统故障依然需要通过重复命令恢复 manifest 完整状态。
- 自动检查只能校验锚点重复、记录顺序和最低信息字段，不能替代 review 对关键决策、迁移前提和风险是否仍有语义价值的判断。

## 审查记录
### 2026-09-03 13:02 optional-tool 权限修正 fresh review
- 变更：对 `atomic_write_bytes` 的 source mode 优先修正及当前 Pi 核心 / optional-tool 未提交批次执行 fresh 双层审查；核对 tool entry、`.env`、`.gitignore` 与 snapshot rollback 四类调用，确认修正恢复原 file copy 权限语义，同时保留环境文件现有 mode 与硬链接安全原子替换。本轮只收敛 session，没有修改实现、staged 区或提交。
- 验证：真实 Browser 隔离重装从 source `0755` 安装、目标漂移为 `0644` 后恢复为 `0755` 且可执行；3 项权限/硬链接定向测试和全量 105 项 `.agentwork` unittest 通过。workflow self-test、Python compileall、Browser wrapper `bash -n`、相关 JSON、source self-host、`git diff --check` 与 Pi `0.84.4` 版本核对通过；session-review 确认 34 个工作区改动均由当前工作集覆盖。
- 风险/待办：未发现新的 Critical/Important，2026-09-02 18:34 的 executable mode Important 已闭环，当前 Pi optional-tool 安全提交门槛关闭。完整 clean-clone 恢复链、Search/MCP 显式 profile、Case 和 Research provider gate 仍属于后续批次；当前分支 `main...origin/main`，staged 区为空，全部 Pi 改动仍未提交。

### 2026-09-02 18:34 optional-tool 原子替换 fresh review
- 变更：对 optional-tool 原子替换修正及当前 Pi 核心 / optional-tool 未提交批次执行 fresh 双层审查；确认单文件 entry、`.env`、`.gitignore` 与文件回滚不再跟随目标硬链接改写项目外 inode。本轮只更新 session，没有修改实现、staged 区或提交。
- 验证：104 项 `.agentwork` unittest、workflow self-test、`install-tool.py` 与对应测试的 Python 编译、Browser wrapper `bash -n`、全部 tool manifest JSON 和 `git diff --check` 通过。额外使用真实 Browser entry 隔离重装复现：source mode 为 `0755`，将已安装目标改为 `0644` 后再次安装返回 0，但目标仍为 `0644` 且不可执行，说明现有 104 项测试未覆盖权限恢复语义。
- 风险/待办：未发现新的 Critical，发现 1 个新的 Important：`atomic_write_bytes` 在调用方提供 `mode_source` 时仍优先保留既有目标 mode，使 executable entry 重装无法恢复 source 权限。需调整为有效 `mode_source` 优先、无 source 时才沿用目标 mode，并补重装权限回归后再次 fresh review。当前分支 `main...origin/main`，staged 区为空，所有 Pi 改动仍未提交。

### 2026-09-02 12:14 Pi optional-tool fresh review
- 变更：对 Pi 核心 bootstrap、Browser / Research / CodeGraph 项目 Skill、manifest 精确安装、Browser session/CDP 默认和平台文档执行 fresh 双层审查；本轮只收敛 session，没有修改实现、staged 区或提交。Pi 核心六个 prompt 与 optional `.pi/skills/**` 的所有权边界保持分离，Skill 相对引用和 trust discovery 与 `v0.84.4` 契约一致。
- 验证：102 项 `.agentwork` unittest、workflow self-test、Python compileall、Browser wrapper `bash -n`、全部相关 JSON、`git diff --check`、source self-host、Pi `0.84.4` 隔离 RPC、`agent-browser 0.34.0 skills get core` 与 CodeGraph CLI `1.5.0` 通过。额外隔离复现显示 `install-tool.py install browser` 在受管文件为项目外硬链接时返回 0，但外部文件首行由项目自有内容变为 tool source frontmatter，目标与外部文件仍保持同一 inode。
- 风险/待办：发现 1 个新的 Important、无新的 Critical：`install-tool.py:228` 的原位复制及 `.env` / `.gitignore` 原位写入可跟随硬链接改写项目外文件，普通事务快照不能恢复外部 inode。optional-tool 批次需先统一原子替换并补成功/回滚回归，再 fresh review；Pi 核心批次此前的独立安全结论仍有效。当前分支 `main...origin/main`，staged 区为空，所有 Pi 改动仍未提交。

### 历史审查摘要（2026-08-07 至 2026-09-02 11:50）
- 2026-09-02 11:50 Pi optional-tool 首批执行：为 Browser、Research、CodeGraph 增加 manifest 管理的 `.pi/skills/**`，保持 settings-last 且不安装 package、extension 或隐式 MCP；Pi `0.84.4` trust/RPC、精确同步、102 项 unittest 与真实 Browser/CodeGraph CLI 检查通过。随后两轮 fresh review 发现并闭环安装器硬链接外写和 executable mode 问题；clean-clone、Search/MCP、Case 与 Research provider gate 继续作为后续批次。
- 2026-09-02 10:46 Pi 核心适配：fresh review 确认 bootstrap 的硬链接外写和 renderer 路径逃逸两项历史 Important 已通过原子替换、canonical path 校验及回归闭环；97 项 unittest、核心 self-test、source self-host 与 Pi `v0.84.4` 隔离 RPC 通过，未发现新的 Critical/Important。该结论只覆盖 Pi 核心 bootstrap，不覆盖随后新增的 optional-tool 安装器路径。
- 2026-08-21 session/review 保真批次：修正无日期/无效日期审查漏检，确认 checker、取证脚本、managed block 与 receipt 边界一致；74 项 source unittest、self-test、source 重复安装和差异检查通过，结果由 `798dded` 纳入，legacy session 不作为当前契约回归样本。
- 2026-08-09 Codex/Research 批次：`luna_worker` bootstrap 的同名冲突、符号链接和受管配置合并边界通过审查并提交为 `d6387db`；Research/provider-neutral 架构、安装事务和评测契约提交为 `d4995af`，真实 provider gate 与旧凭据轮换继续保留为风险。
- 2026-08-07 平台收敛：统一有效 session，修复退役路径精确清理边界并收敛平台与 optional tool 基线，source 回归通过并提交为 `152eadc`；更早核心工作流锚点为 `8b41c9e`、`70fb671`。
