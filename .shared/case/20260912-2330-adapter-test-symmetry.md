# Case: 20260912-2330-adapter-test-symmetry

> 创建: 2026-09-12 23:30
> 简述: 补齐五平台适配层的对称测试覆盖，并把本轮实测到的平台事实固化为可回归的断言

## 任务列表（按优先级）
- [ ] 把 Pi 的 wrapper 正文契约断言移植到 Claude / Codex / OpenCode / Cursor 四家
- [ ] 为四家分别钉住"预期 wrapper 集合"，使某个入口从 spec 消失时测试立即失败
- [ ] 把 `render_bootstrap.py --check` 接入确定性测试，让生成物漂移不再依赖人工记得运行
- [ ] 为"平台入口是否真被发现"补一层可回归检查，替代一次性人工 smoke
- [ ] 复核 Codex skill 发现路径的版本依赖，决定是否同时落地 `.agents/skills`

## 已确认结论（工作快照）
### 目标
- 五个平台的适配层拥有同等强度的自动化验证，不再由适配时间先后决定测试密度。
### 边界
- In Scope: `.agentwork/tests/` 下的适配层测试、`spec.json` 与 renderer 的可测契约、生成物漂移检查的接入方式。
- Out of Scope: 命令描述文本的改写、Cursor 缺 per-command 入口的补齐、高风险操作强制机制的落地。这三项属独立议题，不在本 Case 收敛。
- 其中前两项已由读取链优化独立完成（2026-09-13），仍不纳入本 Case，但后续任务需按已完成后的新形态设计断言，不要再按改动前的入口形态移植。
### 约束
- 当前处于测试阶段，无发布流程也无 CI；所有检查必须能在本地确定性运行，不假设远端流水线存在。
- 不依赖真实 provider 调用与计费请求；平台事实类断言只针对仓库内可读取的生成物与配置。
- 平台运行时行为随版本漂移，断言必须写清所依据的版本基线，不把单一版本的观测外推。
### 已选方案
- 以 `test_pi_adapter.py` 现有断言为模板横向铺开，而不是新设一套框架。
- 平台事实类结论沉淀为"版本基线 + 断言"，参照 Pi 已有的 `compatibility_baseline` 做法。
### 关键决策 / 取舍（可选）
- 测试密度不对称的成因是维护顺序，不是刻意取舍：Pi 适配最后完成，其测试也最后编写，故最完整。既有四家不是被判定为不需要测试。
- Codex 的 `.codex/skills` 在 codex-cli 0.154.0 上实测有效，官方文档仅记载 `.agents/skills`。二者取其一会赌单一版本，故倾向双路径并存，需先验证不会造成重复注入。
- 移植模板的形态已变：Claude wrapper 现有 frontmatter description，六条命令的描述来自 `spec.json` 的 `description` 字段而非标题兜底。任务 1 的断言应针对该新形态，并优先断言结构而非描述原文，避免与文本耦合。

## 计划摘要（可选）
### 关键文件 / 边界
- `.agentwork/tests/test_pi_adapter.py` 是断言模板来源，勿改其现有覆盖。该文件已于 2026-09-13 被读取链优化触碰：断言数与测试函数数均未变（44 / 8，与 HEAD 一致），仅 `case.md` 逐字断言的预期文本随契约更新。
- 新增或扩展的适配测试落在 `.agentwork/tests/`，不改 `.shared/` 工作流契约。
- `.agentwork/bootstrap/spec.json` 与 `render_bootstrap.py` 是被测契约，仅在补可测字段时改动。
### 执行批次 / 优先级
- 先做 Claude 与 OpenCode，二者入口形态最简单且已有实测事实可对照；再做 Codex；Cursor 最后，因其入口形态与其余四家不同。
### 执行策略（可选）
- standard
### 验证策略
- 每批完成后运行 `python3 -m unittest discover -s .agentwork/tests -p 'test_*.py'`，当前基线为 130 项通过。
- 运行 `python3 .shared/scripts/agentwork-check.py self-test` 确认工作流契约未受影响。
- 运行 `python3 .agentwork/bootstrap/render_bootstrap.py --check` 确认生成物无漂移。
### 完成标准（可选）
- 四家各自拥有 wrapper 正文断言与预期集合断言；漂移检查已接入确定性测试；平台事实类断言标注了版本基线。

## 关联工件（可选）
- 平台适配边界与回退流程：`.shared/patterns/platform-adapter.md`
- 生成契约与 renderer：`.agentwork/bootstrap/spec.json`

## 当前批次工作集（可选）
当前无工作集。

## 产出批次（提交锚点）
- 提交: `不适用（尚未执行）` | 范围: `.agentwork/tests/` | 验证: 本 Case 仅登记待办，尚未产生改动

## 风险 / 阻塞
- 平台运行时行为随版本漂移，本轮观测基于 codex-cli 0.154.0；断言若不写明版本基线，未来升级会产生误报或漏报。
- Cursor 与 Pi 无免费的只读列举能力，运行时发现行为无法在不产生计费请求的前提下自动回归，只能退回生成物层面的断言。
- 无 CI 环境，检查是否被执行取决于人工习惯；漂移检查若不接入 `unittest` 或 `self-test`，接入本身等于没做。渲染契约已于 2026-09-13 变更，该风险比登记时更迫切。
- `test_pi_adapter.py` 的 `case.md` 逐字断言现与描述文本耦合，任何描述改写都会打到它。任务 1 应顺带放宽为结构断言。
- 兜底描述字面量原先在渲染器内出现两次，改一处漏一处会让 Pi 与其余平台对同一命令给出不同默认描述；已于 2026-09-13 合并为 `default_wrapper_description()` 单一来源，该项已闭环。
- 更正一处误诊：description 的换行校验看似在两处重复，实际不是冗余，不得删减。`validated_wrapper_specs` 只校验原始 `description` 键，而 `validated_pi_wrappers` 校验解析后的值，是唯一覆盖 `pi_description` 的检查；`test_pi_adapter.py` 的 `metadata-newline` 用例仅靠后者才成立。

## 审查记录
### 2026-09-13 14:49
- 变更：当前工作区共 59 项 staged 改动，内容属于上一轮读取链 / bootstrap 生成物更新；没有新增 Claude、Codex、OpenCode、Cursor 适配测试，没有预期 wrapper 集合断言，也没有把 `render_bootstrap.py --check` 接入确定性测试。本 Case 五项待办保持未完成，当前批次工作集保持为空。
- 验证：`case-review.sh` 取证到 59 项工作区改动且无产出提交锚点；全量回归 130 项通过（跳过 1 项），`agentwork-check.py self-test` 通过，`render_bootstrap.py --check` 通过，`git diff --cached --check` 通过。staged 区未被本轮修改。
- 风险/待办：现有 staged 改动中的 `test_pi_adapter.py` 只有 `case.md` 预期文本同步，不构成本 Case 的测试覆盖。五项待办仍需按原计划执行；Codex 双 skill 路径是否重复注入、三家运行时发现行为和生成漂移测试接入仍未闭环。

### 2026-09-13 00:55
- 变更：本 Case 五项待办仍全部未开始；按取证结果清空当前批次工作集，并标注两项 Out of Scope 已由读取链优化独立完成、移植模板形态已变、`test_pi_adapter.py` 已被触碰但覆盖未减。
- 验证：`case-review.sh` 报工作区 59 项改动、工作集 3 条全部命中，但命中来源均为读取链优化而非本 Case；`test_pi_adapter.py` 断言 44 条、测试函数 8 个，与 HEAD 一致，仅预期文本随契约更新；全量回归 130 项通过，`render_bootstrap.py --check` 零漂移，workflow self-test 通过；staged 区全程为 0。
- 风险/待办：审查时登记了两条渲染器清理项，未在审查阶段执行，因 review 不构成执行许可。其中兜底字面量重复随后已合并闭环；另一条"description 校验重复"经核实为误诊并已撤回，两处校验覆盖不同键，删任一处都会丢覆盖。逐字断言与描述文本耦合需在任务 1 一并处理；漂移检查仍未接入确定性测试。
- 工具缺口：`agentwork-check.py:681` 判定空工作集用的是行列表的成员相等（`section_lines` 返回原始行，见 `:349`），因此空工作集哨兵句必须独占整行，句后追加说明文字会导致 `missing_workset_entries`。本次审查实际踩到两次。该要求在 `.shared/case/README.md` 与 `.shared/commands/review.md` 均未写明，宜放宽为子串匹配或补进文档。

### 2026-09-12 23:30
- 变更：登记五平台测试覆盖不对称这一待办，并把本轮实测到的平台事实写入约束与风险，避免后续重复取证。
- 验证：测试覆盖差异经统计确认，Pi 有 95 条提及其名的断言，OpenCode 与 Cursor 为 0；Codex 与 Claude 各数条且均不针对 wrapper 正文。Codex 入口发现经隔离沙盒实测确认，`.codex/skills` 下 10 个 skill 全部进入模型可见 prompt，`.codex/skills` 与 `.agents/skills` 两个路径同时被发现。OpenCode 经 `opencode debug config` 与 `opencode debug skill` 确认 6 条核心命令加 figma 全部被解析，并从 `.claude/skills/` 发现 anydoc 与 research。
- 风险/待办：Claude、Cursor、Pi 三家的运行时发现行为本轮未实测，仅有官方文档结论；`render_bootstrap.py --check` 存在但未被任何测试或文档调用。
