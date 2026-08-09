# Exa Tool Pack

## 类型

- MCP
- remote web and code research provider
- provisional optional tool with restricted routing；等待现行内容与路由 gate 验证

## 内容

- Exa MCP 接入参考
- 固定 `exa-mcp-server@3.4.0` 的项目级 STDIO wrapper
- 项目根 `.env` 中的 `EXA_API_KEY` 空占位

## 默认工具面

- `web_search_exa`
- `web_fetch_exa`

wrapper 不启用 `agent_run`、`web_search_advanced_exa` 或其他可选工具。

## 边界

- Node.js `>=20.0.0`
- 不自动修改平台 MCP 私有配置
- 不在命令参数或日志中传递、输出 API key
- 远程 provider 只用于允许发送到第三方的公开研究输入
- hosted MCP 可作为 OAuth 或限流匿名接入的替代方案
- 只在原生搜索难以发现公开资料或需要批量 fetch 时使用；已知官方 URL、官方 API/CLI 和本地资料仍优先
