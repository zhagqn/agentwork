# /figma [subcommand] [args]

Figma 设计读取与分析命令（手动触发）。

> 定位：只做“读取设计 + 分析 + brief/review”，直接利用 Figma 官方 MCP 与模型能力，不在命令层重复实现复杂工作流，也不默认直接产出整页代码。

## 默认连接策略（desktop 优先）

- 默认使用 **Figma Desktop MCP server**：`http://127.0.0.1:3845/mcp`
- desktop MCP 默认使用 **selection-based**：
  - 在 Figma desktop app 中选中目标 frame / layer
  - 通过 `/figma focus|read|brief|review` 读取当前选区或对应 nodeId
- 官方 remote MCP `https://mcp.figma.com/mcp` 仅作为 fallback。
- 仅在 desktop MCP 不可用、当前环境无法运行 Figma desktop app，或用户明确提供 Figma 链接时，使用 remote 的 link-based 流程。

## 安装前提

- `figma` 是 optional tool，不属于 bootstrap 默认命令。
- 先安装本 tool pack，再按 `.shared/mcp/figma.md` 接入 desktop MCP。
- MCP 连接与认证由安装后的客户端配置完成，命令集不包含 `/figma init`。

## 触发约束（必须遵守）

- 仅在用户**显式输入** `/figma ...` 时执行；禁止自动触发。
- 默认输出设计摘要、实现建议或审查结论，不直接生成完整页面代码。
- 优先复用 Figma MCP 已提供的信息：节点结构、设计上下文、截图、变量/样式。
- desktop MCP 为主时，优先读取用户在 Figma desktop app 中的当前选区，避免要求用户重复复制链接。
- desktop 不可用或用户明确提供链接时，才切换到 remote MCP。
- 若需要落盘截图、节点上下文或简报文件，默认写入 `[figma-artifact-root]`，建议使用 `.tmp/figma`。

## 子命令

| 子命令                  | 作用                                 | 示例                    |
| ----------------------- | ------------------------------------ | ----------------------- |
| （无）                  | 快速读取一个设计目标并输出摘要       | `/figma`                |
| `focus`                 | 查看 desktop MCP 当前选区             | `/figma focus`          |
| `read [figma-target]`   | 读取节点上下文与截图                 | `/figma read`           |
| `brief [figma-target]`  | 生成实现简报（非代码）               | `/figma brief`          |
| `review [figma-target]` | 审查设计一致性、实现风险与待确认事项 | `/figma review`         |

---

## /figma（无参数）

快速读取一个设计目标并输出“可落地摘要”。

### 参数选择

- 默认通过 desktop MCP 读取当前选区。
- 若用户提供 nodeId，则通过 desktop MCP 读取对应节点。
- 仅当 desktop MCP 不可用或用户明确提供链接时，切换到 remote MCP。
- 若既没有选区、nodeId，也没有链接，优先提示用户在 Figma desktop app 中选中目标；无 desktop 环境时再提示提供 frame / layer 链接。

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

- `focus` 只使用 desktop MCP，并读取 Figma desktop app 当前选区。
- 若 desktop MCP 未连接或没有选区，先提示检查 desktop MCP 并选择目标；当前环境无法运行 desktop 时，再提示改用 `[figma-target]` 链接走 remote fallback。

### 输出要求

- 至少包含：`nodeId`、名称、类型、位置尺寸
- 多选时按列表输出，禁止自动合并
- 无选区时先提示用户在 desktop app 中选择目标；desktop 不可用时再提示切换到 link-based fallback

---

## /figma read [figma-target]

读取一个设计目标的完整上下文，作为 brief / review / 实现输入。

### 参数

- `[figma-target]` 可为：
  - desktop MCP nodeId
  - remote fallback 使用的 Figma frame / layer 链接
- 省略 `[figma-target]` 时读取 desktop 当前选区；显式参数优先使用 nodeId，链接用于 remote fallback。

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
- **desktop 优先**：默认使用 selection-based desktop 流程，通过当前选区或 nodeId 工作。
- **remote 兜底**：desktop 不可用或用户明确提供链接时，再走 link-based remote 流程。
- **临时产物收口**：截图、上下文、简报文件默认写入 `[figma-artifact-root]`。
- 占位符命名统一参考：`.shared/constraints/placeholder-naming.md`
