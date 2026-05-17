# Figma MCP Reference

该文件是 Figma tool pack 的 source-side MCP 参考，供后续按需物化到目标项目。

## 默认路径：官方 remote MCP

- 默认使用 Figma 官方 remote MCP：`https://mcp.figma.com/mcp`
- desktop MCP 仅作为 fallback：`http://127.0.0.1:3845/mcp`
- remote 路径优先使用客户端官方安装 / 认证流程，不再把本地 shell health-check 当作主初始化方式

## 推荐接入流程

1. 安装 `figma` tool pack
2. 按当前客户端接入 Figma 官方 MCP
3. 完成官方认证
4. 用 `/figma read [figma-target]` 或 `/figma review [figma-target]` 做最小验收
5. 若需要 selection-based 工作流，再额外启用 desktop MCP，并用 `/figma focus` 验证

## Codex

### Preferred: Codex app plugin

- 在 Codex app 中打开 `Plugins`
- 安装 `Figma`
- 按客户端提示完成认证

### Manual

```bash
codex mcp add figma --url https://mcp.figma.com/mcp
```

完成后按提示认证。

## Claude Code

### Remote MCP

```bash
claude mcp add --transport http figma https://mcp.figma.com/mcp
```

完成后通过 `/mcp` 在 Claude Code 中完成认证与连通确认。

### Desktop fallback

```bash
claude mcp add --transport http figma-desktop http://127.0.0.1:3845/mcp
```

## Cursor

### Preferred: plugin

在 Cursor agent chat 中执行：

```text
/add-plugin figma
```

按客户端提示完成安装与认证。

### Desktop fallback

若只需要本地选区读取，可配置：

```json
{
  "mcpServers": {
    "figma-desktop": {
      "url": "http://127.0.0.1:3845/mcp"
    }
  }
}
```

## VS Code

### Remote MCP

```json
{
  "servers": {
    "figma": {
      "type": "http",
      "url": "https://mcp.figma.com/mcp"
    }
  }
}
```

### Desktop fallback

```json
{
  "servers": {
    "figma-desktop": {
      "type": "http",
      "url": "http://127.0.0.1:3845/mcp"
    }
  }
}
```

## 关于 desktop check 脚本

- `.shared/scripts/figma-desktop-mcp-check.sh` 仅用于 desktop MCP fallback 的本地 URL 连通性检查
- remote MCP 主路径依赖客户端内的官方认证与连接流程，不以 shell health-check 作为成功标准
- 其他 MCP 客户端按各自文档添加 HTTP server，URL 使用 `https://mcp.figma.com/mcp`
