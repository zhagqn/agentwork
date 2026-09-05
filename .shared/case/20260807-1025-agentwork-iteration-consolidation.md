# Case: 20260807-1025-agentwork-iteration-consolidation

> 创建: 2026-08-07 10:25
> 简述: 收敛 agentwork 核心工作流、平台适配、可选工具与后续迭代的当前有效工作快照

## 任务列表（按优先级）
- [x] 收敛 agentwork bootstrap、平台适配、Research 与 optional-tool 安全边界，并提交已完成批次
- [x] 完成 Pi `v0.84.4` 核心适配、项目文件优先迁移契约及 Browser / Research / CodeGraph 项目级 Skill
- [x] 完成 Case 单轨迁移收尾、源端普通旧 Session 数据分发排除、隔离回归与提交前复核
- [ ] 在隔离新环境验证 clone -> bootstrap -> optional restore -> 凭据补充 -> project trust 的完整恢复链
- [ ] 为 Research 现行 8-case 内容套件与 12-case 路由套件生成可审计结果，通过 gate 后再决定稳定性等级
- [ ] 在服务端轮换曾进入 Git 历史的 research provider 旧凭据

## 已确认结论（工作快照）
### 目标
- 以 agentwork source 为事实源，维护可跨平台同步、可审查和可恢复的核心工作流。
- 使用 Case 作为唯一仓库级任务快照，不依赖平台私有对话状态。

### 边界
- In Scope: Case 核心契约与平台适配、bootstrap 安全同步、Pi 文件优先能力、Research 评测与未闭环安全事项。
- Out of Scope: Git 历史改写、自动 stage/commit、同步真实凭据或平台私有状态、静默修改用户级运行时配置。

### 约束
- 当前支持平台为 Codex、Claude、OpenCode、Cursor、Pi；共享正文保持平台无关，各平台只保留薄封装。
- 可选工具不进入 bootstrap；安装后必须与各自 manifest 完整一致。
- Git index 是用户的提交和 review 边界；非 `/commit` 流程不改变 staged 区。
- source repo 是生成源；安装器只操作 agentwork 管理的路径，不覆盖项目自有资产。
- Pi 的全局安装状态只视为机器级运行时，项目迁移能力优先由仓库文件或可锁定声明表达。

### 已选方案
- 核心工作流使用 `/brain -> /plan -> /case plan -> /case exec -> /case review -> /commit`；不使用 Case 时仍可直接 `/brain -> /plan -> /exec -> /review`。
- Case 完全替代 agentwork Session，不保留旧别名、旧目录读取、双写或下游旧数据检测；普通旧 `.shared/session/*.md` 由内部脚本或 Agent 后续按需处理。
- Case v1 沿用既有手动任务快照结构，只切换领域命名、路径、命令与生成契约，不在本轮引入父子关系、状态机或远程存储。
- Pi 使用项目级 `/case`；Pi 原生 `/session` 仅表示 Pi 对话状态，不参与 agentwork 跨平台接力。
- bootstrap 只安装稳定核心；optional tool 继续通过 `install-tool.py` 和 manifest 显式管理。
- Pi 迁移保持 file-first / declarative / version-pinned / rebuildable / secret-free；用户凭据、trust、browser profile 与原生对话状态不进入仓库。
- Research 保持 provider-neutral；本地与官方资料优先，远程 provider 的稳定性只由现行评测 gate 决定。

### 关键决策 / 取舍（可选）
- 只退役能够确认属于 agentwork 的旧 wrapper 和受管块；“不兼容旧 Session”不等于删除项目自定义文件。
- 普通旧数据在 core 写入清单生成阶段排除，不进入冲突检查、复制或 receipt；此目录级分发边界不恢复兼容读取或迁移框架，精确退役仍沿用既有所有权规则。
- 曾由 core bootstrap receipt 管理的退役 wrapper 采用 receipt 优先：历史 receipt 存在时只删除哈希仍匹配的路径，未记录或已变化的路径持续保留；仅无历史 receipt 时用生成标记兜底。
- `.agentwork/bootstrap-install-state.json` 是受管文件所有权账本，应随 source 基线提交，不作为本地缓存忽略。

### 核心定义 / 流程（可选）
- Case 是显式保存、可由 Git 追踪的任务快照；保存目标、任务、决策、工作集、产出锚点、风险和审查记录，但不保存 Agent runtime state。
- 事实源顺序：agentwork source 规范与 manifests -> 安装器生成/同步 -> 隔离安装态与运行时 smoke。
- Pi 恢复顺序：安装最小 runtime -> clone -> bootstrap -> optional restore -> 补充凭据 -> project trust -> 隔离 smoke。

## 计划摘要（可选）
### 关键文件 / 边界
- `.shared/{commands,patterns,templates,scripts,case}/` 与占位符规范维护 Case 核心契约。
- `.agentwork/bootstrap/**`、`install-bootstrap.py`、平台生成目录与 receipt 维护生成和安全退役。
- 普通旧 Session 数据（包括 source checkout 残留）不进入 core 同步、receipt 或迁移/阻塞逻辑。

### 执行批次 / 优先级
- Case 单轨迁移实现已提交；本笔保存总体与专题 Case，后续继续 clean-clone 和 Research 独立任务。

### 执行策略（可选）
- standard

### 验证策略
- 运行 workflow self-test、Case strict-flow、bootstrap renderer/source self-host、fresh/upgrade/reinstall/rollback 测试；补充源端残留旧数据不被复制、不进入 receipt、不导致下游同名数据冲突的隔离回归。

### 完成标准（可选）
- Case 是所有活动契约中的唯一任务快照；受管旧入口安全退役，普通旧数据未被读取或改写，所有生成与安装验证通过。

## 关联工件（可选）
- Case 单轨迁移专题已转入 `.shared/case/20260905-0930-session-case-unified-migration.md`；后续该专题以独立 Case 接续，本文件保留总体迭代与历史锚点。
- `.tmp/agentwork/brain/20260904-1639-session-case-unified-migration.md`
- `.tmp/agentwork/plan/20260904-1644-session-case-unified-migration.md`
- `.tmp/agentwork/plan/20260828-1332-pi-core-workflow-adapter.md`

## 当前批次工作集（可选）
- 范围: `.shared/case/20260807-1025-agentwork-iteration-consolidation.md`, `.shared/case/20260905-0930-session-case-unified-migration.md` | 主题: 总体与专题快照保存、提交锚点回填
- 范围: `.shared/session/20260807-1025-agentwork-iteration-consolidation.md` | 主题: 旧快照迁移后的原路径删除

## 产出批次（提交锚点）
- 提交: `152eadc refactor(agentwork): 收敛平台适配与迭代快照` | 范围: 核心工作流、平台收敛与精确清理边界 | 验证: source 回归及项目自定义文件保护通过
- 提交: `d4995af feat(research): 完善研究入口与可选 provider 工具链` | 范围: Research、provider 分层与安装事务 | 验证: 确定性测试通过，真实 provider gate 保持待办
- 提交: `d6387db feat(bootstrap): 初始化 Codex 执行子代理` | 范围: Codex agent bootstrap | 验证: 隔离安装、配置解析与 source self-host 通过
- 提交: `798dded feat(session): 完善审查信息保真` | 范围: 历史任务快照审查与 checker 基线 | 验证: 74 项 source unittest、workflow self-test 和 receipt 校验通过
- 提交: `a946ba2 fix(tools): 强化可选工具原子写入边界` | 范围: optional-tool 硬链接安全与权限恢复 | 验证: 105 项 unittest、真实 Browser 重装与回滚验证通过
- 提交: `a590257 feat(pi): 接入核心工作流与可选工具入口` | 范围: Pi 核心适配和 Browser / Research / CodeGraph Skill | 验证: 102 项 unittest、Pi `v0.84.4` RPC、source self-host 与工具检查通过
- 提交: `46a5896 refactor(case): 将 Session 工作流统一为 Case` | 范围: Case 核心契约、bootstrap、平台入口、测试与公开文档 | 验证: 源端数据分发三场景回归先失败后通过，各连续安装两次稳定；09:05 执行批次的 110 项全量 unittest 与本仓库两次 self-host 通过，09:24 fresh review 的 5 项定向回归、workflow/renderer、Case/Plan 与差异检查通过，无新增阻塞问题。Pi `0.84.4` RPC 沿用此前验证；实现已提交
- 提交: `-` | 范围: 两个 Case 快照及旧快照路径迁移 | 验证: 回填真实实现锚点，保留独立后续任务；本条仅记录 Case 自身这一笔

## 风险 / 阻塞
- Research provider 旧凭据只有服务端轮换后才真正失效；Research/Exa 在现行评测完成前仍为 provisional。
- Pi 真实发现基线仅覆盖 `v0.84.4`；未来版本升级需重新核对 prompt、trust 与 RPC 契约。

## 审查记录
### 2026-09-05 09:24 Case 源端数据隔离修正 fresh review
- 变更：复核 core 写入清单、冲突检查、receipt、文件复制及精确退役调用链；普通旧任务数据在内容处理前被排除，旧入口所有权保护未改变，未发现新的阻塞问题。
- 验证：5 项定向回归覆盖源端 fresh/同名目标/self-host 连续安装、旧 receipt 升级、受管块/自定义内容与修改过的旧 wrapper 保护；workflow self-test、renderer、Case/Plan、残留、工作集和差异检查通过。09:05 的 110 项全量测试与本仓库重复同步结果仍有效，本轮未重跑全量、真实 Pi RPC 或 source self-host。
- 风险/待办：源端数据分发 P1 已闭环；当前批次可进入提交范围确认，clean-clone 完整恢复链、Research 评测和凭据轮换仍保留为独立后续任务。实现与暂存区未改动。

### 2026-09-05 08:56 Case 源端数据隔离 review
- 变更：复核 Case 契约与安装边界，确认旧 wrapper receipt 修正仍成立；新发现源端普通旧 Session 数据不再被 core 同步过滤，重新打开迁移收尾任务。
- 验证：51 项 bootstrap、8 项 Pi 测试、workflow self-test、renderer、残留和工作集检查通过；使用合成数据的隔离诊断复现 fresh install 复制并登记旧数据、目标同名旧数据触发 ownership conflict、source self-host 把旧数据记入 receipt 三种结果。本轮未重跑 109 项全量测试或 Pi 真实 RPC。
- 风险/待办：源端数据分发排除与三场景回归已于 09:05 修正，并经 09:24 fresh review 确认闭环；原始复现证据保留在关联迁移 Plan。

### 2026-09-05 00:23 Case 单轨迁移最终 fresh review
- 变更：最终复核 Case 单轨契约、平台生成物、旧入口安全退役、receipt/marker 所有权矩阵、测试与文档边界；未发现新的功能、安全或迁移问题。
- 验证：109 项全量 unittest、workflow self-test、renderer、Case strict-flow、Plan、差异格式与工作集覆盖检查通过；Session 残留仅为精确退役代码/测试、Pi 原生概念及历史事实，暂存区保持为空。
- 风险/待办：Case 单轨迁移批次已达到提交门槛；clean-clone 完整恢复链、Research 评测/凭据事项仍作为独立后续任务保留。

### 历史审查摘要（2026-08-07 至 2026-09-04 23:50）
- 平台、Research、Codex 子代理、任务快照保真和 Pi 核心适配先后通过确定性回归并形成 `152eadc`、`d4995af`、`d6387db`、`798dded`、`a590257`；2026-09-02 Pi optional-tool review 先后复现项目外硬链接 inode 改写与可执行权限恢复缺口，后续由 `a946ba2` 闭环并在 2026-09-03 fresh review 中通过真实权限恢复、105 项 unittest 与 source self-host 验证。未闭环事项保留在当前任务列表与风险中。
- 2026-09-04 22:48—23:50：在既有 108 项测试通过后另行复现旧 wrapper 的 receipt 哈希不匹配但仍含生成标记时被删除；22:55 修正证据优先级并新增连续安装保护，109 项全量回归通过。23:35 的 4 项定向回归通过，同时发现两处文档将 core receipt 规则泛化到历史签名型 tool adapter；23:50 已收窄文档并通过检查，签名型 adapter 原有边界保持不变。此所有权与文档问题已闭环，证据与批次保留在关联迁移 Plan。
