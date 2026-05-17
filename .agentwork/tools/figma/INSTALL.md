# Install Figma Tool

## What gets installed
- `.shared/commands/figma.md`
- `.shared/scripts/figma-desktop-mcp-check.sh`
- `.shared/mcp/figma.md`
- optional thin wrappers for Codex / Claude / Agent / Cursor / Copilot

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
- 按 `.shared/mcp/figma.md` 接入 Figma 官方 MCP
- 默认使用 remote MCP：`https://mcp.figma.com/mcp`
- desktop MCP `http://127.0.0.1:3845/mcp` 仅作为 fallback
- `init` 不再作为运行时 `/figma init` 子命令；初始化直接并入安装与客户端认证流程
- remote 路径建议用 `/figma read [figma-target]` 或 `/figma review [figma-target]` 验证
- 若启用 desktop fallback，可先运行 `.shared/scripts/figma-desktop-mcp-check.sh http://127.0.0.1:3845/mcp`，再用 `/figma focus` 验证
