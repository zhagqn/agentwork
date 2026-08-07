# Figma MCP Reference

该文件定义 Figma tool pack 的 MCP 接入方式与客户端配置边界。

## 默认路径：Figma Desktop MCP

- 默认使用 Figma Desktop MCP：`http://127.0.0.1:3845/mcp`
- 官方 remote MCP 仅作为 fallback：`https://mcp.figma.com/mcp`
- desktop 路径优先读取 Figma desktop app 当前选区或 nodeId，避免重复复制链接
- 仅在 desktop 不可用、当前环境无法运行 Figma desktop app，或用户明确提供链接时使用 remote 路径

## 推荐接入流程

1. 安装 `figma` tool pack
2. 在 Figma desktop app 中启用本地 MCP server
3. 按当前客户端接入 `http://127.0.0.1:3845/mcp`
4. 运行 `.shared/scripts/figma-desktop-mcp-check.sh http://127.0.0.1:3845/mcp` 检查本地连通性
5. 在 Figma 中选择目标节点，用 `/figma focus` 或 `/figma read` 做最小验收
6. 仅在需要 remote fallback 时，以 `figma-remote` 名称额外接入 `https://mcp.figma.com/mcp` 并完成官方认证

## Codex

### Preferred: Desktop MCP

```bash
codex mcp add figma --url http://127.0.0.1:3845/mcp
```

### Remote fallback

```bash
codex mcp add figma-remote --url https://mcp.figma.com/mcp
```

完成后按提示认证。

## Claude Code

### Preferred: Desktop MCP

```bash
claude mcp add --transport http figma http://127.0.0.1:3845/mcp
```

### Remote fallback

```bash
claude mcp add --transport http figma-remote https://mcp.figma.com/mcp
```

完成后通过 `/mcp` 在 Claude Code 中完成认证与连通确认。

## OpenCode

### Preferred: Desktop MCP

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "figma": {
      "type": "remote",
      "url": "http://127.0.0.1:3845/mcp",
      "enabled": true
    }
  }
}
```

> OpenCode 使用 `type: "remote"` 表示 HTTP transport；URL 仍指向本机 desktop MCP。

### Remote fallback

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "figma-remote": {
      "type": "remote",
      "url": "https://mcp.figma.com/mcp",
      "enabled": true
    }
  }
}
```

## Cursor

### Preferred: Desktop MCP

```json
{
  "mcpServers": {
    "figma": {
      "url": "http://127.0.0.1:3845/mcp"
    }
  }
}
```

### Remote fallback

```json
{
  "mcpServers": {
    "figma-remote": {
      "url": "https://mcp.figma.com/mcp"
    }
  }
}
```

## 关于 desktop check 脚本

- `.shared/scripts/figma-desktop-mcp-check.sh` 用于默认 desktop MCP 的本地 URL 连通性检查
- remote MCP fallback 依赖客户端内的官方认证与连接流程，不以 shell health-check 作为成功标准
- 其他 MCP 客户端默认添加 desktop HTTP server，URL 使用 `http://127.0.0.1:3845/mcp`
