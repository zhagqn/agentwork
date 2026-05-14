# Architecture Portal Workflow

本文件记录 `arch` tool 的导航页、catalog 和静态部署规则。目标是让多版本、多分组的架构文档可以稳定生成、独立部署并保持可追溯。

## 产物边界

- 工具生成的静态产物只有：根 `index.html`、item `index.html` 和 `assets/arch.css`
- 事实源是：`catalog.json`、`content/<version>/<item>/index.md`、`diagram.<source>`、`diagram.svg`
- 不内置 server、live reload、搜索、权限、托管预览或客户端 Mermaid 默认渲染
- 所有链接使用相对路径，保证整个站点目录可整体搬迁

## 根目录状态

执行 `/arch` 前先判断目标根目录：

| 状态 | 判断方式 | 默认动作 |
| --- | --- | --- |
| 已初始化站点 | 存在 `catalog.json` | 读取 catalog，更新 item source，并重新生成页面 |
| 全新目录 | 无 `catalog.json` 且无 `content/` | 创建 catalog、content 目录和首批 item |
| 部分内容目录 | 有 `content/` 但缺 `catalog.json` | 先补 catalog，再生成站点 |

## 目录结构

```text
docs/architecture/
├── catalog.json
├── index.html
├── assets/
│   └── arch.css
└── content/
    └── <version>/
        └── <item>/
            ├── index.md
            ├── diagram.mmd | diagram.puml | diagram.dot
            ├── diagram.svg
            └── index.html
```

每个 item 目录只放实际需要的文件：

- `index.md`：面向阅读和评审的说明文档
- `diagram.<source>`：文本图源，默认保留一种
- `diagram.svg`：稳定的展示产物
- `index.html`：renderer 生成的阅读页

## Catalog 规则

`catalog.json` 是站点事实源，页面和资源路径由固定目录结构推导。

最小结构：

```json
{
  "version": 2,
  "site": {
    "id": "project-architecture",
    "title": "Project Architecture",
    "summary": "Static architecture documentation.",
    "default_version": "current"
  },
  "versions": [],
  "items": []
}
```

版本条目推荐字段：

```json
{
  "id": "current",
  "label": "当前版本",
  "summary": "Working copy",
  "order": 10
}
```

item 条目推荐字段：

```json
{
  "id": "renderer-runtime",
  "version": "current",
  "title": "Renderer Runtime",
  "group": "Runtime",
  "summary": "Catalog validation, page generation, and static output.",
  "order": 20,
  "status": "draft",
  "tags": ["runtime"],
  "links": ["current/arch-tool-overview"],
  "source_commit": "-"
}
```

字段约束：

- `version` 固定为 `2`
- `versions[].id` 唯一，推荐 kebab-case
- `items[].id` 在同一 `version` 下唯一
- `items[].version` 必须引用存在的 version
- `items[].links[]` 使用 `version/id` 形式
- 页面路径、Markdown 路径、图源路径和 SVG 路径不写入 catalog，由目录结构推导

## 导航展示规则

- 根导航先按 version `order` 排序，再按 `group` 和 item `order` 排序
- 未填写 `group` 的 item 归到 `Ungrouped`
- 每个 item 卡片至少展示：标题、摘要、版本、图源类型、标签
- `links` 用于展示相关 item，不改变主导航分组

## 图源与 SVG 规则

- 每个 item 目录默认只有一种文本图源
- `diagram.svg` 必须存在，且用于正式页面展示
- 若需要重新生成 SVG，可由外部工具完成，再交给 renderer 统一生成页面

## 校验清单

- `catalog.json` JSON 语法有效
- version 和 item 引用闭环
- 每个 item 目录具备 `index.md`、一种文本图源、`diagram.svg`
- 所有相关链接都在 arch root 内部
- 根导航来自 catalog，而不是手写 HTML
- item 页面来自 source，而不是手写结构事实

推荐命令：

```bash
python3 .shared/scripts/arch-render.py docs/architecture --check
python3 .shared/scripts/arch-render.py docs/architecture
```
