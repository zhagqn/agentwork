# Install Arch Tool

## What gets installed
- `.shared/commands/arch.md`
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
- 通过 `/arch` 用自然语言生成或调整 `catalog.json`、导航页和图表 source
- 新图写入 `diagrams/<diagram-slug>/`，并按 `parent_id` / `order` / 未归组规则合并进 catalog
- 新图优先使用 `layout.mode=auto`，用 `groups` / `rank` 表达结构；仅精修时补 `x/y`
- 架构 / 流程主路径优先使用 `overview`、`topology`、`flow`；其他 Mermaid 类型仅作为参考图
- 通过 `.shared/scripts/arch-render.py docs/architecture --recursive --check` 验证 catalog、source 与链接
- 通过 `.shared/scripts/arch-render.py docs/architecture --recursive` 生成静态 HTML
- 不内置 server、live reload、搜索、权限或托管预览
