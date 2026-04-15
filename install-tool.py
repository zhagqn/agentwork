#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
TOOLS_ROOT = ROOT / '.agentwork' / 'tools'
REGISTRY = TOOLS_ROOT / 'registry.json'


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding='utf-8'))


def find_tool(registry: dict, name: str) -> dict:
    for tool in registry.get('tools', []):
        if tool.get('name') == name:
            tool_dir = TOOLS_ROOT / tool['dir']
            tool_meta = json.loads((tool_dir / 'tool.json').read_text(encoding='utf-8'))
            return {**tool, **tool_meta, 'tool_dir': tool_dir}
    raise SystemExit(f'Unknown tool: {name}')


def normalize_tool_names(raw_names: list[str]) -> list[str]:
    names: list[str] = []
    for item in raw_names:
        for part in item.split(','):
            name = part.strip()
            if name and name not in names:
                names.append(name)
    return names


def target_rel(target: Path, path: Path) -> str:
    try:
        return str(path.relative_to(target))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description='Install one or more optional tools from .agentwork/tools into a target project.')
    parser.add_argument('tool_names', nargs='*', help='one or more tool names (space or comma separated)')
    parser.add_argument('--list', action='store_true', help='list available tools')
    parser.add_argument('-p', '--project-root', required=True, help='target project root (required)')
    args = parser.parse_args()
    registry = load_registry()
    if args.list:
        for tool in registry.get('tools', []):
            print(f"{tool['name']}\t{', '.join(tool.get('kind', []))}")
        return 0

    tool_names = normalize_tool_names(args.tool_names)
    if not tool_names:
        raise SystemExit('at least one tool name is required unless --list is used')

    project_root = Path(args.project_root).resolve()
    grouped = []
    for tool_name in tool_names:
        tool = find_tool(registry, tool_name)
        writes = []
        for entry in tool.get('entries', []):
            src = tool['tool_dir'] / entry['from']
            dst = project_root / entry['to']
            writes.append((entry['surface'], src, dst))
        grouped.append((tool_name, writes))

    print('== Installing tools ==')
    for tool_name, writes in grouped:
        print(f'== Tool: {tool_name} ==')
        for surface, src, dst in writes:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f'- [{surface}] {target_rel(project_root, dst)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
