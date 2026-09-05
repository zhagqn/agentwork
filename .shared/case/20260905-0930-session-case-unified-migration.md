# Case: 20260905-0930-session-case-unified-migration

> 创建: 2026-09-05 09:30
> 简述: Session → Case 单轨迁移的独立任务快照；实现已提交，本笔保存快照与真实提交锚点

## 任务列表（按优先级）
- [x] 将共享命令、工作流、模板、审查脚本及有效任务快照统一为 Case
- [x] 统一 Case 占位符、交叉引用与 checker，移除旧公开检查子命令和 legacy 格式回退
- [x] 同步 bootstrap spec、renderer、各平台 wrapper、source self-host 与 receipt
- [x] 安全退役旧受管入口及 README 受管块，保护项目自定义内容和普通旧任务数据
- [x] 更新公开文档与平台说明，不保留 agentwork Session 兼容入口
- [x] 修正 receipt 所有权优先级、文档适用范围和源端旧数据分发边界
- [x] 完成 fresh、升级、重复安装、冲突、回滚、Pi 适配及全量回归与提交前复核
- [x] 通过 `/commit` 确认提交范围并提交迁移实现；Case 自身随本笔保存

## 已确认结论（工作快照）
### 目标
- Case 是 agentwork 唯一的仓库级任务快照，可跨平台显式恢复，不依赖平台私有对话状态。
### 边界
- In Scope: Case 共享契约、checker、平台生成物、bootstrap 同步与安全退役、当前有效快照、相关测试和文档。
- Out of Scope: 旧任务数据扫描/转换框架、别名或双读双写、Case 数据模型重构、平台原生 session、Git 历史改写、运行时全局配置；clean-clone 完整恢复链和 Research 后续事项仍归总体迭代 Case。
### 约束
- 仅按用户确认的 Git 边界提交；工件保存不代表重新执行实现任务或授权推送。
- 共享正文保持平台无关，平台仅保留薄 wrapper；可选工具不进入核心 bootstrap。
- 不覆盖项目自有文件，不因旧数据无需兼容而扩大删除范围。
### 已选方案
- `/case` 与 `.shared/case/` 完全替代 agentwork `/session`、Pi `/aw-session` 和旧活动目录；不提供兼容入口。
- Case v1 沿用手动任务快照结构，不增加父子关系、状态机或远程存储。
- Codex、Claude、OpenCode、Pi 使用 Case 入口，Cursor 使用共享契约；Pi 原生 `/session` 仍仅表示平台对话状态。
- 普通旧任务文件由内部脚本或 Agent 后续按需迁移，bootstrap 不转换、不读取内容或改写；source 端旧目录仍排除分发，不进入冲突检查、复制或 receipt。
### 关键决策 / 取舍（可选）
- 退役只针对可确认属于 agentwork 的入口和旧 README 受管块；自定义内容与符号链接继续受所有权规则保护。
- 曾由 core receipt 管理的退役入口：receipt 存在时仅哈希匹配可删除，缺项或内容变化持续保留；仅无历史 receipt 时用生成标记兜底。历史签名型 tool adapter 不扩大适用此规则。
- 源端 `session` 目录排除是数据分发保护，不是旧协议兼容层；`project`、`case` 的分发排除同时保留。
- 原临时 Plan 保留为设计和执行证据；后续本专题以此 Case 为当前任务快照，总体迭代 Case 只作跨主题接续入口。

## 计划摘要（可选）
### 关键文件 / 边界
- `.shared/{commands,patterns,templates,scripts,case}/` 与占位符规范负责 Case 语义及检查。
- `install-bootstrap.py`、`.agentwork/bootstrap/` 和 `.agentwork/bootstrap-install-state.json` 负责生成、同步与受管退役。
- `.agentwork/tests/test_install_bootstrap.py`、`.agentwork/tests/test_pi_adapter.py` 负责安装与平台回归。
### 执行批次 / 优先级
- 共享契约、平台生成、安装安全修正及回归已完成并提交；本笔仅保存 Case，后续独立任务回到总体迭代 Case。
### 执行策略（可选）
- standard
### 验证策略
- 已完成 workflow self-test、Case strict-flow、renderer、source self-host 两次同步、全量确定性测试及残留审查。
- 源端残留旧数据回归覆盖 fresh、目标同名数据及 self-host，三个场景各连续安装两次；同时保留旧 receipt、项目自定义内容、冲突和回滚覆盖。
- 后续若实现继续变化，重跑受影响测试；不把此前真实 Pi RPC 验证外推到其他版本。
### 完成标准（可选）
- Case 是所有活动契约中的唯一任务快照，旧受管入口安全退役，普通旧数据不参与分发或迁移，生成及安装验证通过；提交须另经用户确认。

## 关联工件（可选）
- 来源 Plan：`.tmp/agentwork/plan/20260904-1644-session-case-unified-migration.md`
- 来源 Brain：`.tmp/agentwork/brain/20260904-1639-session-case-unified-migration.md`
- 总体迭代及历史提交锚点：`.shared/case/20260807-1025-agentwork-iteration-consolidation.md`

## 当前批次工作集（可选）
- 范围: `.shared/case/20260807-1025-agentwork-iteration-consolidation.md`, `.shared/case/20260905-0930-session-case-unified-migration.md` | 主题: 总体与专题快照保存、提交锚点回填
- 范围: `.shared/session/20260807-1025-agentwork-iteration-consolidation.md` | 主题: 旧快照迁移后的原路径删除

## 产出批次（提交锚点）
- 提交: `46a5896 refactor(case): 将 Session 工作流统一为 Case` | 范围: Case 核心契约、bootstrap、平台入口、测试及文档 | 验证: 09:05 的 110 项全量 unittest、源端三场景连续安装与本仓库两次 self-host 通过；09:24 的 5 项定向回归、workflow/renderer、Case/Plan 和差异检查通过，复核无阻塞问题；实现已提交
- 提交: `-` | 范围: 两个 Case 快照及旧快照路径迁移 | 验证: 回填真实实现锚点，保留已确认决策与验证边界；本条仅记录 Case 自身这一笔

## 风险 / 阻塞
- 当前迁移无已知阻塞问题；用户已确认第二笔 Case 保存范围，不包含远端推送。
- Pi 真实发现证据仅覆盖 `v0.84.4`；最近一次 review 未重跑真实 RPC，升级后需重新验证。

## 审查记录
### 2026-09-05 09:24 源端数据隔离修正复核（沿用已确认结论）
- 变更：确认普通旧数据在 core 内容处理前排除，receipt 与旧入口所有权边界保持一致，无新增阻塞问题。
- 验证：5 项定向回归及 workflow、renderer、Case/Plan、工作集和差异检查通过；09:05 的 110 项全量测试与本仓库重复同步证据仍有效，未重复全量或 Pi 真实 RPC。
- 风险/待办：源端数据分发 P1 已闭环，待提交范围确认；本次 Plan 转换只沿用上述证据，不冒充新一轮实现审查。

### 2026-09-05 08:56 源端旧数据分发问题
- 变更：隔离诊断发现旧目录从过滤集合移除后，普通任务数据会跨项目复制、误登记 receipt，并导致目标同名数据冲突。
- 验证：旧实现三个场景复现；09:05 修正后各连续安装两次通过，110 项全量回归通过。
- 风险/待办：已在 09:24 复核闭环；保留目录级分发排除，不增加兼容读取或迁移机制。

### 2026-09-05 00:23 迁移初次收尾复核
- 变更：共享 Case、平台生成、受管退役及文档在当时审查范围内一致。
- 验证：109 项全量测试及 workflow、renderer、Case/Plan 检查通过；Pi `0.84.4` RPC 已于 09-04 确认六个项目 prompt。
- 风险/待办：当时结论后被 08:56 的源端残留数据发现补充，相关问题现已闭环。

### 历史审查摘要（2026-09-04 17:16 至 23:50）
- 共享契约、生成物与文档分批完成；22:48 复现 receipt 哈希不匹配但仍含生成标记的旧 wrapper 被误删，22:55 修正优先级并通过连续安装及 109 项测试。23:35 发现文档将 core receipt 规则泛化到签名型 tool adapter，23:50 收窄并通过检查。上述问题均已闭环，详细执行证据保留在来源 Plan。
