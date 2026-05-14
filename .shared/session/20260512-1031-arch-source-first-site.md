# Session: arch source-first architecture site

> 创建: 2026-05-12 10:31
> 简述: 重构 arch 命令和 optional tool，使其成为 source-first 架构站工具

## 任务列表（按优先级）
- [x] 重写 `.shared/commands/arch.md`，明确最新 source-first 目录、事实源分层、review 入口、非目标，并删除旧 `diagram.arch.json` 主路径、`diagram.meta.json`、`diagrams/<slug>/`、`arch-html` 等过期表述。
- [x] 同步重写 `.shared/templates/arch/README.md`、`references/layout-best-practices.md`、`references/portal-workflow.md`，让模板文档只描述 `catalog.json + content/<version>/<item>/index.md + diagram.<source> + diagram.svg` 方案。
- [x] 重构 `.shared/scripts/arch-render.py` 为 source-first 静态站 renderer：输入改为 arch root / `catalog.json` / item 目录，校验 catalog、source、SVG 产物与相对链接，生成根 `index.html`、item `index.html` 和共享 CSS。
- [x] 更新 `.shared/templates/arch/page.html.tmpl` 与相关静态页面结构，使输出围绕导航、Markdown 说明、SVG 展示和源码引用组织。
- [x] 迁移 `.shared/templates/arch/examples/arch-tool/` 到新目录结构，替换旧 `diagram.arch.json` 示例为 `content/<version>/<item>/index.md`、文本图源、`diagram.svg` 和新的 `catalog.json`。
- [x] 迁移 `docs/architecture/` 到新结构，并重写 `README.md`、根导航和示例内容，确保 source repo 自身示例不再含旧字段和旧目录。
- [x] 同步 `.agentwork/tools/arch/README.md`、`INSTALL.md`、`shared/commands/arch.md`、`shared/scripts/arch-render.py`、`tool.json` 与各平台 wrapper，保证安装态描述和 source repo 主契约完全一致。
- [x] 清理过期内容：删除或替换 `arch` 相关示例、文档、模板和说明中的兼容讨论、过渡措辞、旧 schema、旧命令示例与失效验证命令。

## 已确认结论（工作快照）
### 目标
- 把 `/arch` 和相关工具整体切换到最新 source-first 静态架构站方案：HTML 负责导航、阅读和部署，Markdown 与文本图源保留为底层事实，SVG / HTML / CSS 只作为可再生成展示产物；不保留兼容层、过渡讨论和过期语义。

### 边界
- In Scope: `/arch` 主命令契约、`arch-render.py`、`arch` 模板与示例、optional tool 安装源、多平台 wrapper、source repo 自身 `docs/architecture/` 示例。
- Out of Scope: 自动兼容旧 `diagram.arch.json` 主路径、外部 SVG 生成后端、CI/部署脚本、非 `arch` 工作流文件。

### 约束
- 调研结论要求“静态目录可直接部署”优先，不引入 server、多层部署或重型前端栈作为默认依赖。
- `catalog.json` 承担站点、版本、导航、层级、交叉引用和追溯元数据，不用 HTML 表达结构事实。
- `content/<version>/<item>/index.md` 和 `diagram.mmd` / `diagram.puml` / `diagram.dot` 等文本图源是可 review 的事实源。
- `diagram.svg` 是发布展示产物，可由外部工具生成；renderer 默认只消费和校验，不内置图源到 SVG 的渲染后端。
- `index.html`、item `index.html`、`assets/arch.css` 是生成产物，不作为底层事实。
- 不保留旧 `diagram.arch.json` 主路径、`diagram.meta.json`、`arch-html` 语义、兼容说明和迁移期表述。
- 执行时不得改变 Git staged 区；arch 重构必须作为独立批次处理。

### 已选方案
- 采用 clean break 的 source-first 静态架构站：`catalog.json + content/<version>/<item>/index.md + diagram.<source> + diagram.svg` 为事实和发布资产，renderer 生成根 `index.html`、item `index.html` 与 `assets/arch.css` 供部署和阅读。
- 默认不保留旧结构兼容、过渡工件引用和“迁移中”语义；session、文档、模板和示例只保留最新方案。

### 推荐方案（待确认，可选）
- 无；当前方向已确认。

### 待确认问题（可选）
- 是否将 `.shared/session/20260512-1031-arch-source-first-site.md` 作为独立 `docs(session)` 批次提交。

### 核心定义 / 流程（可选）
- 推荐根目录：`docs/architecture/`
- 架构项目录：`content/<version>/<item>/`
- 说明事实源：`index.md`
- 图事实源：`diagram.mmd`、`diagram.puml`、`diagram.dot` 等
- 发布展示产物：`diagram.svg`
- HTML / CSS 产物：根 `index.html`、item `index.html`、`assets/arch.css`

## 计划摘要（可选）
> 来源：`.tmp/agentwork/plan/20260514-1157-arch-source-first-refactor.md`

### 关键文件 / 边界
- `.shared/commands/arch.md`
- `.shared/scripts/arch-render.py`
- `.shared/templates/arch/README.md`
- `.shared/templates/arch/page.html.tmpl`
- `.shared/templates/arch/references/layout-best-practices.md`
- `.shared/templates/arch/references/portal-workflow.md`
- `.shared/templates/arch/examples/arch-tool/*`
- `.agentwork/tools/arch/README.md`
- `.agentwork/tools/arch/INSTALL.md`
- `.agentwork/tools/arch/shared/commands/arch.md`
- `.agentwork/tools/arch/shared/scripts/arch-render.py`
- `.agentwork/tools/arch/tool.json`
- `.agentwork/tools/arch/{agent,claude,copilot,cursor}/...`
- `.codex/skills/arch/SKILL.md`
- `docs/architecture/README.md`
- `docs/architecture/*`
- 不修改 `.shared/session/*.md` 之外的 session 文件，不扩散到其他 optional tools 或 bootstrap 核心 workflow。

### 执行批次 / 优先级
- 第一批：重写 `/arch` 主命令与 reference/template 文档，清除旧 schema、旧主路径和过期术语。
- 第二批：重构 `arch-render.py` 为 source-first 静态站 renderer，并收口页面模板结构。
- 第三批：迁移 templates/examples 和 `docs/architecture/` 到新目录结构。
- 第四批：同步 optional tool source、wrappers、安装说明和 source repo 安装态描述。
- 第五批：统一清理过期内容并完成验证。

### 执行策略（可选）
- standard

### 验证策略
- `python3 .shared/scripts/agentwork-check.py plan .tmp/agentwork/plan/20260514-1157-arch-source-first-refactor.md`
- `python3 .shared/scripts/arch-render.py .shared/templates/arch/examples/arch-tool --check`
- `python3 .shared/scripts/arch-render.py .shared/templates/arch/examples/arch-tool`
- `python3 .shared/scripts/arch-render.py docs/architecture --check`
- `python3 .shared/scripts/arch-render.py docs/architecture`
- `git diff --check -- .shared/commands/arch.md .shared/scripts/arch-render.py .shared/templates/arch .agentwork/tools/arch .codex/skills/arch/SKILL.md docs/architecture`
- 人工复核 `rg -n "diagram\\.arch\\.json|diagram\\.meta\\.json|arch-html|diagrams/<|兼容|迁移旧|过渡"` 在 `arch` 相关范围内不再命中过期语义。

### 完成标准（可选）
- `/arch` 全套文档、脚本、模板、示例和 wrapper 只表达最新 source-first 静态站方案。
- `arch-render.py` 能在新 examples 和 `docs/architecture` 上完成 `--check` 与生成。
- `arch` 相关范围内不再残留旧主路径、兼容层或过期说明。

## 关联工件（可选）
- `.tmp/deep-research-report.md`
- `.tmp/agentwork/brain/20260514-1056-arch-source-first-refactor.md`
- `.tmp/agentwork/plan/20260514-1157-arch-source-first-refactor.md`
- `.tmp/arch-install-smoke/`

## 当前批次工作集（可选）
- 范围: `.shared/session/20260512-1031-arch-source-first-site.md` | 主题: 回填提交锚点并压缩 session 审查记录，使当前快照与已提交事实对齐

## 产出批次（提交锚点）
- 提交: `f81e8dc refactor(arch): 切换到 source-first 静态架构站` | 范围: `.shared/commands/arch.md`, `.shared/scripts/arch-render.py`, `.shared/scripts/arch-export-mermaid.py`, `.shared/templates/arch/`, `.agentwork/tools/arch/`, `.codex/skills/arch/SKILL.md`, `.shared/constraints/placeholder-naming.md`, `docs/architecture/`
- 提交: `-` | 范围: `.shared/session/20260512-1031-arch-source-first-site.md`（仅用于 session 文件自身这一笔）

## 风险 / 阻塞
- 当前无功能阻塞；工作区仅剩 session 文件自身待单独提交。
- Mermaid CLI helper 仍依赖本机可用浏览器；若目标环境没有 Chrome/Puppeteer 运行条件，需要单独补运行环境，而不是回退当前契约。
- 文本图源到 `diagram.svg` 的生成仍是外部 helper 流程；若后续希望进一步自动化，需要作为独立增强设计，不反向污染当前 renderer 职责。

## 审查记录
### 2026-05-12 10:31
- 变更：将当前讨论和 plan note 落为可恢复 session 快照，明确目标、边界、已选方案、计划摘要和当前批次工作集。
- 验证：尚未执行代码或文档改造；本次只创建 session 快照。
- 风险/待办：下一步需进入 `/session exec` 或 `$exec` 后再修改 arch 相关文件。

### 2026-05-14 12:01
- 变更：根据最新调研结论和用户确认，刷新 session 为 clean break 的 source-first 静态站方案；同步替换最新 brain/plan 工件，并移除兼容层、过渡讨论和过期引用。
- 验证：`session plan` 快照已更新，`.shared/scripts/agentwork-check.py session .shared/session/20260512-1031-arch-source-first-site.md --strict-flow` 通过。
- 风险/待办：下一步进入 `/session exec`，按最新 plan 直接重构 `/arch` 命令、renderer、模板、optional tool 与 `docs/architecture`。

### 2026-05-14 15:16
- 变更：完成 `/arch` clean break 重构，并按用户反馈持续收紧页面壳；主契约、renderer、模板参考、examples、`docs/architecture`、optional tool 包和平台 wrapper 已全部切到 source-first 结构，`docs/architecture` 改成中文电商业务架构站，页面去掉装饰性说明、重复标题和多余元信息。
- 验证：`python3 -m py_compile .shared/scripts/arch-render.py .shared/scripts/arch-export-mermaid.py .agentwork/tools/arch/shared/scripts/arch-render.py .agentwork/tools/arch/shared/scripts/arch-export-mermaid.py` 通过；source repo、shared example 与安装态 example 的 `arch-render --check` 和重生成通过；旧主路径、过期术语和演示式文案扫描无命中；`git diff --check` 通过。
- 风险/待办：`diagram.svg` 仍由外部 helper 生成，不并入 renderer；若后续要求更强自动化或统一主题，应单独设计生成链路。

### 2026-05-14 20:31
- 变更：将 source-first 静态架构站重构作为独立批次提交，提交锚点为 `f81e8dc refactor(arch): 切换到 source-first 静态架构站`；提交范围覆盖 `/arch` 契约、renderer、Mermaid 导出 helper、模板示例、optional tool 与 `docs/architecture`。
- 验证：提交前已完成 `py_compile`、source repo 与安装态 example 的 renderer `--check` / 重生成，以及 `git diff --check`；提交后 `git status --short` 仅剩当前 session 文件。
- 风险/待办：剩余工作只是在 session 文件自身中回填提交锚点并压缩审查记录，可按 `docs(session)` 独立处理。

### 2026-05-14 20:36
- 变更：执行 `/session review`，根据 `.shared/scripts/session-review.sh` 取证结果，把已提交路径从“当前批次工作集”移出，当前工作集收敛为 session 文件自身；同时回填 `f81e8dc` 并压缩审查记录。
- 验证：`bash .shared/scripts/session-review.sh .shared/session/20260512-1031-arch-source-first-site.md` 已指出旧工作集与当前工作区不一致；收敛后重新运行 `.shared/scripts/agentwork-check.py session .shared/session/20260512-1031-arch-source-first-site.md --strict-flow`。
- 风险/待办：若需要关闭本次任务，还需单独提交当前 session 文件。

## 建议摘录到 Project（可选）
- 无；当前仍属于本次 arch 重构任务上下文，完成后再判断是否沉淀长期项目事实。
