# Case: 20260913-1900-external-review-followup

> 创建: 2026-09-13 19:00 +08:00
> 简述: 落实外部架构审查结论，按三批收口事务退出、工件选取、所有权与平台契约

## 任务列表（按优先级）
- [x] 第一批：补 `install-tool.py` 的 SystemExit 回滚与「第二次写入后抛错」回归
- [x] 第一批：统一所有 latest 入口的选取规则，覆盖 `agentwork-check.py` 与 `case-review.sh` 两处独立 mtime 路径
- [ ] 第二批：建立归属视图，用现有 manifest、core 清单、受管区块声明生成，不手工维护第二张映射表
- [ ] 第二批：anydoc 纳入 registry 并迁移为单一 `tool:anydoc` 所有权，清理孤立收据与持久退订
- [ ] 第二批：统一 schema envelope，补 registry 版本校验负例与旧路径退役协议
- [ ] 第三批：五平台契约矩阵、本地 `verify` 入口、文档单源、压缩政策裁剪、观测时点语义、描述质量样例
- [x] 交叉验证三项未复核的 Important finding（三项均已复现；其中两项的修复属第二批）

## 已确认结论（工作快照）
### 目标
- 按外部审查结论收口三类边界：默认选择与文件所有权分离、两安装器共享事务机制、自动选取工件建立发布契约。
### 边界
- In Scope: `install-bootstrap.py`、`install-tool.py`、`.agentwork/bootstrap/*`、`.shared/scripts/*`、`.agentwork/tests/*`、以及 `.shared/commands` 与 `patterns` 的文档单源改造。
- Out of Scope: CI、发布、打包分发；高风险操作强制拦截；`.shared/` 目录结构调整；把审查包内设计模型直接替换现有安装器。
### 约束
- 审查包内 12 条 ownership、10 条 resolver、4 条 schema 测试是参考模型，不是补丁。落地需自行实现并验收，包内 README 已明确禁止直接替换。
- 五阶段核心流程不是可停用的默认工具；anydoc、research 可作为默认能力，但默认选择不等于安装运行时依赖或写入凭据。
- 命令约束按各命令特点定制，写入许可在可写流程里正向声明，不扩散禁令。
- 临时目录命名与生命周期按各域用途区分，不做统一规范。
### 已选方案
- 采用审查者的三批顺序，仅调整一处：`latest` 只落最小守卫（拒绝不符 `YYYYMMDD-HHMM-slug` 命名、遇歧义显式报错），不一次性实现完整发布协议。该守卫已在第一批落地，完整发布协议仍未做且暂不做。
- 归属拆成两个可查询维度：声明来源与本次安装所有权，提供只读 `audit-ownership` / `explain <path>` 类入口。
- 36 个未入收据文件按三类分别处置，不整体补进 bootstrap 收据。
### 关键决策 / 取舍（可选）
- 「统一 catalog 会新增两安装器耦合」这一保留意见已撤回。实测 `install-bootstrap.py:305-335` 的 `collect_optional_shared_relpaths()` 本来就读 registry 与每个 `tool.json`，缺 entry 直接 SystemExit，耦合早已隐式存在，显式化成本低于原估计。
- 29 个可选工具投影虽与规范源逐字节一致，但内容相同不构成认领许可，只能在显式自举对账操作中建立收据。
- 5 个项目数据文件（三个 Case、`project/agentwork.md`、`.gitkeep`）只做分类可见，不纳入刷新所有权，否则升级会覆盖本地任务数据。

## 计划摘要（可选）
### 关键文件 / 边界（已闭环）
- `install-tool.py:656,661`：事务已补捕 `SystemExit`（含回滚阶段），与 `install-bootstrap.py:897,902` 对称。`fail()` 仍是 `raise SystemExit`（`:55-56`），不改语义。
- `.shared/scripts/agentwork-check.py:320-349,917-944`：latest 改为按文件名 `YYYYMMDD-HHMM` 选取并显式拒绝同戳歧义；不再有 `kind == 'case'` 的 README.md 特例（命名规则已隐含排除）。
- `.shared/scripts/case-review.sh:22-38`：删除独立 mtime 选取，改调统一 latest 入口；只捕获 stdout，stderr 透传。
### 关键文件 / 边界（仍开放）
- `install-tool.py:571` 早于 `:582` 的 action 分支：旧 receipt 路径退役会同时阻断 install 与 uninstall（行号本轮已复核仍准确）。
- `install-tool.py:95-137`：完全未读取或校验 `registry["schema_version"]`；全文该字段出现 0 次。
- `.shared/scripts/agentwork-check.py`：`check_plan` 只校验形态，不判断内容是否已确认；latest 守卫只保证选中对象稳定，不保证其内容可用。
- `.agentwork/tool-receipts/anydoc.json`：五条路径摘要全部过期，且 anydoc 不在 registry 内。
### 执行批次 / 优先级
- 第一批改动面最小且影响真实行为，先做；第二批需先形成统一 catalog/ownership 模型再迁移 anydoc；第三批放最后，避免为即将改变的默认逻辑先堆复制型断言。
### 执行策略（可选）
- standard
### 验证策略
- 每批后运行 `python3 -m unittest discover -s .agentwork/tests -p 'test_*.py'`，当前基线为 133 条运行、OK、1 因无 Pi 跳过（第一批新增 3 条，原基线 130）。
- 运行 `python3 .agentwork/bootstrap/render_bootstrap.py --check` 与 `python3 .shared/scripts/agentwork-check.py self-test`。
- 第二批验收须覆盖真实五路径状态、用户改写、部分缺失、重复迁移、默认包增减、卸载后 bootstrap 同步、manifest 退役路径、未来 schema 拒绝、中途失败回滚，不得只证明 fresh install 成功。
### 完成标准（可选）
- 三批任务各自通过上述验收；未闭环项以显式风险留存，不以形态检查通过替代语义结论。

## 关联工件（可选）
- 外部审查报告：`.tmp/review-package/agentwork-review/agentwork-review.md`
- 审查证据与复现脚本：`.tmp/review-package/agentwork-review/`（inventory、experiments、proposed_contracts、migration_probe、mutation_probe）
- 本地 review note：`.tmp/agentwork/review/20260913-1842-review-package.md`

## 当前批次工作集（可选）
- 范围: `install-tool.py` | 主题: 事务对 SystemExit 的回滚闭环
- 范围: `.agentwork/tests/test_install_tool.py` | 主题: 第二次写入后抛 SystemExit 的回滚回归
- 范围: `.shared/scripts/agentwork-check.py` | 主题: latest 改为文件名时间戳选取并显式拒绝歧义
- 范围: `.shared/scripts/case-review.sh` | 主题: 退掉独立 mtime 路径，改调统一 latest 入口
- 范围: `.agentwork/tests/test_workflow_review.py` | 主题: latest 守卫回归与 fixture 命名对齐
- 范围: `.shared/scripts/README.md` | 主题: latest 选取规则文档同步
- 范围: `.shared/case/20260913-1900-external-review-followup.md` | 主题: 当前 Case 快照与审查记录

## 产出批次（提交锚点）
- 提交: `8a0fb7c fix(installer): 修复事务对 SystemExit 不回滚` | 范围: `install-tool.py`、`.agentwork/tests/test_install_tool.py` | 验证: `run_transaction` 补捕 SystemExit（含回滚阶段）；新增 `test_systemexit_after_second_write_rolls_back`，在改动前的安装器副本上复跑该用例确认失败（`"rolled back" does not match "after receipt write"`），修复后通过
- 提交: `07fbdab fix(workflow): 统一 latest 工件选取规则` | 范围: `.shared/scripts/agentwork-check.py`、`.shared/scripts/case-review.sh`、`.agentwork/tests/test_workflow_review.py`、`.shared/scripts/README.md` | 验证: latest 改为按 `YYYYMMDD-HHMM` 文件名时间戳选取，同戳报 `ambiguous_latest` 并退出 1；`case-review.sh` 删除独立 mtime 选取改调该入口；改动前副本上复现旧行为（选中 `scratch-notes.md`、同戳静默兜底选 twin）；全量 `python3 -m unittest discover -s .agentwork/tests` 133 运行 / OK / 1 跳过，`agentwork-check.py self-test` 与 `render_bootstrap.py --check` 均 PASS

## 风险 / 阻塞
- 两项 Important finding 已复现但未修，属第二批：registry `schema_version` 五种异常形态（缺失 / 999 / 字符串 / null / 列表）全部被接受并载入 10 个工具；旧 receipt 路径退役在 `install-tool.py:571` 早于 `:582` 的 action 分支，install 与 uninstall 同时被阻断。第三项（两条 latest 路径都选中不合命名草稿）已在第一批修复。
- 命令文档与 latest 实际规则存在漂移：`.shared/commands/plan.md:12`、`case.md:47-48`、`exec.md:19`、`review.md:60` 只写「最新的 `.tmp/agentwork/*/*.md`」，未说明按文件名时间戳选取、命名不合规不参与、同戳报错。助手若照字面按修改时间手选，会与 `agentwork-check.py` 得出不同结论——正是本轮消除的「两套并行规则」同类风险。属第三批文档单源任务，本轮未改。
- latest 收紧带来两处可见行为变化，接力前需知悉：`.tmp/agentwork/*` 中 5 个命名不合规的历史工件（`brain/20260511-arch-static-site-refactor.md`、`plan/20260906-external-review-fixes.md`、`plan/20260906-second-audit-fixes.md`、`review/20260506-workflow-deep-review.md`、`review/20260909-adoption-fixes.md`）自此不再参与 latest 选取，需显式传路径；`agentwork-check.py latest` 与 `case-review.sh` 无参输出由绝对路径变为仓库相对路径（与 `case-review.sh` 改动前的历史输出一致）。
- 第一批实现改动已提交为 `8a0fb7c` 与 `07fbdab`；本 Case 快照自身随后单独提交，故其产出批次条目不回填自身 hash。
- 平台发现类结论双方均未在本轮确认：外部审查容器无任何 CLI，我方观测未获第二方复核。`.codex/skills` 在 codex-cli 0.154.0 有效这一结论未被推翻但也未被独立确认。
- 我此前六处断言经复核为错，已在结论中更正：`.shared` 应为 61/36 而非 63/38（多算 3 个 `.pyc`）；Pi 无 95 条正文断言（44 assert / 8 tests，95 系提及数，另一口径为 64）；Pi 有离线 RPC `get_commands` 列举途径；审查记录非硬限 3 条；`--check` 自 `1e6beb1` 起已被测试与文档调用；OpenCode 与 Cursor 有通用 manifest 投影覆盖。引用旧结论前须核对本条。
- `.git/index` 时间已为 16:41:18，无法重建旧 index 状态，故此前 staged 数量时间线的证据强度低于原陈述。Git 提交历史不是 index 历史。
- 无 CI，所有检查依赖本地入口被实际执行；第三批的 `verify` 聚合入口未落地前该风险持续。

## 审查记录
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
