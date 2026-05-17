# Figma Tool Pack

## 类型
- command
- MCP-backed optional tool

## 内容
- shared command definition
- figma desktop MCP check script
- Codex / Claude / Agent 平台入口
- per-tool MCP config reference

## 何时物化
- 项目需要读取/审查 Figma 设计
- 需要 `/figma focus|read|brief|review`
- 需要接入 Figma 官方 MCP，并在当前项目中保留最小设计分析命令

## 当前约束
- 仍是 optional tool，不进入 bootstrap 默认命令
- 默认走 remote MCP；desktop MCP 只用于 selection-based fallback
- 初始化并入安装流程，不保留运行时 `/figma init`
- 首版只覆盖读取/分析设计，不扩展到 write-to-canvas 或 code-to-canvas 工作流
