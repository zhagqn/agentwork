# Session: agentwork source repo 自承载基线

> 创建: 2026-04-15 00:49
> 简述: 反向收敛 agentwork 当前整仓改动，建立 source repo 可直接原地使用 agentwork 工作流的续作基线
> 当前阶段: review

## 任务列表（按优先级）
- [ ] 决定是否将根目录 bootstrap 产物（`.claude/`、`.agent/`、`.cursor/`、`.github/`）纳入正式版本基线
- [ ] 下一轮功能演进开始前，基于本 session 先做一次聚焦 `/brain` 或 `/plan`
- [ ] 若后续要把 source repo 自测扩到可选工具层，再补充 tool self-install / real-cli 回归策略

## 已确认结论（当前版本）
### 目标
- 将 `agentwork` 收敛为可自承载的 workflow source repo：既维护 source 层（`.agentwork/*`），也能在仓库根目录直接使用 agentwork 的核心工作流继续改进自身
- 用一份 session 反向总结当前整仓改动，方便后续在 `agentwork` 目录中直接续作，而不必重新从零梳理上下文
### 边界
- In Scope: 当前 live workflow 文件、bootstrap source、optional tool source、upstream mapping、test harness、source repo 自承载能力与现有上下文结论
- Out of Scope: 新业务功能、可选工具默认预装、提交/发布流程、跨仓库同步自动化
### 约束
- `agentwork` 必须保持 runtime-agnostic，不再绑定 OMX 作为前提
- `.shared/` 只承载项目内直接可用的核心工作流契约；可选工具保留在 `.agentwork/tools/*`
- Session 是手动任务快照，不是 runtime state，不自动加载旧 session
- `/brain`、`/plan`、`/exec`、`/review` 必须支持 standalone 模式，临时工件统一落到 `.tmp/agentwork/*`
- Ralph 只作为 `/exec --ralph` / `/session exec --ralph` 的执行策略存在，不单独扩成平行主工作流
- source repo 原地 bootstrap 时必须跳过与 source 同路径的核心 `.shared` 文件，只刷新根目录适配层与 managed block
### 已选方案
- 采用“四层结构”维护仓库：`.shared/` = 核心 workflow contract，`.agentwork/bootstrap/` = 多 AI 薄封装 source，`.agentwork/tools/` = 可选工具 source，`.agentwork/upstreams/` = 上游方法论映射
- `/session` 只做任务快照和流程串联；真正的工作由 `/brain`、`/plan`、`/exec`、`/review` 完成
- source repo 自身通过 `python3 install-bootstrap.py -p .` 自刷新核心层，optional tools 仍保持按需安装
- 当前 live docs 已明确：handoff 不是新的核心层，session 才是当前任务的主快照
### 核心定义 / 流程（可选）
- `.shared/commands/*`：核心动作定义（session / brain / plan / exec / review / commit）
- `.shared/patterns/*`：工作流边界、跨平台适配、project/session 分层、语义导航约束
- `.shared/templates/*`：session / brain / plan / review / Ralph 辅助工件模板
- `.agentwork/bootstrap/*`：由 `spec.json` + `render_bootstrap.py` 生成的 root / Claude / Antigravity / Cursor / Codex / Copilot 薄封装 source
- `.agentwork/tools/*`：figma / browser / android / godot 的 source-managed optional tool packs
- `test/*`：fresh install、existing reinstall、source repo self-install 的 deterministic harness，以及真实 CLI harness

## 计划摘要（可选）
### 关键文件 / 边界
- source repo 自承载入口：`install-bootstrap.py`、`install-tool.py`
- 核心约束入口：`AGENTS.md`、`.shared/INDEX.md`、`.shared/project/agentwork.md`
- source 生成层：`.agentwork/bootstrap/spec.json`、`.agentwork/bootstrap/render_bootstrap.py`
- optional tool source：`.agentwork/tools/*`
- 验证层：`test/run_deterministic.py`、`test/check_bootstrap_contract.py`
### 执行批次 / 优先级
- 已完成：从 OMX-first 叙事切回 runtime-agnostic 的 agentwork 核心工作流
- 已完成：把 session 收敛为任务快照，把 Ralph 收敛为 `/exec` 的执行策略
- 已完成：把 optional tools 迁到 `.agentwork/tools/*`，把 upstream 映射收敛到 `.agentwork/upstreams/*`
- 已完成：补齐 source repo 原地 bootstrap 能力，并把它纳入 deterministic harness
- 下一批次：围绕具体新功能或改进点，在此基线上重新进入 `/brain` / `/plan`
### 执行策略（可选）
- standard
### 验证策略
- `python3 install-bootstrap.py -p .` 必须在 source repo 根目录成功执行
- `python3 test/run_deterministic.py` 必须覆盖 fresh install、existing reinstall、source repo self-install 三类场景
- `git diff --check` 保持通过；session 归档后再用 `.shared/scripts/session-review.sh` 对照改动清单
### 完成标准（可选）
- source repo 可以原地刷新核心 workflow 层
- 当前整仓改动可通过一份 session 快照直接恢复高价值上下文
- 后续在 `agentwork` 根目录里可以直接接着做下一轮 `/brain`、`/plan`、`/exec` 或 `/review`

## 关联工件（可选）
- `.agentwork/upstreams/superpowers.md`
- `.agentwork/upstreams/oh-my-codex-ralph.md`
- `.tmp/superpowers/`
- `.tmp/oh-my-codex/`
- `.tmp/harness/results/summary.json`

## 产出物（含提交锚点）
- 2026-04-15 00:49 | 文件: `.agent/rules/bootstrap.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agent/workflows/brain.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agent/workflows/commit.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agent/workflows/exec.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agent/workflows/plan.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agent/workflows/review.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agent/workflows/session.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/README.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/agent/rules/bootstrap.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/agent/workflows/brain.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/agent/workflows/commit.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/agent/workflows/exec.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/agent/workflows/plan.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/agent/workflows/review.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/agent/workflows/session.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/claude/CLAUDE.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/claude/commands/brain.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/claude/commands/commit.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/claude/commands/exec.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/claude/commands/plan.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/claude/commands/review.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/claude/commands/session.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/codex/skills/brain/SKILL.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/codex/skills/commit/SKILL.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/codex/skills/exec/SKILL.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/codex/skills/plan/SKILL.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/codex/skills/review/SKILL.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/codex/skills/session/SKILL.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/copilot/copilot-instructions.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/cursor/rules/agentwork-bootstrap.mdc` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/data/project-index.block.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/data/session-readme.block.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/render_bootstrap.py` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/root/AGENTS.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/bootstrap/spec.json` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/README.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/android/INSTALL.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/android/README.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/android/agent/workflows/android.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/android/claude/commands/android.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/android/codex/skills/android/SKILL.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/android/copilot/prompts/android.instructions.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/android/cursor/rules/android.mdc` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/android/shared/commands/android.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/android/shared/scripts/android-shell-pull-fallback.sh` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/android/tool.json` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/browser/INSTALL.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/browser/README.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/browser/agent/skills/browser/SKILL.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/browser/claude/skills/browser/SKILL.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/browser/codex/skills/browser/SKILL.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/browser/copilot/prompts/browser.instructions.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/browser/cursor/rules/browser.mdc` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/browser/shared/skills/browser/SKILL.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/browser/shared/skills/browser/scripts/browser-run.sh` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/browser/tool.json` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/figma/INSTALL.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/figma/README.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/figma/agent/workflows/figma.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/figma/claude/commands/figma.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/figma/codex/skills/figma/SKILL.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/figma/copilot/prompts/figma.instructions.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/figma/cursor/rules/figma.mdc` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/figma/shared/commands/figma.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/figma/shared/mcp/figma.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/figma/shared/scripts/figma-mcp-health-check.sh` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/figma/tool.json` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/godot/INSTALL.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/godot/README.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/godot/agent/workflows/godot.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/godot/codex/skills/godot/SKILL.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/godot/copilot/prompts/godot.instructions.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/godot/cursor/rules/godot.mdc` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/godot/shared/commands/godot.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/godot/tool.json` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/tools/registry.json` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/upstreams/README.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/upstreams/oh-my-codex-ralph.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.agentwork/upstreams/superpowers.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.claude/CLAUDE.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.claude/commands/brain.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.claude/commands/commit.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.claude/commands/exec.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.claude/commands/plan.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.claude/commands/review.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.claude/commands/session.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.cursor/rules/agentwork-bootstrap.mdc` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.github/copilot-instructions.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.gitignore` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/INDEX.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/commands/brain.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/commands/commit.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/commands/exec.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/commands/plan.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/commands/review.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/commands/session.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/constraints/coding-style.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/constraints/destructive-operations.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/constraints/placeholder-naming.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/patterns/platform-adapter.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/patterns/project-management.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/patterns/semantic-navigation.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/patterns/session-workflow.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/project/.gitkeep` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/project/agentwork.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/project/index.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/scripts/README.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/scripts/session-review.sh` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/session/.gitkeep` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/session/20260415-0049-agentwork-self-host-baseline.md` | 提交: - | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/session/README.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/templates/brain.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/templates/plan.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/templates/project.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/templates/ralph-context.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/templates/ralph-progress.json.example` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/templates/review.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `.shared/templates/session.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `AGENTS.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `install-bootstrap.py` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `install-tool.py` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `test/README.md` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `test/cases/brain_readme_intro.json` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `test/cases/exec_ralph_readme_intro.json` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `test/cases/exec_readme_intro.json` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `test/cases/plan_readme_intro.json` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `test/cases/review_readme_intro.json` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `test/cases/session_planning.json` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `test/check_bootstrap_contract.py` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `test/run_deterministic.py` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本
- 2026-04-15 00:49 | 文件: `test/run_real_cli.py` | 提交: 22a1b66 启用 agentwork 自承载工作流基线 | 验证: 工作区已记录当前版本

## 风险 / 阻塞
- 当前仓库仍没有正式 commit，所有“提交锚点”暂时只能写 `-`
- 根目录 bootstrap 产物已生成到工作区，但是否把这些产物作为 source repo 正式基线继续跟踪，仍需后续明确
- optional tools 已 source-managed，但 source repo 场景下的 tool self-install 目前只有人工 smoke / 手动审查，没有纳入 deterministic 自动评分

## 审查记录
### 2026-04-09 05:42
- 变更：完成 agent-work session vs OMX workflow 的深访与 ralplan 收敛，确认真正缺口不是 runtime resume，而是可被其他 AI 手动加载/接力的标准任务快照包
- 验证：对应深访 spec、PRD 与 test-spec 在 agentspace 侧完成审阅并批准
- 风险/待办：需要把结论从 research artifact 落到 agentwork 的 live docs，而不是停留在对比研究里

### 2026-04-12 13:55
- 变更：完成 session-core redesign，明确 session = 当前任务快照，不再引入额外 handoff core / session brain 层
- 验证：草案 `.shared` session artifacts 已落地到 research draft mirror，并与 guidance finding 对齐
- 风险/待办：live docs 仍需进一步去除旧 handoff-core 叙事

### 2026-04-13 04:43
- 变更：完成 live docs alignment、`.agentwork` source-maintenance 迁移、project single-entry 收敛与 Draft marker 清理
- 验证：stale handoff wording 清理通过，consistency marker check 与 `git diff --check` 均通过
- 风险/待办：还需要把 standalone `/brain` `/plan` `/exec` `/review`、Ralph policy、optional tools source layout 进一步统一到 live repo

### 2026-04-13 09:18
- 变更：完成 runtime-agnostic/source-repo refactor：standalone command artifacts、Ralph-on-exec、optional tools `.agentwork/tools/*`、upstream mapping、bootstrap source layout 与 repo 根目录入口脚本全部成形
- 验证：parser / script smoke、tool install `--list`/`--check`、session parser 兼容性与 diff check 均已通过
- 风险/待办：当时 source repo 还不能直接 `install-bootstrap.py -p .`，自承载链路缺最后一段

### 2026-04-15 00:49
- 变更：补齐 source repo 原地 bootstrap 能力；`install-bootstrap.py` 现在会跳过与 source 同路径的核心 `.shared` 文件，并新增 deterministic self-source 场景；同时把当前整仓工作反向总结为本 session
- 验证：`python3 install-bootstrap.py -p .` 通过，`python3 test/run_deterministic.py` 通过（fresh/existing/self-source 全绿），`git diff --check` 通过，`.shared/scripts/session-review.sh .shared/session/20260415-0049-agentwork-self-host-baseline.md` 对照通过（产出物=工作区改动=131）
- 提交锚点：业务基线已提交为 `22a1b66 启用 agentwork 自承载工作流基线`；本 session 文件自身因自引用无法预先写入最终提交 hash，保留 `提交: -`
- 风险/待办：决定 root installed wrappers 是否要纳入正式基线；若未来把 tool self-install 也当成 source repo 的第一类能力，需要补自动化回归
## 建议摘录到 Project（可选）
- 无；本轮已直接把稳定结论回填到 `.shared/project/agentwork.md`
