# Architecture Tool Pack

## 类型
- command

## 内容
- shared 架构图命令定义
- 结构化 `diagram.arch.json` → `index.html` renderer
- 样例模板（总览图 + 子图）
- Codex / Claude / Agent / Cursor / Copilot 薄封装入口

## 何时物化
- 项目需要通过自然语言生成或调整架构图
- 需要总览图 + 子图的静态 drill-down
- 需要在项目内沉淀 `docs/architecture/` 约定

## 当前边界
- 默认通过 `/architecture` 单一入口驱动
- 事实源为 `diagram.arch.json`
- 生成结果为 `index.html`
- `viewport.width/height` 表示最小画布，内容超出时依赖页面滚动查看
- 首轮仅支持页面跳转式 drill-down，不做编辑器、拖拽和外部 DSL 兼容
