# Figma Tool Pack

## 类型
- command
- MCP-backed optional tool

## 内容
- shared command definition
- figma desktop MCP check script
- Codex / Claude / Cursor / OpenCode 平台入口
- per-tool MCP config reference

## 何时物化
- 项目需要读取/审查 Figma 设计
- 需要 `/figma focus|read|brief|review`
- 需要接入 Figma 官方 MCP，并在当前项目中保留最小设计分析命令

## 使用边界
- `figma` 是 optional tool，不进入 bootstrap 默认命令
- 默认走 desktop MCP，通过当前选区或 nodeId 读取设计
- remote MCP 只在 desktop 不可用或用户明确提供 Figma 链接时作为 fallback
- MCP 接入由安装后配置与客户端认证流程完成，命令集不包含 `/figma init`
- 能力范围只覆盖设计读取与分析，不包含 write-to-canvas 或 code-to-canvas 工作流
