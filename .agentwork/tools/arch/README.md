# Arch Tool Pack

## 类型
- command

## 内容
- shared 架构图命令定义
- `catalog.json` + `diagrams/<slug>/` → 静态导航页与图表 HTML renderer
- 语义自动布局：`groups` / `rank` / 连线拓扑可替代手写坐标
- 正交连线、语义箭头配色与 `--check` 验证入口
- 样例模板（导航页 + 总览图 + 关联子图）
- references 布局实践与 portal workflow 文档
- Codex / Claude / Agent / Cursor / Copilot 平台入口

## 何时物化
- 项目需要通过自然语言生成或调整架构图
- 需要一个可独立部署的静态架构导航页
- 需要在项目内沉淀 `docs/architecture/` 约定

## 边界约束
- 默认通过 `/arch` 单一入口驱动
- 事实源为 `catalog.json`、`diagram.arch.json`、`diagram.mmd` 和 `diagram.meta.json`
- 生成结果为根导航 `index.html` 与各图表目录下的 `index.html`
- 默认推荐 `layout.mode=auto`；仅精修图表时使用手动 `x/y`
- `viewport.width/height` 表示最小画布，内容超出时依赖页面滚动查看
- 修改后优先用 renderer `--recursive --check` 检查 catalog、source 与静态输出引用
- 主路径图表类型为 `overview`、`topology`、`flow`；其他 Mermaid 类型仅作为参考图
- 只生成静态 HTML；不内置 server、live reload、搜索、权限或托管预览
- 旧产物不做自动兼容和迁移；旧产物需重新生成到新结构
