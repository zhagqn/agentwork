# Case: 20260913-1900-external-review-followup

> 创建: 2026-09-13 19:00 +08:00
> 简述: 外部审查跟进已收口；新项目可初步引入，旧 research 按显式迁移流程升级

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
- [x] 批次 3：`spec.json` 增 research 默认能力条目并重新渲染，三处适配层文案同步
- [x] 批次 3：同步 `README.md`、`bootstrap/README.md`、`project/agentwork.md`，research 不再是 optional pack
- [x] 批次 3：删除 anydoc 孤儿收据 `.agentwork/tool-receipts/anydoc.json`
- [x] 批次 3：复核 `.agentwork/tool-receipts/` 空目录后两安装器行为仍正常
- [x] 批次 4：`install-tool.py` 补 registry `schema_version` 校验（照抄 `install-bootstrap.py:523-526` 既有范式）
- [x] 批次 4：旧 receipt 路径退役只阻断 install，不再连带堵死 uninstall
- [x] 批次 4：`verify` 聚合入口取最小形态（`.shared/scripts/verify.sh` 串起四条既有门禁，不新增检查逻辑）
- [x] 批次 4：评估后决定不做的三项，理由写入「关键决策 / 取舍」：归属视图、收据 envelope 统一、source repo 自身漂移门禁
- [x] 划界：五平台契约矩阵留在兄弟 Case `20260912-2330-adapter-test-symmetry`（其 5 项中 4 项仍未完成，与本 Case 主题正交）
- [x] 交叉验证三项未复核的 Important finding（三项均已复现；其中两项的修复属第二批）
- [x] 完成审查 P1：消除旧 optional research 升级后 6 条双重所有权，覆盖旧版卸载与用户修改保护
- [x] 完成审查 P2：明确 verify 的 source-only / 目标项目执行边界，目标项目不得调用未分发的测试和渲染器
- [x] 完成审查 P2：verify 区分无 Case 与 latest 歧义/执行失败，失败不得静默跳过
- [x] 完成审查 P2：命令文档显式引用统一 latest 选取契约，消除手选 mtime 歧义

## 已确认结论（工作快照）
### 目标
- 收口事务退出、工件选取、默认能力分发与文件所有权，并验证初步引入项目不会误覆盖或误删除用户文件。
### 边界
- In Scope: 两安装器、bootstrap 渲染与默认能力、registry、research 迁移、相关测试、共享命令/脚本及本 Case。
- Out of Scope: CI、发布打包、真实五平台发现能力验收、research routing gate 实现、Exa/Octocode 提升为默认能力。
- 五平台契约矩阵继续留在关联兄弟 Case；本轮未加载其内容，也不改动其已有工作区修改。
### 约束
- Git index 是用户边界；本轮不暂存、不提交。临时复现只写 .tmp/。
- 外部审查包 12 条 ownership、10 条 resolver、4 条 schema 测试是参考模型，不得直接替换安装器。
- 本轮由用户明确授权完成待办。真实历史工具装卸、删除与故障注入均仅针对自行创建的隔离夹具；不操作外部业务项目。
### 已选方案
- anydoc、research 均作为 bootstrap 默认能力分发；Exa/Octocode 保持 registry-only。默认规则分发不代表安装运行时、写凭据、修改 MCP 配置或通过 routing stable gate。
- anydoc 为 canonical 正文的渲染派生物；research 为静态薄入口，5 条 DEFAULT_SKILL_ENTRIES 加 1 条 core shared canonical，共 6 个目标文件。
- research evals 放在 source-only 的 .agentwork/evals/research/，不进入目标收据。
- latest 按 YYYYMMDD-HHMM-slug.md 文件名时间戳选择，不合命名者排除，最新同戳歧义必须报错；未引入完整发布协议。
- 完成审查结论：四项待办已闭环；当前验证范围内未发现阻塞初步引入的破坏性问题。全新项目可使用；旧 optional research 必须先由仍支持该工具的旧源码正常卸载，再运行当前 bootstrap。不可自动绕过冲突或仅删除收据。
### 关键决策 / 取舍（可选）
- run_transaction 回滚阶段保留 Exception、KeyboardInterrupt、SystemExit：中断时继续尽力恢复并报告残留路径，具有事务边界依据。
- verify 不使用 set -e，以便汇总全部失败；但 latest 失败不得因此变成成功跳过。
- anydoc 孤儿 tool 收据已删：历史五条摘要均过期，bootstrap 的同五条匹配磁盘，tool 通道不可达。该结论只针对当时 source repo，不推及外部旧 research 收据。
- 不做收据 envelope 统一：两安装器不读对方收据，纯形态统一收益低。当前旧 research 跨通道迁移仍必须解决所有权交接，不能用此取舍排除。
- 不新增通用 audit-ownership/explain 查询入口；历史“模型已经无交集”的论据已被旧项目复现推翻，需保留迁移交叉收据验证。
- 未新增 source repo 自身漂移自动门禁；现有 render --check 只覆盖渲染输出，不能替代静态 research 投影与所有目标安装态的比较。
- 保留 renderer canonical 缺失时回退首个 mirror，外部 bootstrap checkout 与夹具依赖其自包含行为。
- 29 个可选工具投影即使逐字节相同也不自动构成 tool 所有权许可；项目 Case、project 文档和 .gitkeep 属项目数据，不纳入刷新所有权。
- “统一 catalog 新增耦合”意见已撤回：collect_optional_shared_relpaths 本已读取 registry/manifest，耦合既存。

## 计划摘要（可选）
### 关键文件 / 边界
- install-tool.py：SystemExit 回滚、registry schema_version 校验、退役 receipt 路径只阻断 install；卸载继续校验路径、symlink 与摘要。
- install-bootstrap.py：DEFAULT_SKILL_ENTRIES 为 9 条；core sweep 排除 registry optional 路径与 source-only verify。preflight 在存在性及内容判断前检查全部 tool 收据交集，已有 core 收据也不能绕过；不可解析、越界或 symlink 收据停止安装。
- .agentwork/bootstrap/spec.json 与 render_bootstrap.py：默认能力扇出数据驱动、路径边界校验、重复目标保护；research 静态入口不在 render --check 覆盖内。
- .shared/scripts/agentwork-check.py 与 case-review.sh：共用 latest resolver；形态校验不证明工件内容已确认。
- .shared/scripts/verify.sh：仅 source repo 可运行且不再分发；无 Case 允许跳过，歧义/执行失败计入失败汇总。旧目标副本仅在历史 bootstrap 摘要匹配时事务退役；用户修改保留。
### 执行批次 / 优先级
- 已提交批次保留；本轮在已有工作区修复上补齐所有权阻断、可执行迁移指引、门禁回归、source-only 退役与文档，四项全部完成。
- 当前实现和 Case 改动尚未提交；未触碰 staged，未改变兄弟 Case 的已有修改。
### 执行策略（可选）
- standard
### 验证策略
- 当前回归基线：148 项运行、OK、1 因无 Pi 跳过；workflow self-test、render --check、当前 Case strict-flow。额外补验旧 verify 退役后收据写入失败的全树回滚。
- 迁移须覆盖旧工具真实安装、bootstrap 升级、重复升级、修改/缺失目标、旧收据退役、旧版卸载，不能只证明 fresh install。
- verify 须覆盖源仓与全新目标项目、无 Case、唯一 Case、最新同戳歧义、checker 执行失败、多项失败聚合。
- 全新项目应保留业务文件、LICENSE、.env，重复安装逐字节幂等，用户改动受管文件时在写入前拒绝。
### 完成标准（可选）
- 四项 P1/P2 均以实现、回归及隔离迁移实测闭环；初步引入验收通过。真实平台发现与 research routing stable gate 不在此次验收范围。

## 关联工件（可选）
- 外部审查报告：`.tmp/review-package/agentwork-review/agentwork-review.md`
- 审查证据与复现脚本：`.tmp/review-package/agentwork-review/`
- 本地原 review note：`.tmp/agentwork/review/20260913-1842-review-package.md`
- 当前方向 plan-source：`.tmp/agentwork/plan/20260914-1227-research-anydoc-default-capability.md`
- 已取代的 anydoc 单项 plan：`.tmp/agentwork/plan/20260914-1132-iteration-direction-adjustment.md`
- 兄弟 Case：`.shared/case/20260912-2330-adapter-test-symmetry.md`（本轮未加载）
- 修复前复现：`.tmp/case-review-followup/probe.py`（旧行为证据，不用于验证修复后结果）。
- 修复后历史工具迁移验证：`.tmp/case-review-followup/migration-check.py`，本轮夹具 `.tmp/migration-check-5ge5scep/`；依赖原 probe 提取的 6141a1f 父提交工具源码。

## 当前批次工作集（可选）
- 范围: `install-bootstrap.py`, `.agentwork/tests/test_install_bootstrap.py` | 主题: 收据交集预检、完整迁移验证与 source-only 退役
- 范围: `.shared/scripts/verify.sh`, `.agentwork/tests/test_verify.py` | 主题: 门禁失败传播与 source-only 边界
- 范围: `.shared/commands/`, `.shared/scripts/README.md`, `README.md`, `.shared/project/agentwork.md` | 主题: latest 统一规则、迁移指引与目标验证入口
- 范围: `.agentwork/bootstrap-install-state.json` | 主题: 自承载刷新后的收据
- 范围: `.shared/case/20260913-1900-external-review-followup.md` | 主题: 本轮实现及完成审查快照

## 产出批次（提交锚点）
- 提交: `429b2c4, 7dc531f` | 范围: 安装器、门禁、相关测试、文档与 bootstrap 收据 | 验证: 148 项运行 / OK / 1 skipped；5 项聚合门禁回归、61 项 bootstrap 回归通过；实际历史 research 工具迁移、用户修改保护、重复安装与旧版再次卸载无改动；source-only 退役注入收据失败后全树恢复。自承载刷新、render --check 与 workflow self-test 通过。主题：bootstrap 安全边界与 latest 命令文档。
- 提交: `d34da1f fix(installer): 校验 registry schema 并放行退役路径的卸载` | 范围: `install-tool.py`、`.agentwork/tests/test_install_tool.py` | 验证: `schema_version` 校验在仓库副本上验五种异常形态（缺失 / 999 / 字符串 / null / 列表）全部被拒、合法 registry 正常载入 9 工具。退役 receipt 路径的修复用真实场景验证：双文件工具装好后源端退役其一，install 仍 rc=1 且报出该路径，uninstall 改为 rc=0 且两个文件与收据全部清理——用户不再被困在既装不了也卸不掉的状态。放开的只是「路径是否在当前 manifest 内」这一条，`safe_target_path` 的 symlink 与越界防护、digest 校验对卸载路径仍生效。`test_install_tool.py` 38 → 40 用例全绿
- 提交: `20292c1 feat(workflow): 新增本地门禁聚合入口` | 范围: `.shared/scripts/verify.sh` | 验证: 39 行，只串起四条既有门禁不新增检查逻辑。两条路径均实测：真实仓库全绿时 rc=0 且四项串齐（137 用例 OK、self-test、`render --check`、Case strict-flow），副本内注入渲染漂移与 Case 破形两处失败后 rc=1 且汇总同时指名两项，中间通过的 self-test 不受影响
- 提交: `a9172a0 docs(research): 同步默认能力文档并清理孤儿收据` | 范围: `.agentwork/bootstrap/spec.json`、三处适配层及其 bootstrap 源产物、`README.md`、`.agentwork/bootstrap/README.md`、`.shared/project/agentwork.md`、`.agentwork/tool-receipts/anydoc.json`（删）、`.agentwork/bootstrap-install-state.json` | 验证: 批次 3 文档单源与清理。`spec.json` 增 research 文案（basic_items 12→13）后 `render --check` 如期报 4 处漂移，重渲染 + 自承载刷新后三处适配层均含该文案且 `--check` rc=0。孤儿收据删除前逐条取证：五条路径摘要全部 STALE，而 bootstrap 收据对同五条全部 CLAIMED+MATCH，且 anydoc 不在 registry、无工具目录、install/uninstall 均报 `Unknown tool`，故删除不丢有效所有权信息。空收据目录下四项行为复核正常：`install-tool.py list` rc=0 / 9 工具、隔离沙箱内 browser 装卸一轮 rc=0 且卸载后收据目录自动清理、自承载刷新 rc=0 且日志完全不提及 tool-receipts。全量 135 运行 / OK / 1 跳过；`self-test` rc=0
- 提交: `6141a1f feat(research): 将研究能力纳入默认 bootstrap` | 范围: `.agentwork/bootstrap/{codex,claude,pi}/skills/research/`、`.agentwork/bootstrap/cursor/rules/research.mdc`、`.agentwork/evals/research/`、`.agentwork/tools/research/`（删）、`.agentwork/tools/registry.json`、`install-bootstrap.py`、`.agentwork/tests/test_{research_routing_contract,pi_optional_tools,install_bootstrap}.py` | 验证: research 迁为 bootstrap 默认能力。registry 10→9 工具，`install-tool.py list` 无 research 且 `install research` 报 `Unknown tool` rc=1；排除集 19→18，core sweep 自动接管 canonical（25→26）；`DEFAULT_SKILL_ENTRIES` 4→9。测试侧解除 registry 成员身份耦合，`STACK` 6 处清零，原「生命周期独立」用例重写为通道隔离（tool 通道拒绝 research 且不留痕迹、provider 通道不产生任何 SKILL.md 或 cursor 规则），新增 provider 未被提升负例。全量 135 运行 / OK / 1 跳过（134→135）；`render --check` rc=0；`self-test` rc=0；仓库副本内自承载刷新 `install-bootstrap.py -p .` rc=0、刷新后 `render --check` rc=0、收据 64 条含 6 条 research 且 `.agentwork/` 前缀 0 条
- 提交: `5eeb97d refactor(bootstrap): 默认能力扇出改为数据驱动` | 范围: `.agentwork/bootstrap/spec.json`、`.agentwork/bootstrap/render_bootstrap.py` | 验证: 默认能力扇出改由 `spec.json` 的 `default_capabilities` 驱动，cursor 规则正文移出渲染器字面量（`grep '默认办公文档解析能力'` 归零）。`render_bootstrap.py --check` rc=0 零漂移、渲染产物仍为 36 个且 anydoc 4 个目标不变，证明纯机制重构、产物逐字节相同；新增 `validated_default_capabilities()` 的 9 个负例（缺键 / 空表 / 非法名 / 绝对路径 / `..` 穿越 / 空 mirror / 缺 rule 字段 / 空白正文 / 多余键）全部被拒；全量回归 133 运行 / OK / 1 跳过
- 提交: `8a0fb7c fix(installer): 修复事务对 SystemExit 不回滚` | 范围: `install-tool.py`、`.agentwork/tests/test_install_tool.py` | 验证: `run_transaction` 补捕 SystemExit（含回滚阶段）；新增 `test_systemexit_after_second_write_rolls_back`，在改动前的安装器副本上复跑该用例确认失败（`"rolled back" does not match "after receipt write"`），修复后通过
- 提交: `07fbdab fix(workflow): 统一 latest 工件选取规则` | 范围: `.shared/scripts/agentwork-check.py`、`.shared/scripts/case-review.sh`、`.agentwork/tests/test_workflow_review.py`、`.shared/scripts/README.md` | 验证: latest 改为按 `YYYYMMDD-HHMM` 文件名时间戳选取，同戳报 `ambiguous_latest` 并退出 1；`case-review.sh` 删除独立 mtime 选取改调该入口；改动前副本上复现旧行为（选中 `scratch-notes.md`、同戳静默兜底选 twin）；全量 `python3 -m unittest discover -s .agentwork/tests` 133 运行 / OK / 1 跳过，`agentwork-check.py self-test` 与 `render_bootstrap.py --check` 均 PASS
- 历史: `2026-09-14 Case 快照同步` | 提交: `9d28b19`、`735e7e7`、`c050e95` | 范围: 本 Case；实现锚点保留于上列，本轮不回填自身提交。

## 风险 / 阻塞
- 无未闭环的本轮 P1/P2。旧 research 采取阻断式迁移，不自动清理收据；须使用原来支持 research 的旧源码正常卸载。当前工具报 Unknown tool 是既定边界，README 已给正确步骤。
- 修改过的受管文件须先备份并核对；旧卸载与新安装都会拒绝直接覆盖/删除。缺少旧源码或不能确认所有权时需人工对账，不能宣称任意旧项目可无操作自动升级。
- 不可解析或 symlink tool 收据阻断 bootstrap，即使当前看不到交集；这是无法证明所有权安全时的保守失败。修复收据后可重试，失败前目标不变。
- 旧 verify 的未修改副本按历史收据摘要退役；用户改写、无收据、symlink 副本保留并报告。目标项目使用 agentwork-check.py 的 self-test 和显式工件检查。
- research 仍为 provisional；真实五平台发现与 routing stable gate 未运行，不给全平台 stable 承诺。无 CI，门禁仍需实际执行。
- 低优先级既有工具缺口：case-review.sh 无范围条目时 fallback 会把反引号 token 当路径，仍不属本轮四项待办；当前规范工作集不触发。WRAPPER_NAME_PATTERN 名称偏窄但约束正确，未扩散重命名。
- latest 兼容变化保留：不合命名历史工件需显式路径；输出为仓库相对路径。只有最新时间戳多候选时报歧义，四个命令文档与统一入口对齐。
- 历史纠错保留：.shared 数量为 61/36；Pi 95 为提及数；Pi 有离线 RPC get_commands；审查不硬限 3 条；render --check 已被测试/文档调用；OpenCode/Cursor 有通用 manifest 覆盖。不存在 managed_agentwork_relpaths 函数，Git 历史不能重建 index 时间线；旧精确证据见本 Case 历史及外审工件。
- 保留全部有效提交锚点与用户已有修改；本轮 working tree 未提交、staged 未更改。兄弟 Case 未加载、未编辑。

## 审查记录
### 2026-09-14 23:59 +08:00
- 变更：复审并完成四项待办；修正已有实现对缺失文件、已有 core 收据、损坏 tool 收据的漏检，将指引改为旧源码卸载；替换仅删收据的测试为真实 tool 装卸。verify 不再分发且旧匹配副本可事务退役；补完整门禁测试并同步四命令、README 与 project 约定。
- 验证：完整 verify rc=0，148 项运行 / OK / 1 skipped，workflow self-test、render --check 通过；之后补验退役事务收据失败回滚，针对性测试通过。历史工具真实迁移、用户修改保护、旧版再次卸载无副作用、新项目业务文件/.env/LICENSE 保全与幂等性均通过。自承载已刷新；Case strict-flow、最终 render --check 与 git diff --check 通过。
- 风险/待办：本轮四项完成，无阻塞初步引入的已知破坏性问题；迁移仍须遵循旧工具卸载前提，真实平台/runtime 与 routing gate 不在范围。未提交且 staged 未改。
- 信息保留：保留此前失败复现、所有 7 个实现锚点、事务/迁移取舍和用户已补充的工作内容；当前工作集按此次实际修改恢复，旧审查按时间保留最近三次。

### 2026-09-14 21:52 +08:00
- 变更：完成审查未通过；登记旧 research 双所有权及旧版卸载破坏、目标项目 verify 不可运行、latest 歧义假绿、命令文档规则未接入。更新完成状态、最终决策、计划、工作集与风险；保留原有用户补充及全部 7 个行为提交锚点，将较早审查归入历史。
- 验证：审阅 8a0fb7c 父提交至 HEAD 的相关实现 diff；case-review 取证确认实现已提交及孤儿工作集路径。沙箱外 verify rc=0，137 项 OK / 1 skipped，self-test 与 render --check 通过。隔离 probe 全部断言通过；目标项目 verify 实跑 rc=1。原样 latest 分支复现假绿，没有伪造全套 verify 运行结果。Case 编辑后 strict-flow 与 git diff --check 通过。
- 风险/待办：四项 P1/P2 尚未修复；全新项目可有限试用，旧 research 项目暂不验收。真实平台 runtime 与 routing gate 未验证，不给全平台 stable 承诺。此次只修改 Case 与临时复现，不修改实现、不提交。
- 信息保留检查：保留目标/边界、所有独立实现锚点、事务与所有权取舍、provisional 前提、迁移实证及历史纠错；移除已提交工作集与被推翻的“无交集”“文档已修”结论。

### 2026-09-14 21:15 +08:00
- 变更：批次 3 与批次 4 落地后的双层 review。修掉两处我自己在 `verify.sh` 里引入的问题：头部注释写「任一失败即以其退出码结束」与实现矛盾（实际累积全部失败后统一 exit 1），已改为准确表述并说明不用 `set -e` 的理由；`run()` 捕获并 `return $status` 属死代码——三个调用点全用 `|| true` 消费，而脚本未开 `set -e` 那三个 `|| true` 本身也不必要，一并简化。脚本 43 → 39 行。
- 验证：追审第二处安装器修复的安全边界，确认放开粒度正确——uninstall 跳过 manifest 归属检查后，`safe_target_path:176-180` 的 symlink 与越界防护、以及 `:572-576` 的 digest 校验均仍生效，故只会删内容与收据匹配的文件，用户改动过的文件仍被阻断（`test_modified_managed_file_blocks_update_and_uninstall` 钉住该行为）。`verify.sh` 简化后重验失败传播未退化：副本内注入渲染漂移 + Case 破形两处失败，rc=1 且汇总同时指名两项，中间通过的 self-test 不受影响。真实仓库跑完整 `verify.sh` rc=0，四项串齐。Case 声称数字全部复核为真：`test_install_tool` 40 用例、全量 137、`verify.sh` 39 行且可执行。
- 风险/待办：当时任务已勾选完成；对应实现现已提交。本轮完成审查发现的新问题见当前风险段，此历史结论不再代表完成状态。
- 保留决策：`verify.sh` 不使用 `set -e`——该脚本的价值正在于跑完四项并报出全部失败项，`set -e` 会让首个失败掩盖其余结果，与设计目标冲突。

### 历史审查摘要（2026-09-13 19:00 ~ 2026-09-14 19:30）
- 09-14 19:30 迁移 review：7 个迁移文件与原路径逐字节一致，evals 三 gate 与 provisional 标记保全；135 项 OK / 1 skipped，render 与 self-test 通过。保留 spec 输入校验与全局渲染路径检查，职责分别是边界报错与所有输出的安全约束；完整迁移提交锚点见产出批次。
- 09-13 建 Case 保存三批计划与外审纠错；09-14 08:10 事务 SystemExit 与 latest 的旧行为已在夹具复现并修复。09:47 双层 review：133 项运行 / OK / 1 skipped，self-test、render --check、strict-flow 通过；修正当时 staged 状态表述。回滚与 latest 行为锚点保留于产出批次。
- registry schema 与退役 receipt 双向阻断随后在批次 4 修复；命令文档 latest 单源化当时并未完成，现重新列入待办。
