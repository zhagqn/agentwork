# Install Pi MCP Tool

## What gets installed

- `.pi/skills/pi-mcp/SKILL.md`: Pi-only usage and safety boundary
- `.shared/scripts/pi-mcp-setup.sh`: explicit project-scoped runtime setup
- `.shared/scripts/pi-mcp-check.sh`: read-only CLI and file-presence check

`install-tool.py` only distributes these files. It does not install Pi, the MCP
extension, an MCP server, or credentials, and it does not modify Pi settings.

## Install

```bash
python3 install-tool.py install pi-mcp -p <path>
```

After reviewing the project and the third-party package, explicitly install the
pinned extension from the target project:

```bash
<path>/.shared/scripts/pi-mcp-setup.sh
```

The setup script runs `pi install -l --approve npm:pi-mcp-extension@1.5.0`.
Pi writes the registration to the target project's
`.pi/settings.json` and installs package files under `.pi/npm/`. The one-run
`--approve` trusts project resources for this install command; it is not a
sandbox or tool-call approval.

Add servers yourself in `.pi/mcp.json`. The extension also reads global
`~/.pi/agent/mcp.json`, so a project file does not isolate or clear global
servers. Keep credentials out of committed configuration.

## Check

```bash
<path>/.shared/scripts/pi-mcp-check.sh
```

The check is read-only and reports only CLI, project config, and extension-file
presence. It does not prove JSON validity, package registration, extension
loading, server connectivity, or credentials.

## Uninstall

Runtime registration and agentwork-managed files have separate ownership. From
the target project, remove the runtime package first when it should no longer
load:

```bash
pi remove -l --approve npm:pi-mcp-extension@1.5.0
python3 <agentwork-source>/install-tool.py uninstall pi-mcp -p <path>
```

The second command removes only unchanged files recorded in the agentwork tool
receipt. It preserves user-owned `.pi/settings.json`, `.pi/mcp.json`, and
credentials. Removing only the agentwork tool files intentionally leaves an
already registered Pi package in place.

## Verified baseline

- Pi `0.85.1`
- `pi-mcp-extension@1.5.0`
- STDIO filesystem MCP discovery and a read-only tool call through Pi's public
  session tool definition

HTTP, SSE, and OAuth flows are outside this initial verification scope. The
pinned top-level package version does not fully pin fresh transitive dependency
resolution.
