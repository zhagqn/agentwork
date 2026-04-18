# Session: agentwork source repo 自承载基线

> 创建: 2026-04-15 00:49
> 简述: 反向收敛 agentwork 当前整仓改动，建立 source repo 可直接原地使用 agentwork 工作流的续作基线

## 任务列表（按优先级）
- [x] 以 `architecture` optional tool 作为当前最优先任务推进 MVP：采用 `diagram.arch.json` + `index.html` 的简约结构，支持总览图 + 子图，并通过页面跳转完成 drill-down
- [x] 在当前 session 下通过 `/exec` 落地 `.agentwork/tools/architecture/` 工具骨架、renderer、样例与 deterministic 安装/隔离回归
- [x] 在实现中补齐 architecture 关键小决策：保留可选 `/architecture review`、默认自动初始化、首轮使用绝对坐标、slug 仅推荐英文 kebab-case
- [x] 对 `architecture` tool 做一次 `/review`，并在当前项目中安装工具后以“当前工作流架构”为目标完成真实渲染测试
- [x] 确认 `architecture` tool 当前实现已基本满足需求；后续按 optional tool 并入 baseline，并保留当前项目内已安装 wrapper 与 `docs/architecture/` 作为自承载验证样例
- [x] 补强 `/brain` 的“澄清结果 + 方案对比 + 推荐决策”流程，并收敛 `session` / workflow / template 的重复定义，避免 session mode 与 standalone mode 行为漂移
- [ ] 在下一轮按 baseline 边界整理并提交 `architecture` tool 相关改动
- [ ] 决定是否将根目录 bootstrap 产物（`.claude/`、`.agent/`、`.cursor/`、`.github/`）纳入正式版本基线
- [ ] 若后续要把 source repo 自测扩到可选工具层，再补充 tool self-install / real-cli 回归策略
- [ ] 若后续仍发现 `/brain` 会绕过澄清或方案对比，再补 checklist 或 review 侧结构化校验

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
- session 不设置固定“当前阶段”字段；推进状态以任务列表、已确认结论、当前批次工作集与审查记录表达
- `/brain` 必须先显式产出“澄清结果 + 方案对比 + 推荐决策”，不能直接跳到“已选方案”或 `/plan`
- `/brain`、`/plan`、`/exec`、`/review` 必须支持 standalone 模式，临时工件统一落到 `.tmp/agentwork/*`
- Ralph 只作为 `/exec --ralph` / `/session exec --ralph` 的执行策略存在，不单独扩成平行主工作流
- source repo 原地 bootstrap 时必须跳过与 source 同路径的核心 `.shared` 文件，只刷新根目录适配层与 managed block
### 已选方案
- 采用“四层结构”维护仓库：`.shared/` = 核心 workflow contract，`.agentwork/bootstrap/` = 多 AI 薄封装 source，`.agentwork/tools/` = 可选工具 source，`.agentwork/upstreams/` = 上游方法论映射
- `/session` 只做任务快照和流程串联；真正的工作由 `/brain`、`/plan`、`/exec`、`/review` 完成
- `/brain` 作为 brain 流程的唯一完整规范；`/session brain` 与 `session-workflow` 只保留引用和 session-mode 额外约束，避免多处定义漂移
- source repo 自身通过 `python3 install-bootstrap.py -p .` 自刷新核心层，optional tools 仍保持按需安装
- 当前 live docs 已明确：handoff 不是新的核心层，session 才是当前任务的主快照
### 当前最优先续作
- 新增 optional tool：`architecture`
- 当前 MVP 采用 manifest-first 的简约结构：`diagram.arch.json` = 事实源，`index.html` = render output
- 每一层图单独产出一个 `index.html`，通过父子链接完成页面跳转；当前不做详情面板、浏览器内编辑或外部 DSL 兼容
- 当前目录约定：正式产物放 `docs/architecture/`，临时探索落到 `.tmp/architecture/`
- 当前默认使用系统字体栈，不内置字体 assets，不依赖 Google Fonts
- 当前对外使用方式收敛为单一 `/architecture` 入口，由自然语言驱动生成与后续调整
- 当前已落地：tool source、renderer、总览图 + 子图样例、deterministic render smoke
- 当前图面原则已收敛：主图/子图统一最小宽度 1480；`viewport.width` / `height` 表示最小画布，内容超出时由页面滚动承载；内容较少时优先收紧节点间距
- 当前 review 结论：`architecture` 已基本满足本轮自用需求，可继续按 optional tool 并入后续 baseline
### 核心定义 / 流程（可选）
- `.shared/commands/*`：核心动作定义（session / brain / plan / exec / review / commit）
- `.shared/patterns/*`：工作流边界、跨平台适配、project/session 分层、语义导航约束
- `.agentwork/bootstrap/*`、`.agentwork/tools/*`、`test/*`：source 生成层、可选工具层与 deterministic harness

## 计划摘要（可选）
### 关键文件 / 边界
- 当前 architecture 入口：`.agentwork/tools/architecture/`、`.agentwork/tools/registry.json`、`install-tool.py`
- 当前 architecture 执行面：`.agentwork/tools/architecture/shared/commands/architecture.md`、`.agentwork/tools/architecture/shared/scripts/architecture-render.py`
- 当前 source repo 约束入口：`AGENTS.md`、`.shared/INDEX.md`、`.shared/project/agentwork.md`
- 当前回归入口：`test/run_deterministic.py`、`test/check_bootstrap_contract.py`
### 执行批次 / 优先级
- 已完成：runtime-agnostic/self-host baseline、optional tool source、upstream mapping、deterministic self-source 回归
- 已完成当前最高优先级批次：`architecture` optional tool MVP 第一轮；已落工具骨架、`diagram.arch.json` schema v1、总览图 + 子图样例、静态 HTML renderer 与 deterministic render smoke
- 当前文档批次：补强 `/brain` 的澄清 / 方案对比约束，并把重复定义收敛到 `/brain` 主定义；当前工作区改动尚未提交
- 下一批次：按 baseline 边界整理并提交 `architecture` tool 相关改动；后续再评估是否补更细的坐标分组能力或 tool self-install / real-cli 回归
### 执行策略（可选）
- standard
### 验证策略
- `python3 install-tool.py -l`
- `python3 install-tool.py -i architecture -p <tmp-project>`
- `python3 install-tool.py -u architecture -p <tmp-project>`
- 对样例 `diagram.arch.json` 运行 `architecture-render.py`
- `python3 test/run_deterministic.py`
- `git diff --check`
### 完成标准（可选）
- `architecture` 已能作为 optional tool 被安装和卸载
- 至少存在 1 组总览图 + 子图样例，证明 drill-down 模式跑通
- 当前文档已明确 `docs/architecture/` 与 `.tmp/architecture/` 的分层约定，以及“source 优先、render output 次之”的边界
- 当前整仓改动可通过这份 session 快照直接恢复高价值上下文，并继续在本 session 下推进 `/exec` / `/review`

## 关联工件（可选）
- `.agentwork/upstreams/superpowers.md`
- `.agentwork/upstreams/oh-my-codex-ralph.md`
- `.tmp/superpowers/`
- `.tmp/oh-my-codex/`
- `.tmp/harness/results/summary.json`
- `.tmp/agentwork/brain/20260416-0011-architecture-tool.md`
- `.tmp/agentwork/plan/20260416-0950-architecture-tool.md`
- `docs/architecture/`

## 当前批次工作集（可选）
- `.shared/commands/brain.md`
- `.shared/commands/session.md`
- `.shared/patterns/session-workflow.md`
- `.shared/templates/brain.md`
- `.shared/session/20260415-0049-agentwork-self-host-baseline.md`

## 产出批次（提交锚点）
- 提交: `8b41c9e feat(self-host): 启用 agentwork 自承载工作流基线` | 范围: `.agentwork/bootstrap/`, `.agentwork/tools/`, `.agentwork/upstreams/`, `.agent/`, `.claude/`, `.cursor/`, `.github/`, `.shared/`, `.gitignore`, `install-tool.py`, `test/README.md`, `test/cases/`, `test/check_bootstrap_contract.py`, `test/run_real_cli.py`
- 提交: `19f2aa7 fix(bootstrap): 修复 self-install 的 source-root 引导文案` | 范围: `AGENTS.md`, `install-bootstrap.py`, `test/run_deterministic.py`
- 提交: `e7e2c8c refactor(session): 收敛 session 轻量产出格式` | 范围: `.agentwork/bootstrap/data/session-readme.block.md`, `.shared/commands/commit.md`, `.shared/commands/exec.md`, `.shared/commands/review.md`, `.shared/commands/session.md`, `.shared/scripts/README.md`, `.shared/scripts/session-review.sh`, `.shared/session/README.md`, `.shared/templates/session.md`
- 提交: `791b31a docs(session): 补充 session load 取证规则` | 范围: `.agentwork/bootstrap/data/session-readme.block.md`, `.shared/commands/session.md`, `.shared/patterns/session-workflow.md`, `.shared/session/README.md`
- 提交: `45bad97 docs(commit): 明确 session 自身锚点规则` | 范围: `.shared/commands/commit.md`, `.shared/session/README.md`
- 提交: `cf4efdd feat(architecture): 新增架构图 optional tool` | 范围: `.agentwork/tools/architecture/`, `.agentwork/tools/README.md`, `.agentwork/tools/registry.json`, `.agent/`, `.claude/`, `.cursor/`, `.github/prompts/architecture.instructions.md`, `.shared/commands/architecture.md`, `.shared/scripts/architecture-render.py`, `.shared/templates/architecture/`, `.shared/constraints/placeholder-naming.md`, `docs/architecture/`, `install-bootstrap.py`, `test/README.md`, `test/run_deterministic.py`
- 提交: `-` | 范围: `.shared/session/20260415-0049-agentwork-self-host-baseline.md`

## 风险 / 阻塞
- 当前仓库已建立提交历史，但 session 文件自身仍因自引用无法预先写入“最终那一次 session 提交”的 hash
- `architecture` 若过早把 schema、命令面或交互做大，会很快偏离“简约、自用、语言驱动”的当前边界
- `architecture` 当前允许 source 自带坐标且不内置字体 assets，意味着首轮图面质量会更依赖 prompt 与样例，而不是自动布局或视觉素材
- 当前已完成 `/review`，未发现阻断性实现问题；当前剩余主要是 baseline 提交边界，而不是实现缺口
- 根目录 bootstrap 产物已提交到仓库，但是否将这些产物长期视为 source repo 正式基线，仍需后续明确
- optional tools 已 source-managed，但 source repo 场景下的 tool self-install 目前只有人工 smoke / 手动审查，没有纳入 deterministic 自动评分
- 当前 `/brain` 约束已压回 live docs 与模板，但还没有脚本级 checklist 或 review 侧结构化校验；若 agent 行为仍不稳定，需要再补自动检查

## 审查记录
### 2026-04-19 00:13
- 变更：围绕 `/brain` 的执行约束做了一轮 live docs 收敛：补强“澄清结果 + 方案对比 + 推荐决策”的显式要求，更新 `brain` 模板，并把 `/session brain` 与 `session-workflow` 改为引用 `/brain` 这份单一完整规范；同时把本 session 的当前批次工作集切换为本轮实际修改的 5 个文件
- 验证：`.shared/scripts/session-review.sh .shared/session/20260415-0049-agentwork-self-host-baseline.md` 已对齐为 5 个当前批次文件与 5 个工作区改动，无未记录或过期条目；`git diff --check` 通过
- 风险/待办：当前 4 个 brain/session 相关文档已 staged，而 session 文件自身仍未 staged；若后续准备提交，需要决定是否把“文档收敛”与“session 记录”拆开提交；若 agent 仍绕过 `/brain` 流程，再补 checklist 或 review 侧结构化校验

### 2026-04-16 14:32
- 变更：移除 session 固定“当前阶段”字段，更新 session 模板、README、bootstrap data block 与 `/session` 文档，改为只通过任务列表、结论、当前批次工作集与审查记录表达推进状态；同时回填本轮 `architecture` 业务提交锚点 `cf4efdd`
- 验证：`.shared/scripts/session-review.sh .shared/session/20260415-0049-agentwork-self-host-baseline.md` 通过；`git diff --check` 通过
- 风险/待办：若未来需要更强结构化约束，可再单独定义 session 必填项校验；当前不再引入阶段枚举

### 2026-04-16 13:49
- 变更：完成 `architecture` tool 第二轮收敛，补齐“最小画布 + 内容超出时自动扩张 + 页面滚动承载”的 renderer 规则，修复 source repo 原地 bootstrap 会误扩散 optional tool `.shared` 子目录的问题；同时把当前工作流主图与子图统一为最小宽度 1480，并调整页面容器使 SVG 与外层边框对齐
- 验证：`python3 install-tool.py -l` 通过；`python3 .shared/scripts/architecture-render.py docs/architecture --recursive` 通过；`python3 test/run_deterministic.py` 通过；`git diff --check` 通过；source / installed 的 renderer、command、template 副本已确认同步
- review 结论：未发现阻断性实现问题；`architecture` 当前已基本满足本轮需求，决定作为 optional tool 后续并入 baseline；当前项目内已安装 wrapper 与 `docs/architecture/` 保留为 source repo 自承载验证样例

### 2026-04-16 10:30
- 变更：在当前项目中安装 `architecture` tool，新增 `.shared/commands/architecture.md`、`.shared/scripts/architecture-render.py`、对应多助手 wrapper，并以 `agentwork` 当前工作流架构为目标新增 `docs/architecture/diagram.arch.json` 与子图；随后用安装态 renderer 生成 `docs/architecture/index.html` 与 `docs/architecture/nodes/workflow-core/index.html`
- 验证：`python3 install-tool.py -i architecture -p .` 通过；`python3 .shared/scripts/architecture-render.py docs/architecture --recursive` 通过；root 页面已包含 `nodes/workflow-core/index.html` 链接，child 页面已包含 `../../index.html` breadcrumb；`git diff --check` 通过
- review 结论：未发现阻断性实现问题；当前剩余是仓库策略问题，而不是实现缺口，主要是是否提交 `architecture` tool MVP，以及是否把当前 source repo 内的安装态 wrapper 与 `docs/architecture/` 视为正式基线

### 2026-04-16 10:22
- 变更：完成 `architecture` optional tool MVP 第一轮实现，新增 tool source、shared command、`architecture-render.py`、总览图 + 子图样例、跨 AI wrapper，以及 deterministic `architecture_render_smoke`
- 验证：`python3 install-tool.py -l` 通过；`python3 .agentwork/tools/architecture/shared/scripts/architecture-render.py .agentwork/tools/architecture/shared/templates/architecture/examples/architecture-tool --recursive` 通过；`python3 test/run_deterministic.py` 通过；`git diff --check` 通过
- 风险/待办：下一步优先对当前实现做 `/review`，再决定是否提交；更复杂的自动布局、字体资源、自定义 DSL 兼容仍明确不在本轮范围

### 2026-04-16 10:10
- 变更：完成 `architecture` optional tool 的 brain + plan 收敛，并将其回写为本 session 的当前最优先任务；当前方案已锁定为 `diagram.arch.json` + `index.html`、总览图 + 子图、页面跳转式 drill-down、系统字体栈、语言驱动单入口
- 验证：已产出 `.tmp/agentwork/brain/20260416-0011-architecture-tool.md` 与 `.tmp/agentwork/plan/20260416-0950-architecture-tool.md`，并将关键结论同步回本 session
- 风险/待办：仍有少量 implementation-level 小决策待在 `/exec` 中按需要补齐，包括显式 `/architecture review` 是否保留、自动初始化规则、坐标字段边界与 slug 约束

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
- 验证：`python3 install-bootstrap.py -p .` 通过，`python3 test/run_deterministic.py` 通过（fresh/existing/self-source 全绿），`git diff --check` 通过；对应基线改动已归档到 `8b41c9e`
- 提交锚点：业务基线已提交为 `8b41c9e feat(self-host): 启用 agentwork 自承载工作流基线`；本 session 文件自身因自引用无法预先写入最终提交 hash，保留 `提交: -`
- 风险/待办：决定 root installed wrappers 是否要纳入正式基线；若未来把 tool self-install 也当成 source repo 的第一类能力，需要补自动化回归

### 2026-04-15 09:22
- 变更：修复原地 self-install 会把 source-root `AGENTS.md` 覆盖成 target-root 版本的问题；现在 self-install 会保留 source repo 引导文案，并把该约束纳入 deterministic harness
- 验证：`python3 install-bootstrap.py -p .` 通过且 `AGENTS.md` 保留 source-root 标记；`python3 test/run_deterministic.py` 继续全绿；`git diff --check` 通过
- 提交锚点：source-root 回归修复已提交为 `19f2aa7 fix(bootstrap): 修复 self-install 的 source-root 引导文案`
- 风险/待办：若后续还要让 source repo 支持更多“原地安装”变体，需要继续防止 source/target 文案或生成物互相覆盖

### 2026-04-15 16:07
- 变更：将 session 产出格式收敛为“当前批次工作集 + 产出批次（提交锚点）”；同步更新模板、`session-review.sh`、相关命令文档，并按新规范重构本 session
- 验证：`bash -n .shared/scripts/session-review.sh` 通过；`.shared/scripts/session-review.sh .shared/session/20260415-0049-agentwork-self-host-baseline.md` 能正确解析 1 个当前批次文件与 3 个已提交锚点；当前样例 session 已从逐文件锚点清单收敛为按批次归档
- 提交锚点：session 轻量格式收敛主体已提交为 `e7e2c8c refactor(session): 收敛 session 轻量产出格式`；本 session 文件自身保留 `提交: -`
- 风险/待办：若后续希望按目录范围自动展开或校验“产出批次”的覆盖面，需要额外定义范围语法；当前版本只把它当作轻量索引而非严格 manifest

### 2026-04-15 16:28
- 变更：补充 session 自身提交锚点的实践规则，并明确 `/session load` 只恢复任务快照；需要精确实现、真实 diff 或提交边界时，继续读取实际文件并按需使用 git 取证
- 验证：`git diff --check` 通过；`python3 test/run_deterministic.py` 通过；新增规则已回填到 `.shared/commands/session.md`、`.shared/patterns/session-workflow.md`、`.shared/session/README.md` 与 bootstrap data block
- 提交锚点：load 取证规则已提交为 `791b31a docs(session): 补充 session load 取证规则`；本 session 文件自身保留 `提交: -`
- 风险/待办：当前只约束“需要时主动取证”，尚未把 `git show <commit>` / `git diff <commit>^!` 之类细化成固定模板，后续若发现 agent 行为仍不稳定再补

### 2026-04-15 16:30
- 变更：进一步明确 session 文件自身的锚点规则：允许“自身这一笔”继续保留 `提交: -`，不要求为了回填 session 自身再额外做第三次提交
- 验证：`.shared/commands/commit.md` 与 `.shared/session/README.md` 已同步补上该约束，规则与当前 session 轻量双提交实践一致
- 提交锚点：该规则已提交为 `45bad97 docs(commit): 明确 session 自身锚点规则`；本 session 文件自身仍保留 `提交: -`
- 风险/待办：若未来出现需要对 session 文件自身做严格可追溯闭环的场景，再单独设计不依赖第三次提交的标记方式

### 2026-04-15 16:43
- 变更：将本地未 push 的历史提交统一重写为 label 风格，并同步回填本 session 中引用到的提交 hash 与标题
- 验证：重写后 `git log --reverse --format='%h %s'` 已统一为 label 风格；当前 session 的提交锚点已同步为新 hash
- 提交锚点：本轮仅更新 session 记录；本 session 文件自身继续保留 `提交: -`
- 风险/待办：若后续继续重写更早历史或拆分旧提交，需要再次同步回填 session 中的提交锚点

## 建议摘录到 Project（可选）
- 无；本轮已直接把稳定结论回填到 `.shared/project/agentwork.md`
