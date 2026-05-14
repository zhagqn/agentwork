# Architecture Layout Best Practices

本文件记录 `arch` tool 在 source-first 静态架构站中的稳定实践。重点不在运行时布局算法，而在让 Markdown、文本图源、SVG 和页面产物保持清晰、一致、可验证。

## Skill / Tool 组织

- 入口保持短：入口说明只负责触发规则和主定义路径
- 详细规则下沉：catalog、导航、页面结构和 review 清单放在 template / references 中
- 示例要可执行：样例必须包含 `catalog.json`、`index.md`、文本图源、`diagram.svg`
- 脚本要可验证：renderer 既能生成页面，也要支持 `--check`

## Source 建模

- `catalog.json` 管版本、分组、顺序、交叉引用和追溯元数据
- `index.md` 只放面向读者的说明，不重复写 catalog 导航事实
- 每个 item 目录默认只保留一种文本图源，避免多个源文件并列漂移
- `diagram.svg` 视为稳定发布产物；若换主题或布局，可重新生成后再提交

## Markdown 与源码组织

- 标题和段落保持短而清晰，避免把 README 级长文塞进 item 页面
- 业务解释写在 `index.md`，不要把长说明硬塞进图节点文本
- 原始图源保留为可 review 文本，文件名固定为 `diagram.<source>`
- 若需要展示补充材料，优先放在 Markdown 列表或短代码块中，而不是扩展 catalog schema

## SVG 与页面展示

- `diagram.svg` 应为可直接内嵌的完整 SVG 文本，而不是依赖外部脚本二次渲染
- 页面默认内嵌 SVG，并保留原始文件链接，便于阅读和取证
- SVG 设计优先保证首屏可读，其次再考虑复杂视觉效果
- 移动端通过 `overflow:auto`、响应式容器和 `max-width:100%` 承载图宽

## Catalog 书写

- version 只描述长期并存的版本层，例如 `current`、`v1`
- `group` 用来表达导航聚合，而不是替代版本
- `order` 使用稀疏数字，预留插入空间
- `links` 只表达相关阅读路径，使用 `version/id` 形式
- `source_commit` 只写可追溯标识，不承担状态流转

## Review 清单

- `catalog.json` 能通过 `arch-render.py --check`
- 每个 item 目录都存在 `index.md`、文本图源和 `diagram.svg`
- Markdown、SVG、源码链接和相关项链接是否闭环
- 导航分组、排序和版本标记是否能独立表达站点结构
- 生成的 `index.html` 和 `assets/arch.css` 是否只来自 renderer
