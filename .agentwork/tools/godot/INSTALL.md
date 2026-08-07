# Install Godot Tool

## What gets installed
- `.shared/commands/godot.md`
- thin wrappers for Codex / Cursor / OpenCode

## Install
```bash
python3 install-tool.py install godot -p <path>
python3 install-tool.py -i godot -p <path>
```

## Uninstall
```bash
python3 install-tool.py uninstall godot -p <path>
python3 install-tool.py -u godot -p <path>
```

## After install
- ensure `godot` CLI is available
- run `/godot init`
- default outputs should land under `.tmp/godot/`
