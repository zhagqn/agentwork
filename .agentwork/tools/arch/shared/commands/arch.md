# /arch [arch-root] <arch-task-desc>

架构图生成与调整命令（手动触发）。

> 定位：在项目内通过自然语言生成和维护可独立部署的静态架构文档。默认由 agent 根据生成描述判断图表类型，并产出 `catalog.json` + 导航页 + 图表静态 HTML。

## 第一性原则（必须遵守）

1. 静态产物优先：工具只生成可独立部署的静态文件，不内置 server、live reload、搜索、权限或托管预览。
2. 导航优先：正式产物默认维护 `catalog.json` 和导航页；已有导航时新图按实际关系合并进去。
3. 首图即建站：目标根目录没有图表历史时，第一次生成图表必须同时初始化导航页和 `catalog.json`。
4. source 优先：`diagram.arch.json` / `diagram.mmd` / `diagram.meta.json` 是事实源，`index.html` 是 render output。
5. agent 判型优先：用户没有明确指定图表类型或显示维度时，由 agent 根据生成描述选择合适图表类型。
6. 边界清晰：只把适合架构和流程的图表纳入主路径；其他 Mermaid 类型仅作为参考型静态图表。

## 输入规则

- `[arch-root]` 可选；省略时默认使用：
  - `docs/architecture/`，若用户明确要求临时草稿则使用 `.tmp/architecture/`
- `<arch-task-desc>` 必填，建议包含：
  - 目标：要生成还是要调整
  - 范围：总览图、某个节点、某个子图、还是独立参考图
  - 关系：是否挂到某个父图、是否独立平铺、是否只做交叉引用
  - 约束：是否指定 Mermaid 类型、显示维度、输出方式、是否只改文案/连线

## 推荐表达（口语化）

- `/arch 生成当前项目的总览架构图，并为 renderer 节点补一层子图`
- `/arch 生成 renderer runtime 流程图，挂到 system-overview 下`
- `/arch 生成一个独立的数据模型图，放到导航页未归组区域`
- `/arch .tmp/architecture 先画一个临时草图，并生成导航页`

## 默认执行流程

1. 确认目标根目录；若不存在，可直接初始化
2. 检测导航状态：
   - 有 `catalog.json`：读取并把新图合并到现有导航
   - 无 `catalog.json` 且无图表历史：生成首图并初始化导航
   - 有旧式根目录图表但无 `catalog.json`：不做兼容迁移；需要时重新生成到新结构
3. 根据用户描述判断图表类型、source 类型和渲染方式
4. 写入对应图表目录 `diagrams/<diagram-slug>/`
5. 渲染该图表的 `index.html`
6. upsert `catalog.json` 条目，维护 `parent_id` / `order` / `links`
7. 重新生成根目录导航页 `index.html`
8. 运行 source、catalog、href 与静态输出检查
9. 输出改动文件、图表判型理由、导航合并结果与仍待确认的问题

## 目录约定

### 正式产物

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

### 临时产物

```text
.tmp/architecture/<arch-spike>/
├── index.html
├── catalog.json
└── diagrams/
```

每个图表目录只保留该图实际需要的 source 文件：

- 架构 HTML 图：`diagram.arch.json` + `index.html`
- Mermaid 原生参考图：`diagram.mmd` + `index.html`
- Mermaid 结构源转架构图：`diagram.mmd` + `diagram.meta.json` + `diagram.arch.json` + `index.html`

## 导航与 catalog 规则

- `catalog.json` 是导航事实源，根目录 `index.html` 是导航 render output。
- `parent_id` 表示父子关系；有父图的图表按 `order` 出现在父图下。
- 无 `parent_id` 且没有子图的图表作为未归组图表平铺在导航页。
- `links` 只表示交叉引用，不影响层级和排序。
- `order` 使用稀疏数字，默认按 `10`、`20`、`30` 预留插入空间。
- 新图生成时必须 upsert catalog；不得手改导航页来表达结构事实。

`catalog.json` 最小结构：

```json
{
  "version": 1,
  "site": {
    "id": "project-architecture",
    "title": "Project Architecture",
    "summary": "Static architecture documentation."
  },
  "diagrams": [
    {
      "id": "system-overview",
      "title": "System Overview",
      "type": "overview",
      "view": "arch-html",
      "href": "diagrams/system-overview/index.html",
      "summary": "System boundary and major components.",
      "order": 10,
      "status": "draft"
    }
  ]
}
```

详细 workflow 见 `.shared/templates/arch/references/portal-workflow.md`。

## 图表类型选择

默认由 agent 根据生成描述判型；用户明确指定图表类型、显示维度或输出方式时，以用户要求为准。

适合纳入 arch 主路径的类型：

- `overview`：系统总览、模块关系、边界关系；source 使用 `diagram.arch.json`
- `topology`：服务 / 资源 / 部署拓扑；Mermaid source 优先使用 `architecture-beta`
- `flow`：流程、管线、依赖 DAG；Mermaid source 优先使用 `flowchart LR/TB`

可作为静态参考图登记到导航，但不进入 arch renderer 主路径的 Mermaid 类型：

- 行为 / schema 参考：`sequenceDiagram`、`stateDiagram-v2`、`erDiagram`、`classDiagram`、`requirementDiagram`、`treeView-beta`
- 报告 / 规划 / 指标参考：`gantt`、`kanban`、`journey`、`timeline`、`pie`、`xychart`、`sankey`、`quadrantChart`、`mindmap`、`packet` 等

C4 / Structurizr / ZenUML 不作为默认主路径输入；需要时先作为 `.tmp` 调研或项目自定义扩展。

## `diagram.arch.json` 推荐结构

默认使用语义自动布局：LLM 只维护结构事实，renderer 负责排版。

```json
{
  "id": "overview",
  "title": "Project Architecture",
  "summary": "一句话摘要",
  "layout": {
    "mode": "auto",
    "direction": "lr"
  },
  "groups": [
    {
      "id": "entry",
      "label": "Entry",
      "kind": "actor",
      "node_ids": ["web"]
    },
    {
      "id": "service",
      "label": "Service",
      "kind": "backend",
      "node_ids": ["api"]
    }
  ],
  "nodes": [
    {
      "id": "web",
      "label": "Web",
      "kind": "frontend",
      "lines": ["用户入口"]
    },
    {
      "id": "api",
      "label": "API",
      "kind": "backend",
      "lines": ["FastAPI", "业务入口"]
    }
  ],
  "edges": [
    {
      "from": "web",
      "to": "api",
      "label": "HTTPS"
    }
  ],
  "cards": [
    {
      "title": "Runtime",
      "items": ["FastAPI", "PostgreSQL"]
    }
  ],
  "children": [
    {
      "node_id": "api",
      "path": "../api-detail"
    }
  ]
}
```

## 结构规范

- `layout.mode`：
  - `auto`：推荐默认；节点可省略 `x/y`，按 `groups`、`rank` 或连线拓扑自动排布
  - `manual`：精修模式；每个节点必须同时提供 `x` 和 `y`
- `layout.direction`：支持 `lr`（从左到右）和 `tb`（从上到下）
- `groups[]`：推荐用于 LLM 和开发者共同阅读；每个分组用 `node_ids` 明确包含哪些节点
- `nodes[].rank`：不想写 `groups` 时可用数字表达层级；适合线性流程或渲染器内部链路
- `nodes[].group` / `layer` / `lane`：可作为轻量分组字段；有 `groups[]` 时优先跟随 `groups[].node_ids`
- `edges[].flow`：可选，支持 `sync`、`data`、`read`、`write`、`control`、`async`、`event`、`dependency`，renderer 会给出稳定颜色 / 虚线风格
- `children[].path` 推荐使用相对路径；在标准 `diagrams/<slug>/` 结构中，兄弟子图通常写成 `../<child-slug>`

## 布局实践

- 详细布局规则见 `.shared/templates/arch/references/layout-best-practices.md`
- 导航、catalog 与静态部署规则见 `.shared/templates/arch/references/portal-workflow.md`
- renderer 默认使用正交连线，连线从节点边中点附近进出，避免连接到角落
- 连线标签带背景并尝试避开节点盒子；`edges[].flow` 会同步影响线条和箭头颜色
- 分组、连线、节点、连线标签按固定层级渲染，避免箭头压住文字或标签被节点遮挡
- 修改 source 后优先运行图表 source 检查和 catalog 检查

## 边界约束

- renderer 只负责从结构化 source 渲染静态 HTML，不把 `index.html` 作为事实源反向解析
- `viewport.width` / `viewport.height` 视为最小画布值；内容超出时 renderer 自动扩张，页面容器通过滚动承载
- 内容较少时优先收紧节点间距，不为“撑满宽度”硬拉画布
- 默认使用系统字体栈，不依赖 Google Fonts，也不内置字体 assets
- 只生成静态 HTML 文件；server、live reload、搜索、权限控制不纳入 `/arch` 范围
- 旧产物不做自动兼容和迁移；旧产物需通过 `/arch` 重新生成到新结构

## /arch review [diagram-ref]

可选审查入口。用于在不改图的前提下，检查以下问题：

- 节点命名是否清晰
- 连线是否缺失或方向错误
- 子图链接是否闭环
- 文字是否溢出
- `catalog.json` 中的 `id`、`parent_id`、`href`、`order` 是否有效
- 导航页是否由 catalog 生成，相关图和未归组图表是否归位
- `diagram.arch.json` 与 `index.html` 是否明显失配
- renderer `--check` 是否通过

`[diagram-ref]` 可为 arch root、图表目录或具体 source 文件；省略时默认检查 `docs/architecture`。
