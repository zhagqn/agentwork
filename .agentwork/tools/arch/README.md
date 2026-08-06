# Arch Tool Pack

## 类型
- command

## 内容
- source-first 架构站命令定义
- `catalog.json` + `content/<version>/<item>/` → 静态导航页与 item 页面 renderer
- Mermaid CLI 导出 helper（把 `diagram.mmd` 刷新成 `diagram.svg`）
- Markdown 说明、文本图源、SVG 展示产物与共享 CSS
- `--check` 验证入口
- 样例模板与参考文档
- Codex / Claude / Agent / Cursor / Copilot / OpenCode 平台入口

## 何时物化
- 项目需要通过自然语言生成或调整静态架构文档站
- 需要一个可独立部署的 `docs/architecture/` 目录
- 需要把 Markdown、文本图源和 SVG 作为可 review 的事实源保留在仓库中

## 边界约束
- 默认通过 `/arch` 单一入口驱动
- 事实源为 `catalog.json`、`index.md`、`diagram.<source>` 和 `diagram.svg`
- 生成结果为根导航 `index.html`、item `index.html` 与 `assets/arch.css`
- 页面路径由 `version + id` 推导，不在 catalog 里重复维护 `href`
- 默认不内置前端脚本、server、live reload、搜索、权限或托管预览
- renderer 本身不承担文本图源到 SVG 的页面运行时渲染；对 Mermaid 源可通过独立 helper 统一导出
- Mermaid 导出与页面 render 必须串行；renderer 会在 `diagram.<source>` 新于 `diagram.svg` 时直接失败
- 修改后优先用 renderer `--check` 检查 catalog、source、SVG 与链接
