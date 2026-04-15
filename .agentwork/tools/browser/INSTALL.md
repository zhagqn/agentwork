# Install Browser Tool

## What gets installed
- `.shared/skills/browser/SKILL.md`
- `.shared/skills/browser/scripts/browser-run.sh`
- optional thin wrappers for Codex / Claude / Antigravity

## Install
```bash
python3 install-tool.py install browser -p <path>
python3 install-tool.py -i browser -p <path>
```

## Uninstall
```bash
python3 install-tool.py uninstall browser -p <path>
python3 install-tool.py -u browser -p <path>
```

## After install
- ensure `agent-browser` is available in the target environment
- browser outputs default to project `.tmp/browser`
