# Arch 模板

该目录提供 `arch` tool 的最小模板与样例。

## 内容
- `page.html.tmpl`：静态页面外壳模板
- `examples/arch-tool/`：source-first 架构站样例
- `references/layout-best-practices.md`：Markdown、图源、SVG 与页面编排实践
- `references/mermaid-style-presets.md`：Mermaid 基础样式与可选参考风格
- `references/portal-workflow.md`：catalog、版本、分组、导航与静态部署规则

## 推荐用法
- 新 arch root 默认创建 `catalog.json`、`index.html`、`assets/arch.css` 和 `content/<version>/<item>/`
- 新 item 默认写 `index.md`、一种文本图源和对应 `diagram.svg`
- `index.md` 默认描述业务事实，不写“用于演示页面效果”“用于观察布局”之类的自述文案
- 若版本语义没有更强业务词，推荐使用 `mainline` / `scenario` 作为版本 id，并在页面上显示为“主线” / “场景”
- 若图源是 Mermaid，推荐先用 `.shared/scripts/arch-export-mermaid.py` 把 `diagram.mmd` 导出为 `diagram.svg`
- 若图源是 Mermaid，默认优先复用 `references/mermaid-style-presets.md` 中的 `editorial-base`
- 页面路径由 `version + id` 推导，不在 catalog 中重复维护
- 导航按 `version + group + order` 渲染，交叉引用使用 `links`
- 通过 `.shared/scripts/arch-render.py docs/architecture --check` 校验 catalog、source、SVG 与链接
- 通过 `.shared/scripts/arch-render.py docs/architecture` 生成静态页面和共享 CSS
