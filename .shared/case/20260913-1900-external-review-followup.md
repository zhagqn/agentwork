# Case: 20260913-1900-external-review-followup

> 创建: 2026-09-13 19:00 +08:00
> 简述: 落实外部架构审查结论，按三批收口事务退出、工件选取、所有权与平台契约

## 任务列表（按优先级）
- [x] 第一批：补 `install-tool.py` 的 SystemExit 回滚与「第二次写入后抛错」回归
- [x] 第一批：统一所有 latest 入口的选取规则，覆盖 `agentwork-check.py` 与 `case-review.sh` 两处独立 mtime 路径
- [x] 批次 1：渲染器里 anydoc 的硬编码扇出抽成数据驱动默认能力表，cursor `.mdc` 正文改单一来源
- [x] 批次 1：research 的 5 个平台源文件迁入 `.agentwork/bootstrap/`
- [x] 批次 1：`DEFAULT_SKILL_ENTRIES` 由 4 条扩到 9 条，确认 5 层嵌套子路径正确落地
- [x] 批次 1：registry 摘除 research 条目并删除 `.agentwork/tools/research/` 已迁移部分
- [x] 批次 1：evals 契约迁至 source-only 新家 `.agentwork/evals/research/`
- [x] 批次 2：重构 `test_research_routing_contract.py`，解除 registry 成员身份耦合并保留仍有效断言
- [x] 批次 2：`PI_OPTIONAL_TOOLS` 摘除 research，其 Pi 入口断言移到默认能力侧
- [x] 批次 2：`test_install_bootstrap.py` 默认 skill 断言由 4 条扩到 9 条
- [x] 批次 2：补负例确认 Exa / Octocode 未被一并提升，仍只在 registry
- [ ] 批次 3：`spec.json` 增 research 默认能力条目并重新渲染，三处适配层文案同步
- [ ] 批次 3：同步 `README.md`、`bootstrap/README.md`、`project/agentwork.md`，research 不再是 optional pack
- [ ] 批次 3：删除 anydoc 孤儿收据 `.agentwork/tool-receipts/anydoc.json`
- [ ] 批次 3：复核 `.agentwork/tool-receipts/` 空目录后两安装器行为仍正常
- [ ] 遗留（未排期）：registry `schema_version` 校验、旧 receipt 路径退役顺序、归属视图、收据 envelope 统一、`verify` 聚合入口、source repo 自身漂移门禁
- [ ] 待你确认：五平台契约矩阵是否交回兄弟 Case `20260912-2330-adapter-test-symmetry`
- [x] 交叉验证三项未复核的 Important finding（三项均已复现；其中两项的修复属第二批）

## 已确认结论（工作快照）
### 目标
- 按外部审查结论收口三类边界：默认选择与文件所有权分离、两安装器共享事务机制、自动选取工件建立发布契约。
### 边界
- In Scope: `install-bootstrap.py`、`install-tool.py`、`.agentwork/bootstrap/*`（含 `render_bootstrap.py`、`spec.json`）、`.agentwork/tools/registry.json`、`.agentwork/tools/research/*`、`.shared/scripts/*`、`.agentwork/tests/*`、以及 `.shared/commands` 与 `patterns` 的文档单源改造。
- Out of Scope: CI、发布、打包分发；高风险操作强制拦截；`.shared/` 目录结构调整；把审查包内设计模型直接替换现有安装器；把 Exa / Octocode 一并提升为默认能力（二者仍为 registry-only provider）；research 正文方法论改写；routing 评测 gate 本身的实现。
### 约束
- 审查包内 12 条 ownership、10 条 resolver、4 条 schema 测试是参考模型，不是补丁。落地需自行实现并验收，包内 README 已明确禁止直接替换。
- 五阶段核心流程不是可停用的默认工具；anydoc、research 可作为默认能力，但默认选择不等于安装运行时依赖或写入凭据。
- 命令约束按各命令特点定制，写入许可在可写流程里正向声明，不扩散禁令。
- 临时目录命名与生命周期按各域用途区分，不做统一规范。
### 已选方案
- 采用审查者的三批顺序，仅调整一处：`latest` 只落最小守卫（拒绝不符 `YYYYMMDD-HHMM-slug` 命名、遇歧义显式报错），不一次性实现完整发布协议。该守卫已在第一批落地，完整发布协议仍未做且暂不做。
- 归属拆成两个可查询维度：声明来源与本次安装所有权，提供只读 `audit-ownership` / `explain <path>` 类入口。
- 36 个未入收据文件按三类分别处置，不整体补进 bootstrap 收据。
- research 与 anydoc 统一为 bootstrap 默认能力：两者均由 bootstrap 收据认领、均不在 registry、均无 tool 收据，共用同一条分发通道与同一套所有权证据。
- 两者的**投影方式不同，不可套用同一模型**（实测）：anydoc 的 3 份平台文件与 canonical 逐字节相同（`2aecb3c655fd`），是派生物，须继续由渲染器生成；research 的 5 份是手写薄入口，共三种互不相同的变体（codex 与 claude 同为 592B `cffe16b0922c`，pi 另有 770B 且 description 写「Pi task」，cursor 为 590B），均指回 85B/6356B 的 canonical。故 research 走**静态文件**放入 BOOTSTRAP 由 `DEFAULT_SKILL_ENTRIES` 拾取，渲染器不碰。依据是 BOOTSTRAP 树已有静态文件先例：39 个文件中 6 个不在渲染列表（`README.md`、`spec.json`、`render_bootstrap.py` 属输入，`data/*.block.md`、`opencode/.gitignore` 属手写内容）。代价是这 5 份不受 `render --check` 漂移保护，与既有 `data/*.block.md` 同等待遇。
### 关键决策 / 取舍（可选）
- 「统一 catalog 会新增两安装器耦合」这一保留意见已撤回。实测 `install-bootstrap.py:305-335` 的 `collect_optional_shared_relpaths()` 本来就读 registry 与每个 `tool.json`，缺 entry 直接 SystemExit，耦合早已隐式存在，显式化成本低于原估计。
- 29 个可选工具投影虽与规范源逐字节一致，但内容相同不构成认领许可，只能在显式自举对账操作中建立收据。
- 5 个项目数据文件（三个 Case、`project/agentwork.md`、`.gitkeep`）只做分类可见，不纳入刷新所有权，否则升级会覆盖本地任务数据。
- anydoc 归属方向已反转：外部审查原写「纳入 registry 迁移为 `tool:anydoc`」，实测证明该方向会重新制造双所有权。bootstrap 收据 claim 全部 5 条 anydoc 路径且摘要全部匹配磁盘，孤儿 tool 收据 claim 同样 5 条但摘要全部过期；anydoc 不在 registry、无工具目录，`install-tool.py install/uninstall anydoc` 均报 `Unknown tool` rc=1，该收据任何代码路径都不可达。它是 `33adeab` 迁移时手写并一起提交的残留物（`git log` 显示只有这一笔历史），正确动作是删除而非复活。
- 分发通道的分流开关是 `collect_optional_shared_relpaths()`：排除集由 registry 派生，现含 `skills/research/SKILL.md` 而不含 anydoc。research 摘出 registry 后 core sweep 会自动接管 `.shared/skills/research/SKILL.md`，无需显式登记。
- evals 落点选 `.agentwork/bootstrap/research/evals/` 已排除两处风险：`render_bootstrap.py:720-728` 的 `--check` 只遍历 rendered 列表比对磁盘，不反向枚举 BOOTSTRAP 找多余文件；bootstrap 全仓仅两处 rglob 且都在 `.shared` 上，BOOTSTRAP 树一律显式路径消费，故放入其中的文件天然保持 source-only。

## 计划摘要（可选）
### 关键文件 / 边界（已闭环）
- `install-tool.py:656,661`：事务已补捕 `SystemExit`（含回滚阶段），与 `install-bootstrap.py:897,902` 对称。`fail()` 仍是 `raise SystemExit`（`:55-56`），不改语义。
- `.shared/scripts/agentwork-check.py:320-349,917-944`：latest 改为按文件名 `YYYYMMDD-HHMM` 选取并显式拒绝同戳歧义；不再有 `kind == 'case'` 的 README.md 特例（命名规则已隐含排除）。
- `.shared/scripts/case-review.sh:22-38`：删除独立 mtime 选取，改调统一 latest 入口；只捕获 stdout，stderr 透传。
### 关键文件 / 边界（仍开放）
- `install-bootstrap.py:91-96,359`：`DEFAULT_SKILL_ENTRIES` 是 `(src, dst, label)` 平铺元组、消费处硬编码 `'file'`。anydoc 4 条均单文件；research 有 6 个待装文件跨 5 个面，需新增 5 条（shared 那条由 core sweep 接管），总数 4 → 9。
- `.agentwork/bootstrap/spec.json` 的 `default_capabilities` 与 `render_bootstrap.py:432-474,486` 已闭环：扇出改数据驱动，cursor 规则正文由 `render_capability_rule()` 生成，`safe_spec_relpath()` 拒绝绝对路径与 `..` 穿越。canonical 缺失时回退首个 mirror 的自包含行为保留（外部 bootstrap checkout 与测试夹具依赖它）。
- `.agentwork/tests/test_research_routing_contract.py:17-19,50-123`：`ROUTING_CASES` 与 README 断言都从 `TOOLS_ROOT/research` 读，`STACK` 含 research 且断言其 registry 成员身份与 manifest 形态；共 23 处引用，删目录即破。
- `.agentwork/tests/test_pi_optional_tools.py:17-20`、`test_install_bootstrap.py:131-134`：前者 `PI_OPTIONAL_TOOLS` 含 research，后者显式列 4 条默认 skill。
- `.agentwork/bootstrap/spec.json` `.common.basic_items[11]`：anydoc 默认能力文案的单一来源，渲染进 `AGENTS.md`、`.claude/CLAUDE.md`、`.cursor/rules/agentwork-bootstrap.mdc`。
- `install-tool.py:571` 早于 `:582` 的 action 分支：旧 receipt 路径退役会同时阻断 install 与 uninstall（行号本轮已复核仍准确）。属遗留未排期项。
- `install-tool.py:95-137`：完全未读取或校验 `registry["schema_version"]`；全文该字段出现 0 次。属遗留未排期项。
- `.shared/scripts/agentwork-check.py`：`check_plan` 只校验形态，不判断内容是否已确认；latest 守卫只保证选中对象稳定，不保证其内容可用。
### 执行批次 / 优先级
- 已完成的第一批（事务退出、latest 选取）保持闭环。后续按「机制 → 测试 → 文档」排序：批次 1 先落分发机制，因为测试要针对它断言；批次 2 紧随对齐测试，它是后续一切的门禁；批次 3 文档最后，它描述的是完工形态。
- 遗留未排期项（schema_version 校验、旧 receipt 退役顺序、归属视图、envelope 统一、`verify` 入口、自身漂移门禁）在本次迁移完成后再排，避免为即将变动的所有权模型先堆断言。
### 执行策略（可选）
- standard
### 验证策略
- 每批后运行 `python3 -m unittest discover -s .agentwork/tests -p 'test_*.py'`，当前基线为 133 条运行、OK、1 因无 Pi 跳过（第一批新增 3 条，原基线 130）。
- 运行 `python3 .agentwork/bootstrap/render_bootstrap.py --check` 与 `python3 .shared/scripts/agentwork-check.py self-test`。
- 批次 1 须实测：core sweep 自动带上 `.shared/skills/research/SKILL.md`；bootstrap 收据 claim research 全部 6 条路径且摘要匹配；`install-tool.py list` 不再含 research；`install-tool.py install research` 报 `Unknown tool`；隔离目标项目全新 bootstrap 后 research 五面入口齐全且 5 层嵌套的 `agents/openai.yaml` 未丢失。
- 批次 3 后重跑 `install-bootstrap.py -p .` 自承载刷新，确认幂等且零漂移。
- 渲染器改动必须有产物层对照，不只看测试通过。
- 遗留项验收须覆盖真实五路径状态、用户改写、部分缺失、重复迁移、默认包增减、卸载后 bootstrap 同步、manifest 退役路径、未来 schema 拒绝、中途失败回滚，不得只证明 fresh install 成功。
### 完成标准（可选）
- 三批任务各自通过上述验收；未闭环项以显式风险留存，不以形态检查通过替代语义结论。

## 关联工件（可选）
- 外部审查报告：`.tmp/review-package/agentwork-review/agentwork-review.md`
- 审查证据与复现脚本：`.tmp/review-package/agentwork-review/`（inventory、experiments、proposed_contracts、migration_probe、mutation_probe）
- 本地 review note：`.tmp/agentwork/review/20260913-1842-review-package.md`
- 本次方向调整 plan note：`.tmp/agentwork/plan/20260914-1227-research-anydoc-default-capability.md`（本 Case 当前批次的 plan-source）
- 前一版仅处理 anydoc 归属的 plan note：`.tmp/agentwork/plan/20260914-1132-iteration-direction-adjustment.md`（已被上者取代）
- 兄弟 Case（五平台测试对称化）：`.shared/case/20260912-2330-adapter-test-symmetry.md`

## 当前批次工作集（可选）
- 范围: `.agentwork/bootstrap/spec.json` | 主题: 新增 default_capabilities 数据表，承载 canonical / mirror_to / cursor_rule
- 范围: `.agentwork/bootstrap/render_bootstrap.py` | 主题: 默认能力扇出改数据驱动，cursor 规则正文脱离字面量
- 范围: `.agentwork/bootstrap/codex/skills/research/`, `.agentwork/bootstrap/claude/skills/research/`, `.agentwork/bootstrap/pi/skills/research/` | 主题: research 三个 skill 平台入口迁入 bootstrap，作为静态文件由 DEFAULT_SKILL_ENTRIES 拾取
- 范围: `.agentwork/bootstrap/cursor/rules/research.mdc` | 主题: research 的 Cursor 规则入口迁入 bootstrap
- 范围: `.agentwork/evals/research/` | 主题: evals 契约迁出 tools 树，并承载 provisional 状态标记
- 范围: `.agentwork/tools/research/` | 主题: 目录整体移除（5 组文件已迁出，4 个残余文件已删）
- 范围: `.agentwork/tools/registry.json` | 主题: 摘除 research 条目（10 → 9 个工具）
- 范围: `install-bootstrap.py` | 主题: DEFAULT_SKILL_ENTRIES 4 → 9 条，含唯一 5 层嵌套资产
- 范围: `.agentwork/tests/test_research_routing_contract.py` | 主题: 解除 registry 成员身份耦合，用例改验通道隔离，补 provider 未被提升负例
- 范围: `.agentwork/tests/test_pi_optional_tools.py` | 主题: PI_OPTIONAL_TOOLS 摘除 research，Pi 入口断言移到默认能力侧
- 范围: `.agentwork/tests/test_install_bootstrap.py` | 主题: 默认 skill 断言 4 → 9 条
- 范围: `.shared/case/20260913-1900-external-review-followup.md` | 主题: 本 Case 快照（含 /case plan 方向调整，尚未提交）

## 产出批次（提交锚点）
- 提交: `6141a1f feat(research): 将研究能力纳入默认 bootstrap` | 范围: `.agentwork/bootstrap/{codex,claude,pi}/skills/research/`、`.agentwork/bootstrap/cursor/rules/research.mdc`、`.agentwork/evals/research/`、`.agentwork/tools/research/`（删）、`.agentwork/tools/registry.json`、`install-bootstrap.py`、`.agentwork/tests/test_{research_routing_contract,pi_optional_tools,install_bootstrap}.py` | 验证: research 迁为 bootstrap 默认能力。registry 10→9 工具，`install-tool.py list` 无 research 且 `install research` 报 `Unknown tool` rc=1；排除集 19→18，core sweep 自动接管 canonical（25→26）；`DEFAULT_SKILL_ENTRIES` 4→9。测试侧解除 registry 成员身份耦合，`STACK` 6 处清零，原「生命周期独立」用例重写为通道隔离（tool 通道拒绝 research 且不留痕迹、provider 通道不产生任何 SKILL.md 或 cursor 规则），新增 provider 未被提升负例。全量 135 运行 / OK / 1 跳过（134→135）；`render --check` rc=0；`self-test` rc=0；仓库副本内自承载刷新 `install-bootstrap.py -p .` rc=0、刷新后 `render --check` rc=0、收据 64 条含 6 条 research 且 `.agentwork/` 前缀 0 条
- 提交: `5eeb97d refactor(bootstrap): 默认能力扇出改为数据驱动` | 范围: `.agentwork/bootstrap/spec.json`、`.agentwork/bootstrap/render_bootstrap.py` | 验证: 默认能力扇出改由 `spec.json` 的 `default_capabilities` 驱动，cursor 规则正文移出渲染器字面量（`grep '默认办公文档解析能力'` 归零）。`render_bootstrap.py --check` rc=0 零漂移、渲染产物仍为 36 个且 anydoc 4 个目标不变，证明纯机制重构、产物逐字节相同；新增 `validated_default_capabilities()` 的 9 个负例（缺键 / 空表 / 非法名 / 绝对路径 / `..` 穿越 / 空 mirror / 缺 rule 字段 / 空白正文 / 多余键）全部被拒；全量回归 133 运行 / OK / 1 跳过
- 提交: `8a0fb7c fix(installer): 修复事务对 SystemExit 不回滚` | 范围: `install-tool.py`、`.agentwork/tests/test_install_tool.py` | 验证: `run_transaction` 补捕 SystemExit（含回滚阶段）；新增 `test_systemexit_after_second_write_rolls_back`，在改动前的安装器副本上复跑该用例确认失败（`"rolled back" does not match "after receipt write"`），修复后通过
- 提交: `07fbdab fix(workflow): 统一 latest 工件选取规则` | 范围: `.shared/scripts/agentwork-check.py`、`.shared/scripts/case-review.sh`、`.agentwork/tests/test_workflow_review.py`、`.shared/scripts/README.md` | 验证: latest 改为按 `YYYYMMDD-HHMM` 文件名时间戳选取，同戳报 `ambiguous_latest` 并退出 1；`case-review.sh` 删除独立 mtime 选取改调该入口；改动前副本上复现旧行为（选中 `scratch-notes.md`、同戳静默兜底选 twin）；全量 `python3 -m unittest discover -s .agentwork/tests` 133 运行 / OK / 1 跳过，`agentwork-check.py self-test` 与 `render_bootstrap.py --check` 均 PASS

## 风险 / 阻塞
- 批次 1 与批次 2 已作为单一原子单元一次推进完毕（共 9 项），当前无红测试、无双所有权窗口。原判断成立：该组改动确实一次打红 5 个用例、跨 3 个文件，与预测一致。仅剩批次 3 的 4 项文档与清理。
- evals 落点为 `.agentwork/evals/research/`，偏离原计划的 `.agentwork/bootstrap/research/evals/`。理由是 BOOTSTRAP 语义为「待分发」，放其外让「永不分发」成为结构事实。依据是实测而非推断：仓库副本内 `install-bootstrap.py -p .` rc=0、刷新后 `render --check` rc=0、收据 64 条含 6 条 research 且 `.agentwork/` 前缀 0 条，说明 bootstrap 从不认领 `.agentwork/` 下任何路径。（推进过程中我曾编造过一个不存在的 `managed_agentwork_relpaths()` 对账机制并据此声称该落点会致 rc=8 冲突；该函数在工作区与 HEAD 中均不存在，结论已被上述实测推翻，勿再引用。）
- 被删 `tools/research/README.md` 的 `- provisional` 标记已抢救至 `.agentwork/evals/research/README.md` 的「当前状态」区，测试断言改指该处；其「单一入口」与「安全边界」内容已由 canonical SKILL.md 的对应章节覆盖。**尚未落地**：该 README 的安装边界（provider 独立、不装 MCP/CLI、不改 `.env`、不改平台 MCP 配置）需在批次 3 写入 `project/agentwork.md` 与 `bootstrap/README.md`，目前仅存于 git 历史。
- 两项 Important finding 已复现但未修，属第二批：registry `schema_version` 五种异常形态（缺失 / 999 / 字符串 / null / 列表）全部被接受并载入 10 个工具；旧 receipt 路径退役在 `install-tool.py:571` 早于 `:582` 的 action 分支，install 与 uninstall 同时被阻断。第三项（两条 latest 路径都选中不合命名草稿）已在第一批修复。
- 命令文档与 latest 实际规则存在漂移：`.shared/commands/plan.md:12`、`case.md:47-48`、`exec.md:19`、`review.md:60` 只写「最新的 `.tmp/agentwork/*/*.md`」，未说明按文件名时间戳选取、命名不合规不参与、同戳报错。助手若照字面按修改时间手选，会与 `agentwork-check.py` 得出不同结论——正是本轮消除的「两套并行规则」同类风险。属第三批文档单源任务，本轮未改。
- latest 收紧带来两处可见行为变化，接力前需知悉：`.tmp/agentwork/*` 中 5 个命名不合规的历史工件（`brain/20260511-arch-static-site-refactor.md`、`plan/20260906-external-review-fixes.md`、`plan/20260906-second-audit-fixes.md`、`review/20260506-workflow-deep-review.md`、`review/20260909-adoption-fixes.md`）自此不再参与 latest 选取，需显式传路径；`agentwork-check.py latest` 与 `case-review.sh` 无参输出由绝对路径变为仓库相对路径（与 `case-review.sh` 改动前的历史输出一致）。
- **需你确认的前提**：`research/README.md:7` 明确标 `- provisional：结构回归通过，等待现行内容与路由 gate 验证`，`test_research_routing_contract.py:115` 正在断言该标记存在；`project/agentwork.md:50` 又规定 routing contract 只有通过固定评测 gate 才可标 stable。把 provisional 能力提升为「所有项目默认获得」与该约束有张力。当前处理是保留 provisional 标记与 gate 要求，把「默认分发」与「契约 stable」当作两件事（anydoc 即先例：默认规则 + 运行时延迟安装 + hosted OCR 单独授权）。若要求先过 gate 再提升，本计划需整体后移。
- 渲染器抽象化会触碰所有平台生成产物，`render --check` 是唯一护栏，改动期间须每步验证。
- `.codex/skills/research/agents/openai.yaml` 是 5 层路径，比收据中现存最深的 4 层更深一级，`DEFAULT_SKILL_ENTRIES` 单文件模型对它是新场景，易漏。机制上 `install-bootstrap.py:147,583` 会自动建中间目录，风险低但需实测。
- 删除 `.agentwork/tools/research/` 属删目录操作，且会一并移除 `INSTALL.md`、`README.md`；须先确认 evals 新家就位再删。
- research 提升后，既有自承载项目重装会撞 ownership conflict（已实测：有文件无收据时报 `ownership conflict (unmanaged file)` rc=1）。冲突面由 tool 侧转到 bootstrap 侧，需在批次 1 验证既有项目升级路径。
- 第一批实现改动与 Case 快照已全部提交（`8a0fb7c`、`07fbdab`、`9d28b19`），工作区干净。
- 平台发现类结论双方均未在本轮确认：外部审查容器无任何 CLI，我方观测未获第二方复核。`.codex/skills` 在 codex-cli 0.154.0 有效这一结论未被推翻但也未被独立确认。
- 我此前六处断言经复核为错，已在结论中更正：`.shared` 应为 61/36 而非 63/38（多算 3 个 `.pyc`）；Pi 无 95 条正文断言（44 assert / 8 tests，95 系提及数，另一口径为 64）；Pi 有离线 RPC `get_commands` 列举途径；审查记录非硬限 3 条；`--check` 自 `1e6beb1` 起已被测试与文档调用；OpenCode 与 Cursor 有通用 manifest 投影覆盖。引用旧结论前须核对本条。
- `.git/index` 时间已为 16:41:18，无法重建旧 index 状态，故此前 staged 数量时间线的证据强度低于原陈述。Git 提交历史不是 index 历史。
- 无 CI，所有检查依赖本地入口被实际执行；第三批的 `verify` 聚合入口未落地前该风险持续。

## 审查记录
### 2026-09-14 19:30 +08:00
- 变更：批次 1 与批次 2 共 9 项作为原子单元一次落地后的双层 review。修掉一处真实冗余：`test_research_routing_contract.py` 的 `research_targets` 构造用 `item.split("/", 1)[0]` 与 `[1]` 拼回原串，与直接前置点号等价，两次 split 纯属浪费，已简化为 `f'.{item}'`。修正 Case 中 evals 落点记录的依据表述。
- 验证：内容保全逐字节取证——7 个迁移文件（含 5 层嵌套 `agents/openai.yaml`）全部与 HEAD 原路径相同；evals README 148→155 行，`固定输入` 之后正文逐字节未变，三处 Gate 定义与 provisional 标记均在。Case 声称的数字全部复核为真：registry 9 工具、排除集 18、`DEFAULT_SKILL_ENTRIES` 9 条（anydoc 4 + research 5，源文件全部存在）、`test_install_bootstrap` 默认 skill 9 条、`STACK` 残留 0。全量 135 运行 / OK / 1 跳过；`render --check` rc=0；`self-test` rc=0。
- 风险/待办：批次 3 的 4 项未动。被删 `tools/research/README.md` 的安装边界仍只存于 git 历史，须在批次 3 落入 `project/agentwork.md` 与 `bootstrap/README.md`。
- 保留决策：`safe_spec_relpath()` 与 `validate_rendered_paths()` 对绝对路径 / `..` 的检查存在部分重叠，但依 `coding-style.md`「输入格式校验尽量放在边界层」予以保留——前者在 spec 输入边界给出可定位的错误信息，后者是覆盖 wrapper、agent 等所有渲染目标的深层网，二者职责不同。`validated_default_capabilities()` 沿用 `validated_wrapper_specs()` 与 `load_env_keys()` 既有的精确键集校验风格，属一致性优先，不因表内暂只有一条而削减。
- 已知瑕疵（未改）：`WRAPPER_NAME_PATTERN` 被借用于校验默认能力名。其约束（小写连字符标识符）对二者都正确，复用避免了重复常量，但名称语义偏窄；重命名会触碰本次范围外的既有调用，留作后续。

### 2026-09-14 09:47 +08:00
- 变更：完成本轮 Case 与工作产物双层 review。第一批实现保持当前意图，未发现新的 Critical、Important 或 Major 行为问题；将 Case 快照自身纳入当前批次工作集，并修正“仅在 working tree、未改动 staged 区”的过期状态描述。
- 验证：`.shared/scripts/case-review.sh 20260913-1900-external-review-followup` 取证后无未覆盖实现路径；全量 `python3 -m unittest discover -s .agentwork/tests -p 'test_*.py'` 为 133 运行 / OK / 1 跳过；`agentwork-check.py self-test`、`render_bootstrap.py --check`、Case strict-flow 均通过。self-test 仅输出 fixture 中预期的重复提交锚点 warning。
- 风险/待办：registry `schema_version` 校验、旧 receipt 路径退役、命令文档与 latest 规则单源化、第三批 `verify` 聚合入口和平台契约矩阵仍未落地。

### 2026-09-14 08:10 +08:00
- 变更：第一批两项落地并交叉验证三项 Important finding。`install-tool.py` 事务补捕 `SystemExit`（含回滚阶段）；`agentwork-check.py` 的 latest 改为按文件名时间戳选取、同戳报 `ambiguous_latest` 退出 1；`case-review.sh` 退掉独立 mtime 选取改调该入口。本轮 review 又自修两处：`case-review.sh` 曾用 `2>&1` 捕获，会把未来任何 stderr 混入 Case 路径，改为只捕获 stdout；`ARTIFACT_NAME_RE` 的 `[^/]+` 对 `path.name` 是冗余约束，简化为 `.+`。
- 验证：三项 finding 均在隔离夹具复现（非推断），其中 latest 与 schema_version 两项另在「改动前副本」上确认旧行为——旧规则选中 `scratch-notes.md`、同戳静默兜底选 twin、五种 schema 形态全部放行。新增回归 `test_systemexit_after_second_write_rolls_back` 在改动前安装器上确认失败（`"rolled back" does not match "after receipt write"`），修复后通过。`pick_latest_case` 三分支（仅 README、同戳歧义、唯一合规）逐一实跑。全量 133 运行 / OK / 1 跳过；`self-test`、`render_bootstrap.py --check`、Case strict-flow、`case-review.sh` 均通过。
- 风险/待办：`schema_version` 未校验与旧 receipt 双向阻断仍未修（第二批）；命令文档未写明 latest 规则，存在助手手选与工具结论不一致的漂移（第三批）；5 个命名不合规历史工件不再参与 latest 选取。
- 保留决策：`run_transaction` 回滚阶段的 catch 元组保留 `KeyboardInterrupt` 与 `SystemExit`，与 `install-bootstrap.py:902` 对称——回滚期收到中断时记录为 rollback_error 并继续尽力回滚，优于半写状态逃逸，属有明确事务边界依据的防御。

### 2026-09-13 19:00 +08:00
- 变更：保存外部审查结论与三批推进计划为本 Case；记录六处自有断言更正、撤回「耦合新增」保留意见、并把三项待验证 Important finding 登记为风险。
- 验证：六处争议数字均经独立复核（`git ls-files .shared` 为 61、收据覆盖 25、未覆盖 36；anydoc 五条路径摘要全部匹配 bootstrap 而非工具收据）；E12 与 E13 在隔离夹具复现，latest 选中明确标注「待决策」的草稿且 `check_plan` 判 PASS，仅 touch 旧文件即切回；`install-bootstrap.py:305-335` 确认本就读取 registry 与 tool.json。本地 review note 的定向回归为 `test_install_tool` 37/37、`test_install_bootstrap` 55/55、`test_workflow_review` 7/7。
- 风险/待办：三项 Important finding 待复现；平台发现类结论缺第二方确认；`latest` 最小守卫与完整发布协议的取舍需在第一批落地时定稿。
