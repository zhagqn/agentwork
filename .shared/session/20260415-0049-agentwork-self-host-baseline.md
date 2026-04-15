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
- 用一份 session 快照承接 source repo 的后续续作，而不必重新从零梳理上下文
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
- `.agentwork/bootstrap/*`、`.agentwork/tools/*`、`test/*`：source 生成层、可选工具层与 deterministic harness

## 计划摘要（可选）
### 关键文件 / 边界
- 自承载入口：`install-bootstrap.py`、`install-tool.py`
- 核心约束入口：`AGENTS.md`、`.shared/INDEX.md`、`.shared/project/agentwork.md`
- source 生成与验证：`.agentwork/bootstrap/spec.json`、`.agentwork/bootstrap/render_bootstrap.py`、`test/run_deterministic.py`
### 执行批次 / 优先级
- 已完成：runtime-agnostic/self-host baseline、optional tool source、upstream mapping、deterministic self-source 回归
- 下一批次：围绕具体新功能或改进点，在此基线上重新进入 `/brain` / `/plan`
### 执行策略（可选）
- standard
### 验证策略
- `python3 install-bootstrap.py -p .`
- `python3 test/run_deterministic.py`
- `git diff --check`
### 完成标准（可选）
- source repo 可以原地刷新核心 workflow 层
- 当前整仓改动可通过这份 session 快照直接恢复高价值上下文
- 后续在 `agentwork` 根目录里可以直接接着做下一轮 `/brain`、`/plan`、`/exec` 或 `/review`

## 关联工件（可选）
- `.agentwork/upstreams/superpowers.md`
- `.agentwork/upstreams/oh-my-codex-ralph.md`
- `.tmp/superpowers/`
- `.tmp/oh-my-codex/`
- `.tmp/harness/results/summary.json`

## 当前批次工作集（可选）
- `.shared/session/20260415-0049-agentwork-self-host-baseline.md`

## 产出批次（提交锚点）
- 提交: `22a1b66 启用 agentwork 自承载工作流基线` | 范围: `.agentwork/bootstrap/`, `.agentwork/tools/`, `.agentwork/upstreams/`, `.agent/`, `.claude/`, `.cursor/`, `.github/`, `.shared/`, `.gitignore`, `install-tool.py`, `test/README.md`, `test/cases/`, `test/check_bootstrap_contract.py`, `test/run_real_cli.py`
- 提交: `3733aa2 修复 self-install 的 source-root 引导文案` | 范围: `AGENTS.md`, `install-bootstrap.py`, `test/run_deterministic.py`
- 提交: `510f209 收敛 session 轻量产出格式` | 范围: `.agentwork/bootstrap/data/session-readme.block.md`, `.shared/commands/commit.md`, `.shared/commands/exec.md`, `.shared/commands/review.md`, `.shared/commands/session.md`, `.shared/scripts/README.md`, `.shared/scripts/session-review.sh`, `.shared/session/README.md`, `.shared/templates/session.md`
- 提交: `2fbaf62 补充 session load 取证规则` | 范围: `.agentwork/bootstrap/data/session-readme.block.md`, `.shared/commands/session.md`, `.shared/patterns/session-workflow.md`, `.shared/session/README.md`
- 提交: `-` | 范围: `.shared/session/20260415-0049-agentwork-self-host-baseline.md`

## 风险 / 阻塞
- 当前仓库已建立提交历史，但 session 文件自身仍因自引用无法预先写入“最终那一次 session 提交”的 hash
- 根目录 bootstrap 产物已提交到仓库，但是否将这些产物长期视为 source repo 正式基线，仍需后续明确
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
- 验证：`python3 install-bootstrap.py -p .` 通过，`python3 test/run_deterministic.py` 通过（fresh/existing/self-source 全绿），`git diff --check` 通过；对应基线改动已归档到 `22a1b66`
- 提交锚点：业务基线已提交为 `22a1b66 启用 agentwork 自承载工作流基线`；本 session 文件自身因自引用无法预先写入最终提交 hash，保留 `提交: -`
- 风险/待办：决定 root installed wrappers 是否要纳入正式基线；若未来把 tool self-install 也当成 source repo 的第一类能力，需要补自动化回归

### 2026-04-15 09:22
- 变更：修复原地 self-install 会把 source-root `AGENTS.md` 覆盖成 target-root 版本的问题；现在 self-install 会保留 source repo 引导文案，并把该约束纳入 deterministic harness
- 验证：`python3 install-bootstrap.py -p .` 通过且 `AGENTS.md` 保留 source-root 标记；`python3 test/run_deterministic.py` 继续全绿；`git diff --check` 通过
- 提交锚点：source-root 回归修复已提交为 `3733aa2 修复 self-install 的 source-root 引导文案`
- 风险/待办：若后续还要让 source repo 支持更多“原地安装”变体，需要继续防止 source/target 文案或生成物互相覆盖

### 2026-04-15 16:07
- 变更：将 session 产出格式收敛为“当前批次工作集 + 产出批次（提交锚点）”；同步更新模板、`session-review.sh`、相关命令文档，并按新规范重构本 session
- 验证：`bash -n .shared/scripts/session-review.sh` 通过；`.shared/scripts/session-review.sh .shared/session/20260415-0049-agentwork-self-host-baseline.md` 能正确解析 1 个当前批次文件与 3 个已提交锚点；当前样例 session 已从逐文件锚点清单收敛为按批次归档
- 提交锚点：session 轻量格式收敛主体已提交为 `510f209 收敛 session 轻量产出格式`；本 session 文件自身保留 `提交: -`
- 风险/待办：若后续希望按目录范围自动展开或校验“产出批次”的覆盖面，需要额外定义范围语法；当前版本只把它当作轻量索引而非严格 manifest

### 2026-04-15 16:28
- 变更：补充 session 自身提交锚点的实践规则，并明确 `/session load` 只恢复任务快照；需要精确实现、真实 diff 或提交边界时，继续读取实际文件并按需使用 git 取证
- 验证：`git diff --check` 通过；`python3 test/run_deterministic.py` 通过；新增规则已回填到 `.shared/commands/session.md`、`.shared/patterns/session-workflow.md`、`.shared/session/README.md` 与 bootstrap data block
- 提交锚点：load 取证规则已提交为 `2fbaf62 补充 session load 取证规则`；本 session 文件自身保留 `提交: -`
- 风险/待办：当前只约束“需要时主动取证”，尚未把 `git show <commit>` / `git diff <commit>^!` 之类细化成固定模板，后续若发现 agent 行为仍不稳定再补

## 建议摘录到 Project（可选）
- 无；本轮已直接把稳定结论回填到 `.shared/project/agentwork.md`
