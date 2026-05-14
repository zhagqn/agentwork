# /arch [arch-root] <arch-task-desc>

架构文档生成与调整命令（手动触发）。

> 定位：在项目内通过自然语言生成和维护可独立部署的 source-first 静态架构站。事实源是 `catalog.json`、Markdown 说明和文本图源，发布默认展示静态 `diagram.svg`，`index.html` 与 `assets/arch.css` 由 renderer 生成。

## 第一性原则（必须遵守）

1. source-first：`catalog.json`、`content/<version>/<item>/index.md` 和 `diagram.<source>` 是事实源，`diagram.svg`、`index.html`、`assets/arch.css` 是产物。
2. 静态部署优先：默认输出必须能被整个目录直接托管，不依赖 server、runtime 渲染、live reload、搜索、权限或托管预览。
3. 导航统一：站点导航、版本、分组、顺序和交叉引用只由 `catalog.json` 表达，不手改 HTML 表达结构事实。
4. SVG-first：线上默认展示 `diagram.svg`；客户端 Mermaid/JS 不作为默认主路径。
5. 简单契约优先：页面路径、原始文件路径和样式路径由固定目录结构推导，不在 catalog 里重复维护派生字段。

## 输入规则

- `[arch-root]` 可选；省略时默认使用：
  - `docs/architecture/`
  - 若用户明确要求临时草稿，则使用 `.tmp/architecture/`
- `<arch-task-desc>` 必填，建议至少包含：
  - 目标：生成新图、补文档，还是调整已有内容
  - 范围：总览、某个运行时流程、某个版本下的一组图，还是独立参考图
  - 约束：版本、分组、图源类型、是否只改文案、是否补充交叉引用
- 若没有更贴切的领域词，版本 id 推荐使用 `mainline` / `scenario`，页面展示标签可对应“主线” / “场景”。

## 推荐表达（口语化）

- `/arch 生成当前项目的总览架构站，并补两张关键流程图`
- `/arch 生成 payment runtime 流程图，放到主线版本的支付分组`
- `/arch .tmp/architecture 先画一个临时草图，输出可直接打开的静态目录`
- `/arch 只补 inventory-overview 的文档说明和 SVG，不改 catalog 分组`

## 默认执行流程

1. 确认目标根目录；若不存在，可直接初始化
2. 检查或创建 `catalog.json`
3. 根据任务描述确定版本、item id、分组和图源类型
4. 写入或更新 `content/<version>/<item>/index.md`、`diagram.<source>`、`diagram.svg`
5. upsert `catalog.json` 中对应 item 条目
6. 若图源是 Mermaid，优先通过 `.shared/scripts/arch-export-mermaid.py` 刷新 `diagram.svg`
7. 运行 renderer 生成根 `index.html`、item `index.html` 和 `assets/arch.css`
8. 运行 `--check` 验证 catalog、source、SVG 和链接
9. 输出改动文件、结构决策、仍待确认的问题

## 目录约定

### 正式产物

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

### 临时产物

```text
.tmp/architecture/
├── catalog.json
├── index.html
├── assets/
└── content/
```

每个 item 目录只保留该 item 必需的文件：

- `index.md`：说明事实源
- `diagram.mmd` / `diagram.puml` / `diagram.dot`：文本图事实源，默认只保留一种
- `diagram.svg`：发布展示产物
- `index.html`：renderer 生成的 item 页面

## Catalog 规则

- `catalog.json` 是站点事实源，页面路径由 `version + id` 推导。
- item 页面固定为：`content/<version>/<id>/index.html`
- 原始 Markdown 固定为：`content/<version>/<id>/index.md`
- 图源固定为：`content/<version>/<id>/diagram.<source>`
- SVG 固定为：`content/<version>/<id>/diagram.svg`
- 分组使用 `group`；排序使用 `order`；交叉引用使用 `links`
- `links` 使用 `version/id` 形式，避免跨版本歧义

`catalog.json` 最小结构：

```json
{
  "version": 2,
  "site": {
    "id": "project-architecture",
    "title": "项目架构站",
    "summary": "基于 source-first 契约维护的静态架构文档。",
    "default_version": "mainline"
  },
  "versions": [
    {
      "id": "mainline",
      "label": "主线",
      "order": 10
    }
  ],
  "items": [
    {
      "id": "system-overview",
      "version": "mainline",
      "title": "系统总览",
      "group": "平台",
      "summary": "展示系统边界和核心链路。",
      "order": 10,
      "status": "草稿",
      "tags": ["总览"],
      "links": ["mainline/runtime-flow"],
      "source_commit": "-"
    }
  ]
}
```

## 图源边界

默认主路径只维护适合静态架构站的文本图源：

- `diagram.mmd`：Mermaid
- `diagram.puml`：PlantUML
- `diagram.dot`：Graphviz DOT

`/arch` 的 renderer 默认职责仍然是维护 source、SVG 与静态页面，不把文本图源转成 SVG 的逻辑塞进页面运行时。

对 `diagram.mmd`，推荐用 Mermaid CLI 固定导出 `diagram.svg`：

```bash
python3 .shared/scripts/arch-export-mermaid.py docs/architecture
```

这样 Mermaid 预览与最终页面会共享同一份语义源，避免再靠手写 SVG 维持视觉。

## 页面与导航规则

- 根 `index.html` 展示站点摘要、版本分组、导航卡片和交叉引用入口
- item `index.html` 展示说明文档、内嵌 SVG、原始文件链接和源码预览
- `assets/arch.css` 为全站共享样式，由 renderer 统一生成
- 所有链接必须为相对路径，保证整个目录可搬迁

## 文案约束

- `index.md` 默认写业务事实：背景、职责、关键链路、边界、依赖、异常处理或运维关注点
- 文案必须与 `diagram.<source>` 的节点和连线语义一致，不写脱离图源的补充故事
- 不写“这张图用于演示”“观察页面效果”“验证滚动/样式/页面壳”这类自述式说明
- renderer、导出方式、模板结构和样式行为属于工具说明，不进入业务正文
- `mainline` 版本优先表达长期稳定结构；`scenario` 版本优先表达特定时段、角色、目标、指标和处置边界

## Review 入口

### `/arch review [diagram-ref]`

用于在不改图的前提下，检查以下问题：

- `catalog.json` 的版本、版本列表、item 列表和引用是否有效
- `content/<version>/<item>/` 是否同时具备 `index.md`、文本图源和 `diagram.svg`
- Markdown、SVG 和源码链接是否闭环
- 根导航是否按 `version + group + order` 正确生成
- item 页面是否由 source 渲染，而不是手写结构事实
- 交叉引用是否指向有效的 `version/id`
- renderer `--check` 是否通过

`[diagram-ref]` 可为 arch root、`catalog.json`、item 目录或 item 目录内的 source 文件；省略时默认检查 `docs/architecture`。

## 边界约束

- renderer 只负责校验和生成静态页面，不把 HTML 反向解析成事实源
- 默认不生成或维护前端脚本；若项目需要额外 JS，视为项目自定义扩展
- 默认不依赖任何特定 runtime；文本图源到 SVG 的生成由外部工具或人工流程负责
- 输出应适合桌面和移动端阅读；常规尺寸图按容器缩放，超宽 SVG 自动切换为横向滚动
