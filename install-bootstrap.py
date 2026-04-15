#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BOOTSTRAP = ROOT / '.agentwork' / 'bootstrap'
DATA = BOOTSTRAP / 'data'
SHARED_ROOT = ROOT / '.shared'

BLOCK_TARGETS = [
    (Path('.shared/project/index.md'), DATA / 'project-index.block.md', '# Project 索引\n\n## 本项目自定义内容\n'),
    (Path('.shared/session/README.md'), DATA / 'session-readme.block.md', '# Session 目录说明\n\n## 本项目补充说明\n'),
]


def copy_file(src: Path, dst: Path) -> None:
    if src.resolve() == dst.resolve():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree(src: Path, dst: Path) -> None:
    if src.resolve() == dst.resolve():
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def refresh_generated_bootstrap() -> None:
    renderer = BOOTSTRAP / 'render_bootstrap.py'
    if renderer.exists():
        subprocess.run([sys.executable, str(renderer)], check=True)


def collect_core_shared_writes(target: Path):
    writes = []
    for src in sorted(x for x in SHARED_ROOT.rglob('*') if x.is_file()):
        rel = src.relative_to(SHARED_ROOT)
        if rel.parts and rel.parts[0] in {'project', 'session'}:
            continue
        writes.append((src, target / '.shared' / rel, 'file', 'core shared file'))
    return writes


def collect_writes(target: Path):
    writes = []
    writes.extend(collect_core_shared_writes(target))
    root_bootstrap = ROOT / 'AGENTS.md' if target.resolve() == ROOT.resolve() else BOOTSTRAP / 'root' / 'AGENTS.md'
    writes.append((root_bootstrap, target / 'AGENTS.md', 'file', 'root bootstrap file'))
    writes.append((BOOTSTRAP / 'claude' / 'CLAUDE.md', target / '.claude' / 'CLAUDE.md', 'file', 'Claude bootstrap file'))
    for src in sorted((BOOTSTRAP / 'claude' / 'commands').glob('*.md')):
        writes.append((src, target / '.claude' / 'commands' / src.name, 'file', 'Claude wrapper'))
    writes.append((BOOTSTRAP / 'agent' / 'rules' / 'bootstrap.md', target / '.agent' / 'rules' / 'bootstrap.md', 'file', 'Antigravity bootstrap file'))
    for src in sorted((BOOTSTRAP / 'agent' / 'workflows').glob('*.md')):
        writes.append((src, target / '.agent' / 'workflows' / src.name, 'file', 'Antigravity wrapper'))
    writes.append((BOOTSTRAP / 'cursor' / 'rules' / 'agentwork-bootstrap.mdc', target / '.cursor' / 'rules' / 'agentwork-bootstrap.mdc', 'file', 'Cursor rule'))
    for src in sorted((BOOTSTRAP / 'codex' / 'skills').iterdir()):
        if src.is_dir():
            writes.append((src, target / '.codex' / 'skills' / src.name, 'dir', 'Codex skill wrapper'))
    writes.append((BOOTSTRAP / 'copilot' / 'copilot-instructions.md', target / '.github' / 'copilot-instructions.md', 'file', 'Copilot repository instructions'))
    return writes


def parse_block(block_text: str):
    start_match = re.search(r'<!--\s*AGENTWORK:[^>]+:START\s*-->', block_text)
    end_match = re.search(r'<!--\s*AGENTWORK:[^>]+:END\s*-->', block_text)
    if not start_match or not end_match or start_match.start() >= end_match.start():
        raise SystemExit('bootstrap data block must contain one AGENTWORK START/END pair')
    return start_match.group(0), end_match.group(0), block_text[start_match.start():end_match.end()]


def upsert_block(target_file: Path, block_file: Path, default_scaffold: str) -> None:
    block_text = block_file.read_text(encoding='utf-8')
    start_marker, end_marker, block = parse_block(block_text)
    if target_file.exists():
        text = target_file.read_text(encoding='utf-8')
    else:
        text = default_scaffold.rstrip() + '\n\n'
    start_idx = text.find(start_marker)
    end_idx = text.find(end_marker)
    if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
        end_idx += len(end_marker)
        text = text[:start_idx] + block + text[end_idx:]
    else:
        if text and not text.endswith('\n'):
            text += '\n'
        text += block + '\n'
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(text, encoding='utf-8')


def update_managed_indexes(target: Path) -> None:
    (target / '.shared' / 'project').mkdir(parents=True, exist_ok=True)
    (target / '.shared' / 'session').mkdir(parents=True, exist_ok=True)
    for rel, block_file, scaffold in BLOCK_TARGETS:
        upsert_block(target / rel, block_file, scaffold)


def target_rel(target: Path, path: Path) -> str:
    try:
        return str(path.relative_to(target))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description='Install agentwork bootstrap into a target project, or refresh the source repo in place.')
    parser.add_argument('-p', '--project-root', required=True, help='target project root (required)')
    args = parser.parse_args()

    refresh_generated_bootstrap()
    target = Path(args.project_root).resolve()
    writes = collect_writes(target)

    print('== Installing bootstrap ==')
    for src, dst, kind, label in writes:
        if src.resolve() == dst.resolve():
            print(f'- [skip] {label}: {target_rel(target, dst)} (source==target)')
            continue
        if kind == 'dir':
            copy_tree(src, dst)
        else:
            copy_file(src, dst)
        print(f'- [{kind}] {label}: {target_rel(target, dst)}')
    print()
    print('== Updating managed data layer ==')
    update_managed_indexes(target)
    print('- refreshed managed project/session index blocks')
    print('- left existing local project/session files in place')
    print('- left existing installed tool files in place')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
