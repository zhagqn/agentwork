#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from test.checks import (
    check_contains,
    check_text_collection_with_all,
    check_text_tree_with_required_and_any_groups,
    find_text_file_with_all,
    find_text_file_with_required_and_any,
)

ROOT = Path(__file__).resolve().parent.parent
RUNS_ROOT = ROOT / '.tmp' / 'integrated-harness' / 'runs'
SCENARIO_ROOT = ROOT / 'test' / 'flow'
SUPPORTED_PROVIDERS = ('codex', 'claude')
HTTP_PROBE_SCRIPT = 'scripts/http-json-probe.mjs'
HTTP_PROBE_DOC = 'docs/http-json-probe.md'
HTTP_FIXTURE_SERVER = 'fixtures/http-json-probe-server.mjs'
HEARTBEAT_SECONDS = 30
MAX_INDEPENDENT_EXEC_ATTEMPTS = 2
AGENT_LOG_PREFIXES = (
    'codex',
    'claude',
    'user',
    'exec',
    'tool',
    'assistant',
    'result',
)
AGENT_LOG_KEYWORDS = (
    '{"changed_files"',
    '{"created_files"',
    '{"touched_files"',
    '"summary"',
    'succeeded in ',
    'failed in ',
    'usage limit',
)


def now_id() -> str:
    return datetime.now().strftime('%Y%m%d-%H%M%S')


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec='seconds')


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def append_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as handle:
        handle.write(content)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def load_flow() -> dict:
    # 场景文件只描述用户命令输入和调用顺序，脚本本身不内嵌测试提示词。
    return read_json(SCENARIO_ROOT / 'flow.json')


def render_command_input(input_name: str, values: dict[str, str]) -> str:
    template_path = SCENARIO_ROOT / input_name
    return template_path.read_text(encoding='utf-8').format(**values)


def text_file_snapshot(root: Path, pattern: str = '*.md') -> dict[str, str]:
    # 用文件快照发现命令生成的真实工件，避免固定测试文件名。
    if not root.exists():
        return {}
    return {
        str(path.relative_to(root)): path.read_text(encoding='utf-8')
        for path in root.rglob(pattern)
        if path.is_file()
    }


def changed_text_files(root: Path, before: dict[str, str], pattern: str = '*.md') -> list[str]:
    after = text_file_snapshot(root, pattern)
    return sorted(rel for rel, content in after.items() if before.get(rel) != content)


def discover_changed_file(root: Path, before: dict[str, str], failures: list[str], label: str, pattern: str = '*.md') -> str | None:
    changed = changed_text_files(root, before, pattern)
    if len(changed) != 1:
        failures.append(f'{label}_changed_file_count:{changed}')
        return None
    return changed[0]


def discover_session_file(project: Path, before: dict[str, str], failures: list[str]) -> str | None:
    session_root = project / '.shared/session'
    changed = [rel for rel in changed_text_files(session_root, before) if rel != 'README.md']
    if len(changed) != 1:
        failures.append(f'session_changed_file_count:{changed}')
        return None
    return f'.shared/session/{changed[0]}'


def find_http_probe_doc(project: Path) -> Path | None:
    candidates = [project / HTTP_PROBE_DOC, project / 'README.md']
    docs_root = project / 'docs'
    if docs_root.exists():
        candidates.extend(sorted(path for path in docs_root.rglob('*.md') if path.is_file()))
    for path in candidates:
        if not path.is_file():
            continue
        content = path.read_text(encoding='utf-8')
        if 'http-json-probe' in content and 'node' in content:
            return path
    return None


def http_fixture_server_candidates(project: Path) -> list[Path]:
    candidates = [
        project / HTTP_FIXTURE_SERVER,
        project / 'scripts/fixtures/http-json-probe-server.mjs',
        project / 'scripts/http-json-probe-fixture-server.mjs',
        project / 'scripts/fixture-server.mjs',
    ]
    for root_rel in ['fixtures', 'scripts']:
        root = project / root_rel
        if root.exists():
            candidates.extend(sorted(path for path in root.rglob('*.mjs') if path.is_file()))
    seen: set[Path] = set()
    valid: list[tuple[int, Path]] = []
    for path in candidates:
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        name = path.name.lower()
        if any(token in name for token in ['acceptance', 'check', 'test', 'spec']):
            continue
        content = path.read_text(encoding='utf-8')
        if '/ok' not in content or '/bad-contract' not in content:
            continue
        if 'createServer' not in content or '.listen(' not in content:
            continue
        score = 0
        if 'fixture' in name:
            score += 4
        if 'server' in name:
            score += 3
        if path.parent.name == 'fixtures':
            score += 2
        valid.append((score, path))
    return [path for _, path in sorted(valid, key=lambda item: (-item[0], str(item[1])))]


def can_start_http_fixture_server(project: Path, fixture_server: Path) -> bool:
    project = project.resolve()
    fixture_server = fixture_server.resolve()
    host = '127.0.0.1'
    port = free_local_port()
    env = dict(os.environ)
    env['HOST'] = host
    env['PORT'] = str(port)
    probe_root = project / '.tmp/integrated-harness-fixture-discovery'
    probe_root.mkdir(parents=True, exist_ok=True)

    for index, cmd in enumerate([
        ['node', str(fixture_server), '--port', str(port)],
        ['node', str(fixture_server)],
    ], start=1):
        stdout_path = probe_root / f'{fixture_server.stem}-{index}.stdout.txt'
        stderr_path = probe_root / f'{fixture_server.stem}-{index}.stderr.txt'
        with stdout_path.open('w', encoding='utf-8') as stdout_handle, stderr_path.open('w', encoding='utf-8') as stderr_handle:
            server = subprocess.Popen(
                cmd,
                cwd=project,
                text=True,
                stdout=stdout_handle,
                stderr=stderr_handle,
                env=env,
            )
            try:
                if wait_for_port(host, port, server, timeout=3):
                    return True
            finally:
                if server.poll() is None:
                    server.terminate()
                    try:
                        server.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        server.kill()
                        server.wait()
    return False


def find_http_fixture_server(project: Path) -> Path | None:
    for path in http_fixture_server_candidates(project):
        if can_start_http_fixture_server(project, path):
            return path
    return None


def http_probe_artifacts(project: Path) -> tuple[bool, Path | None, Path | None]:
    return (
        (project / HTTP_PROBE_SCRIPT).exists(),
        find_http_probe_doc(project),
        find_http_fixture_server(project),
    )


def which_provider(requested: str | None) -> str:
    providers = [requested] if requested else list(SUPPORTED_PROVIDERS)
    for provider in providers:
        if provider and shutil.which(provider):
            return provider
    raise SystemExit(f'no supported provider executable found: {providers}')


def command_label(cmd: list[str]) -> str:
    if not cmd:
        return '<empty>'
    head = Path(cmd[0]).name
    if len(cmd) >= 2:
        return f'{head} {Path(cmd[1]).name if cmd[1].endswith(".py") else cmd[1]}'
    return head


def live_log_path(log_stem: Path) -> Path:
    try:
        results = log_stem.parents[2]
    except IndexError:
        return log_stem.parent / 'live.md'
    return results / 'live.md'


def should_echo_agent_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith('+') or stripped[0].isdigit():
        return False
    lower = stripped.lower()
    if any(lower.startswith(prefix) for prefix in AGENT_LOG_PREFIXES):
        return True
    if stripped.startswith('ERROR') or stripped.startswith('Error:') or lower.startswith('usage limit'):
        return True
    return any(keyword in lower for keyword in AGENT_LOG_KEYWORDS)


def format_live_line(label: str, stream: str, line: str) -> str:
    return f'- `{now_iso()}` `{label}` `{stream}` {line.rstrip()}\n'


def stream_process_output(
    pipe,
    log_path: Path,
    live_path: Path,
    label: str,
    stream: str,
    captured: list[str],
) -> None:
    with log_path.open('w', encoding='utf-8') as log_handle:
        for line in iter(pipe.readline, ''):
            captured.append(line)
            log_handle.write(line)
            log_handle.flush()
            if should_echo_agent_line(line):
                cleaned = line.rstrip()
                log(f'[agent:{stream}] {label}: {cleaned}')
                append_text(live_path, format_live_line(label, stream, cleaned))
    pipe.close()


def run_process(cmd: list[str], cwd: Path, timeout: int, log_stem: Path, label: str | None = None) -> subprocess.CompletedProcess[str]:
    start = time.monotonic()
    label = label or command_label(cmd)
    final_stdout_path = log_stem.with_suffix('.stdout.txt')
    final_stderr_path = log_stem.with_suffix('.stderr.txt')
    live_path = live_log_path(log_stem)
    log(f'[start] {label}')
    append_text(live_path, format_live_line(label, 'harness', '[start]'))
    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    timed_out = False

    process_handle = subprocess.Popen(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
    )
    assert process_handle.stdout is not None
    assert process_handle.stderr is not None
    stdout_thread = threading.Thread(
        target=stream_process_output,
        args=(process_handle.stdout, final_stdout_path, live_path, label, 'stdout', stdout_parts),
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=stream_process_output,
        args=(process_handle.stderr, final_stderr_path, live_path, label, 'stderr', stderr_parts),
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()

    last_heartbeat = start
    while True:
        returncode = process_handle.poll()
        if returncode is not None:
            break
        now = time.monotonic()
        elapsed = now - start
        if elapsed >= timeout:
            timed_out = True
            process_handle.kill()
            process_handle.wait()
            break
        if now - last_heartbeat >= HEARTBEAT_SECONDS:
            message = f'[running] {label} ... {int(elapsed)}s elapsed'
            log(message)
            append_text(live_path, format_live_line(label, 'harness', message))
            last_heartbeat = now
        time.sleep(1)

    stdout_thread.join(timeout=5)
    stderr_thread.join(timeout=5)
    duration = time.monotonic() - start
    stdout = ''.join(stdout_parts)
    stderr = ''.join(stderr_parts)
    returncode = 124 if timed_out else process_handle.returncode
    if timed_out:
        stderr = stderr + f'\nTIMEOUT after {timeout}s\n'
        append_text(final_stderr_path, f'\nTIMEOUT after {timeout}s\n')
    process = subprocess.CompletedProcess(cmd, returncode, stdout, stderr)
    write_text(log_stem.with_suffix('.meta.json'), json.dumps({
        'cmd': cmd,
        'cwd': str(cwd),
        'returncode': process.returncode,
        'duration_seconds': round(duration, 2),
        'stdout_log': str(final_stdout_path),
        'stderr_log': str(final_stderr_path),
        'live_log': str(live_path),
    }, ensure_ascii=False, indent=2) + '\n')
    status = 'PASS' if process.returncode == 0 else f'FAIL exit={process.returncode}'
    done_message = f'[done] {label} -> {status} ({int(duration)}s) logs={log_stem.parent.name}/{log_stem.name}.*.txt'
    log(done_message)
    append_text(live_path, format_live_line(label, 'harness', done_message))
    return process


def ensure_git_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(['git', 'init'], cwd=path, text=True, capture_output=True, check=False)


def stage_logs(results: Path, stage: str) -> Path:
    path = results / 'logs' / stage
    path.mkdir(parents=True, exist_ok=True)
    return path


def install_bootstrap(target: Path, logs: Path, name: str) -> subprocess.CompletedProcess[str]:
    ensure_git_repo(target)
    return run_process(
        ['python3', str(ROOT / 'install-bootstrap.py'), '-p', str(target)],
        cwd=ROOT,
        timeout=180,
        log_stem=logs / name,
        label=f'{name}: install-bootstrap',
    )


def build_provider_command(
    provider: str,
    repo: Path,
    user_input: str,
    schema_path: Path,
    output_path: Path,
    model: str | None,
    reasoning_effort: str | None,
    service_tier: str | None,
) -> tuple[list[str], Path | None]:
    # user_input 模拟真实用户命令，例如 `$session load ...`，不是额外约束提示词。
    if provider == 'codex':
        last_message = output_path.with_suffix('.last-message.json')
        cmd = [
            'codex',
            'exec',
            '--sandbox',
            'workspace-write',
            '-c',
            'approval_policy="never"',
        ]
        if model:
            cmd.extend(['--model', model])
        if reasoning_effort:
            cmd.extend(['-c', f'model_reasoning_effort="{reasoning_effort}"'])
        if service_tier:
            cmd.extend(['-c', f'service_tier="{service_tier}"'])
        cmd.extend([
            '--skip-git-repo-check',
            '--output-schema',
            str(schema_path),
            '--output-last-message',
            str(last_message),
            '-C',
            str(repo),
            user_input,
        ])
        return cmd, last_message
    if provider == 'claude':
        schema_text = schema_path.read_text(encoding='utf-8')
        cmd = [
            'claude',
            '-p',
            '--dangerously-skip-permissions',
            '--output-format',
            'json',
            '--json-schema',
            schema_text,
        ]
        if model:
            cmd.extend(['--model', model])
        if reasoning_effort:
            cmd.extend(['--effort', reasoning_effort])
        cmd.append(user_input)
        return cmd, None
    raise ValueError(f'unsupported provider: {provider}')


def parse_provider_output(provider: str, process: subprocess.CompletedProcess[str], last_message: Path | None) -> tuple[dict | None, str | None]:
    try:
        if provider == 'codex':
            if not last_message or not last_message.exists():
                return None, 'missing_codex_last_message'
            return read_json(last_message), None
        if provider == 'claude':
            payload = json.loads(process.stdout)
            structured = payload.get('structured_output')
            if structured is None:
                return None, 'missing_claude_structured_output'
            return structured, None
    except json.JSONDecodeError as exc:
        return None, f'json_decode_error:{exc}'
    return None, 'unknown_provider'


def provider_failure_reason(process: subprocess.CompletedProcess[str], parse_error: str | None) -> str | int:
    combined_output = f'{process.stdout}\n{process.stderr}'
    lower = combined_output.lower()
    if process.returncode == 124 or 'timeout after' in lower:
        return 'provider_timeout'
    if 'usage limit' in lower:
        return 'provider_usage_limit'
    if 'selected model is at capacity' in lower:
        return 'provider_model_at_capacity'
    if '429 too many requests' in lower or 'exceeded retry limit' in lower:
        return 'provider_rate_limited'
    return parse_error or process.returncode


def run_provider_task(
    provider: str,
    model: str | None,
    reasoning_effort: str | None,
    service_tier: str | None,
    repo: Path,
    logs: Path,
    name: str,
    user_input: str,
    schema: dict,
    timeout: int,
) -> tuple[subprocess.CompletedProcess[str], dict | None, str | None]:
    # schema/output 放在目标项目自己的 .tmp 下，确保每次 run 相互隔离。
    provider_root = repo / '.tmp' / 'integrated-harness-provider'
    schema_path = provider_root / f'{name}.schema.json'
    output_path = provider_root / f'{name}.output.json'
    write_text(schema_path, json.dumps(schema, ensure_ascii=False, indent=2) + '\n')
    cmd, last_message = build_provider_command(
        provider, repo, user_input, schema_path, output_path, model, reasoning_effort, service_tier
    )
    process = run_process(cmd, cwd=repo, timeout=timeout, log_stem=logs / name, label=f'{name}: {provider}')
    output_json, parse_error = parse_provider_output(provider, process, last_message)
    if output_json is not None:
        write_text(output_path, json.dumps(output_json, ensure_ascii=False, indent=2) + '\n')
    return process, output_json, parse_error


def run_command_input_task(
    provider: str,
    model: str | None,
    reasoning_effort: str | None,
    service_tier: str | None,
    project: Path,
    logs: Path,
    task: dict,
    values: dict[str, str],
) -> tuple[subprocess.CompletedProcess[str], dict | None, str | None]:
    command_input = render_command_input(task['input'], values)
    return run_provider_task(
        provider,
        model,
        reasoning_effort,
        service_tier,
        project,
        logs,
        task['name'],
        command_input,
        common_schema(task.get('required_key', 'touched_files')),
        int(task.get('timeout', 420)),
    )


def result(name: str, ok: bool, failures: list[str], details: dict | None = None) -> dict:
    return {
        'name': name,
        'ok': ok,
        'failures': failures,
        'details': details or {},
    }


def build_summary(
    run_id: str,
    provider: str,
    model: str | None,
    reasoning_effort: str | None,
    service_tier: str | None,
    started_at: str,
    run_root: Path,
    project: Path,
    stages: list[dict],
    status: str,
) -> dict:
    return {
        'run_id': run_id,
        'provider': provider,
        'model': model,
        'reasoning_effort': reasoning_effort,
        'service_tier': service_tier,
        'status': status,
        'started_at': started_at,
        'updated_at': now_iso(),
        'run_root': display_path(run_root),
        'project': display_path(project),
        'stages': stages,
    }


def write_reports(results: Path, stem: str, summary: dict) -> None:
    write_text(results / f'{stem}.json', json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    write_text(results / f'{stem}.md', render_summary(summary))


def common_schema(required_key: str = 'touched_files') -> dict:
    return {
        'type': 'object',
        'properties': {
            required_key: {'type': 'array', 'items': {'type': 'string'}},
            'summary': {'type': 'string'},
            'verification': {'type': 'string'},
        },
        'required': [required_key, 'summary', 'verification'],
        'additionalProperties': False,
    }


def free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return int(sock.getsockname()[1])


def wait_for_port(host: str, port: int, process: subprocess.Popen[str], timeout: float = 10) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def run_http_probe_checks(project: Path, fixture_server: Path, logs: Path, failures: list[str]) -> None:
    project = project.resolve()
    fixture_server = fixture_server.resolve()
    host = '127.0.0.1'
    port = free_local_port()
    env = dict(os.environ)
    env['HOST'] = host
    env['PORT'] = str(port)
    stdout_path = logs / 'http-probe-fixture-server.stdout.txt'
    stderr_path = logs / 'http-probe-fixture-server.stderr.txt'
    started_at = time.monotonic()
    attempts: list[dict] = []
    server: subprocess.Popen[str] | None = None
    server_stdout = None
    server_stderr = None

    try:
        for index, cmd in enumerate([
            ['node', str(fixture_server), '--port', str(port)],
            ['node', str(fixture_server)],
        ], start=1):
            attempt_stdout = stdout_path if index == 1 else logs / f'http-probe-fixture-server-attempt-{index}.stdout.txt'
            attempt_stderr = stderr_path if index == 1 else logs / f'http-probe-fixture-server-attempt-{index}.stderr.txt'
            server_stdout = attempt_stdout.open('w', encoding='utf-8')
            server_stderr = attempt_stderr.open('w', encoding='utf-8')
            server = subprocess.Popen(
                cmd,
                cwd=project,
                text=True,
                stdout=server_stdout,
                stderr=server_stderr,
                env=env,
            )
            ready = wait_for_port(host, port, server)
            attempts.append({
                'cmd': cmd,
                'ready': ready,
                'returncode': server.poll(),
                'stdout_log': str(attempt_stdout),
                'stderr_log': str(attempt_stderr),
            })
            if ready:
                stdout_path = attempt_stdout
                stderr_path = attempt_stderr
                break
            if server.poll() is None:
                server.terminate()
                try:
                    server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()
            server_stdout.close()
            server_stderr.close()
            server_stdout = None
            server_stderr = None
            server = None

        if server is None or server.poll() is not None:
            failures.append('http_probe_fixture_server_failed')
            return

        ok_url = f'http://{host}:{port}/ok'
        bad_url = f'http://{host}:{port}/bad-contract'
        ok = run_process(
            ['node', str(project / HTTP_PROBE_SCRIPT), ok_url, '--expect', 'status=ok', '--require', 'version'],
            cwd=project,
            timeout=60,
            log_stem=logs / 'http-probe-ok',
            label='independent_commands: http probe ok',
        )
        if ok.returncode != 0:
            failures.append('http_probe_ok_failed')

        bad = run_process(
            ['node', str(project / HTTP_PROBE_SCRIPT), bad_url, '--expect', 'status=ok', '--require', 'version'],
            cwd=project,
            timeout=60,
            log_stem=logs / 'http-probe-bad',
            label='independent_commands: http probe bad',
        )
        if bad.returncode == 0:
            failures.append('http_probe_bad_unexpected_pass')
    finally:
        if server is not None and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
        if server_stdout is not None:
            server_stdout.close()
        if server_stderr is not None:
            server_stderr.close()
        write_text(logs / 'http-probe-fixture-server.meta.json', json.dumps({
            'cmd': attempts[-1]['cmd'] if attempts else ['node', str(fixture_server)],
            'cwd': str(project),
            'returncode': server.returncode if server is not None else None,
            'duration_seconds': round(time.monotonic() - started_at, 2),
            'stdout_log': str(stdout_path),
            'stderr_log': str(stderr_path),
            'attempts': attempts,
        }, ensure_ascii=False, indent=2) + '\n')


def run_install_stage(project: Path, results: Path) -> dict:
    log('[stage] install_standard')
    failures: list[str] = []
    logs = stage_logs(results, 'install_standard')

    # 先验证 source repo 的安装入口存在，再安装到本次唯一临时项目。
    for rel in ['install-bootstrap.py', 'install-tool.py']:
        if not (ROOT / rel).exists():
            failures.append(f'missing_source_script:{rel}')

    install = install_bootstrap(project, logs, 'install-bootstrap')
    if install.returncode != 0:
        failures.append('bootstrap_install_failed')

    contract = run_process(
        ['python3', str(ROOT / 'test/check_bootstrap_contract.py'), str(project)],
        cwd=ROOT,
        timeout=120,
        log_stem=logs / 'install-bootstrap-contract',
        label='install_standard: check-bootstrap-contract',
    )
    if contract.returncode != 0:
        failures.append('bootstrap_contract_failed')

    tool = run_process(
        ['python3', str(ROOT / 'install-tool.py'), '-i', 'arch', '-p', str(project)],
        cwd=ROOT,
        timeout=120,
        log_stem=logs / 'install-tool-arch',
        label='install_standard: install-tool arch',
    )
    if tool.returncode != 0:
        failures.append('arch_install_failed')

    for rel in [
        '.shared/commands/arch.md',
        '.shared/scripts/arch-render.py',
        '.shared/templates/arch/examples/arch-tool/catalog.json',
        '.codex/skills/arch/SKILL.md',
    ]:
        if not (project / rel).exists():
            failures.append(f'missing_arch_target:{rel}')

    if (project / 'install-bootstrap.py').exists() or (project / 'install-tool.py').exists():
        failures.append('source_install_script_leaked_to_target')

    example = project / 'docs/architecture'
    if (project / '.shared/templates/arch/examples/arch-tool').exists():
        shutil.copytree(project / '.shared/templates/arch/examples/arch-tool', example)
        render = run_process(
            ['python3', str(project / '.shared/scripts/arch-render.py'), str(example), '--recursive', '--check'],
            cwd=project,
            timeout=120,
            log_stem=logs / 'install-arch-render-check',
            label='install_standard: arch-render --check',
        )
        if render.returncode != 0:
            failures.append('arch_render_check_failed')

    write_text(project / 'README.md', '# Demo Repo\n\n用于测试已安装 agentwork 工作流的临时项目。\n')

    stage = result('install_standard', not failures, failures, {
        'project': display_path(project),
        'installer_root': display_path(ROOT),
    })
    log(f'[stage-done] install_standard -> {"PASS" if stage["ok"] else "FAIL"}')
    return stage


def run_workflow_commands_stage(
    provider: str,
    model: str | None,
    reasoning_effort: str | None,
    service_tier: str | None,
    project: Path,
    results: Path,
) -> dict:
    log('[stage] independent_commands')
    failures: list[str] = []
    logs = stage_logs(results, 'independent_commands')
    flow = load_flow()['independent_commands']

    # Standalone flow 使用真实 `$brain/$plan/$exec/$review` 命令输入串起来。
    brain_root = project / '.tmp/agentwork/brain'
    plan_root = project / '.tmp/agentwork/plan'
    review_root = project / '.tmp/agentwork/review'
    values = {
        'probe_script': HTTP_PROBE_SCRIPT,
        'probe_doc': HTTP_PROBE_DOC,
    }

    # 每一步执行后只接受一个新增/变更工件，防止命令污染其他 standalone 目录。
    brain_before = text_file_snapshot(brain_root)
    process, output, parse_error = run_command_input_task(
        provider, model, reasoning_effort, service_tier, project, logs, flow[0], values
    )
    if process.returncode != 0 or parse_error:
        failures.append(f'brain_provider_failed:{provider_failure_reason(process, parse_error)}')
        stage = result('independent_commands', False, failures, {'project': display_path(project)})
        log('[stage-done] independent_commands -> FAIL')
        return stage
    brain_file = discover_changed_file(brain_root, brain_before, failures, 'brain')
    if brain_file:
        brain_target = f'.tmp/agentwork/brain/{brain_file}'
        values['brain_file'] = brain_target
        check_contains(project / brain_target, '## 方案对比', failures, 'brain_note')
        check_contains(project / brain_target, 'HTTP', failures, 'brain_note')
        check_contains(project / brain_target, 'JSON', failures, 'brain_note')
        check_contains(project / brain_target, '/plan', failures, 'brain_note')
    check_contains(project / 'README.md', '用于测试已安装 agentwork 工作流的临时项目。', failures, 'brain_readme_unchanged')
    if 'brain_file' not in values:
        stage = result('independent_commands', False, failures, {'project': display_path(project)})
        log('[stage-done] independent_commands -> FAIL')
        return stage

    plan_before = text_file_snapshot(plan_root)
    process, output, parse_error = run_command_input_task(
        provider, model, reasoning_effort, service_tier, project, logs, flow[1], values
    )
    if process.returncode != 0 or parse_error:
        failures.append(f'plan_provider_failed:{provider_failure_reason(process, parse_error)}')
        stage = result('independent_commands', False, failures, {'project': display_path(project)})
        log('[stage-done] independent_commands -> FAIL')
        return stage
    plan_file = discover_changed_file(plan_root, plan_before, failures, 'plan')
    if plan_file:
        plan_target = f'.tmp/agentwork/plan/{plan_file}'
        values['plan_file'] = plan_target
        check_contains(project / plan_target, '## 任务列表（按优先级）', failures, 'plan')
        check_contains(project / plan_target, HTTP_PROBE_SCRIPT, failures, 'plan')
    if 'plan_file' not in values:
        stage = result('independent_commands', False, failures, {'project': display_path(project)})
        log('[stage-done] independent_commands -> FAIL')
        return stage

    exec_attempts = 0
    for attempt in range(1, MAX_INDEPENDENT_EXEC_ATTEMPTS + 1):
        exec_task = dict(flow[2])
        if attempt > 1:
            exec_task['name'] = f'{flow[2]["name"]}-{attempt}'
        process, output, parse_error = run_command_input_task(
            provider, model, reasoning_effort, service_tier, project, logs, exec_task, values
        )
        exec_attempts = attempt
        if process.returncode != 0 or parse_error:
            failures.append(f'{exec_task["name"]}_provider_failed:{provider_failure_reason(process, parse_error)}')
            stage = result('independent_commands', False, failures, {
                'project': display_path(project),
                'exec_attempts': exec_attempts,
            })
            log('[stage-done] independent_commands -> FAIL')
            return stage
        script_ok, doc_file, fixture_server = http_probe_artifacts(project)
        if script_ok and doc_file and fixture_server:
            break

    script_ok, doc_file, fixture_server = http_probe_artifacts(project)
    if not script_ok:
        failures.append(f'missing_http_probe_file:{HTTP_PROBE_SCRIPT}')
    if doc_file is None:
        failures.append('missing_http_probe_doc:http-json-probe')
    if fixture_server is None:
        failures.append('missing_http_probe_fixture_server:/ok,/bad-contract')
    check_contains(project / values['plan_file'], '- [x]', failures, 'exec_plan')
    if doc_file is not None:
        check_contains(doc_file, 'node', failures, 'http_probe_doc')
    if script_ok and fixture_server is not None:
        run_http_probe_checks(project, fixture_server, logs, failures)

    review_before = text_file_snapshot(review_root)
    process, output, parse_error = run_command_input_task(
        provider, model, reasoning_effort, service_tier, project, logs, flow[3], values
    )
    if process.returncode != 0 or parse_error:
        failures.append(f'review_provider_failed:{provider_failure_reason(process, parse_error)}')
    review_file = discover_changed_file(review_root, review_before, failures, 'review')
    if review_file:
        review_target = f'.tmp/agentwork/review/{review_file}'
        check_contains(project / review_target, HTTP_PROBE_SCRIPT, failures, 'review')
        check_contains(project / review_target, 'Critical', failures, 'review')
        check_contains(project / review_target, 'none', failures, 'review')

    stage = result('independent_commands', not failures, failures, {
        'project': display_path(project),
        'exec_attempts': exec_attempts,
        'http_probe_doc': display_path(doc_file) if doc_file else None,
        'http_fixture_server': display_path(fixture_server) if fixture_server else None,
    })
    log(f'[stage-done] independent_commands -> {"PASS" if stage["ok"] else "FAIL"}')
    return stage


def seed_turborepo(repo: Path) -> None:
    # 只种下足够验证 workspace 边界的最小 Turborepo 壳层。
    files = {
        'package.json': json.dumps({
            'name': 'mini-dinner-flow-smoke',
            'private': True,
            'packageManager': 'pnpm@9.0.0',
            'scripts': {'build': 'turbo build', 'typecheck': 'turbo typecheck'},
            'devDependencies': {'turbo': '^2.0.0', 'typescript': '^5.0.0'},
        }, ensure_ascii=False, indent=2) + '\n',
        'pnpm-workspace.yaml': 'packages:\n  - "apps/*"\n  - "packages/*"\n',
        'turbo.json': json.dumps({
            'tasks': {
                'build': {'dependsOn': ['^build'], 'outputs': ['dist/**']},
                'typecheck': {'dependsOn': ['^typecheck'], 'outputs': []},
            }
        }, ensure_ascii=False, indent=2) + '\n',
        'README.md': '# Mini Dinner Flow\n\n简化的 Turborepo 餐饮点单测试仓库。\n',
        'apps/api/src/main.ts': 'export const apiName = "mini-dinner-api";\n',
        'apps/admin/src/app.tsx': 'export const adminName = "mini-dinner-admin";\n',
        'apps/h5/src/app.tsx': 'export const h5Name = "mini-dinner-h5";\n',
        'packages/shared/src/index.ts': 'export type ApiStatus = "ok";\n',
    }
    for rel, content in files.items():
        write_text(repo / rel, content)


def run_turborepo_flow_stage(
    provider: str,
    model: str | None,
    reasoning_effort: str | None,
    service_tier: str | None,
    project: Path,
    results: Path,
) -> dict:
    log('[stage] turborepo_iteration_flow')
    failures: list[str] = []
    logs = stage_logs(results, 'turborepo_iteration_flow')
    flow = load_flow()['turborepo_iteration_flow']
    seed_turborepo(project)
    # Session mode 默认只更新 session；若出现 standalone 工件，说明命令边界漂移。
    standalone_roots = [
        project / '.tmp/agentwork/brain',
        project / '.tmp/agentwork/plan',
        project / '.tmp/agentwork/review',
    ]
    standalone_before = {
        str(path.relative_to(project))
        for root in standalone_roots
        if root.exists()
        for path in root.rglob('*')
        if path.is_file()
    }

    # 每次 provider 调用都是新进程，所以 exec/review 的输入会先 load 已发现的 session。
    session_before = text_file_snapshot(project / '.shared/session')
    values: dict[str, str] = {}
    for index, task in enumerate(flow):
        process, output, parse_error = run_command_input_task(
            provider, model, reasoning_effort, service_tier, project, logs, task, values
        )
        if process.returncode != 0 or parse_error:
            failures.append(f'{task["name"]}_provider_failed:{provider_failure_reason(process, parse_error)}')
            stage = result('turborepo_iteration_flow', False, failures, {
                'project': display_path(project),
                'session_file': values.get('session_file'),
            })
            log('[stage-done] turborepo_iteration_flow -> FAIL')
            return stage
        if index == 0:
            session_file = discover_session_file(project, session_before, failures)
            if session_file is None:
                break
            values['session_file'] = session_file

    session_file = values.get('session_file', '.shared/session/<missing>')

    for rel in [session_file, 'README.md']:
        if not (project / rel).exists():
            failures.append(f'missing_turborepo_file:{rel}')

    # Harness 只检查第一轮基础框架和 Mini Dinner 核心概念，不要求完整依赖安装/服务联调。
    find_text_file_with_required_and_any(
        project,
        'packages/shared/src',
        ['Dinner'],
        ['Query', 'Command', 'Request', 'Response', 'Data', 'ApiResult'],
        failures,
        'shared_types',
    )
    check_text_tree_with_required_and_any_groups(
        project,
        'apps/api/src',
        ['Dinner'],
        [
            ['@mini-dinner/shared', 'packages/shared/src', 'from "../../shared"', 'from "./shared"', 'from "../shared"'],
            ['Controller', 'UseCase', 'ApplicationService', 'Service'],
            ['Repository', 'infrastructure', 'drizzle', 'schema'],
        ],
        failures,
        'api_boundary_skeleton',
    )
    check_text_tree_with_required_and_any_groups(
        project,
        'apps/h5/src',
        ['Dinner'],
        [
            ['Client', 'Transport', 'Loader', 'Page', 'State', 'Adapter', 'Model'],
            ['@mini-dinner/shared', 'packages/shared/src', 'from "../shared"', 'from "./shared"'],
        ],
        failures,
        'h5_boundary_skeleton',
    )
    find_text_file_with_all(project, 'docs', ['Mini Dinner Flow'], failures, 'mini_dinner_doc')
    check_text_collection_with_all(project, ['README.md', 'docs'], ['验收'], failures, 'mini_dinner_acceptance_doc')
    check_contains(project / 'README.md', 'Mini Dinner Flow', failures, 'README.md')

    session_check = run_process(
        ['python3', str(ROOT / 'test/check_session_standard.py'), str(project / session_file), '--strict-flow'],
        cwd=ROOT,
        timeout=120,
        log_stem=logs / 'turborepo-session-standard',
        label='turborepo_iteration_flow: check-session-standard',
    )
    if session_check.returncode != 0:
        failures.append('turborepo_session_standard_failed')

    standalone_after = {
        str(path.relative_to(project))
        for root in standalone_roots
        if root.exists()
        for path in root.rglob('*')
        if path.is_file()
    }
    new_standalone = sorted(standalone_after - standalone_before)
    if new_standalone:
        failures.append(f'session_mode_created_standalone_artifacts:{new_standalone}')

    stage = result('turborepo_iteration_flow', not failures, failures, {
        'project': display_path(project),
        'session_file': session_file,
    })
    log(f'[stage-done] turborepo_iteration_flow -> {"PASS" if stage["ok"] else "FAIL"}')
    return stage


def render_summary(summary: dict) -> str:
    lines = [
        '# Integrated Harness Summary',
        '',
        f'- run_id: `{summary["run_id"]}`',
        f'- provider: `{summary["provider"]}`',
        f'- model: `{summary.get("model") or ""}`',
        f'- reasoning_effort: `{summary.get("reasoning_effort") or ""}`',
        f'- service_tier: `{summary.get("service_tier") or ""}`',
        f'- status: `{summary["status"]}`',
        f'- started_at: `{summary["started_at"]}`',
        f'- updated_at: `{summary["updated_at"]}`',
        f'- finished_at: `{summary.get("finished_at", "")}`',
        f'- run_root: `{summary["run_root"]}`',
        f'- project: `{summary["project"]}`',
        '',
        '## Stages',
        '',
        '| Stage | Status | Failures |',
        '| --- | --- | ---: |',
    ]
    for item in summary['stages']:
        lines.append(f'| `{item["name"]}` | `{"PASS" if item["ok"] else "FAIL"}` | `{len(item["failures"])}` |')
    for item in summary['stages']:
        if item['failures']:
            lines.extend(['', f'### {item["name"]}'])
            for failure in item['failures']:
                lines.append(f'- `{failure}`')
    return '\n'.join(lines) + '\n'
