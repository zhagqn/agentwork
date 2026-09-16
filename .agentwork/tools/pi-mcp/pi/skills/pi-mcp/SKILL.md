---
name: pi-mcp
description: Enable and inspect the optional project-scoped Pi MCP client.
---
# Pi MCP

This optional tool is Pi-only. Other agents and the core bootstrap do not use it.

From the project root, after reviewing the third-party package:

```bash
.shared/scripts/pi-mcp-setup.sh
.shared/scripts/pi-mcp-check.sh
```

`setup` runs `pi install -l --approve npm:pi-mcp-extension@1.5.0` (one-time trust for this install command), so the package is recorded in project `.pi/settings.json` and installed under `.pi/npm/`. It does not modify `.pi/mcp.json`; add MCP servers explicitly and keep credentials outside committed files. Pi project trust is required before project packages/extensions load.

The extension reads both global `~/.pi/agent/mcp.json` and project `.pi/mcp.json`; a project file does not clear global servers. Review that inheritance before enabling eager servers. The extension's server `env` values are literals; it does not interpolate shell variables.

Both scripts locate the project from their installed `.shared/scripts/` directory. `check` only reports CLI and file presence; it does not validate JSON, registration, loading, or connectivity. It does not print configuration values. Run `pi remove -l --approve npm:pi-mcp-extension@1.5.0` from the project root before removing this agentwork tool when the extension registration must also be removed. Keep user MCP configuration.

Pi 0.85.1 package installation and extension bridging were tested with `pi-mcp-extension@1.5.0` and the filesystem MCP server: the MCP tools appeared in Pi's public and active tool lists, and a tool call through Pi's public session definition succeeded. The pinned package version does not lock all transitive dependencies.
