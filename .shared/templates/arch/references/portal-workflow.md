# Architecture Portal Workflow

本文件记录 `arch` tool 的导航页、catalog 和静态部署规则。目标是让多图表架构文档可以稳定生成、合并和独立部署。

## 产物边界

- 工具只生成静态文件：`index.html`、`catalog.json`、`diagrams/*`。
- 不内置 server、live reload、搜索、权限、托管预览。
- 任何部署方式都由宿主项目负责，例如 GitHub Pages、nginx、S3、内部文档站。
- 所有链接使用相对路径，保证整个 `docs/architecture/` 可整体搬迁。

## 根目录状态

执行 `/arch` 前先判断目标根目录：

| 状态 | 判断方式 | 默认动作 |
| --- | --- | --- |
| 已有导航 | 存在 `catalog.json` | 读取 catalog，并把新图 upsert 到导航 |
| 全新目录 | 无 `catalog.json`、无根 `diagram.arch.json`、无 `diagrams/*` | 生成首图，同时初始化 catalog 和导航页 |
| 旧产物 | 存在根 `diagram.arch.json` 但无 `catalog.json` | 不做兼容迁移；旧产物需重新生成到新结构 |
| 部分产物 | 有 `diagrams/*` 但无 `catalog.json` | 先生成或重建 catalog，再生成导航页 |

## 目录结构

```text
docs/architecture/
├── index.html
├── catalog.json
└── diagrams/
    └── <diagram-slug>/
        ├── index.html
        ├── diagram.arch.json
        ├── diagram.mmd
        └── diagram.meta.json
```

每个图表目录只放实际需要的 source：

- `diagram.arch.json`：结构化架构图 source
- `diagram.mmd`：Mermaid source
- `diagram.meta.json`：Mermaid 不能稳定表达的 renderer metadata
- `index.html`：该图表静态输出

## Catalog 规则

`catalog.json` 是导航事实源，根 `index.html` 只从 catalog 渲染。

最小结构：

```json
{
  "version": 1,
  "site": {
    "id": "project-architecture",
    "title": "Project Architecture",
    "summary": "Static architecture documentation."
  },
  "diagrams": []
}
```

图表条目推荐字段：

```json
{
  "id": "renderer-runtime",
  "parent_id": "system-overview",
  "title": "Renderer Runtime",
  "type": "flow",
  "view": "flowchart + arch-html",
  "href": "diagrams/renderer-runtime/index.html",
  "summary": "Source validation, layout, SVG generation, and HTML output.",
  "order": 20,
  "status": "draft",
  "tags": ["runtime"],
  "links": ["source-topology"]
}
```

字段约束：

- `id` 必须唯一，推荐 kebab-case。
- `href` 必须指向 arch root 内的相对路径。
- `parent_id` 必须引用已存在的 diagram id。
- `order` 使用稀疏数字，默认 `10`、`20`、`30`。
- `links` 只表达交叉引用，不改变层级。

## 导航展示规则

- 有 `parent_id` 的图表展示为父图下的关联子图。
- 关联子图按 `order` 升序排列，order 相同再按 `title`。
- 无 `parent_id` 且没有子图的图表展示为 standalone 卡片。
- 有 `links` 的图表可展示交叉引用，但不进入对方子树。

## 图表类型边界

主路径只支持架构和流程类：

- `overview`：系统总览，source 为 `diagram.arch.json`
- `topology`：服务、资源、部署拓扑，Mermaid source 可用 `architecture-beta`
- `flow`：流程、管线、依赖 DAG，Mermaid source 可用 `flowchart LR/TB`

其他 Mermaid 类型仅作为静态参考图登记到 catalog，不作为 arch renderer 的结构化 source。

## 校验清单

- `catalog.json` JSON 语法有效。
- 每个 `id` 唯一。
- 每个 `parent_id` 都存在。
- 不存在 parent cycle。
- 每个 `href` 都存在，且不跳出 arch root。
- standalone 集合符合“无 parent 且无 children”规则。
- 相关图排序稳定。
- 导航页由 catalog 生成，不手写结构事实。

推荐命令：

```bash
python3 .shared/scripts/arch-render.py docs/architecture --recursive --check
python3 .shared/scripts/arch-render.py docs/architecture --recursive
```
