#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REQUIRED_FILES = [
    'AGENTS.md',
    '.shared/INDEX.md',
    '.shared/commands/session.md',
    '.shared/project/index.md',
    '.shared/session/README.md',
    '.claude/CLAUDE.md',
    '.agent/rules/bootstrap.md',
    '.cursor/rules/agentwork-bootstrap.mdc',
    '.github/copilot-instructions.md',
    '.codex/skills/session/SKILL.md',
]

CODEX_SKILLS = [
    '.codex/skills/brain/SKILL.md',
    '.codex/skills/plan/SKILL.md',
    '.codex/skills/exec/SKILL.md',
    '.codex/skills/review/SKILL.md',
    '.codex/skills/session/SKILL.md',
    '.codex/skills/commit/SKILL.md',
]

LEAK_PATTERNS = [
    'agentwork.md',
    '.agentwork/',
    'install-bootstrap.py',
    'install-tool.py',
    'source repo',
]

SKIP_DIRS = {'.git', '.tmp'}
PROJECT_START = '<!-- AGENTWORK:PROJECT-INDEX:START -->'
PROJECT_END = '<!-- AGENTWORK:PROJECT-INDEX:END -->'
SESSION_START = '<!-- AGENTWORK:SESSION-README:START -->'
SESSION_END = '<!-- AGENTWORK:SESSION-README:END -->'


def iter_text_files(root: Path):
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def main() -> int:
    if len(sys.argv) != 2:
        print('usage: check_bootstrap_contract.py <repo>', file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    failures: list[str] = []

    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            failures.append(f'missing:{rel}')

    for rel in CODEX_SKILLS:
        path = root / rel
        if not path.exists():
            failures.append(f'missing:{rel}')
            continue
        text = path.read_text(encoding='utf-8')
        if not text.startswith('---\n'):
            failures.append(f'codex_skill_missing_frontmatter:{rel}')

    project_index = root / '.shared/project/index.md'
    if not project_index.exists():
        failures.append('missing:.shared/project/index.md')
    else:
        text = project_index.read_text(encoding='utf-8')
        if PROJECT_START not in text or PROJECT_END not in text:
            failures.append('missing_project_index_block')
        if 'agentwork.md' in text:
            failures.append('project_index_leaks_agentwork_md')
        if (root / '.shared/project/local.md').exists() and 'LOCAL' not in (root / '.shared/project/local.md').read_text(encoding='utf-8'):
            failures.append('local_project_file_not_preserved')

    session_readme = root / '.shared/session/README.md'
    if not session_readme.exists():
        failures.append('missing:.shared/session/README.md')
    else:
        text = session_readme.read_text(encoding='utf-8')
        if SESSION_START not in text or SESSION_END not in text:
            failures.append('missing_session_readme_block')

    for path in iter_text_files(root):
        try:
            text = path.read_text(encoding='utf-8')
        except Exception:
            continue
        for pattern in LEAK_PATTERNS:
            if pattern in text:
                failures.append(f'leak:{path.relative_to(root)}:{pattern}')

    if failures:
        print('\n'.join(failures))
        return 1

    print('bootstrap_contract:PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
