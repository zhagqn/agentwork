# Session: integrated test standard

> 创建: 2026-05-04 11:03
> 简述: 记录旧集成诊断退场，以及核心 workflow 回归已收敛到命令内建自检脚本后的最终快照。

## 任务列表（按优先级）
- [x] 确认旧集成诊断已不再作为核心 workflow 的主要验证入口，相关资产退出当前主线。
- [x] 将 core workflow 的回归与工件形态检查收敛到 `.shared/scripts/agentwork-check.py` 与 `.shared/scripts/session-review.sh`。
- [x] 在 `/brain`、`/plan`、`/exec`、`/review`、`/session` 文档中固化工件边界、自检要求和 session 收敛规则。
- [x] 将本 session 从长篇 run 历史压缩为可恢复的历史专题快照。
- [x] 清理当前活跃文档、session 与架构图中的旧集成诊断历史引用，避免把旧入口误读为现役事实。

## 已确认结论（工作快照）
### 目标
- 为后续阅读保留一份可恢复快照：解释旧集成诊断为什么退出核心 workflow，以及现在应该看哪些入口。

### 边界
- In Scope: `.shared/scripts/agentwork-check.py`、`.shared/scripts/session-review.sh`、`.shared/scripts/README.md`、`.shared/commands/*`、`.shared/project/agentwork.md`、本 session 的历史收敛。
- Out of Scope: 恢复旧集成诊断目录、重新引入 provider integrated run 作为固定回归、清理其他专题或 optional tool 改动。

### 约束
- 当前默认本地回归入口是 `python3 .shared/scripts/agentwork-check.py self-test`。
- `/brain`、`/plan` 只落 `.tmp/agentwork/*`；写 session 必须显式经过 `/session plan`；`/review` / `/session review` 需结合 `session-review.sh` 与 session strict-flow 自检。
- 真实 provider E2E 只保留人工 smoke / 兼容性调查价值，不再作为默认 gate。
- 旧集成诊断目录已删除；历史 run 结果只作为取证，不应继续占据顶部快照。

### 已选方案
- 用 `.shared/scripts/agentwork-check.py` 承担 `brain` / `plan` / `exec` / `review` / `session` / `latest` / `self-test` 的确定性工件检查。
- 用 `.shared/scripts/session-review.sh` 负责 session 工作集与工作区事实取证。
- 全局稳定事实收敛到 `.shared/project/agentwork.md` 与 `.shared/session/20260415-0049-agentwork-self-host-baseline.md`；本 session 仅保留旧集成诊断退场专题的结论与最小历史摘要。

### 核心定义 / 流程（可选）
- 当前主线 workflow 是 `/brain -> /plan -> /session plan -> /session exec -> /session review`。

## 计划摘要（可选）
### 关键文件 / 边界
- `.shared/scripts/agentwork-check.py` | 命令内建 harness 事实源。
- `.shared/scripts/session-review.sh`、`.shared/scripts/README.md` | session 取证与脚本文档。
- `.shared/commands/brain.md`、`.shared/commands/plan.md`、`.shared/commands/exec.md`、`.shared/commands/review.md`、`.shared/commands/session.md` | 工件边界、自检要求和 session 收敛规则。
- `.shared/project/agentwork.md`、`.shared/session/20260415-0049-agentwork-self-host-baseline.md` | 当前稳定入口和全局基线说明。
- `.shared/session/20260504-1103-integrated-test-standard.md` | 本专题的历史快照。

### 执行批次 / 优先级
- 已完成：旧集成诊断退居历史专题，主回归切换到 `agentwork-check.py self-test`。
- 已完成：命令文档、自检脚本和 bootstrap wrapper 文案对齐“命令入口，读取共享规则”。
- 已完成：本 session 与相关活跃文档中的旧入口引用已清理为当前事实口径。

### 执行策略（可选）
- standard

### 验证策略
- `bash .shared/scripts/session-review.sh .shared/session/20260504-1103-integrated-test-standard.md`
- `python3 .shared/scripts/agentwork-check.py session .shared/session/20260504-1103-integrated-test-standard.md --strict-flow`
- `python3 .shared/scripts/agentwork-check.py self-test`
- `git diff --check -- .shared/session/20260504-1103-integrated-test-standard.md`

### 完成标准（可选）
- 顶部工作快照不再把旧集成诊断入口写成现役事实。
- 本 session 只保留旧集成诊断退场后的稳定结论、当前入口和最小历史摘要。
- session strict-flow 自检通过。

## 关联工件（可选）
- `.shared/session/20260415-0049-agentwork-self-host-baseline.md`

## 当前批次工作集（可选）
- 范围: `.shared/session/20260504-1103-integrated-test-standard.md` | 主题: 将旧集成诊断专题压缩为历史快照，并同步本轮清理结果

## 产出批次（提交锚点）
- 历史: `2026-05-04 至 2026-05-10 旧集成诊断试验与回撤` | 范围: 历史集成诊断目录、provider split-process 诊断探索（现已退场）
- 提交: `-` | 范围: `.shared/session/20260504-1103-integrated-test-standard.md`

## 风险 / 阻塞
- 本 session 只收敛旧集成诊断退场专题；若后续继续整理其他 session 或 optional tool 文档，应在对应专题中单独续作。

## 审查记录
### 2026-05-13 session review
- 变更：按当前仓库事实重写本 session 顶部快照，并继续清理活跃文档、session 与架构图里会误导续作的旧集成诊断入口表述，改为 `agentwork-check.py self-test` + `session-review.sh` 的当前回归模型。
- 验证：旧集成诊断目录已删除；当前 workflow 入口与自检要求已在 `.shared/scripts/agentwork-check.py`、`.shared/scripts/README.md`、`.shared/commands/*`、`.shared/project/agentwork.md`、self-host baseline session 与 `docs/architecture` 中对齐。
- 风险/待办：若后续还要进一步压缩历史术语，只需继续整理更早审查记录或历史专题说明，不影响当前主线理解。

### 阶段摘要
- 2026-05-04 至 2026-05-10：围绕旧集成诊断做过多轮实验，先后收敛过阶段边界差分、真实产物断言、provider split-process 桥接与 session strict-flow 检查，最终确认整套 provider integrated run 成本高且不稳定，不适合作为默认回归主线。
- 2026-05-11 至 2026-05-13：core workflow 的确定性回归收敛到 `.shared/scripts/agentwork-check.py` 与命令文档内建自检；旧集成诊断退出核心理解入口，本 session 退为历史专题快照。

## 建议摘录到 Project（可选）
- 无；稳定结论已同步到 `.shared/project/agentwork.md` 与 `.shared/session/20260415-0049-agentwork-self-host-baseline.md`。
