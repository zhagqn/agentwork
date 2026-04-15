# /godot [godot-project-path] <godot-task-desc>

Godot 自动化联调工作流命令（手动触发）。

> 定位：跨项目通用能力入口。默认通过“口语化任务描述”驱动执行，优先使用官方稳定能力（CLI/LSP/DAP），按需接入社区 MCP。

## 第一性原则（必须遵守）

1. 能力优先于工具：先定义“初始化、执行、取证、回退”能力，再绑定 provider。
2. 官方基座优先：默认优先 Godot CLI/LSP/DAP，可选叠加社区 MCP。
3. 取证优先：失败先保留运行日志、错误摘要、测试报告，再下结论。
4. 安全默认值：默认低风险动作；涉及批量改写/删除资产等高风险操作必须确认。

## 前置检查（按需启用）

- 模板默认不预置 Godot MCP。
- 若执行时 provider 不存在/不可用，先执行 `/godot init` 完成项目级配置，再继续 `/godot ...`。
- 命令语义面向 Godot 4.x；若项目版本较旧，先在 `init` 阶段记录兼容差异。

## 子命令（精简）

| 子命令 | 作用 | 示例 |
| --- | --- | --- |
| `init` | 初始化 Godot 工作流能力（一次性配置） | `/godot init` |
| （默认）`[godot-project-path] <godot-task-desc>` | 用口语化描述直接安排联调任务（推荐） | `/godot ./demo-game 验证启动到主菜单流程，失败时保留日志` |

---

## /godot init 是做什么的？

`/godot init` 的目标是“把执行环境准备好”，不是“执行业务联调”。

### 主要作用

1. 检查 `godot` 可执行文件与版本（建议记录 `godot --version`）
2. 识别项目路径（`project.godot` 所在目录）与默认 `[godot-project-path]`
3. 选择 provider 策略（`official-cli`、`mcp-stdio`、`mcp-http-plugin`）
4. 写入项目级配置（优先 `.codex/config.toml`、`.mcp.json`）
5. 做一次最小验收（`launch/run/log`）

### 通过标准

- 至少可执行 1 条稳定链路（推荐：官方 CLI）
- 能采集到最小证据（运行日志）
- 失败时具备回退路径（回退到官方 CLI/LSP/DAP）

---

## /godot [godot-project-path] <godot-task-desc>

用自然语言描述你想完成的 Godot 联调事项，助手负责拆解并执行。

### 输入规则

- `[godot-project-path]` 可选；省略时默认使用：
  - `GODOT_PROJECT_PATH` 环境变量，或
  - 当前目录（要求存在 `project.godot`）
- `<godot-task-desc>` 必填，建议包含：
  - 目标（验证什么）
  - 范围（场景/脚本/流程）
  - 约束（轮次、超时、证据类型）

### 推荐表达（口语化）

- `/godot 验证项目是否可启动并进入主场景，失败时保留日志`
- `/godot ./game 运行 headless 冒烟，并输出错误摘要`
- `/godot 检查玩家移动脚本改动后是否引入报错，附测试报告`

### 助手默认执行流程

1. 先做最小连通性检查（可执行文件、项目路径）
2. 按任务描述拆解步骤并串行执行
3. 自动采集关键证据（运行日志、错误摘要、测试报告），默认写入项目根 `.tmp/godot/`
4. provider 失败时自动回退到官方 CLI/LSP/DAP
5. 输出可复核结论（通过率、失败点、证据路径、下一步建议）

### 输出要求

- 给出任务理解摘要（1-3 行）
- 给出执行结果与证据路径
- 给出风险与下一步（如需）

---

## 推荐通用实践

- 日常默认使用 `/godot [godot-project-path] <godot-task-desc>`，减少子命令记忆成本。
- “先小范围冒烟，再扩展回归批次”，避免一次性大范围失败。
- 对社区 MCP 采用可插拔策略，避免绑定单实现。
- 临时产物默认写入项目根 `.tmp/`，Godot 任务固定在 `.tmp/godot/`。
- 占位符命名统一参考：`.shared/constraints/placeholder-naming.md`
