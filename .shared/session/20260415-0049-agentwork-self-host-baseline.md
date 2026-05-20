# Session: agentwork source repo 自承载基线

> 创建: 2026-04-15 00:49
> 简述: 反向收敛 agentwork 当前整仓改动，建立 source repo 可直接原地使用 agentwork 工作流的续作基线

## 任务列表（按优先级）
- [x] 建立 `agentwork` source repo 自承载基线：核心 workflow、bootstrap source、optional tool source、upstream mapping 与 deterministic harness 可在本仓库原地维护。
- [x] 完成 `architecture` optional tool MVP，并收敛为 `arch` 命名：tool source、renderer、模板、样例、安装入口与 deterministic smoke 均已落地。
- [x] 收敛 workflow/session 规则：`/session` 只做任务快照与流程串联，`/brain`、`/plan`、`/exec`、`/review` 通过 `.tmp/agentwork/*` 工件协作。
- [x] 拆清 `/brain`、`/plan` 与 `/session plan` 边界：`/brain` 只做需求澄清和方案收敛，`/plan` 只产出 plan 工件，写入 session 必须显式经过 `/session plan`。
- [x] 明确根目录 bootstrap 产物属于 source repo 正式基线：`AGENTS.md`、`.claude/`、`.agent/`、`.cursor/`、`.github/`、`.codex/skills/*` 以 `.agentwork/bootstrap/*` 与本地 harness 为事实源。
- [x] 复核并收敛 workflow 语义：按实际约束区分必做流程、执行顺序、关键纪律和检查清单，统一 session-ref、计划摘要、当前批次工作集、产出批次、风险 / 阻塞等核心术语。
- [x] 固化 subagent 协作规范：作为可选执行 pattern，明确委派契约、简洁输出格式、模型默认继承和主 agent 验收责任，不并入 `/exec` 或 `/review` 必做流程。
- [x] 增加 `agentwork-check.py` 命令内建 harness，并把核心命令的落盘自检入口统一到 `.shared/scripts/`。
- [x] 同步 bootstrap source、project/index 文档与平台入口文案，使“命令入口，读取共享规则”成为统一表述。
- [x] 增加 `command-preview.sh` 命令输出 preview 策略，并同步到 bootstrap 启动约束，降低未知大输出对上下文的冲击。
- [ ] 若后续要把 source repo 自测扩到可选工具层，再补充 tool self-install / real-cli 回归策略。
- [ ] 若后续仍发现 `/brain`、`/plan` 或 `/session plan` 边界被绕过，再补结构化校验或 review 侧检查。

## 已确认结论（工作快照）
### 目标
- 将 `agentwork` 收敛为可自承载的 workflow source repo：既维护 source 层（`.agentwork/*`），也能在仓库根目录直接使用 agentwork 的核心工作流继续改进自身。
- 用一份 session 快照承接 source repo 的后续续作，而不必重新从零梳理上下文。

### 边界
- In Scope: 当前 live workflow 文件、bootstrap source、source repo 安装态 core wrappers、project/session 文档、自检脚本与现有上下文结论。
- Out of Scope: 新业务功能、可选工具默认预装、`arch` source-first 重构本身、提交/发布流程、跨仓库同步自动化。

### 约束
- `agentwork` 必须保持 runtime-agnostic，不再绑定 OMX 作为前提。
- `.shared/` 只承载项目内直接可用的核心工作流契约；可选工具保留在 `.agentwork/tools/*`。
- Session 是手动任务快照，不是 runtime state，不自动加载旧 session。
- session 不设置固定阶段字段；推进状态以任务列表、已确认结论、计划摘要、当前批次工作集、产出批次、风险与审查记录表达。
- `/brain` 只做需求澄清、问题域拆分、方案对比和推荐决策，产物只落到 `.tmp/agentwork/brain/*.md`；完整执行计划仍由 `/plan` 承接。
- `/plan` 只接收已确认设计，产物只落到 `.tmp/agentwork/plan/*.md`；把已确认结果写入 session 的唯一入口是 `/session plan [plan-source]`。
- `/review` 和 `/session review` 必须同时对照 session 快照与当前工作区事实；完成前使用 `.shared/scripts/session-review.sh` 取证，并用 `.shared/scripts/agentwork-check.py session <session-ref> --strict-flow` 校验形态。
- `.shared/scripts/agentwork-check.py` 是核心命令的本地确定性 harness；真实 provider E2E 和 real-cli 只作为人工 smoke / 兼容性调查，不作为默认回归或合并 gate。
- Ralph 只作为 `/exec --ralph` / `/session exec --ralph` 的执行策略存在，不单独扩成平行主工作流。
- Subagent 是可选协作机制，不改变 `/exec` 或 `/review` 的核心语义；读取触发由 `/exec`、`/review` 和 session workflow 规定，委派契约、输出格式和验收责任由 `.shared/patterns/subagent-workflow.md` 规定。
- source repo 原地 bootstrap 时必须跳过与 source 同路径的核心 `.shared` 文件，只刷新根目录适配层与 managed block。

### 已选方案
- 采用“四层结构”维护仓库：`.shared/` = 核心 workflow contract，`.agentwork/bootstrap/` = 多 AI 平台入口 source，`.agentwork/tools/` = 可选工具 source，`.agentwork/upstreams/` = 上游方法论映射。
- 核心命令分层固定为：`/brain` 负责设计收敛，`/plan` 负责计划落地，`/session plan` 负责写入快照，`/exec` 负责执行，`/review` 负责双层审查。
- source repo 自身通过 `python3 install-bootstrap.py -p .` 自刷新核心层；平台入口是由 `.agentwork/bootstrap/*` 生成的“命令入口，读取共享规则”，不是独立规范源。
- 核心 workflow 的本地回归入口收敛为 `.shared/scripts/agentwork-check.py self-test`；旧集成诊断只保留在专题 session 和历史取证中，不再作为主要理解入口。
- 工具级或专题级深度迭代使用独立 session 维护；本基线只保留跨批次稳定事实，不重复记录 `arch`、旧集成诊断等专题实现细节。

## 当前能力快照
- 核心 workflow 已固定为 `/brain` -> `/plan` -> `/session plan` -> `/session exec` -> `/session review` 的分层协作模型。
- `.shared/scripts/agentwork-check.py` 已覆盖 `brain`、`plan`、`exec`、`review`、`session`、`latest` 与 `self-test`。
- `.shared/scripts/command-preview.sh` 已作为未知或可能大输出命令的默认 preview 入口，按 `exit/bytes/lines` 元信息与首尾采样保护上下文。
- source repo 可以原地刷新 bootstrap，并把 `.agentwork/bootstrap/*` 同步到根目录 core wrappers；tool 级实现细节以各自 session 为准。

## 关键入口
- 核心 workflow：`.shared/commands/*`
- 工作流边界：`.shared/patterns/*`
- 命令自检：`.shared/scripts/agentwork-check.py`
- 命令输出 preview：`.shared/scripts/command-preview.sh`
- session 取证：`.shared/scripts/session-review.sh`
- source 生成层：`.agentwork/bootstrap/*`
- 可选工具层：`.agentwork/tools/*`
- upstream mapping：`.agentwork/upstreams/*`
- 安装入口：`install-bootstrap.py`、`install-tool.py`
- source repo 入口约束：`AGENTS.md`、`.shared/INDEX.md`、`.shared/project/agentwork.md`

## 计划摘要（可选）
### 关键文件 / 边界
- `.shared/commands/brain.md`、`.shared/commands/plan.md`、`.shared/commands/exec.md`、`.shared/commands/review.md`、`.shared/commands/session.md`、`.shared/patterns/session-workflow.md`：核心命令分层、strict-flow 与 session 快照职责。
- `.shared/INDEX.md`、`.shared/project/`、`.shared/templates/brain.md`、`.shared/templates/plan.md`、`.shared/templates/session.md`：目录说明、project 入口和模板语义同步。
- `.shared/scripts/agentwork-check.py`、`.shared/scripts/README.md`：本地确定性 harness 与脚本文档。
- `.shared/scripts/command-preview.sh`：未知或可能大输出命令的固定 preview 策略，默认返回小输出全文或大输出首尾采样。
- `.agentwork/bootstrap/`、`.agent/workflows/`、`.claude/commands/`：bootstrap source 与 source repo 安装态 core wrapper 同步。
- `.shared/session/20260504-1103-integrated-test-standard.md`：记录旧集成诊断退场后的专题快照，不再作为主理解入口。
- 不把 `.shared/commands/arch.md`、`.shared/scripts/arch-render.py`、`.agentwork/tools/arch/`、`docs/architecture/`、`.shared/session/20260512-1031-arch-source-first-site.md` 混入当前批次。

### 执行批次 / 优先级
- 第一批：移除旧 `standalone / session mode` 与 `/session brain` 过渡措辞，固定 `/brain -> /plan -> /session plan` 分层。
- 第二批：补齐 `agentwork-check.py`、command docs 自检要求、project/index/template 文档同步。
- 第三批：同步 bootstrap source 与 source repo 安装态 core wrappers，压缩 self-host / integrated-test session 快照并清退旧集成诊断的主入口定位。
- 第四批：补充命令输出 preview 策略脚本，并把“未知或大输出优先 preview”同步到 bootstrap 与各平台入口。

### 执行策略（可选）
- standard

### 验证策略
- `bash .shared/scripts/session-review.sh .shared/session/20260415-0049-agentwork-self-host-baseline.md`
- `python3 .shared/scripts/agentwork-check.py session .shared/session/20260415-0049-agentwork-self-host-baseline.md --strict-flow`
- `python3 .shared/scripts/agentwork-check.py self-test`
- `.shared/scripts/command-preview.sh -- seq 2000`
- `git diff --check -- .shared/session/20260415-0049-agentwork-self-host-baseline.md`

### 完成标准（可选）
- 顶部工作快照不再保留过期的 `/session brain`、`standalone mode` 或旧集成诊断主入口描述。
- 当前批次工作集与风险能准确覆盖 self-host workflow / harness 收敛，不把 `arch` source-first 等其他专题混入当前 session。
- session 能通过 strict-flow 自检，审查记录只保留高信号结论，不继续堆过渡讨论。

## 关联工件（可选）
- `.shared/session/20260504-1103-integrated-test-standard.md`
- `.shared/session/20260512-1031-arch-source-first-site.md`

## 产出批次（提交锚点）
- 历史: `self-host/source-repo 基线建立与 arch MVP` | 范围: `8b41c9e`, `19f2aa7`, `e7e2c8c`, `791b31a`, `45bad97`, `cf4efdd`, `3fec736`, `0629327`
- 提交: `55d1cbb docs(workflow): 收敛工作流与 session 维护规则` | 范围: workflow/session 规则、bootstrap 入口、browser shared skill、project/session 目录约定、`session-review.sh`
- 提交: `2d4f371 docs(workflow): 收敛工作流语义与契约检查` | 范围: `.shared/commands/*`, `.shared/patterns/*`, `.shared/project/*`, `.shared/scripts/*`, `.shared/templates/*`, `.agentwork/bootstrap/*`, 历史集成诊断资产
- 提交: `419d387 docs(workflow): 固化 subagent 协作和回归契约` | 范围: subagent workflow pattern、`/exec` `/review` 入口引用、bootstrap contract
- 提交: `269ebfa docs(workflow): 收敛命令入口并移除 test harness 主流程` | 范围: 核心命令分层、bootstrap / wrapper 入口文案、`.shared/scripts/agentwork-check.py`、`.shared/project/*` 与历史 `test/` 资产清退
- 提交: `1da3a8e docs(session): 清理旧集成诊断历史引用` | 范围: `.shared/project/agentwork.md`, `.shared/session/20260504-1103-integrated-test-standard.md`, `.shared/session/20260415-0049-agentwork-self-host-baseline.md`（清理旧集成诊断历史引用，并回填本轮 session / project 最终口径）
- 提交: `835faba feat(workflow): 增加命令输出 preview 策略` | 范围: `.shared/scripts/command-preview.sh`, `.shared/scripts/README.md`, `.shared/INDEX.md`, `.agentwork/bootstrap/*`, root / 平台 bootstrap 入口（补充命令输出 preview 策略并同步启动约束）

## 当前批次工作集（可选）
- 范围: `.shared/scripts/command-preview.sh` | 主题: 固定命令输出 preview 策略，保留退出码并按总量选择全文或首尾采样
- 范围: `.shared/scripts/README.md` | 主题: 记录 `command-preview.sh` 用法、默认阈值和不足时的追加取证策略
- 范围: `.shared/INDEX.md` | 主题: 将命令输出 preview 入口纳入核心 workflow 索引
- 范围: `.agentwork/bootstrap/` | 主题: 在 bootstrap 单一源与生成基线中加入未知或大输出优先 preview 的启动约束
- 范围: `AGENTS.md` | 主题: 同步 source repo 根入口的 command preview 约束
- 范围: `.claude/` | 主题: 同步 Claude 安装态入口的 command preview 约束
- 范围: `.agent/` | 主题: 同步 Antigravity 安装态入口的 command preview 约束
- 范围: `.cursor/` | 主题: 同步 Cursor 安装态入口的 command preview 约束
- 范围: `.github/` | 主题: 同步 Copilot 安装态入口的 command preview 约束
- 范围: `.shared/session/20260415-0049-agentwork-self-host-baseline.md` | 主题: 收敛本轮 session review 后的当前批次、风险和审查记录

## 风险 / 阻塞
- optional tools 已 source-managed，但 source repo 场景下的 tool self-install / real-cli 还没有纳入本地确定性回归。
- `agentwork-check.py` 只覆盖 workflow 工件形态和关键契约，不替代真实 provider 行为、optional tool 效果或人工质量判断。
- `command-preview.sh` 是机械 preview，不替代完整取证；结构化输出、错误上下文在中段或诊断仍不充分时，需要继续按行号、偏移或更窄命令追加读取。

## 审查记录
### 2026-05-20 session review
- 发现：当前实现改动集中在 `command-preview.sh`、脚本文档、`.shared/INDEX.md`、bootstrap 单一源与各平台生成入口；脚本辅助审查发现 session 的旧当前批次工作集仍指向 integrated-test 清理路径，未覆盖当前 15 个工作区改动。
- 修正：已将当前批次工作集改写为本轮 command preview 相关路径，补充未提交产出批次、能力快照、关键入口、风险说明和本条审查记录；实现审查未发现阻塞性问题。
- 回填：已将旧集成诊断清理批次回填为 `1da3a8e docs(session): 清理旧集成诊断历史引用`，并将 command preview 批次回填为 `835faba feat(workflow): 增加命令输出 preview 策略`。
- 验证：已运行 `git status --short`、`git diff --stat`、`.shared/scripts/session-review.sh .shared/session/20260415-0049-agentwork-self-host-baseline.md`、针对核心脚本 / bootstrap 的 diff 审查、`python3 .shared/scripts/agentwork-check.py session .shared/session/20260415-0049-agentwork-self-host-baseline.md --strict-flow`、`python3 .shared/scripts/agentwork-check.py self-test`、`bash -n .shared/scripts/command-preview.sh`、`.shared/scripts/command-preview.sh -- seq 2000` 与 `git diff --check`。
- 风险/待办：preview 策略只能降低默认上下文压力，不能证明输出已经语义完整；后续若需要更强行为保障，可把 targeted slice / keyword scan 做成脚本参数。

### 2026-05-13 session review
- 变更：按当前 dirty tree 重写 self-host baseline 顶部快照，补齐 `计划摘要`，把旧 `/session brain` 和旧集成诊断主入口表述改为当前 `/brain -> /plan -> /session plan` 与 `agentwork-check.py self-test` 语义，并压缩过长的产出批次 / 审查记录。
- 验证：已运行 `.shared/scripts/session-review.sh .shared/session/20260415-0049-agentwork-self-host-baseline.md`、`python3 .shared/scripts/agentwork-check.py session .shared/session/20260415-0049-agentwork-self-host-baseline.md --strict-flow`、`python3 .shared/scripts/agentwork-check.py self-test` 与 `git diff --check -- .shared/session/20260415-0049-agentwork-self-host-baseline.md`。
- 风险/待办：本轮只清理 self-host / integrated-test 两份 session 与 project 入口；`arch` 等其他专题继续由各自 session 维护。

### 2026-05-11 brain / session 边界复核
- 变更：保留 brain / plan 分层，只强化需求澄清、问题域拆分、方案对比质量和高影响确认门；随后把“session 写入”从讨论阶段进一步拆开，为后续 `/session plan` 收敛铺平语义边界。
- 验证：已运行 targeted `git diff --check`、`.shared/scripts/session-review.sh .shared/session/20260415-0049-agentwork-self-host-baseline.md`；当时旧工作集与当前 brain 批次不匹配，已在本轮 session review 中继续收敛。
- 风险/待办：若模型仍把推荐方案直接写成已选方案或跳过 `/plan`，需要补 deterministic prompt 检查或 review 侧结构化校验。

### 2026-05-06 workflow 语义复核
- 变更：吸收 `.tmp/agentwork/review` 中仍有价值的建议，补强 `/plan` 与 `/exec` 约束；随后按实际约束统一 session-ref、review-source、计划摘要、当前批次工作集、产出批次、风险 / 阻塞等核心术语。
- 验证：已运行 `python3 install-bootstrap.py -p .`、当时的历史集成诊断回归、`.shared/scripts/session-review.sh .shared/session/20260415-0049-agentwork-self-host-baseline.md` 与 `git diff --check`；相关结果只作为历史取证保留。
- 风险/待办：这条记录只作为历史取证保留；当前默认回归入口已转向 `.shared/scripts/agentwork-check.py self-test`，不再把旧集成诊断入口视为主要理解入口。

### 阶段摘要
- 2026-04-09 - 2026-04-15：完成 research 结论到 live docs 的落地，确认 session 是当前任务快照而非 runtime state；完成 runtime-agnostic/source-repo refactor、source repo 原地 bootstrap、自承载基线和 session 轻量产出格式。
- 2026-04-16 - 2026-05-03：完成 `architecture` optional tool MVP 与 `architecture` -> `arch` 命名收敛；补强 `/brain` 澄清、方案对比与推荐决策约束，并清理 bootstrap/工具文档中的临时态描述。
- 2026-05-04 - 2026-05-13：完成 workflow 语义、subagent pattern、brain/plan/session 写入边界、命令自检 harness 与 source repo 入口文案的连续收敛；self-host baseline session 改为只保留稳定快照，不再承载过渡讨论。

## 建议摘录到 Project（可选）
- 无；稳定结论已在 `.shared/project/agentwork.md` 中维护。
