# Session: arch source-first architecture site

> 创建: 2026-05-12 10:31
> 简述: 重构 arch 命令和 optional tool，使其成为 source-first 架构站工具

## 任务列表（按优先级）
- [ ] 固化 `/arch` 新契约：HTML 作为导航、阅读和部署外壳，文本图源作为底层事实，SVG / HTML / CSS 作为可再生成展示产物。
- [ ] 重构 `arch-render.py` 为标准库静态站 renderer：校验 catalog/source/artifact 并生成根导航、item 页面和 CSS。
- [ ] 更新模板、示例和 source repo `docs/architecture/`，使它们使用 source-first 架构站目录。
- [ ] 同步 optional tool source 与跨助手 wrapper，保证安装态与 source 层一致。
- [ ] 更新 arch 安装态验证与 renderer 检查入口，并完成最小验证。

## 已确认结论（工作快照）
### 目标
- 将 `arch` 从结构化图 renderer 重构为 source-first 架构站工具：HTML 负责导航、阅读和部署，Mermaid / PlantUML / Graphviz 等文本源保留为底层事实，SVG / HTML / CSS 只作为可再生成展示产物。

### 边界
- In Scope: `/arch` 命令契约、arch optional tool 文档与 wrappers、renderer、模板样例、source repo `docs/architecture` 示例、安装态验证与 renderer 断言。
- Out of Scope: 引入 Node / Mermaid CLI / Graphviz / PlantUML / Kroki 作为默认依赖、启动服务、live reload、搜索、权限、CI 发布、自动从展示层反向修改源文件。

### 约束
- `catalog.json` 管站点、版本、导航、层级、交叉引用和追溯，不用 HTML 表达结构事实。
- `content/<version>/<item>/index.md` 和 `diagram.mmd` / `diagram.puml` / `diagram.dot` 等文本图源是可 review 的事实源。
- `diagram.svg` 是发布展示产物，可由外部工具生成；renderer 默认只消费和校验，不内置图源到 SVG 的渲染后端。
- `index.html`、item `index.html`、`assets/arch.css` 是生成产物，不作为底层事实。
- 执行时不得改变 Git staged 区；当前工作树已有其他无关改动，arch 重构必须按独立批次处理。

### 已选方案
- 采用 source-first architecture site：`catalog.json + content/<version>/<item>/index.md + diagram.<source> + diagram.svg` 为事实和发布资产，renderer 生成静态 HTML/CSS 供部署和阅读。
- 不采纳 `.tmp/arch-static-site-refactor-tracked.patch` 的整套字段和目录原样实现；只吸收 HTML 架构站、SVG-first、Markdown/Mermaid source、标准库 renderer 的可用思路。

### 推荐方案（待确认，可选）
- 无；当前方向已确认。

### 待确认问题（可选）
- 无；下一步可进入 `/session exec` 或 `$exec`。

### 核心定义 / 流程（可选）
- 推荐根目录：`docs/architecture/`
- 架构项目录：`content/<version>/<item>/`
- 说明事实源：`index.md`
- 图事实源：`diagram.mmd`、`diagram.puml`、`diagram.dot` 等
- 发布展示产物：`diagram.svg`
- HTML / CSS 产物：根 `index.html`、item `index.html`、`assets/arch.css`

## 计划摘要（可选）
> 来源：`.tmp/agentwork/plan/20260512-1029-arch-source-first-site.md`

### 关键文件 / 边界
- `.shared/commands/arch.md`：主命令契约，改为架构站 source-first 语义。
- `.shared/scripts/arch-render.py`：标准库 renderer，负责校验 catalog/source/artifact 并生成静态站。
- `.shared/templates/arch/`：新目录结构、示例、参考文档和页面/样式模板。
- `.agentwork/tools/arch/`：optional tool source，需要与 `.shared` 安装态保持一致。
- `.codex/skills/arch/SKILL.md`、`.agentwork/tools/arch/{claude,agent,cursor,copilot,codex}/`：平台入口同步新语义。
- `docs/architecture/`：source repo 自身示例，迁移为新架构站结构。
- `.shared/scripts/arch-render.py` 与安装文档：arch 的最小验证入口，不再依赖独立 harness。
- 不改变 staged 区；不混入当前工作树中其他无关改动。

### 执行批次 / 优先级
- 第一批：更新 `/arch` 主契约、reference 文档和 catalog v2 结构说明。
- 第二批：重构 renderer，保留标准库边界，支持 arch root / catalog 输入、check 和静态生成。
- 第三批：更新 templates/examples 与 `docs/architecture/` 示例，并生成 HTML/CSS。
- 第四批：同步 optional tool source、wrappers 和安装文档。
- 第五批：更新安装态验证说明，清理旧主路径术语并验证。

### 执行策略（可选）
- standard

### 验证策略
- `python3 .shared/scripts/arch-render.py .shared/templates/arch/examples/arch-tool --check`
- `python3 .shared/scripts/arch-render.py .shared/templates/arch/examples/arch-tool`
- `python3 .shared/scripts/arch-render.py docs/architecture --check`
- `python3 .shared/scripts/arch-render.py docs/architecture`
- 需要验证安装态时，使用 `python3 install-tool.py install arch -p <临时项目路径>` 后再运行 renderer `--check`。
- `git diff --check -- .shared/commands/arch.md .shared/scripts/arch-render.py .shared/templates/arch .agentwork/tools/arch docs/architecture .codex/skills/arch/SKILL.md`

### 完成标准（可选）
- `/arch` 文档和所有 wrappers 一致表达 source-first 架构站，而不是旧结构化图 renderer。
- 新样例和 `docs/architecture` 都能通过 renderer `--check` 并生成可直接部署的静态 HTML / CSS。
- Mermaid 图源保留为事实源，SVG / HTML / CSS 明确是产物；后续换展示层不需要修改底层图源。
- arch optional tool 安装到临时项目后，样例可通过 smoke check。

## 关联工件（可选）
- `.tmp/deep-research-report.md`
- `.tmp/arch-static-site-refactor-tracked.patch`
- `.tmp/agentwork/plan/20260512-1029-arch-source-first-site.md`

## 当前批次工作集（可选）
- 范围: `.shared/commands/arch.md` | 主题: 固化 source-first 架构站契约、目录结构、catalog v2、review 规则和边界约束
- 范围: `.shared/scripts/arch-render.py` | 主题: 重构标准库 renderer，校验 source/artifact 并生成静态站
- 范围: `.shared/templates/arch/` | 主题: 更新模板、样例和参考文档到 `content/<version>/<item>/` 结构
- 范围: `.agentwork/tools/arch/` | 主题: 同步 optional tool source、安装说明和跨助手 wrapper
- 范围: `.codex/skills/arch/SKILL.md` | 主题: 同步 Codex arch skill 的简述和入口约束
- 范围: `docs/architecture/` | 主题: 迁移 source repo 自身架构示例到 source-first 架构站

## 产出批次（提交锚点）
- 提交: `-` | 范围: `.shared/session/20260512-1031-arch-source-first-site.md`（仅用于 session 文件自身这一笔）

## 风险 / 阻塞
- 这是公共工具契约变更，执行前应按独立批次处理，不混入当前工作树已有 session/test 无关改动。
- 如果要求 SVG 必须存在，首图生成会依赖人工或外部工具先生成 SVG；这是刻意保持默认工具链简单的取舍。
- 如果后续希望 renderer 自动生成 SVG，需要作为可选增强单独设计，不能反向污染默认标准库主路径。

## 审查记录
### 2026-05-12 10:31
- 变更：将当前讨论和 plan note 落为可恢复 session 快照，明确目标、边界、已选方案、计划摘要和当前批次工作集。
- 验证：尚未执行代码或文档改造；本次只创建 session 快照。
- 风险/待办：下一步需进入 `/session exec` 或 `$exec` 后再修改 arch 相关文件。

## 建议摘录到 Project（可选）
- 无；当前仍属于本次 arch 重构任务上下文，完成后再判断是否沉淀长期项目事实。
