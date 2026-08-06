# Install Figma Tool

## What gets installed
- `.shared/commands/figma.md`
- `.shared/scripts/figma-desktop-mcp-check.sh`
- `.shared/mcp/figma.md`
- optional thin wrappers for Codex / Claude / Agent / Cursor / Copilot / OpenCode

## Install
```bash
python3 install-tool.py install figma -p <path>
python3 install-tool.py -i figma -p <path>
```

## Uninstall
```bash
python3 install-tool.py uninstall figma -p <path>
python3 install-tool.py -u figma -p <path>
```

## After install
- 按 `.shared/mcp/figma.md` 接入 Figma Desktop MCP
- 默认使用 desktop MCP：`http://127.0.0.1:3845/mcp`
- remote MCP `https://mcp.figma.com/mcp` 仅在 desktop 不可用或用户明确使用链接时作为 fallback
- MCP 连接与认证由客户端完成，命令集不包含 `/figma init`
- 先运行 `.shared/scripts/figma-desktop-mcp-check.sh http://127.0.0.1:3845/mcp` 检查本地连接，再用 `/figma focus` 或 `/figma read` 验证
- 若启用 remote fallback，再按客户端提示完成官方认证，并用 `/figma read [figma-target]` 验证链接读取
