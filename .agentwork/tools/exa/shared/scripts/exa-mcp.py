#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess

PACKAGE = 'exa-mcp-server@3.4.0'
ENABLED_TOOLS = 'web_search_exa,web_fetch_exa'
ASSIGNMENT = re.compile(r'^\s*(?:export\s+)?EXA_API_KEY\s*=(.*)$')


def fail(message: str) -> None:
    raise SystemExit(f'[exa-mcp] {message}')


def parse_api_key(env_path: Path) -> tuple[str, str | None]:
    if not env_path.exists():
        return 'missing', None
    if env_path.is_symlink() or not env_path.is_file():
        fail('.env must be a regular project-root file')
    try:
        lines = env_path.read_text(encoding='utf-8').splitlines()
    except (OSError, UnicodeError) as exc:
        fail(f'cannot read project-root .env: {exc}')

    matches: list[str] = []
    for line in lines:
        match = ASSIGNMENT.fullmatch(line)
        if match is not None:
            matches.append(match.group(1).strip())
    if not matches:
        return 'missing', None
    if len(matches) != 1:
        fail('.env contains duplicate EXA_API_KEY assignments')

    raw = matches[0]
    if raw.startswith(('\'', '"')):
        quote = raw[0]
        if len(raw) < 2 or raw[-1] != quote:
            fail('EXA_API_KEY has an unmatched quote')
        value = raw[1:-1]
    else:
        value = raw
    if '\x00' in value:
        fail('EXA_API_KEY contains a null byte')
    return ('configured', value) if value else ('empty', None)


def node_major() -> int | None:
    try:
        result = subprocess.run(
            ['node', '--version'],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
    except OSError:
        return None
    value = result.stdout.strip().lstrip('v').split('.', 1)[0]
    return int(value) if value.isdigit() else None


def main() -> int:
    parser = argparse.ArgumentParser(description='Start the pinned Exa MCP server with project-local settings.')
    parser.add_argument('--check', action='store_true', help='report credential and runtime readiness without secrets')
    parser.add_argument('--project-root', help='override the project root; intended for isolated validation')
    args = parser.parse_args()

    project_root = (
        Path(args.project_root).resolve()
        if args.project_root
        else Path(__file__).resolve().parents[2]
    )
    status, api_key = parse_api_key(project_root / '.env')
    major = node_major()
    node_ready = major is not None and major >= 20
    npx_ready = shutil.which('npx') is not None
    if args.check:
        print(f'[exa-mcp] EXA_API_KEY: {status}')
        print(f'[exa-mcp] node: {"compatible" if node_ready else "missing-or-incompatible"}')
        print(f'[exa-mcp] npx: {"available" if npx_ready else "missing"}')
        return 0 if status == 'configured' and node_ready and npx_ready else 1
    if api_key is None:
        fail(f'EXA_API_KEY is {status}; fill the project-root .env before starting local STDIO')
    if not node_ready:
        fail('Node.js >=20.0.0 is required')
    if not npx_ready:
        fail('npx is required')

    child_env = os.environ.copy()
    child_env['EXA_API_KEY'] = api_key
    child_env['ENABLED_TOOLS'] = ENABLED_TOOLS
    try:
        os.execvpe('npx', ['npx', '-y', PACKAGE], child_env)
    except OSError as exc:
        fail(f'failed to start npx: {exc}')


if __name__ == '__main__':
    raise SystemExit(main())
