# Install Architecture Tool

## What gets installed
- `.shared/commands/architecture.md`
- `.shared/scripts/architecture-render.py`
- `.shared/templates/architecture/`
- optional thin wrappers for Codex / Claude / Antigravity / Cursor / Copilot

## Install
```bash
python3 install-tool.py install architecture -p <path>
python3 install-tool.py -i architecture -p <path>
```

## Uninstall
```bash
python3 install-tool.py uninstall architecture -p <path>
python3 install-tool.py -u architecture -p <path>
```

## After install
- 正式产物默认放 `docs/architecture/`
- 临时草稿默认放 `.tmp/architecture/`
- 通过 `/architecture` 用自然语言生成或调整 `diagram.arch.json`
- 通过 `.shared/scripts/architecture-render.py` 渲染为 `index.html`
