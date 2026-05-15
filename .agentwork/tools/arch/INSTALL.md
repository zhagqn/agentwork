# Install Arch Tool

## What gets installed
- `.shared/commands/arch.md`
- `.shared/scripts/arch-export-mermaid.py`
- `.shared/scripts/arch-render.py`
- `.shared/templates/arch/`
- optional thin wrappers for Codex / Claude / Antigravity / Cursor / Copilot

## Install
```bash
python3 install-tool.py install arch -p <path>
python3 install-tool.py -i arch -p <path>
```

## Uninstall
```bash
python3 install-tool.py uninstall arch -p <path>
python3 install-tool.py -u arch -p <path>
```

## After install
- 正式产物默认放 `docs/architecture/`
- 临时草稿默认放 `.tmp/architecture/`
- 通过 `/arch` 用自然语言生成或调整 `catalog.json`、`content/<version>/<item>/` 下的 source 与 SVG
- 若图源是 Mermaid，先通过 `.shared/scripts/arch-export-mermaid.py docs/architecture` 刷新 `diagram.svg`
- renderer 负责生成根导航 `index.html`、item `index.html` 和 `assets/arch.css`
- `arch-export-mermaid.py` 和 `arch-render.py` 不要并行执行；否则页面可能吃到旧的 `diagram.svg`
- 先通过 `.shared/scripts/arch-render.py docs/architecture --check` 验证 catalog、source、SVG、链接与新鲜度
- 再通过 `.shared/scripts/arch-render.py docs/architecture` 生成静态页面
- 不内置 server、live reload、搜索、权限或托管预览
