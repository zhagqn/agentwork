# /figma [subcommand] [args]

Figma 设计读取与分析命令（手动触发）。

> 定位：首版只做“读取设计 + 分析 + brief/review”，尽量直接利用 Figma 官方 MCP 与模型能力，不在命令层重复实现复杂工作流，也不默认直接产出整页代码。

## 默认连接策略（remote 优先）

- 默认使用 **Figma 官方 remote MCP server**。
- remote MCP 主地址：`https://mcp.figma.com/mcp`
- desktop MCP 仅作为 fallback：`http://127.0.0.1:3845/mcp`
- remote MCP 读取设计时，默认使用 **link-based**：
  - 复制 Figma frame / layer 链接
  - 把链接交给 `/figma read|brief|review`
- selection-based 只适用于 desktop MCP；不要把它当作首版默认主路径。

## 安装前提

- `figma` 是 optional tool，不属于 bootstrap 默认命令。
- 先安装本 tool pack，再按 `.shared/mcp/figma.md` 接入 MCP。
- 初始化不通过运行时 `/figma init` 完成，而是直接并入安装流程与客户端认证流程。

## 触发约束（必须遵守）

- 仅在用户**显式输入** `/figma ...` 时执行；禁止自动触发。
- 默认输出设计摘要、实现建议或审查结论，不直接生成完整页面代码。
- 首版优先复用 Figma MCP 已提供的信息：节点结构、设计上下文、截图、变量/样式。
- remote MCP 为主时，不要求用户先打开 desktop app 或先选中本地元素；能用链接就用链接。
- 若需要落盘截图、节点上下文或简报文件，默认写入 `[figma-artifact-root]`，建议使用 `.tmp/figma`。

## 子命令

| 子命令                  | 作用                                 | 示例                    |
| ----------------------- | ------------------------------------ | ----------------------- |
| （无）                  | 快速读取一个设计目标并输出摘要       | `/figma`                |
| `focus`                 | 查看 desktop MCP 当前选区（可选）    | `/figma focus`          |
| `read [figma-target]`   | 读取节点上下文与截图                 | `/figma read`           |
| `brief [figma-target]`  | 生成实现简报（非代码）               | `/figma brief`          |
| `review [figma-target]` | 审查设计一致性、实现风险与待确认事项 | `/figma review`         |

---

## /figma（无参数）

快速读取一个设计目标并输出“可落地摘要”。

### 参数选择

- 若当前已接入 desktop MCP 且用户正在本地选区上工作：默认读取当前选区。
- 否则优先要求或使用 `[figma-target]` 链接。
- 若既没有选区也没有链接，提示用户提供 frame / layer 链接。

### 执行流程

1. 先获取高层结构：`get_metadata`
2. 再获取设计上下文：`get_design_context`
3. 补截图：`get_screenshot`
4. 需要样式来源时，再补 `get_variable_defs`
5. 输出摘要（非代码）：
   - 设计目标
   - 信息层级
   - 视觉策略
   - 实施提醒

---

## /figma focus

查看 desktop MCP 的当前焦点元素。

### 适用边界

- 仅当用户已接入 desktop MCP，并且在 Figma desktop app 中有当前选区时，`focus` 才是主路径。
- 若当前是 remote MCP，或没有选区，则直接提示改用 `[figma-target]` 链接。

### 输出要求

- 至少包含：`nodeId`、名称、类型、位置尺寸
- 多选时按列表输出，禁止自动合并
- 无选区时明确提示切换到 link-based 流程

---

## /figma read [figma-target]

读取一个设计目标的完整上下文，作为后续 brief / review / 实现输入。

### 参数

- `[figma-target]` 可为：
  - Figma frame / layer 链接
  - desktop MCP 当前选区对应的 nodeId
- 首版推荐优先使用链接；nodeId 主要用于 desktop fallback。

### 执行规则

1. 先 `get_design_context`
2. 必须补 `get_screenshot` 做视觉对照
3. 需要变量或样式来源时，再调 `get_variable_defs`
4. 若节点过大或信息过多：先 `get_metadata` 拆子节点，再按需读取
5. 若需保存截图或节点 JSON，默认写入 `[figma-artifact-root]/screenshots/` 与 `[figma-artifact-root]/context/`

---

## /figma brief [figma-target]

生成“可实现但不绑定代码栈”的实现简报。

### 输出模板（建议固定）

1. **设计目标与场景**：这块设计要解决什么问题
2. **结构拆分建议**：建议按职责拆成哪些模块
3. **交互与状态**：默认 / 悬停 / 激活 / 禁用 / 异常；缺失项标“待确认”
4. **视觉策略**：色彩、层级、节奏、留白、对齐规则
5. **实现建议**：优先级、依赖、风险、验收要点

### 约束

- 禁止直接给出整段页面代码
- 允许给 token / 规格建议，但必须标明“建议值”或“待设计确认”

---

## /figma review [figma-target]

审查设计一致性与落地风险，优先发现问题而非直接实现。

### 检查清单（精简）

- 信息层级是否清晰
- 状态覆盖是否完整
- 视觉一致性是否稳定
- 是否存在明显可复用机会
- 是否存在文案溢出、多语言、极端尺寸、资源缺失等落地风险

### 输出格式

- 先列问题（按严重度）
- 再给修正建议（最小改动优先）
- 最后给“需设计师确认”的待办清单

---

## 通用最佳实践

- **先小后大**：先读目标局部节点，避免整页拉取导致上下文过大。
- **先结构后样式**：先确认信息架构与交互，再讨论视觉细节。
- **截图必对照**：读取上下文后总是补截图，降低误读概率。
- **变量缺失可接受**：当 `get_variable_defs` 为空时，先记录现状，再提出规范化建议。
- **remote 优先**：默认优先 link-based remote 流程。
- **desktop 兜底**：需要选区驱动或本地调试时，再走 `focus` / nodeId 路径。
- **临时产物收口**：截图、上下文、简报文件默认写入 `[figma-artifact-root]`。
- 占位符命名统一参考：`.shared/constraints/placeholder-naming.md`
