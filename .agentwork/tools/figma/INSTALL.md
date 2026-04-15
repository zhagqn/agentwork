# Install Figma Tool

## What gets installed
- `.shared/commands/figma.md`
- `.shared/scripts/figma-mcp-health-check.sh`
- `.shared/mcp/figma.md`
- optional thin wrappers for Codex / Claude / Antigravity

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
- configure project-level Figma MCP according to `.shared/mcp/figma.md`
- validate with `/figma focus`
