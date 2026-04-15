#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
TOOLS_ROOT = ROOT / '.agentwork' / 'tools'
REGISTRY = TOOLS_ROOT / 'registry.json'
COMMANDS = {'install', 'uninstall', 'list'}


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


def build_tool_entries(project_root: Path, tool: dict) -> list[tuple[str, Path, Path]]:
    entries = []
    for entry in tool.get('entries', []):
        src = tool['tool_dir'] / entry['from']
        dst = project_root / entry['to']
        entries.append((entry['surface'], src, dst))
    return entries


def copy_entry(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dst.exists():
            if dst.is_symlink() or dst.is_file():
                dst.unlink()
            else:
                shutil.rmtree(dst)
        shutil.copytree(src, dst)
        return 'dir'
    shutil.copy2(src, dst)
    return 'file'


def remove_entry(dst: Path) -> str:
    if dst.is_symlink() or dst.is_file():
        dst.unlink()
        return 'file'
    if dst.is_dir():
        shutil.rmtree(dst)
        return 'dir'
    return 'missing'


def prune_empty_parents(path: Path, project_root: Path) -> None:
    current = path
    while current != project_root and current.exists():
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def resolve_action(raw_args: list[str], install_flag: bool, uninstall_flag: bool, list_flag: bool) -> tuple[str, list[str]]:
    if list_flag:
        if raw_args:
            raise SystemExit('list does not accept tool names')
        return 'list', []
    if install_flag:
        return 'install', raw_args
    if uninstall_flag:
        return 'uninstall', raw_args
    if not raw_args:
        raise SystemExit('command is required: install, uninstall, list, or use -i/-u/-l')
    action = raw_args[0]
    if action not in COMMANDS:
        raise SystemExit(f'unknown command: {raw_args[0]}')
    return action, raw_args[1:]


def main() -> int:
    parser = argparse.ArgumentParser(description='Manage optional tools from .agentwork/tools in a target project.')
    parser.add_argument('args', nargs='*', help='command + tool names; commands: install, uninstall, list')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-i', action='store_true', help='install one or more tools from positional tool names')
    group.add_argument('-u', action='store_true', help='uninstall one or more tools from positional tool names')
    group.add_argument('-l', action='store_true', help='list available tools')
    parser.add_argument('-p', '--project-root', help='target project root (required for install/uninstall)')
    args = parser.parse_args()
    registry = load_registry()
    action, raw_tool_names = resolve_action(args.args, args.i, args.u, args.l)

    if action == 'list':
        for tool in registry.get('tools', []):
            print(f"{tool['name']}\t{', '.join(tool.get('kind', []))}")
        return 0

    if not args.project_root:
        raise SystemExit('project root is required for install/uninstall')

    tool_names = normalize_tool_names(raw_tool_names)
    if not tool_names:
        raise SystemExit('at least one tool name is required for install/uninstall')

    project_root = Path(args.project_root).resolve()
    grouped = []
    for tool_name in tool_names:
        tool = find_tool(registry, tool_name)
        grouped.append((tool_name, build_tool_entries(project_root, tool)))

    if action == 'uninstall':
        print('== Uninstalling tools ==')
        for tool_name, entries in grouped:
            print(f'== Tool: {tool_name} ==')
            for surface, _, dst in sorted(entries, key=lambda item: len(item[2].parts), reverse=True):
                removed_kind = remove_entry(dst)
                if removed_kind == 'missing':
                    print(f'- [skip] {surface}: {target_rel(project_root, dst)} (missing)')
                    continue
                prune_empty_parents(dst.parent, project_root)
                print(f'- [remove-{removed_kind}] {surface}: {target_rel(project_root, dst)}')
        return 0

    print('== Installing tools ==')
    for tool_name, entries in grouped:
        print(f'== Tool: {tool_name} ==')
        for surface, src, dst in entries:
            copied_kind = copy_entry(src, dst)
            print(f'- [{copied_kind}:{surface}] {target_rel(project_root, dst)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
