# Renderer Runtime

这个 item 只关心 renderer 的职责边界。

## Validation

1. `catalog.json` 结构正确
2. 每个 item 目录具备 Markdown、图源和 SVG
3. 相关链接都留在 arch root 内

## Output

- 根 `index.html`
- item `index.html`
- `assets/arch.css`

## Non-goals

- 不把 `diagram.mmd` 自动渲染成 SVG
- 不维护前端搜索、筛选和脚本运行时
