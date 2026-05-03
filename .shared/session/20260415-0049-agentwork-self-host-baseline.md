# Session: agentwork source repo 自承载基线

> 创建: 2026-04-15 00:49
> 简述: 反向收敛 agentwork 当前整仓改动，建立 source repo 可直接原地使用 agentwork 工作流的续作基线

## 任务列表（按优先级）
- [x] 建立 `agentwork` source repo 自承载基线：核心 workflow、bootstrap source、optional tool source、upstream mapping 与 deterministic harness 可在本仓库原地维护。
- [x] 完成 `architecture` optional tool MVP，并收敛为 `arch` 命名：tool source、renderer、模板、样例、安装入口与 deterministic smoke 均已落地。
- [x] 收敛 workflow/session 规则：`/session` 只做任务快照与流程串联，`/brain`、`/plan`、`/exec`、`/review` 支持 standalone 模式。
- [x] 补强 `/brain` 的“澄清结果 + 方案对比 + 推荐决策”约束，并避免 session mode 与 standalone mode 定义漂移。
- [x] 明确根目录 bootstrap 产物属于 source repo 正式基线：`AGENTS.md`、`.claude/`、`.agent/`、`.cursor/`、`.github/`、`.codex/skills/*` 以 `.agentwork/bootstrap/*` 与 deterministic harness 为事实源。
- [ ] 若后续要把 source repo 自测扩到可选工具层，再补充 tool self-install / real-cli 回归策略。
- [ ] 若后续仍发现 `/brain` 会绕过澄清或方案对比，再补 checklist 或 review 侧结构化校验。

## 已确认结论（工作快照）
### 目标
- 将 `agentwork` 收敛为可自承载的 workflow source repo：既维护 source 层（`.agentwork/*`），也能在仓库根目录直接使用 agentwork 的核心工作流继续改进自身。
- 用一份 session 快照承接 source repo 的后续续作，而不必重新从零梳理上下文。

### 边界
- In Scope: 当前 live workflow 文件、bootstrap source、optional tool source、upstream mapping、test harness、source repo 自承载能力与现有上下文结论。
- Out of Scope: 新业务功能、可选工具默认预装、提交/发布流程、跨仓库同步自动化。

### 约束
- `agentwork` 必须保持 runtime-agnostic，不再绑定 OMX 作为前提。
- `.shared/` 只承载项目内直接可用的核心工作流契约；可选工具保留在 `.agentwork/tools/*`。
- Session 是手动任务快照，不是 runtime state，不自动加载旧 session。
- session 不设置固定阶段字段；推进状态以任务列表、已确认结论、当前批次工作集与审查记录表达。
- `/brain` 必须先显式产出“澄清结果 + 方案对比 + 推荐决策”，不能直接跳到“已选方案”或 `/plan`。
- `/brain`、`/plan`、`/exec`、`/review` 必须支持 standalone 模式，临时工件统一落到 `.tmp/agentwork/*`。
- Ralph 只作为 `/exec --ralph` / `/session exec --ralph` 的执行策略存在，不单独扩成平行主工作流。
- source repo 原地 bootstrap 时必须跳过与 source 同路径的核心 `.shared` 文件，只刷新根目录适配层与 managed block。

### 已选方案
- 采用“四层结构”维护仓库：`.shared/` = 核心 workflow contract，`.agentwork/bootstrap/` = 多 AI 薄封装 source，`.agentwork/tools/` = 可选工具 source，`.agentwork/upstreams/` = 上游方法论映射。
- `/session` 只做任务快照和流程串联；真正的工作由 `/brain`、`/plan`、`/exec`、`/review` 完成。
- `/brain` 作为 brain 流程的唯一完整规范；`/session brain` 与 `session-workflow` 只保留引用和 session-mode 额外约束。
- source repo 自身通过 `python3 install-bootstrap.py -p .` 自刷新核心层；optional tools 仍保持按需安装。
- 根目录适配层产物属于 source repo 正式基线，不视为临时生成物；事实源为 `.agentwork/bootstrap/*`。

## 当前能力快照
- `arch` optional tool 已从 `architecture` 收敛完成；命令、wrapper、renderer、模板目录与 registry 均使用 `arch`。
- `arch` MVP 采用 catalog-first / source-first 结构：`catalog.json` 管导航，`diagram.arch.json` / `diagram.mmd` 为图表事实源，`index.html` 为 render output。
- 每个图表目录单独产出 `index.html`，通过 catalog 与父子/关联链接完成静态导航；当前不做浏览器内编辑、权限控制或托管预览。
- 当前目录约定：正式产物放 `docs/architecture/`，临时探索落到 `.tmp/architecture/`。
- 当前默认使用系统字体栈，不内置字体 assets，不依赖 Google Fonts。
- 当前对外使用方式收敛为单一 `/arch` 入口，由自然语言驱动生成、调整与 review。
- 当前图面原则：`viewport.width` / `height` 表示最小画布，内容超出时由页面滚动承载；内容较少时优先收紧节点间距。

## 关键入口
- 核心 workflow：`.shared/commands/*`
- 工作流边界：`.shared/patterns/*`
- source 生成层：`.agentwork/bootstrap/*`
- 可选工具层：`.agentwork/tools/*`
- upstream mapping：`.agentwork/upstreams/*`
- 回归入口：`test/run_deterministic.py`、`test/check_bootstrap_contract.py`
- source repo 入口约束：`AGENTS.md`、`.shared/INDEX.md`、`.shared/project/agentwork.md`

## 产出批次（提交锚点）
- 历史: `self-host/session 基线闭环` | 范围: `8b41c9e`, `19f2aa7`, `e7e2c8c`, `791b31a`, `45bad97`
- 提交: `cf4efdd feat(architecture): 新增架构图 optional tool` | 范围: architecture optional tool MVP、安装态 wrapper、renderer、样例、`docs/architecture/` 与 deterministic smoke
- 提交: `3fec736 docs(brain): 收敛 brain 流程约束` | 范围: `/brain` 澄清 / 方案对比 / 推荐决策约束、session/workflow 引用收敛
- 提交: `0629327 feat(arch): 将 architecture optional tool 收敛为 arch` | 范围: `architecture` -> `arch` optional tool 主体、安装态 wrapper、renderer、模板、样例、安装入口与 deterministic smoke
- 提交: `55d1cbb docs(workflow): 收敛工作流与 session 维护规则` | 范围: workflow/session 规则、bootstrap 入口、browser shared skill、project/session 目录约定、`session-review.sh`
- 提交: `-` | 范围: `.shared/commands/review.md`, `.shared/session/20260415-0049-agentwork-self-host-baseline.md`（本次 session review 规范与快照收敛提交；不再追加提交回填自身 hash）

## 当前批次工作集（可选）
- 范围: `.shared/commands/review.md` | 主题: 补充 session review 收敛维护最佳实践
- 范围: `.shared/session/20260415-0049-agentwork-self-host-baseline.md` | 主题: 删除过期信息和过渡讨论内容，保留可恢复任务的长期快照

## 风险 / 阻塞
- `arch` 若过早把 schema、命令面或交互做大，会偏离“简约、自用、语言驱动”的当前边界。
- `arch` 当前允许 source 自带坐标且不内置字体 assets，首轮图面质量会更依赖 prompt 与样例，而不是自动布局或视觉素材。
- optional tools 已 source-managed，但 source repo 场景下的 tool self-install 目前只有人工 smoke / 手动审查，没有纳入 deterministic 自动评分。
- 当前 `/brain` 约束已压回 live docs 与模板，但还没有脚本级 checklist 或 review 侧结构化校验；若 agent 行为仍不稳定，需要再补自动检查。

## 审查记录
### 2026-05-04 session review
- 变更：删除过期提交边界、reset 过程、临时讨论和命令流水；将审查记录压缩为阶段摘要，并把“清理过渡过程、保留长期快照、不追加提交回填 session 自身 hash”的规则补入 `/review` 规范。
- 验证：已运行 `.shared/scripts/session-review.sh .shared/session/20260415-0049-agentwork-self-host-baseline.md` 与 `git diff --check`；提交前再运行 `git diff --cached --check`。
- review 结论：当前 session 不再承担过渡讨论存档，只作为 source repo 自承载基线的恢复快照；本次提交后不再为了回填自身锚点追加提交。

### 阶段摘要
- 2026-04-09 - 2026-04-15：完成 research 结论到 live docs 的落地，确认 session 是当前任务快照而非 runtime state；完成 runtime-agnostic/source-repo refactor、source repo 原地 bootstrap、自承载基线、session 轻量产出格式、session load 取证规则与 session 自身锚点规则。
- 2026-04-16 - 2026-04-19：完成 `architecture` optional tool MVP 与本仓库安装态验证；移除 session 固定阶段字段；补强 `/brain` 澄清、方案对比与推荐决策约束；提交 `cf4efdd` 与 `3fec736` 后回填真实锚点。
- 2026-04-30 - 2026-05-03：完成 `architecture` 到 `arch` 的命名收敛、catalog-first renderer、Mermaid reference 支持、bootstrap/工具文档去临时态、browser shared skill frontmatter 修复、session-review 删除/迁移路径误报修复，以及脚本调用链低风险清理。
- 2026-05-04：`arch` tool 与 workflow/session 收敛主体已经提交为 `0629327` 与 `55d1cbb`；self-host baseline session 已收敛为长期恢复快照；当前仅保留本次 review 规范与 session 快照收敛这一笔。

## 建议摘录到 Project（可选）
- 无；稳定结论已在 `.shared/project/agentwork.md` 中维护。
