#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import sys

PACKAGE = 'octocode-mcp@18.2.2'
TOOLS = (
    'ghSearchCode',
    'ghSearchRepos',
    'ghSearchPullRequests',
    'ghSearchIssues',
    'ghSearchCommits',
    'ghGetFileContent',
    'ghViewRepoStructure',
)
TOOLS_SET = frozenset(TOOLS)


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


def gh_auth_available() -> bool:
    if shutil.which('gh') is None:
        return False
    result = subprocess.run(
        ['gh', 'auth', 'status'],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def blocked_tool_call(message: dict) -> str | None:
    if message.get('method') != 'tools/call':
        return None
    params = message.get('params')
    if not isinstance(params, dict):
        return 'invalid tools/call params'
    name = params.get('name')
    if name not in TOOLS_SET:
        return f'tool is not allowed: {name}'
    if name != 'ghGetFileContent':
        return None
    arguments = params.get('arguments')
    queries = arguments.get('queries') if isinstance(arguments, dict) else None
    if not isinstance(queries, list) or not queries:
        return 'ghGetFileContent requires a non-empty queries list'
    for query in queries:
        if not isinstance(query, dict):
            return 'ghGetFileContent queries must be objects'
        read_type = query.get('type', 'file')
        if read_type == 'directory':
            return 'ghGetFileContent type=directory is disabled; use file reads only'
        if read_type != 'file':
            return 'ghGetFileContent only allows type=file'
        query['type'] = 'file'
    return None


def restrict_tools_list(message: dict) -> dict:
    result = message.get('result')
    tools = result.get('tools') if isinstance(result, dict) else None
    if not isinstance(tools, list):
        return message
    result['tools'] = [
        tool for tool in tools
        if isinstance(tool, dict) and tool.get('name') in TOOLS_SET
    ]
    for tool in result['tools']:
        if tool.get('name') != 'ghGetFileContent':
            continue
        schema = tool.get('inputSchema')
        try:
            type_schema = schema['properties']['queries']['items']['properties']['type']
        except (KeyError, TypeError):
            continue
        schema['properties']['queries']['items']['properties']['type'] = {
            'type': 'string',
            'enum': ['file'],
            'default': 'file',
            'description': 'File reads only; directory materialization is disabled by agentwork.',
        }
    return message


def write_message(stream, message: dict) -> None:
    stream.write((json.dumps(message, separators=(',', ':')) + '\n').encode('utf-8'))
    stream.flush()


def proxy_mcp(child: subprocess.Popen[bytes]) -> int:
    if child.stdin is None or child.stdout is None:
        child.terminate()
        raise SystemExit('[octocode-mcp] failed to open child stdio')

    def forward_signal(signum, _frame) -> None:
        if child.poll() is None:
            child.send_signal(signum)

    signal.signal(signal.SIGTERM, forward_signal)
    signal.signal(signal.SIGINT, forward_signal)
    selector = selectors.DefaultSelector()
    selector.register(child.stdout, selectors.EVENT_READ, 'server')
    tools_list_ids: set[object] = set()
    client_open = True
    server_open = True
    buffers = {'client': bytearray(), 'server': bytearray()}
    try:
        selector.register(sys.stdin.buffer, selectors.EVENT_READ, 'client')
    except (OSError, ValueError):
        client_open = False
        child.stdin.close()
    try:
        while server_open:
            for key, _ in selector.select():
                channel = key.data
                chunk = os.read(key.fileobj.fileno(), 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    if channel == 'client':
                        client_open = False
                        child.stdin.close()
                    else:
                        server_open = False
                    continue
                buffer = buffers[channel]
                buffer.extend(chunk)
                while b'\n' in buffer:
                    line, _, remainder = buffer.partition(b'\n')
                    buffer[:] = remainder
                    line += b'\n'
                    if channel == 'client':
                        try:
                            message = json.loads(line)
                        except json.JSONDecodeError:
                            child.stdin.write(line)
                            child.stdin.flush()
                            continue
                        reason = blocked_tool_call(message)
                        if reason is not None:
                            if 'id' in message:
                                write_message(sys.stdout.buffer, {
                                    'jsonrpc': '2.0',
                                    'id': message['id'],
                                    'error': {'code': -32602, 'message': reason},
                                })
                            continue
                        if message.get('method') == 'tools/list' and 'id' in message:
                            tools_list_ids.add(message['id'])
                        write_message(child.stdin, message)
                        continue

                    try:
                        message = json.loads(line)
                    except json.JSONDecodeError:
                        sys.stdout.buffer.write(line)
                        sys.stdout.buffer.flush()
                        continue
                    if message.get('id') in tools_list_ids:
                        tools_list_ids.discard(message.get('id'))
                        message = restrict_tools_list(message)
                    write_message(sys.stdout.buffer, message)
    finally:
        selector.close()
        if child.poll() is None:
            if client_open:
                child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
    return child.returncode or 0


def main() -> int:
    parser = argparse.ArgumentParser(description='Start pinned Octocode MCP with a read-only research surface.')
    parser.add_argument('--check', action='store_true', help='report runtime and auth availability without token details')
    parser.add_argument('--project-root', help='override the project root; intended for isolated validation')
    args = parser.parse_args()

    project_root = (
        Path(args.project_root).resolve()
        if args.project_root
        else Path(__file__).resolve().parents[2]
    )
    major = node_major()
    if args.check:
        print(f'[octocode-mcp] node: {"compatible" if major is not None and major >= 20 else "missing-or-incompatible"}')
        print(f'[octocode-mcp] npx: {"available" if shutil.which("npx") else "missing"}')
        has_env_token = any(os.environ.get(name, '').strip() for name in (
            'OCTOCODE_TOKEN',
            'GH_TOKEN',
            'GITHUB_TOKEN',
            'GITHUB_PERSONAL_ACCESS_TOKEN',
        ))
        auth = 'env' if has_env_token else ('gh-cli' if gh_auth_available() else 'missing')
        print(f'[octocode-mcp] github-auth: {auth}')
        print(f'[octocode-mcp] tools: {len(TOOLS)} read-only')
        return 0 if major is not None and major >= 20 and shutil.which('npx') and auth != 'missing' else 1

    if major is None or major < 20:
        raise SystemExit('[octocode-mcp] Node.js >=20.0.0 is required')
    if shutil.which('npx') is None:
        raise SystemExit('[octocode-mcp] npx is required')

    child_env = os.environ.copy()
    child_env.pop('ENABLE_TOOLS', None)
    child_env.pop('DISABLE_TOOLS', None)
    child_env['TOOLS_TO_RUN'] = ','.join(TOOLS)
    child_env['ENABLE_LOCAL'] = 'false'
    child_env['ENABLE_CLONE'] = 'false'
    child_env['ENABLE_RELEASES'] = 'false'
    child_env['ENABLE_DISCUSSIONS'] = 'false'
    child_env['OCTOCODE_ENABLE_STATS'] = '0'
    child_env['OCTOCODE_HOME'] = str(project_root / '.tmp' / 'agentwork' / 'octocode')
    child_env['WORKSPACE_ROOT'] = str(project_root)
    try:
        child = subprocess.Popen(
            ['npx', '-y', PACKAGE],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
            env=child_env,
        )
    except OSError as exc:
        raise SystemExit(f'[octocode-mcp] failed to start npx: {exc}') from exc
    return proxy_mcp(child)


if __name__ == '__main__':
    raise SystemExit(main())
