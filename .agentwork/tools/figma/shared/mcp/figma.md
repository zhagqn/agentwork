# Figma MCP Reference

该文件是 Figma tool pack 的 source-side MCP 参考，供后续按需物化到目标项目。

## 推荐接入流程
1. 确认 Figma Desktop MCP URL（默认 `http://127.0.0.1:3845/mcp`）
2. 运行健康检查：
   ```bash
   .shared/scripts/figma-mcp-health-check.sh http://127.0.0.1:3845/mcp
   ```
3. 仅写入**项目级**配置，不默认写全局配置
4. 完成后用 `/figma focus` 验证

## Codex (`.codex/config.toml`)
```toml
[mcp_servers.figma]
url = "http://127.0.0.1:3845/mcp"
startup_timeout_sec = 30
enabled = true
```

## Claude (`.mcp.json`)
```json
{
  "mcpServers": {
    "figma": {
      "type": "http",
      "url": "http://127.0.0.1:3845/mcp"
    }
  }
}
```
