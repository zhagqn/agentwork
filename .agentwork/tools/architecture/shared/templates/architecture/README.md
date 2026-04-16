# Architecture Templates

该目录提供 `architecture` tool 的最小模板与样例。

## 内容
- `page.html.tmpl`：静态 HTML 页面模板
- `examples/architecture-tool/`：总览图 + 子图样例

## 推荐用法
- 参考样例结构创建 `docs/architecture/diagram.arch.json`
- 通过 `.shared/scripts/architecture-render.py docs/architecture --recursive` 生成 `index.html`
