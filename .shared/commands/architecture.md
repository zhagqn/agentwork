# /architecture [architecture-root] <architecture-task-desc>

架构图生成与调整命令（手动触发）。

> 定位：在项目内通过自然语言维护 `diagram.arch.json`，并渲染为可直接打开的 `index.html`。默认面向“自用、简约、可跳转”的静态架构图，不要求用户记多条子命令。

## 第一性原则（必须遵守）

1. source 优先：`diagram.arch.json` 是事实源，`index.html` 是 render output。
2. 结构优先：先明确节点、连线、子图，再讨论视觉细节。
3. 简约优先：首轮只做页面跳转式 drill-down，不引入编辑器、拖拽或重前端 runtime。
4. 项目内落盘优先：正式产物默认放 `docs/architecture/`，临时探索默认放 `.tmp/architecture/`。

## 输入规则

- `[architecture-root]` 可选；省略时默认使用：
  - `docs/architecture/`，若用户明确要求临时草稿则使用 `.tmp/architecture/`
- `<architecture-task-desc>` 必填，建议包含：
  - 目标：要生成还是要调整
  - 范围：根图、某个节点、还是某个子图
  - 约束：是否新增子图、是否保留现有布局、是否只改文案/连线

## 推荐表达（口语化）

- `/architecture 生成当前项目的总览架构图，并为 renderer 节点补一层子图`
- `/architecture docs/architecture 调整 API 节点位置，补一条到缓存层的连线`
- `/architecture .tmp/architecture 先画一个临时草图，只要总览图不要子图`

## 默认执行流程

1. 确认目标根目录；若不存在，可直接初始化最小目录结构
2. 读取或创建 `diagram.arch.json`
3. 按自然语言更新：
   - 节点
   - 连线
   - 摘要卡片
   - `children` 子图映射
4. 必要时补对应子图目录下的 `diagram.arch.json`
5. 通过 `.shared/scripts/architecture-render.py` 渲染为 `index.html`
6. 输出改动文件、渲染结果与仍待确认的问题

## 目录约定

### 正式产物

```text
docs/architecture/
├── diagram.arch.json
├── index.html
└── nodes/
    └── <slug>/
        ├── diagram.arch.json
        ├── index.html
        └── nodes/
```

### 临时产物

```text
.tmp/architecture/
├── diagram.arch.json
└── index.html
```

## `diagram.arch.json` 最小结构

```json
{
  "id": "overview",
  "title": "Project Architecture",
  "summary": "一句话摘要",
  "nodes": [
    {
      "id": "api",
      "label": "API",
      "kind": "backend",
      "x": 360,
      "y": 220,
      "w": 180,
      "h": 88,
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
      "path": "nodes/api"
    }
  ]
}
```

## 当前约束

- 坐标当前采用绝对定位；图表以自用和简约为前提，不强求自动布局
- `viewport.width` / `viewport.height` 视为最小画布值；内容超出时 renderer 自动扩张，页面容器通过滚动承载
- 内容较少时优先收紧节点间距，不为“撑满宽度”硬拉画布
- 默认使用系统字体栈，不依赖 Google Fonts，也不内置字体 assets
- 当前不兼容 Mermaid / C4 / Structurizr 等外部 DSL
- `children[].path` 推荐使用英文 kebab-case slug

## /architecture review [diagram-ref]

可选审查入口。用于在不改图的前提下，检查以下问题：

- 节点命名是否清晰
- 连线是否缺失或方向错误
- 子图链接是否闭环
- 文字是否溢出
- `diagram.arch.json` 与 `index.html` 是否明显失配

`[diagram-ref]` 可为目录路径或具体 `diagram.arch.json` 路径；省略时默认检查 `docs/architecture/diagram.arch.json`。
