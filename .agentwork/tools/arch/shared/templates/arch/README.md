# Architecture Templates

该目录提供 `arch` tool 的最小模板与样例。

## 内容
- `page.html.tmpl`：静态 HTML 页面模板
- `examples/arch-tool/`：总览图 + 子图样例
- `references/layout-best-practices.md`：schema、布局、连线与 review 清单
- `references/portal-workflow.md`：导航页、catalog、图表关系与静态部署规则

## 推荐用法
- 新 arch root 默认创建 `docs/architecture/catalog.json`、导航 `index.html` 和 `diagrams/<diagram-slug>/`
- 新图默认使用 `layout.mode=auto`，通过 `groups`、`rank` 或连线关系表达布局意图
- 需要像素级精修时再为全部节点补 `x/y`，并可设置 `layout.mode=manual`
- 架构 / 流程主路径优先使用 `overview`、`topology`、`flow`
- 其他 Mermaid 类型作为参考型静态图登记到 catalog，不进入 arch renderer 主路径
- 生成图表后同步 upsert `catalog.json`，再重新生成导航页
- 通过 `.shared/scripts/arch-render.py docs/architecture --recursive` 渲染导航页和所有可识别图表
