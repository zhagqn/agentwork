# Case: 20260912-2330-adapter-test-symmetry

> 创建: 2026-09-12 23:30
> 简述: 补齐五平台适配层的对称测试覆盖，并把本轮实测到的平台事实固化为可回归的断言

## 任务列表（按优先级）
- [x] 按用户最新要求移除过期 Codex 默认子代理：停止生成注册，退役已知受管配置和文件，保留用户改写内容
- [x] 补齐 Claude / Codex / OpenCode 的 wrapper 正文契约，以及 Cursor rule 与六条共享命令引用契约
- [x] 为四家钉住独立于 spec 的预期入口集合，使入口从 spec 消失时测试失败
- [x] 把 `render_bootstrap.py --check` 接入确定性测试，让生成物漂移不再依赖人工记得运行
- [x] 补齐安装态静态入口检查：入口集合、元数据、正文引用及共享目标存在性
- [x] 将 Codex 0.154.0 实际安装态及路径布局的离线发现验证接入可显式启用的正式测试
- [x] 使用 Pi 0.84.4 / 0.85.1 验证六个核心 prompt 的信任、cwd 与禁用开关行为，并接入正式回归
- [ ] 后续验证 Claude / Cursor 运行时发现；当前对这两家仍以静态安装契约为边界
- [x] 复核 Codex 0.154.0 skill 发现路径：保留 `.codex/skills`，不增加双路径副本
- [x] 完成当前迁移评估：维持 `.codex/skills`，本次不实施 `.agents/skills` 迁移；目标版本需求变化时另开迁移任务

## 已确认结论（工作快照）
### 目标
- 优先补齐 Claude、Codex、Cursor 的适配层自动化验证；OpenCode 使用频率低，仅保留基础集合、正文和安装态覆盖，不投入专项运行时调查（用户本轮确认）。
### 边界
- 2026-09-15 用户追加：完全移除默认 Codex 子代理机制，范围扩展到安装器、生成源、source 自承载入口、测试及对应文档；旧名称仅作为退役兼容标识保留。
- In Scope: `.agentwork/tests/` 下的适配层测试、`spec.json` 与 renderer 的可测契约、生成物漂移检查的接入方式。
- Out of Scope: 命令描述文本的改写、Cursor 缺 per-command 入口的补齐、高风险操作强制机制的落地。这三项属独立议题，不在本 Case 收敛。
- 描述文本已由读取链优化更新；Cursor 当前仍无 per-command 入口，通过 rule 引用六条共享命令。本 Case 检查此现有形态，不新增命令入口。
### 约束
- 当前处于测试阶段，无发布流程也无 CI；所有检查必须能在本地确定性运行，不假设远端流水线存在。
- 默认回归不依赖真实 provider 调用与计费请求；适配测试检查生成物与安装态。Codex 0.154.0 离线测试通过 AGENTWORK_CODEX_DISCOVERY=1 显式启用，未启用时明确跳过；启用后版本不匹配或缺少 runtime 会失败，不伪装通过。
- 平台运行时行为随版本漂移，断言必须写清所依据的版本基线，不把单一版本的观测外推。
### 已选方案
- 沿用 unittest 与现有 renderer 加载方式，在 `test_adapter_contracts.py` 覆盖三家 wrapper 和 Cursor rule；固定集合不从 spec 推导，避免共同缩减导致漏报。
- 正文、固定集合和静态安装态检查已完成；Codex 保留现有 `.codex/skills` 单路径，正式离线发现回归已接入，迁移评估以当前不实施结项。OpenCode 不作为前置条件。
- 平台事实类结论沉淀为"版本基线 + 断言"，参照 Pi 已有的 `compatibility_baseline` 做法。
### 关键决策 / 取舍（可选）
- 测试密度不对称的成因是维护顺序，不是刻意取舍：Pi 适配最后完成，其测试也最后编写，故最完整。既有四家不是被判定为不需要测试。
- 2026-09-15 复核：官方文档列出 `.agents/skills` 项目发现路径，并明确同名 skill 不合并。codex-cli 0.154.0 的离线 `skills/list` 实测确认，单独使用 `.codex/skills` 或 `.agents/skills` 均正常发现；两处同名时，无论内容相同或不同，均返回两条启用入口。根目录和子目录查询共 8 个场景结果一致、无解析错误。
- 当前增加双路径没有已证实收益，重复发现风险已确认，因此保留 `.codex/skills`。未来单路径迁移的收益是对齐官方公开契约，不代表提升模型能力，也没有旧路径即将失效的证据；迁移不涉及 `.codex/config.toml` 与 `.codex/agents`。
- 移植模板的形态已变：Claude wrapper 现有 frontmatter description，六条命令的描述来自 `spec.json` 的 `description` 字段而非标题兜底。任务 1 的断言应针对该新形态，并优先断言结构而非描述原文，避免与文本耦合。

## 计划摘要（可选）
### 关键文件 / 边界
- `.agentwork/tests/test_pi_adapter.py` 是断言模板来源；保留元数据、参数和共享引用覆盖，将 case 整段文本比较改为结构断言，解除描述原文耦合。
- 新增或扩展的适配测试落在 `.agentwork/tests/`，不改 `.shared/` 工作流契约。
- `spec.json` 已移除默认子代理定义；renderer 同时移除子代理生成逻辑并修正 Cursor frontmatter 顺序。安装器增加保守退役路径：旧收据优先，无收据仅接受已知文件摘要，配置移除必须保持其余 TOML 语义不变。
### 执行批次 / 优先级
- 本批完成静态契约、Codex 离线发现和 Pi 两版本离线发现检查，OpenCode 共用基础断言；Claude / Cursor 运行时验证保持未完成。
### 执行策略（可选）
- standard
### 验证策略
- Pi 使用 PATH 中的运行时，或通过 `AGENTWORK_PI_EXECUTABLE` 指定可执行路径（支持项目相对路径）。认可版本限定为已实测的 0.84.4 / 0.85.1，不自动接受其他版本。
- 本机 Pi 为 0.85.1；隔离基线安装命令：`npm install --prefix .tmp/pi-runtime-0844 --no-audit --no-fund @earendil-works/pi-coding-agent@0.84.4`。重现基线测试：`AGENTWORK_PI_EXECUTABLE=.tmp/pi-runtime-0844/node_modules/.bin/pi python3 -m unittest discover -s .agentwork/tests -p 'test_pi*.py'`。两版本均实测 14 项通过，无跳过；不降级全局 Pi，不修改平台配置或安装契约。
- Codex 离线兼容性：`AGENTWORK_CODEX_DISCOVERY=1 python3 -m unittest discover -s .agentwork/tests -p 'test_codex_discovery.py'`；仅支持 CLI 0.154.0，隔离 CODEX_HOME，无模型请求，覆盖实际安装和四种布局的根目录 / 子目录共 10 个查询。
- 最新验证：`AGENTWORK_CODEX_DISCOVERY=1 .shared/scripts/verify.sh` 最终 157 项全部通过、无跳过，Pi / Codex 均实际通过；workflow self-test 与 renderer --check 通过。本轮修复退役误删风险并调整 Octocode EOF 测试后重新全量通过。
- 也可直接运行 `.shared/scripts/verify.sh`，它串起 unittest、workflow self-test、`render_bootstrap.py --check` 与 Case strict-flow 四项（`20292c1` 新增）。
- 运行 `python3 .shared/scripts/agentwork-check.py self-test` 确认工作流契约未受影响。
- 运行 `python3 .agentwork/bootstrap/render_bootstrap.py --check` 确认生成物无漂移。
### 完成标准（可选）
- 三家 wrapper 与 Cursor rule 均有正文和独立预期集合断言；安装态静态检查与漂移检查通过。运行时发现另行验收，需按版本记录证据。

## 关联工件（可选）
- 平台适配边界与回退流程：`.shared/patterns/platform-adapter.md`
- 生成契约与 renderer：`.agentwork/bootstrap/spec.json`
- 正式 Codex 离线发现回归：`.agentwork/tests/test_codex_discovery.py`
- 正式 Pi 核心 prompt 离线发现：`.agentwork/tests/test_pi_discovery.py`；Pi 可选 skill 发现：`.agentwork/tests/test_pi_optional_tools.py`
- Codex 路径调查：`.tmp/codex-path-probe/findings.md`；可复现脚本 `.tmp/codex-path-probe/probe.py`；8 场景原始结果 `.tmp/codex-path-probe/results.json`（临时证据，关键结论已保留在本 Case）
- 官方 skill 发现契约：https://developers.openai.com/codex/skills （2026-09-15 已获取；本地快照 `.tmp/codex-skills-official.html`）

## 当前批次工作集（可选）
当前无工作集。

## 产出批次（提交锚点）
- 提交: `adb75e6` | 范围: `.agentwork/tests/`、Cursor renderer / canonical / 自承载入口 | 验证: 四平台正文与固定集合、安装态检查及 Cursor frontmatter 修复；Codex 0.154.0 实际安装与双路径发现，Pi 0.84.4 / 0.85.1 各 14 项通过。静态契约与运行时发现分开验收，Claude / Cursor 运行时仍留待办
- 提交: `3a6ed5c` | 范围: `install-bootstrap.py`、`.agentwork/bootstrap/`、`.codex/`、相关文档 | 验证: 默认子代理不再生成或注册；旧收据及无收据摘要识别、用户改写保留、TOML 语义保护和回滚有覆盖，安装器 65 项通过；自承载旧文件与注册已清除
- 提交: `4fde0d8` | 范围: `.agentwork/tests/test_octocode_mcp.py` | 验证: 子进程保持管道打开以验证不等待 EOF，消除短计时竞态；定向 4 项及最终全量 157 项全部通过、无跳过，self-test、renderer 与 diff 检查通过
- 历史: 提交前阶段曾出现 Octocode 1 秒响应超时；相关测试修正已包含在上述独立批次。Codex 路径调查的临时证据及关键结论保留在关联工件、已确认结论与风险节。

## 风险 / 阻塞
- Octocode 原测试的 1 秒响应 / 3 秒退出时序存在启动速度竞态，现改为子进程保持管道打开直到输入关闭，10 秒只作挂起保护。定向与最终全量通过；代理生产代码未变，本轮未验证远程 provider E2E。
- Codex 路径发现已在 0.154.0 离线复核；未覆盖其他 CLI 版本、桌面端、IDE 或实际模型调用选择。两条列表记录不等于执行两次，列表顺序不构成优先级保证。
- Pi 0.84.4 / 0.85.1 的核心 prompt 与可选 skill 发现均已验证；核心 prompt 使用 get_commands 检查六个名称、无重复、来源路径、描述，以及未授权 / 子目录 / 禁用时不加载。验证不调用模型，未覆盖 prompt 执行后的模型遵循效果。其他 Pi 版本不外推，Claude / Cursor 运行时仍未验证。
- 默认静态检查只能证明仓库安装契约，Codex 正式离线测试已接入但默认跳过。双路径不去重已确认且方案已排除；未来若另开单路径迁移，需处理用户自定义 skill 冲突、安装收据与旧受管入口退役，不自动覆盖或搬迁。
- 无 CI 环境，聚合检查仍需人工运行；漂移检查已接入 unittest 与 verify.sh，该接入事项已闭环。
- 兜底描述字面量原先在渲染器内出现两次，改一处漏一处会让 Pi 与其余平台对同一命令给出不同默认描述；已于 2026-09-13 合并为 `default_wrapper_description()` 单一来源，该项已闭环。
- 更正一处误诊：description 的换行校验看似在两处重复，实际不是冗余，不得删减。`validated_wrapper_specs` 只校验原始 `description` 键，而 `validated_pi_wrappers` 校验解析后的值，是唯一覆盖 `pi_description` 的检查；`test_pi_adapter.py` 的 `metadata-newline` 用例仅靠后者才成立。

## 审查记录
### 2026-09-15 23:07 +08:00
- 变更：本轮发现并修复退役误删风险：无收据时旧 agent 文件改为完整已知摘要识别；移除配置块前比较 TOML 语义，防止修改多行字符串或丢失块后追加字段。新增 3 项复现测试，并纠正“spec / 安装器未改”的过期快照。Octocode 再现 1 秒响应超时后，将 fake server 改为读取 stdin 至关闭、持续保持 stdout 打开；响应截止时间仅作为 10 秒挂起保护，保留“不等待 EOF”的实际协议断言，未改代理生产代码。
- 验证：安装器 65 项、Octocode 4 项定向通过；最终全量 157 项通过、无跳过，workflow self-test、renderer --check、本 Case strict-flow 与 diff 检查通过。保留 Codex / Pi 真实发现覆盖、受管文件退役与回滚证据，未改 staged 区。当前未发现阻塞初步引入的破坏性问题。
- 风险/待办：Claude / Cursor CLI 可用，但本轮所查 help 未提供项目入口列举接口，未执行模型请求或界面加载验证，仍留待办；不以静态检查代替运行时验收。默认子代理的自定义内容保留策略是防误删边界，不承诺强制删除用户配置。

### 2026-09-15 22:15 +08:00
- 变更：将 Codex 0.154.0 离线发现接入显式启用的正式测试，覆盖实际安装的 6 个命令及 2 个默认能力、4 种路径布局、根目录和子目录共 10 个查询；当前不迁移 skill 目录的评估结项。收紧 Cursor frontmatter 检查后暴露生成标记位于 YAML 之前的问题，已调整 renderer 并同步两份启动 rule。未变更安装器、收据或用户文件保护策略。
- 验证：Cursor 新断言在修复前确实失败；修复后含 Codex 的全量门禁 152 项通过、1 项 Pi 跳过，self-test 和 renderer 检查通过。case-review.sh 确认 7 个工作集条目覆盖全部改动，本 Case strict-flow 和 diff 检查通过。未发现阻塞初步引入的破坏性问题，结论以静态安装契约与 CLI 0.154.0 发现为边界。
- 风险/待办：Claude / Cursor 真实运行时与 Pi 核心 prompt 发现尚未验证，保持待办；不安装额外 runtime，不发送模型请求，不以静态通过宣称全平台运行时通过。

### 2026-09-15 00:00 -07:00
- 变更：复核本批 3 个工作区文件，补上 wrapper frontmatter 重复键检查，避免转字典时吞掉重复字段；纠正 Cursor 已补齐 per-command 入口的旧表述，并明确 Codex 0.154.0 为历史观测。未发现其他阻塞问题。
- 验证：本轮 11 项适配测试通过；重复 name 字段故障注入被断言拒绝。上一执行轮全量 151 项通过、1 项跳过，本轮局部修正后未重复全量。case-review.sh 确认 3 个工作集条目覆盖全部工作区改动，暂存区未修改。
- 风险/待办：静态安装契约不能证明运行时发现；离线发现与 Codex 路径兼容性继续未完成。OpenCode 维持基础覆盖。


### 历史审查摘要（2026-09-12 至 2026-09-14）
- 2026-09-14 22:10 +08:00：外部核对确认漂移测试已由 `1e6beb1` 接入（clean / missing / drift / unknown），基线抬升到 137 项，四家预期集合及 Codex 路径决策当时仍待办。工作集解析器把反引号内 hash 误作路径的问题再次复现，和下述空工作集哨兵缺口同源，尚未处理。
- 2026-09-13 14:49：59 项 staged 改动属读取链优化，本 Case 尚未执行；全量 130 项通过（跳过 1 项），self-test、renderer 与 cached diff 检查通过，未改暂存区。当时的覆盖、漂移接入和双路径缺口已由后续批次处理，其余平台运行时验证仍未闭环。
- 2026-09-13 00:55：本 Case 尚未执行，59 项改动均属读取链优化；Pi 44 条断言 / 8 个测试函数覆盖未减，全量 130 项、renderer 检查及 self-test 通过，staged 为 0。兜底描述重复随后闭环，description 校验重复的误诊已撤回（原因保留在风险节）；当时未接入漂移测试、逐字断言耦合等问题现已解决。
- 工具缺口：`agentwork-check.py:681` 判定空工作集用的是行列表的成员相等（`section_lines` 返回原始行，见 `:349`），因此空工作集哨兵句必须独占整行，句后追加说明文字会导致 `missing_workset_entries`。本次审查实际踩到两次。该要求在 `.shared/case/README.md` 与 `.shared/commands/review.md` 均未写明，宜放宽为子串匹配或补进文档。

- 2026-09-12 23:30：登记覆盖不对称（Pi 95 条名称相关断言，OpenCode / Cursor 为 0，Codex / Claude 各数条但不含 wrapper 正文）；隔离实测 Codex `.codex/skills` 下 10 个 skill 可见，`.codex/skills` 与 `.agents/skills` 均被发现，但未证明双路径去重。OpenCode debug config / debug skill 解析 6 条核心命令及 figma，并从 `.claude/skills/` 发现 anydoc、research。Claude / Cursor / Pi 当时未测运行时发现；漂移测试接入当时未完成。
