# Case: DeepSeek Harness 核心平台适配

> 创建: 2026-10-22 12:00
> 简述: 核心适配已提交至 b270bda，Desktop T5 补验与独立复核双通过；T1–T6 完成，本 Case 随 docs(case) 批次归档。
> 规格来源: .tmp/agentwork/spec/20261022-1116-dsh-core-adapter.md

## 任务列表（按优先级）

- [x] T1 补齐 dsh 平台元数据和八个薄技能源，加入生成与入口契约检查 | 覆盖: D1, D2, D3, D4, D7, D8 | 依赖: 无 | 完成: 六命令与两个默认能力均有可分发源，目标存在，格式和相对路径明确，保持共享语义与其他平台来源；生成、安装元数据不含 plan 或 review 别名 | 验证: 在已有 adapter 测试体系中验证独立固定的八入口集合、有效 frontmatter、共享目标与薄适配边界，运行对应的 unittest discovery
- [x] T2 将八个入口接入 bootstrap 的文件级安装与收据事务，补安装边界回归 | 覆盖: D4, D5, D8, D10 | 依赖: T1 | 完成: 清洁安装可用，二次安装幂等；改写文件、同名自定义内容、符号链接及同级用户文件按现有策略保留；tool 重叠在写入前失败；失败和中断恢复目标与收据，外部安装不改 source checkout | 验证: 运行 test_adapter_contracts.py、test_install_bootstrap.py 与新增 dsh 相关用例，按安装前后文件摘要验证成功、保留、失败和回滚场景
- [x] T3 补平台文档并完成 source 自承载同步，验证既有平台回归 | 覆盖: D1, D2, D4, D5, D6, D7, D8, D9, D10 | 依赖: T1, T2 | 完成: 项目根具备八个受管入口且收据正确，文档写明标准模式、原生 plan 区别和工具延后；既有平台没有语义回归，生成检查一致 | 验证: 通过 python3 install-bootstrap.py -p . 执行事务式同步，再运行完整 unittest、agentwork-check.py self-test 与 render_bootstrap.py --check；比较真实仓库 staged diff，保持暂存边界不变
- [x] T4 用固定发布包检查已安装项目的规则与技能发现，保存可复核证据 | 覆盖: D2, D3, D4, D7, D8, D9, D10 | 依赖: T3 | 完成: 在隔离临时项目中发现并加载八个已安装入口，项目根、Git 子目录、无 Git 根及 worktree 标记场景按约定解析；用户技能并存且没有 home 配置写入；明确此结果只证明加载机制 | 验证: 使用已缓存或显式项目级准备的 0.2.1-rc.2 指令加载器与 skill provider 检查真实安装结果，将版本、目录、目标与结果写入 .tmp/；此步骤不接真实模型且不加入默认测试下载依赖
- [x] T5 在官方 Desktop 标准模式完成核心流程的受控验收 | 覆盖: D2, D3, D6, D7, D8, D9, D10 | 依赖: T4 | 完成: 记录 Desktop 与内置 runtime 版本，在无私有代码的临时工作区和新会话中验证共享规则读取、brain 与 spec 落盘、显式 exec 和 audit、显式 Case 接力及 commit 确认边界；anydoc、research 可加载；未自动提交、加载旧 Case 或开启额外运行能力 | 验证: 按下述 Desktop 清单逐项记录操作、工件和 checker 结果，区分观察与模型陈述；无可用 Desktop 交互或模型通道时保留该任务未完成，不用 npx Web 结果代替
- [x] T6 完成适配审查与支持范围收敛 | 覆盖: D1, D2, D3, D4, D5, D6, D7, D8, D9, D10 | 依赖: T3, T4, T5 | 完成: 对照本 spec 与实际 diff 给出规格、质量双结论，无未解决的重要问题，文档仅声明已验证的支持范围，所有真实运行证据已脱敏 | 验证: 对本 spec 和当前工作产物执行 audit，运行 agentwork-check.py audit 的 --fail-on-major 检查；如修复影响代码或生成物，再运行受影响的既有 gate

## 已确认结论（工作快照）

### 目标

- 为 agentwork 增加可安装、可自承载、可验证的 dsh 核心适配，让官方 Desktop 的标准模式能够发现并执行现有六个阶段流程，同时获得 anydoc、research 默认能力入口。

### 边界

- In Scope：八个 dsh 技能的源与项目入口；renderer 与 bootstrap 的精确安装、收据、回滚和自承载；相关 adapter 与安装器测试；固定发布包的发现检查；Desktop 标准模式的受控任务验收；平台和使用文档。
- Out of Scope：可选工具的 dsh wrapper、MCP patch 或索引初始化；改写 `install-tool.py`；安装或注册 CLI；读取或修改用户凭据、profile、全局指令和历史对话；原生计划模式改造；PTC、SSH、第三方 TUI、自动续跑或团队编排的支持声明；真实 Git 提交、推送或调整用户暂存区。
- Case 创建轮按 `/case spec` 新建快照并原样保留 D1–D10、T1–T6；来源 spec 保持冻结。T5/T6 已由后续会话推进，创建轮的“仅新增 Case、不执行 T5/T6”只描述当时范围。
- 仅关联显式来源 spec 及本任务已产生的证据，不加载其他旧 Case。
- 提交收尾：用户在独立复核后通过 `/commit` 与“都提交”明确授权连续完成 dsh 实现和当前 Case 两笔提交；排除用户独立的 `frontend-design.md`、对应收据摘要和 `.tmp/`。Desktop 验收夹具继续保留无提交、staged 为空的事实。

### 约束

- Case 是任务状态的唯一事实源；来源 spec 冻结为决策追溯工件，后续不回写其 checkbox。保留 D1–D10 和完整 T1–T6 任务契约，当前 T1–T6 均已完成。
- 默认简体中文；临时工作区和证据统一写入 `.tmp/`。真实仓库暂存区保持用户边界，未经明确要求不 stage、commit 或 push。
- 保留 `.shared/` 工作流语义与各平台来源；anydoc 的 dsh 薄入口不改变其他平台的正文镜像，research 保持手写平台指针。
- Desktop 验收使用公开、无私有代码的临时夹具，新会话、标准模式、正常项目写权限、原生计划模式关闭；不靠修改 preset、完全访问或自动批准掩盖问题。T5 与补验会话均记录为 Standard（`workspace-write + ask`）；权限值来自所存运行时上下文，preset 名称和计划模式来自执行方记录，没有独立 GUI 导出，不能仅凭权限值证明所选 preset。
- 已有 Desktop 与内置 runtime 的版本记录为 `0.2.1-rc.2`，与机制基线一致；该版本已随 T5 补验使用。Case 的创建或加载不继承历史执行授权；后续执行仍须当前明确意图。

### 已选方案

- D1 保留 `.shared/commands/*`、`.shared/skills/*` 及共享工件作为工作流语义事实源，dsh 作为新增平台适配；不重写共享流程，不开发新的 Agent loop、bundle、preset 或 UI 面板。来源：已采纳的薄适配方案与现有平台分层约束。
- D2 核心安装精确提供 `.dsh/skills/{brain,spec,exec,audit,case,commit,anydoc,research}/SKILL.md` 八个入口；不新增 agentwork 的 plan、review 或 session 别名，不将其他平台入口迁到 `.agents/skills`。来源：本轮八入口范围与用户对 spec 命名的明确纠正。
- D3 dsh 入口包含有效的 name、description 元数据与最小平台指引，完整读取对应共享定义；必须说明技能资源目录与项目根的区别，用户原始参数交给共享流程解释，不依赖 `$ARGUMENTS` 或其他平台的文件展开语法。来源：已验证的发现格式、相对路径和 slash 调用机制。
- D4 八个入口纳入 bootstrap 的 canonical 源、分发计划与 source repo 自承载；沿用现有 wrappers 元数据、默认能力分发方式和所有权模型，不手工长期维护未受管的根目录副本。来源：已采纳的 renderer、安装器与收据接入范围。
- D5 安装保持现有预检、哈希收据、幂等、回滚与冲突处理：用户改写文件、同名自定义入口和符号链接按现行规则保留并报告；tool 收据认领重叠或受管块损坏仍在首个目标写入前拒绝。只认领八个具体入口，不接管整个 `.dsh/`，不清理未知同级文件。来源：现有 bootstrap 兼容红线。
- D6 本轮使用标准模式作为运行验收基线，保持 dsh 原生计划模式关闭，以免其禁止写文件的指引阻止 brain、spec 工件落盘；不改原生 `/plan`、权限预设或用户配置，也不自动启用 goal、loop、schedule 或 subagent。来源：已确认的首次使用和验收顺序。
- D7 保留共享工作流的实际意图与权限边界：spec 不是执行授权，旧 Case 只在显式引用时加载，exec 保持当前批次，commit 仅响应真实的明确提交意图且遵守现有范围确认；不把 slash token、已加载 skill、原生计划批准或 UI 变更快照当成额外许可。来源：现有共享契约与已识别的 dsh 运行差异。
- D8 核心 bootstrap 只分发规则入口；本轮不安装 dsh、Node、Python、MCP server 或其他工具运行时，不修改用户 home、模型、凭据、日志上传开关、Desktop profile 或全局配置。CodeGraph、Browser、Figma 等可选接线留到后续。来源：已确认的核心优先、工具按需顺序与项目安装边界。
- D9 验证分为仓库确定性回归、固定发布包机制检查、官方 Desktop 实际任务验收三层；分别记录结果，不以静态文件存在或 Web 首页可访问宣称完整工作流兼容。真实 provider 与 Desktop 检查保持显式人工兼容调查，不进入默认回归 gate。来源：研究证据范围与仓库现有验证约定。
- D10 更新平台说明、bootstrap 说明、自承载基线和项目稳定事实；标明 dsh 研究版本及 Desktop 的实际验收状态。现有 Codex、Claude、OpenCode、Cursor、Pi 的入口与行为保持兼容，平台入口继续由各自源维护。来源：新增平台的正式分发与文档要求。

### 关键决策 / 取舍（可选）

- 核心静态适配、固定发布包加载与 Desktop `0.2.1-rc.2` 标准模式 T5 已完成：同夹具第二会话显式加载 Case，真实提交请求获得范围确认后被真实取消，staged 未变、无提交。
- dsh 机制基线是 `@deepseek-ai/dsh@0.2.1-rc.2`，tag `dsh-v0.2.1-rc.2`，commit `687f282e8625c6b8d11ff58211a90524be2e4317`。
- 既有版本取证记录指向本机 Desktop 的 Info.plist、app.asar 和 runtime.json，版本为 `0.2.1-rc.2`；本轮复审核对保存的证据，未重读用户 profile 或历史会话。版本一致不构成长期支持证明，升级后须重验。
- T4 的无 Git 正向检查使用探测专用文件系统边界隔离父 source 仓库 `.git`，内部读取委托发布包 LocalFileSystem；标准 LocalFileSystem 的 cwd 不构成沙箱。直接 host 探测会找到父仓库入口；无 Git 隔离视图中的子目录会回退为自身，发现零技能。
- T4 的 worktree 场景只验证构造的 `.git` 文件标记，未验证真实 Git worktree 注册、切换、快照或 Desktop 工作区选择。AGENTS 中的共享路径不会自动展开；T5 补验已附实际 read 返回、行数与节标题，仍属模型记录，复核时以证据文件为准。

### 核心定义 / 流程（可选）

- 八入口：`.dsh/skills/{brain,spec,exec,audit,case,commit,anydoc,research}/SKILL.md`。前六个指向 `.shared/commands/` 同名文件，后两个指向 `.shared/skills/` 同名 `SKILL.md`。
- dsh 入口按加载器提供的技能资源目录向上三级定位项目根，再读取根规则、启动必读和共享定义；保留原始子命令、引号和带空格路径。无 Git 且祖先无标记时，以选定项目根作为 Session cwd。
- agentwork 使用 `/spec`，没有 `/plan`、`/review`、`/session` 别名。dsh 原生计划模式与 agentwork 规格工件不同；加载 skill 或引用 slash token 都不构成额外执行或提交许可。

## 计划摘要（可选）

### 关键文件 / 边界

- `.agentwork/bootstrap/spec.json`、`render_bootstrap.py`、`dsh/skills/`：dsh 元数据、生成式入口与 research 手写薄指针。
- `install-bootstrap.py`：八文件精确分发，复用预检、收据、保留与回滚；不改 `install-tool.py`。
- `.dsh/skills/`、`.agentwork/bootstrap-install-state.json`、`AGENTS.md`：已通过事务完成的 source 自承载基线，不手工长期维护根副本。
- `.agentwork/tests/`：入口契约、真实安装、用户内容与符号链接保留、tool 重叠及失败/中断恢复回归。
- `README.md`、`.agentwork/bootstrap/README.md`、`.shared/patterns/platform-adapter.md`、`.shared/project/agentwork.md`：使用方式、已验证范围与 Desktop 未覆盖边界。
- T5 使用 `.tmp/agentwork/t5-fixture-20261022/` 公开夹具与独立证据；未把真实 source 工作树作为模型副作用对象。

### 执行批次 / 优先级

- T1/T2 已完成：八个可分发薄入口、精确安装、收据与安装边界回归。
- T3/T4 已完成：文档和 source 自承载、完整仓库检查、固定发布包机制验证。
- T5 已完成：夹具会话提供八入口、根规则、brain/spec/exec/audit 证据；补验会话 `session-5e265bca` 在同一夹具工作区显式加载 Case，并完成真实提交请求 → 范围确认 → 取消，staged 未变、无提交。
- T6 复审及 13:58 独立复核已完成：四份文档限定已验证范围，自承载收据与当前文件一致；补验证据、实际 diff 和新鲜回归支持规格与质量双通过，未解决 Critical/Important 为零。
- 提交收尾：dsh 实现与正式文档已落入 `b270bda`；当前 Case 回填真实锚点后随本笔归档。用户独立的 `frontend-design.md` 及对应收据摘要留在工作区；Desktop 或内置 runtime 升级后重跑 T5。

### 验证策略

- Case 同步后运行 `python3 .shared/scripts/agentwork-check.py case .shared/case/20261022-1200-dsh-core-adapter.md --strict-flow`；该检查只验证工件形态，不替代业务回归或正式 audit。
- 实现变化后重跑受影响测试；需要完整 gate 时使用 `python3 -m unittest discover -s .agentwork/tests -p 'test_*.py'`、`python3 .shared/scripts/agentwork-check.py self-test`、`python3 .agentwork/bootstrap/render_bootstrap.py --check`。不自动选择旧 Case 或本机最新 spec。
- T4 复现入口为 `node .tmp/agentwork/dsh-core-validation/probe.mjs`，只使用已缓存或项目级准备的同版本包，不进入默认 gate，不连接真实模型。
- Desktop 按以下清单记录可观察读取、输出工件、checker 结果和取消的提交确认，区分直接观察与模型自述；失败时回退共享定义，不放宽权限或更改用户配置。

#### Desktop 受控验收清单

| 检查 | 操作与可观察结果 |
| --- | --- |
| 版本与工作区 | 记录应用版本、可获得的内置 dsh 版本和所选临时项目根；与 0.2.1-rc.2 不一致时单独记录，重新检查差异后再声明该版本受支持 |
| 技能入口 | 新建标准模式会话，确认八个 agentwork 入口可发现和加载，项目内其他技能可继续存在 |
| 根规则 | 从实际读取记录确认 AGENTS.md 及其启动必读被读取；使用临时项目公开夹具，不发送本仓库私有材料 |
| brain 与 spec | 以小型公开文本任务运行 brain，确认设计后运行 spec；工件分别写入约定目录，并通过对应 checker |
| exec 与 audit | 显式进入 exec，仅修改临时夹具中的约定文件；运行局部验证，再显式 audit，检查双结论与验证事实 |
| Case 接力 | 只在该临时项目中显式创建并加载测试 Case，换新会话后恢复同一工件，不扫描或加载真实仓库旧 Case |
| commit 边界 | 验证讨论或引用命令不造成提交；真正的提交请求先出现共享定义要求的范围确认，随后取消，不执行真实提交或 push |
| 默认能力 | 显式加载 anydoc、research，核对共享定义、输出位置、依赖延迟安装与远程数据规则；不调用额外 provider |
| 暂存区 | 记录受控任务前后真实 Git index 与 staged diff；dsh 的私有快照不应改变用户的 index |

- Desktop 实测不得自动提交或推送，不启用 goal、loop、schedule、subagent 或可选工具接线；anydoc/research 仅核对规则，不为演示下载工具、启用 hosted OCR 或调用远程 provider。
- T6 执行任务行约定的 audit 和 `agentwork-check.py audit --fail-on-major` 验证；Case 本体继续使用 `case --strict-flow`，不能用同步检查代替审查通过。

### 完成标准（可选）

- T1–T6 均已完成；T5 的补验证据与 T6 的双结论以最近审查记录为准。
- 同夹具新会话恢复、真实提交请求/取消已补齐；T6 复审及独立复核通过，未解决 Critical/Important 为零。受控验收不等于对每次模型执行、preset UI 或工具审批的机械保证。
- dsh 实现已提交至 `b270bda`，当前 Case 随本笔归档；用户独立的前端规范和对应收据摘要留在工作区。恢复时重新读取 git status/diff 和相关文件，不能把本快照或旧测试结果当作最新仓库事实。

## 关联工件（可选）

- `.tmp/agentwork/spec/20261022-1116-dsh-core-adapter.md`：已冻结的规格来源；完整决策和任务已在本 Case 保留，跨 checkout 缺失来源文件不妨碍恢复。
- `.tmp/research/dsh-20261022/report.md`、`probe-results.json`、`runtime-smoke-results.json`：实施前研究，不能替代本轮正式适配验收。
- `.tmp/agentwork/dsh-core-install-tests.log`：T2 安装器最终回归日志。
- `.tmp/agentwork/dsh-core-self-host.log`：T3 自承载事务记录。
- `.tmp/agentwork/dsh-core-full-tests.log`、`dsh-core-checker-self-test.log`：T3 完整回归与 workflow 自检记录。
- `.tmp/agentwork/dsh-core-validation/report.md`、`results.json`、`probe.mjs`、`probe.log`：T4 结论、版本/目录/摘要、复现脚本与最终原始输出。
- `.tmp/agentwork/dsh-staged-before.patch`：T3/T4 暂存区对比基线，当时为空。
- `.tmp/agentwork/t5-fixture-20261022/`、`.tmp/agentwork/dsh-core-t5-fixture-install.log`：T5 公开夹具与安装记录（73/73 收据）；夹具内 `.tmp/t5-evidence/` 含九项观察、brain/spec/audit 工件、Case 与 git 前后证据。
- `.tmp/agentwork/dsh-t5-cross-session-load.md`：T5 Case 跨会话加载记录（夹具会话 → 当前会话）。
- `.tmp/agentwork/audit/20261022-1255-dsh-core-adapter-final.md`：12:55 历史初审及当时的 Minor 处置；其完成结论已被本 Case 的 13:09 复核替代，保留原文供追溯。
- `.tmp/agentwork/dsh-core-t6-gates.log`：文档更新后的全量 unittest、self-test 与 render 检查。
- `.tmp/agentwork/t5-fixture-20261022/.tmp/t5-evidence/relay/`：T5 补验 A/B 证据（会话状态、Case 加载原始返回、提交请求/范围确认/取消时间线与 git 前后状态）。
- `.tmp/agentwork/audit/20261022-1350-dsh-core-adapter-reaudit.md`：T6 复审双结论、Minor 处置与验证事实。
- `.tmp/agentwork/dsh-core-t6-final-gates.log`、`.tmp/agentwork/dsh-core-t6-selfhost.log`：最终 gate 与自承载收据同步记录。
- `.tmp/agentwork/dsh-t5-handoff.md`：标准模式步骤、逐项提示词与证据模板。
- `.tmp/agentwork/dsh-core-validation-rerun/`、`.tmp/agentwork/dsh-core-t5-unittest.log`、`dsh-core-t5-full-tests.log`：本轮复跑证据。
- `.tmp/agentwork/dsh-src/`：从 app.asar 提取的 dsh 快照源码摘录，用于核对 index 行为。
- `.tmp/agentwork/dsh-audit-20261022/`：13:09 独立复核的完整回归、workflow 自检、夹具 checker、收据差异和 staged 对比证据。
- `.tmp/agentwork/dsh-audit-20261022-135529/`：13:58 独立复核的新鲜回归、夹具 checker、source/夹具收据、读取返回比对、审查前后 Case 取证与 staged/worktree 边界记录；当前结论以最近审查记录为准。
- `.tmp/agentwork/commit-dsh-20261022-141618/`：用户确认的两笔提交范围、收据局部补丁、提交日志与提交前后边界核对；默认不纳入 Git。

## 当前批次工作集（可选）

当前无工作集。dsh 实现已提交，当前 Case 随本笔归档；用户独立的前端规范及其收据摘要不归本任务，验证证据见关联工件。

## 产出批次（提交锚点）

- 提交: `b270bda7205fc738a6c0d4686e86c8346d55b5a9 feat(dsh): 增加核心工作流适配与 Desktop 验收支持` | 范围: `.agentwork/bootstrap/`, `install-bootstrap.py`, `.agentwork/tests/`, `.dsh/skills/`, `.agentwork/bootstrap-install-state.json`, `AGENTS.md`, `README.md`, `.shared/patterns/platform-adapter.md`, `.shared/project/agentwork.md` | 验证: T1–T3/T6 实现、测试和限定支持文档共 30 文件；八入口源/根副本/收据一致，文件级幂等、用户内容/符号链接保留、tool 重叠及失败/中断/收据回滚均有回归；T2 安装器 78 项、dsh 2 项、既有入口 3 项和 Pi 8 项专项通过；最终全量 193 项（190 通过、3 条件跳过）、self-test、生成与 diff 检查通过。提交包含 platform-adapter 收据更新，排除 frontend-design 的摘要变更。
- 历史: `T4 本地机制验证（证据未纳入 Git）` | 范围: `.tmp/agentwork/dsh-core-validation/` | 验证: 官方 0.2.1-rc.2 对三个真实安装目标的 7 个正向场景均加载八技能、2 个反向检查符合预期；用户技能并存，项目与隔离 home 摘要未变。复现入口及无 Git/构造 worktree 标记限制见关联工件与关键取舍，不以此替代 Desktop 验收。
- 历史: `T5 准备与补验（证据未纳入 Git）` | 范围: `.tmp/agentwork/t5-fixture-20261022/`, `.tmp/agentwork/dsh-core-validation-rerun/`, `.tmp/agentwork/dsh-t5-handoff.md` | 验证: 公开夹具八入口、两个用户技能样本及 73/73 收据就绪；初始 3 项测试通过，功能落地后 6 项通过。新会话 `session-5e265bca` 在同夹具显式加载 Case，真实请求 → 范围确认 → 真实取消，三次 Git 状态一致、staged 为空、无提交；原始 read 返回、消息及 checker 见 relay 证据。准备轮固定包复跑 7 正向/2 反向、隔离 home 未变；当时尚未运行 Desktop。
- 历史: `13:58 独立复核（证据未纳入 Git）` | 范围: `.tmp/agentwork/dsh-audit-20261022-135529/`, `.tmp/agentwork/audit/20261022-1350-dsh-core-adapter-reaudit.md` | 验证: Case 返回与当前文件一致，source/夹具收据各 73/73，八入口匹配 canonical 源；新鲜 193 项回归、workflow 自检、生成检查、夹具 6 项与全部 checker、13:50 audit gate 均通过；冻结 spec 与当时 staged 基线未变。12:55 初审被 13:09 复核否决，13:50 补验复审和 13:58 独立复核双通过；原始记录与历史审查均保留，本轮未重跑 Desktop 或读取 profile/历史会话。
- 提交: `-` | 范围: `.shared/case/20261022-1200-dsh-core-adapter.md` | 验证: 当前 docs(case) 批次仅归档本 Case；保留 D1–D10、完整 T1–T6、有效证据与最近三次审查，回填实际实现锚点并清理已提交工作集；自身 hash 由 Git 历史追溯，不为回填自身再追加提交。

## 风险 / 阻塞

- T5/T6 已完成，当前没有未解决的 Critical/Important；权限提示未被触发，可选工具/MCP/PTC/SSH/第三方 TUI 与自动续跑均不在已验证范围。
- dsh 为预览版；机制验证只覆盖 0.2.1-rc.2，不自动外推新版本。用户自定义同名技能可能被安装器保留，实际来源必须核对。
- 技能资源目录、Session cwd 和 shell cwd 不同；T4 无 Git 检查有探测专用文件系统边界，worktree 只用构造的文件标记。T5 夹具自带独立空 `.git` 阻断祖先发现；未在 Desktop 真实交互中复验无 Git 回退或真实 Git worktree 操作。
- 13:58 独立复核以用户已完成 Desktop 补验的说明、所存会话/消息/工具返回及实际文件核对受控流程，没有读取私有会话历史。Case 返回可逐行匹配，根规则读取仍主要是执行方保存的路径/行数记录；没有完整原始工具会话导出，不把这些记录表述成独立捕获的运行时轨迹，也不外推所有后续会话的遵从性。
- Standard preset 名称与计划模式未独立取自 UI；补验未重读内嵌 dsh 版本，沿用首次应用包证据。`workspace-write + ask` 不能单独证明所选 preset；升级或扩大支持范围时重新采集版本、模式与原始工具记录。
- `.tmp/` 证据和冻结 spec 默认不随 Git 迁移；跨 checkout 应显式保留需要的证据或重新运行验证。本 Case 已内嵌决策、任务、清单和结论，但历史验证不能冒充恢复后的新鲜证据。
- 早期 T5 为核对 preset 读取过 `~/.dsh/profiles/desktop/package.json`（仅 bundles），属于已披露的范围偏差；补验与本轮未重复，后续不用 profile 或历史会话取证。anydoc description 与 `spec.json` 仍重复维护，当前一致。
- 四份文档已限定受控核心范围，八入口源/根副本/收据一致，`platform-adapter` 收据漂移已关闭。用户独立的 `frontend-design.md` 未暂存修改及其随自承载更新的摘要按本次确认范围排除，保留工作区内容；已提交收据保留该规范原摘要，工作区收据仍匹配用户修改后的文件。
- 用户 12:22 建立的 31 文件 staged 基线在只读审查与提交规划期间保持不动，摘要为 `674ee82351ffd1eb387935566ed03eb57071c5721bf8e73cb80bfd9965817a1c`；用户随后明确授权两笔连续提交，第一笔精确提交 30 个实现文件，本 Case 随第二笔归档。不推送，不纳入前端规范及对应摘要；旧 dsh 私有 index 源码观察不替代实际 Git 边界核对。

## 审查记录

### 2026-10-22 13:58
- 变更：独立复核 Desktop 完成后的当前 Case、真实 diff、T5 首次与补验证据及四份支持文档；T5/T6 保持完成，收敛快照、计划、工作集、产出与风险。本轮仅修改 Case 与 ignored 取证文件。
- 验证：本轮完整 unittest 193 项，190 通过、3 项可选检查按条件跳过；workflow self-test、render `--check`、diff 检查通过。夹具 6 项测试与 brain/spec/exec/audit/case checker 全部通过，原始 Case 读取返回逐行匹配；source 和夹具收据各 73/73 一致，八个 dsh 入口与 canonical 源匹配；13:50 audit 工件 `--fail-on-major` 通过。D1–D10、T1–T6 契约与冻结 spec 一致，spec 摘要未变；用户 staged 摘要保持原样，夹具 staged 为空且仍无 HEAD。本轮未重跑 Desktop、未读取 profile 或历史会话。
- 结论：规格符合 通过；质量规范 通过。限定为已记录的 0.2.1-rc.2 公开夹具核心流程受控验收，不宣称权限提示或范围外运行能力已验证。
- Findings：无未解决 Critical / Important。
- 问题：[规格] Minor M1：preset/计划模式及根规则读取缺少独立 UI 或完整工具会话导出，补验内嵌 dsh 版本沿用首次证据；所存记录与当前文件一致，但不能表述为独立捕获的全量轨迹 | 处置: 转后续（升级或扩大支持范围时补留模式/版本元数据和原始工具导出；本 Case 已明确证据层级，本轮不重复 Desktop 验收）。
- 问题：[规格] Minor M2：早期 profile 元数据只读超出任务边界，读取事实无法事后撤销；补验与本轮均未重复 | 处置: 转后续（保留历史偏差，后续限公开应用元数据、当前会话和界面取证）。
- 问题：[质量] Minor M3：anydoc description 在共享 frontmatter 与 `spec.json` 重复维护，当前一致 | 处置: 转后续（后续修改描述时同步两处，避免增加本轮无关实现）。
- 外部结论处置：采纳 13:50 复审的双通过及 Minor 处置；13:09 的 A1 已由同夹具新会话和真实请求/确认/取消补齐，A2 已由四份文档明确验收范围关闭，M2 收据漂移已修复。依据为补验消息原文、Case 返回、Git 证据、实际文件及本轮新鲜检查，不以 checkbox 或结构 gate 代替实质审查。
- 风险/待办：无需为本轮再跑 Desktop；版本或声明范围变化后重验。权限提示、可选工具/MCP/PTC/SSH 等仍未覆盖；frontend-design 及其收据摘要属于用户独立改动，提交需显式请求并尊重现有 staged 边界。

### 2026-10-22 13:50
- 变更：T5 补验 A/B 完成（同夹具第二会话显式加载 Case；真实提交请求 → 范围确认 → 真实取消）；四份文档收敛为最终范围；自承载收据同步 platform-adapter 摘要；Case 收敛。
- 验证：全量 193 项（190 通过、3 项按条件跳过）、self-test PASS、render `--check` 退出码 0；夹具 6 项测试与 checker、73/73 收据；取消前后 staged 为空、无 commit；`agentwork-check.py audit ... --fail-on-major` PASS。
- 结论：规格符合 通过；质量规范 通过。
- 问题：无 Critical / Important；Minor 3 条（补验未重读内嵌 dsh 版本、早期 profile 只读、anydoc 描述重复维护）转后续。
- 风险/待办：Desktop 或内置 runtime 升级后重跑 T5；提交需用户显式请求；frontend-design 归属待确认。

### 2026-10-22 13:09
- 变更：独立复核 dsh 接手后的 Case、staged/unstaged diff、公开夹具与已保存证据；将 T5/T6 恢复未完成，更新目标快照、计划、工作集、产出和风险；原始证据与 12:55 审查记录保留。
- 验证：本轮完整 unittest 193 项，190 通过、3 项既有可选运行时检查按条件跳过；workflow self-test、render 检查与 diff 检查通过。夹具 6 项测试、brain/spec/exec/audit/case checker、73/73 收据通过；根八技能逐字节匹配 canonical 源及收据；staged 内容保持原样。本轮没有执行 Desktop 交互，也没有重读用户 profile 或历史会话。
- 结论：规格符合 不通过；质量规范 不通过。核心实现与确定性回归保留通过结论，Desktop 完成条件及支持声明尚未闭环。
- 问题：[规格] Important A1：T5 清单要求同一公开夹具工作区中新会话恢复，以及真实提交请求后的确认与取消；`observations.md:165`、`:188` 和 `dsh-t5-cross-session-load.md:18` 明确记录冷读/source 会话加载、没有真实用户请求或取消。T5 已勾选且 T6 依赖它完成，超出了证据能够支持的范围 | 处置: 转后续（T5 补齐真实交互与可核对会话记录；本轮已纠正 checkbox，缺失验证仍未闭环）。
- 问题：[质量] Important A2：四份文档仍使用“已完成核心流程受控验收”或 accepted 的支持声明（如 `README.md:169`、`:315`、bootstrap README:49、platform-adapter:92、project/agentwork:57），未明确 T5 必验交互缺失；与原完成标准及项目诚实原则不符 | 处置: 转后续（T6 按实际覆盖范围修正文案，T5 完成前保留部分验收口径，再进行正式完成审查）。
- 问题：[规格] Minor M1：既有 T5 为核对 preset 读取了用户 profile 元数据，超出 Case 的读取边界；事实已披露，本轮未重复该操作 | 处置: 转后续（后续只核对公开夹具、应用版本元数据及当前会话/界面状态，保留历史偏差，不把只读访问当作允许读取 profile 的新规则）。
- 问题：[质量] Minor M2：platform-adapter 文案与自承载收据摘要不一致；差异见 `.tmp/agentwork/dsh-audit-20261022/receipt-mismatches.json`，另一个 frontend-design 差异属于用户独立修改，不归本任务 | 处置: 转后续（T6 文案收敛后同步受影响收据，并核对归属，不改动用户 staged 基线）。
- 外部结论处置：12:55 初审对第二夹具会话按 Minor 转后续却仍认定 T5/T6 全部完成，并给出当前可完成 gate | 处置: 拒绝（原 Case 与 runbook 要求完整清单，演练和不同工作区的加载不能豁免该完成条件；结构 gate 的 PASS 不判定证据充分性）。
- 风险/待办：未解决 Critical 为零、Important 两项；先补 T5 交互，再完成 T6 支持声明、摘要同步与复审。Case 结构通过不代表本轮审查 gate 通过；用户主动 staged 基线及无关 frontend-design 改动均保留。

### 历史审查摘要（2026-10-22 12:55）
- 2026-10-22 12:55 初审曾以 193 项回归、夹具 6 项与 checker、73/73 收据及 audit gate 通过给出双通过，却将同夹具第二会话和真实提交交互缺失按 Minor 接受；该完成结论被 13:09 独立复核否决，后经 13:50 真实补验关闭。原文见 `.tmp/agentwork/audit/20261022-1255-dsh-core-adapter-final.md`；profile 只读偏差、anydoc 描述重复维护及版本升级后重验要求保留为当前边界。
