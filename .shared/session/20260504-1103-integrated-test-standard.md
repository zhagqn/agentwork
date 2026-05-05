# Session: integrated test standard

> 创建: 2026-05-04 11:03
> 简述: 收敛 agentwork 测试体系；当前结论是完整 provider integrated harness 保留为人工触发的集成诊断入口，不作为每轮固定测试流程。

## 任务列表（按优先级）
- [x] 将旧分散小 case 收敛为单个 integrated harness 方向，并验证安装、独立命令、session flow 和 drift 检查可以在同一个临时项目中串联。
- [x] 将真实命令输入从脚本主体拆出，按 `$brain` / `$plan` / `$exec` / `$review` 和 `$session load` 的实际使用方式分次调用。
- [x] 将测试目录重构为 `test/run.py`、`test/harness.py`、`test/checks.py`、`test/stages/`、`test/flow/`，删除旧入口和旧场景目录。
- [x] 根据连续 provider run 的成本和不稳定性，将完整 integrated harness 降级为人工触发的集成诊断入口。
- [x] 将 `/review` 的 session mode 规则从原则描述优化为必做流程、收敛 checklist 和禁止项。
- [ ] 后续如需稳定固定测试，另行设计无 provider 或低 provider 依赖的本地确定性检查。

## 已确认结论（工作快照）
### 目标
- 当前不再继续把完整 provider integrated harness 稳定化为每轮固定测试。
- `python3 test/run.py` 保留为人工触发的集成诊断入口，用于必要时验证真实 provider + workflow 的组合行为。
- 固定测试的后续方向应是更小、更确定、低 token 或无 token 的本地检查。

### 边界
- In Scope: `test/` 测试入口、阶段拆分、flow 输入、断言工具、临时 run 目录模型、session drift 检查。
- In Scope: `install-bootstrap.py`、`install-tool.py` 在临时目标项目中的安装行为验证。
- Out of Scope: 将完整 provider integrated harness 作为 CI 或每轮固定回归命令。
- Out of Scope: 证明 provider 原生 subagent 是否真的启动；只能验证工件契约和流程记录。
- Out of Scope: 真实业务完整性、发布流程、远程仓库操作和跨机器持久化测试结果。

### 约束
- 临时项目和结果统一写入 `.tmp/integrated-harness/runs/{run-id}/`。
- 单个 run 内只创建一个目标项目 `project/`，先安装 agentwork，再在同一项目内执行后续诊断。
- 完整 provider 集成测试只能人工触发；文档和 project 入口不能把它描述为稳定固定回归。
- session flow 中 `$session exec` 与 `$session review` 前必须显式 `$session load <session-id>`；独立 provider 进程里 load 与后续命令放在同一次输入中。
- 测试命令输入和调用顺序属于 `test/flow/` 资产，入口脚本只负责调度、resume 和结果汇总。

### 已选方案
- `test/run.py`: 集成诊断入口，负责新建 run、resume、阶段选择和报告刷新。
- `test/stages/`: install / independent / session 三个薄阶段入口。
- `test/harness.py`: 共享执行、provider 调用、日志、阶段主体和 run 结果写入。
- `test/checks.py`: 文本与产物断言工具。
- `test/flow/`: provider 调用顺序和真实命令输入。
- `test/check_bootstrap_contract.py`: bootstrap 安装契约检查器。
- `test/check_session_standard.py`: session 结构和 drift 检查器。
- `.shared/commands/review.md`: session review 的可执行化收敛规则。
- 已删除旧入口和旧场景资产：`test/run_integrated.py`、`test/run_real_cli.py`、`test/run_deterministic.py`、`test/cases/`、`test/scenarios/integrated/`。

## 计划摘要（可选）
### 关键文件 / 边界
- `test/README.md` | 测试目录说明、入口、flow 资产和输出目录。
- `test/run.py` | 诊断入口与 resume / stage 调度。
- `test/harness.py` | 底层执行、provider 适配、实时日志、阶段主体。
- `test/checks.py` | 断言辅助。
- `test/stages/` | 阶段入口。
- `test/flow/` | 命令输入。
- `.shared/commands/review.md` | session mode review 的必做流程、checklist 和禁止项。
- `.shared/project/agentwork.md` | source repo 长期入口说明。
- `.shared/session/20260504-1103-integrated-test-standard.md` | 当前任务快照。

### 执行批次 / 优先级
- 已完成：测试目录重构、旧入口删除、run-level 隔离、三阶段诊断入口和 session 记录收敛。
- 暂停推进：不继续把完整 provider integrated harness 稳定化为固定测试。
- 后续可选：设计无 provider 或少 provider 的本地确定性检查。

### 执行策略（可选）
- standard

### 验证策略
- 常规本地验证：`py_compile`、`python3 -m json.tool test/flow/flow.json`、`check_session_standard.py --strict-flow`、`git diff --check`。
- 入口轻量验证：`python3 test/run.py --help`。
- 不消耗 provider 的诊断验证：`python3 test/run.py --stage install`。
- 完整 provider integrated harness 仅在人工需要诊断时运行。

### 完成标准（可选）
- 测试目录入口清晰，旧分散 case 和旧 harness 不再是理解测试体系的主路径。
- `test/run.py` 可人工触发并生成可复盘的 `.tmp/integrated-harness/runs/{run-id}/results/`。
- session 和 project 文档明确：完整 provider integrated harness 暂不作为稳定固定测试流程。

## 关联工件（可选）
- `.tmp/integrated-harness/runs/20260505-231612/results/summary.json` | 最近一次完整 provider 诊断失败样例，install 与 independent 通过，session 阶段失败于文本断言。

## 当前批次工作集（可选）
- 范围: `.shared/session/20260504-1103-integrated-test-standard.md` | 主题: 压缩为当前可恢复任务快照
- 范围: `.shared/commands/review.md` | 主题: 将 session review 收敛维护规则改为可执行 checklist
- 范围: `.shared/project/agentwork.md` | 主题: 将 `test/run.py` 标记为人工触发的集成诊断入口
- 范围: `test/` | 主题: 保留重构后的诊断入口、阶段拆分、flow 输入和本地检查器

## 产出批次（提交锚点）
- 提交: `-` | 范围: `.shared/session/20260504-1103-integrated-test-standard.md`（当前 session 快照与审查记录压缩）
- 提交: `1169209 docs(commands): 收敛 session 命令边界` | 范围: `.shared/commands/review.md`（session mode review 必做流程与收敛 checklist）
- 提交: `3873ce6 test: 重构集成诊断入口` | 范围: `.shared/project/agentwork.md`（集成诊断入口说明）
- 提交: `3873ce6 test: 重构集成诊断入口` | 范围: `test/run.py`, `test/harness.py`, `test/checks.py`, `test/stages/`, `test/flow/`, `test/README.md`（测试目录重构和诊断入口收敛）

## 风险 / 阻塞
- 完整 provider integrated harness 成本高、稳定性不足，当前不适合作为每轮固定测试。
- 当前 `test/run.py` 仍可用于人工诊断，但不应被文档或 CI 误读为稳定回归命令。
- 后续固定测试需要重新设计为更小、更确定、低 token 或无 token 的本地检查。

## 审查记录
### 阶段摘要：2026-05-04 至 2026-05-05 21:44
- 变更：从旧小 case 迁移到 integrated harness；经历真实 provider 分步调用、HTTP JSON probe 场景、Mini Dinner Flow session 场景、实时日志、模型参数、fast mode、provider 失败分类和多轮断言收窄。
- 验证：多次真实 run 证明 install 和独立命令链路可以跑通；session flow 也能在强模型配置下推进，但最终产物断言和 provider 稳定性反复造成高成本失败。
- 结论：完整 provider 端到端测试有诊断价值，但不适合继续扩张为固定回归标准。

### 2026-05-05 23:45
- 变更：将 `test/run_integrated.py` 方向收敛为新结构：`test/run.py`、`test/harness.py`、`test/checks.py`、`test/stages/`、`test/flow/`。
- 观察：run `20260505-231612` 中 `install_standard` 与 `independent_commands` 均通过，`turborepo_iteration_flow` 失败于 `shared_types` 文本断言。
- 结论：长链路 provider 输出、断言边界和模型稳定性仍会让固定回归成本过高。

### 2026-05-05 23:56
- 发现：`.shared/project/agentwork.md` 曾把 `python3 test/run.py` 描述为普通回归验证，与当前“人工触发诊断入口”的定位不一致。
- 修正：已将 project 文档改为“集成诊断入口（人工触发）：`python3 test/run.py`”。
- 风险/待办：当前测试重构未再跑完整 provider integrated harness，符合“暂停稳定化、降低 token 消耗”的决策。

### 2026-05-06 00:05
- 发现：前一次 `$session review` 只追加审查记录，没有严格执行 session 收敛维护；旧目标、旧路径和长篇历史流水仍留在 session 中。
- 修正：已压缩任务、结论、计划摘要、当前批次工作集、产出批次、风险和审查记录；历史过程流水合并为阶段摘要，只保留最近仍有追踪价值的审查项。
- 验证：已运行 session 标准检查、Python 编译检查和 diff whitespace 检查。

### 2026-05-06 00:12
- 变更：优化 `.shared/commands/review.md`，把 session mode 从原则性说明改为必做流程、Session 收敛维护 checklist 和禁止结果。
- 结论：后续 `/session review` 不应只追加审查记录；必须同步维护任务、结论、计划摘要、当前批次工作集、产出批次、风险和审查记录。
- 验证：已对 `.shared/commands/review.md` 运行 diff whitespace 检查。

## 建议摘录到 Project（可选）
- 当前集成诊断入口为 `python3 test/run.py`；完整 provider integrated harness 暂定位为人工触发的诊断/实验回归，不作为稳定固定测试流程。
