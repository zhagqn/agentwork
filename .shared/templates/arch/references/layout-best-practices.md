# Architecture Layout Best Practices

本文件记录 `arch` tool 的稳定绘图实践。目标不是复刻通用图表库，而是让 LLM 维护的 `diagram.arch.json` 更容易得到可读、可验证、可迭代的静态架构图。

## Skill / Tool 组织

- 入口保持短：入口说明只说明何时触发、读取哪个主定义、运行哪个脚本。
- 详细规则下沉：schema、布局、连线、审查清单放在 template / references 文档中，避免多个入口重复定义。
- 示例要可执行：样例必须包含 `diagram.arch.json`，并能通过 renderer 生成 `index.html`。
- 脚本要可验证：renderer 不只生成文件，也要提供不写文件的检查入口，供 review / CI / deterministic harness 使用。

## Source 建模

- `diagram.arch.json` 是事实源，`index.html` 只作为输出。
- 新图优先写语义结构：`nodes`、`groups`、`edges`、`cards`、`children`。
- 默认使用 `layout.mode=auto`；只有需要像素级精修时才切换到 `manual` 并补齐所有 `x/y`。
- 分层架构优先用 `groups[].node_ids` 表达阅读顺序；线性流程可用 `nodes[].rank`。
- `edges[].flow` 用语义类型表达连线含义，推荐值：`sync`、`data`、`read`、`write`、`control`、`async`、`event`、`dependency`。

## 布局与连线

- 节点之间保留稳定间距，避免为了撑满画布而拉大空白。
- 默认间距按“可读优先”的层级图基线处理：外边距 `64/72`、列间距 `96`、同组节点间距 `44`、分组内边距 `28/56`。
- 同组节点上下间距应接近节点高度的一半；三节点分组应仍能明显区分每个节点和连线标签。
- 连线默认采用正交路径，尽量从节点边中点附近进出，不连接到角落。
- 连线标签必须有背景，且优先避开节点盒子。
- 分组框先画，连线其次，节点再上层，连线标签最后画，保证层级清楚。
- 画布尺寸以内容为准自动扩张；`viewport.width/height` 只表示最小画布。

## 视觉规则

- 使用稳定的语义颜色，不为单个图临时扩展大量色值。
- 字体使用系统字体栈，避免依赖远程字体或额外 assets。
- 文案保持短句；节点详情放在 `lines`，大段说明放在 `cards`。
- 子图入口应有明确视觉提示；`children[].path` 使用英文 kebab-case slug。

## Review 清单

- `diagram.arch.json` 能通过 `arch-render.py --check`。
- `children` 指向的子图都存在，并可递归检查。
- 节点、分组、连线命名是否能独立表达结构事实。
- 连线方向是否符合请求、数据流或依赖方向。
- 生成的 `index.html` 只来自 source 渲染，不手改输出文件。
