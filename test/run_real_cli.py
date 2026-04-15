#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import shutil
import subprocess
import tempfile
import time
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEST_ROOT = ROOT / 'test'
CASE_ROOT = TEST_ROOT / 'cases'
TMP = ROOT / '.tmp' / 'real-harness'
REPOS = TMP / 'repos'
RESULTS = TMP / 'results'
SUPPORTED_PROVIDERS = ('codex', 'claude')
MAX_PROVIDER_ATTEMPTS = 2
RETRYABLE_ERROR_MARKERS = (
    'Selected model is at capacity',
    'rate limit',
    'rate_limit',
    'temporarily unavailable',
)
DEFAULT_HEARTBEAT_SECONDS = 15
HEARTBEAT_SECONDS = DEFAULT_HEARTBEAT_SECONDS


def log_progress(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec='seconds')


def load_case(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def which_available(providers: list[str]) -> list[str]:
    return [provider for provider in providers if shutil.which(provider)]


def run(cmd: list[str], cwd: Path, timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
    )


def summarize_results(providers: list[str], case_dicts: list[dict], results: list[dict]) -> dict:
    expected_count = len(providers) * len(case_dicts)
    ok_count = sum(1 for result in results if result.get('ok'))
    failed_results = [result for result in results if not result.get('ok')]
    timed_out_count = sum(1 for result in results if result.get('timed_out'))
    complete_run = len(results) == expected_count

    by_provider = []
    for provider in providers:
        provider_results = [result for result in results if result.get('provider') == provider]
        provider_expected = len(case_dicts)
        provider_ok = sum(1 for result in provider_results if result.get('ok'))
        provider_failed = len(provider_results) - provider_ok
        by_provider.append(
            {
                'provider': provider,
                'expected_count': provider_expected,
                'result_count': len(provider_results),
                'ok_count': provider_ok,
                'failed_count': provider_failed,
                'all_ok': len(provider_results) == provider_expected and provider_failed == 0,
            }
        )

    failed_summary = [
        {
            'provider': result['provider'],
            'case': result['case'],
            'returncode': result['returncode'],
            'timed_out': result['timed_out'],
            'failed_assertions': result['failed_assertions'],
        }
        for result in failed_results
    ]

    if not complete_run:
        overall_status = 'incomplete'
        grade = 'yellow'
    elif failed_results:
        overall_status = 'fail'
        grade = 'red'
    else:
        overall_status = 'pass'
        grade = 'green'

    return {
        'generated_at': now_iso(),
        'design_basis': [
            '断言风格参考 promptfoo 的 deterministic assertions：优先 file/json/contains 这类可编程检查。',
            '遵循 OpenAI eval best practices：先做 task-specific 自动检查，再用人工审查校准。',
            '遵循 Anthropic 评估建议：优先代码评分，复杂判断再交给人工或后续的 LLM judge。',
        ],
        'overview': {
            'overall_status': overall_status,
            'grade': grade,
            'complete_run': complete_run,
            'expected_result_count': expected_count,
            'result_count': len(results),
            'ok_count': ok_count,
            'failed_count': len(failed_results),
            'timed_out_count': timed_out_count,
            'started_at': results[0]['started_at'] if results else None,
            'finished_at': results[-1]['finished_at'] if results else None,
            'duration_seconds': round(sum(result.get('duration_seconds', 0.0) for result in results), 2),
        },
        'providers': providers,
        'cases': [case['name'] for case in case_dicts],
        'by_provider': by_provider,
        'failed_summary': failed_summary,
        'results': results,
    }


def render_markdown_summary(summary: dict) -> str:
    overview = summary['overview']
    lines = [
        '# Real Harness Summary',
        '',
        '## 总览',
        f'- 生成时间: `{summary["generated_at"]}`',
        f'- 状态: `{overview["overall_status"]}`',
        f'- 等级: `{overview["grade"]}`',
        f'- 完整运行: `{overview["complete_run"]}`',
        f'- 结果数: `{overview["result_count"]}` / `{overview["expected_result_count"]}`',
        f'- 通过: `{overview["ok_count"]}`',
        f'- 失败: `{overview["failed_count"]}`',
        f'- 超时: `{overview["timed_out_count"]}`',
        f'- 开始时间: `{overview["started_at"]}`',
        f'- 结束时间: `{overview["finished_at"]}`',
        f'- 总耗时(秒): `{overview["duration_seconds"]}`',
        '',
        '## Provider 统计',
        '',
        '| Provider | 结果数 | 期望数 | 通过 | 失败 | 全通过 |',
        '| --- | ---: | ---: | ---: | ---: | --- |',
    ]

    for item in summary['by_provider']:
        lines.append(
            f'| `{item["provider"]}` | `{item["result_count"]}` | `{item["expected_count"]}` | `{item["ok_count"]}` | `{item["failed_count"]}` | `{item["all_ok"]}` |'
        )

    lines.extend(
        [
            '',
            '## Case 结果',
            '',
            '| Provider | Case | 状态 | 退出码 | 超时 | 耗时(秒) | 开始时间 | 结束时间 | 失败断言数 |',
            '| --- | --- | --- | ---: | --- | ---: | --- | --- | ---: |',
        ]
    )
    for result in summary['results']:
        status = 'PASS' if result['ok'] else 'FAIL'
        lines.append(
            f'| `{result["provider"]}` | `{result["case"]}` | `{status}` | `{result["returncode"]}` | `{result["timed_out"]}` | `{result["duration_seconds"]}` | `{result["started_at"]}` | `{result["finished_at"]}` | `{len(result["failed_assertions"])}` |'
        )

    if summary['failed_summary']:
        lines.extend(['', '## 失败摘要'])
        for item in summary['failed_summary']:
            lines.extend(
                [
                    '',
                    f'### `{item["provider"]}` / `{item["case"]}`',
                    f'- `returncode`: `{item["returncode"]}`',
                    f'- `timed_out`: `{item["timed_out"]}`',
                    f'- `failed_assertions`: `{len(item["failed_assertions"])}`',
                ]
            )
            for failure in item['failed_assertions']:
                lines.append(f'  - `{failure}`')
    else:
        lines.extend(['', '## 失败摘要', '', '- 无失败项。'])

    lines.extend(['', '## Design Basis'])
    for basis in summary['design_basis']:
        lines.append(f'- {basis}')

    return '\n'.join(lines) + '\n'


def write_summary_reports(name: str, summary: dict) -> None:
    write_text(RESULTS / f'{name}.json', json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    write_text(RESULTS / f'{name}.md', render_markdown_summary(summary))


def run_with_progress(cmd: list[str], cwd: Path, timeout_seconds: int, label: str) -> tuple[subprocess.CompletedProcess[str], bool, float]:
    start = time.monotonic()
    log_progress(f'[start] {label}')

    stdout_tmp = tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False, dir=RESULTS, prefix='live-', suffix='.stdout.tmp')
    stderr_tmp = tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False, dir=RESULTS, prefix='live-', suffix='.stderr.tmp')
    stdout_path = Path(stdout_tmp.name)
    stderr_path = Path(stderr_tmp.name)
    stdout_tmp.close()
    stderr_tmp.close()

    timed_out = False
    try:
        with stdout_path.open('w', encoding='utf-8') as stdout_handle, stderr_path.open('w', encoding='utf-8') as stderr_handle:
            process = subprocess.Popen(
                cmd,
                cwd=str(cwd),
                text=True,
                stdout=stdout_handle,
                stderr=stderr_handle,
            )
            last_heartbeat_at = start
            while True:
                returncode = process.poll()
                if returncode is not None:
                    break
                now = time.monotonic()
                elapsed = now - start
                if elapsed >= timeout_seconds:
                    timed_out = True
                    process.kill()
                    process.wait()
                    log_progress(f'[timeout] {label} after {int(elapsed)}s')
                    break
                if now - last_heartbeat_at >= HEARTBEAT_SECONDS:
                    log_progress(f'[running] {label} ... {int(elapsed)}s elapsed')
                    last_heartbeat_at = now
                time.sleep(1)

        stdout = stdout_path.read_text(encoding='utf-8')
        stderr = stderr_path.read_text(encoding='utf-8')
    finally:
        stdout_path.unlink(missing_ok=True)
        stderr_path.unlink(missing_ok=True)

    elapsed = time.monotonic() - start
    returncode = 124 if timed_out else process.returncode
    log_progress(f'[done] {label} -> exit={returncode} elapsed={int(elapsed)}s')
    return subprocess.CompletedProcess(cmd, returncode, stdout, stderr), timed_out, elapsed


def ensure_git_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(['git', 'init'], cwd=str(path), text=True, capture_output=True, check=False)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def sha256_text(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def path_value_matches(actual: str, expected: str, repo: Path) -> bool:
    try:
        actual_path = Path(actual)
        expected_path = (repo / expected).resolve()
        if actual_path.is_absolute():
            return actual_path.resolve() == expected_path
        return (repo / actual_path).resolve() == expected_path
    except Exception:
        return False


def snapshot_file_hashes(repo: Path, paths: list[str]) -> dict[str, str | None]:
    hashes: dict[str, str | None] = {}
    for rel in paths:
        path = repo / rel
        hashes[rel] = sha256_text(path) if path.exists() else None
    return hashes


def materialize_case_repo(case: dict, provider: str) -> tuple[Path, dict]:
    repo = REPOS / f'{provider}-{case["name"]}'
    ensure_git_repo(repo)
    bootstrap, _, _ = run_with_progress(
        ['python3', str(ROOT / 'install-bootstrap.py'), '-p', str(repo)],
        cwd=ROOT,
        timeout_seconds=180,
        label=f'bootstrap {provider}/{case["name"]}',
    )
    write_text(RESULTS / f'{provider}-{case["name"]}.bootstrap.stdout.txt', bootstrap.stdout)
    write_text(RESULTS / f'{provider}-{case["name"]}.bootstrap.stderr.txt', bootstrap.stderr)
    if bootstrap.returncode != 0:
        raise RuntimeError(f'bootstrap install failed for {provider}:{case["name"]}')
    for rel, content in case.get('setup_files', {}).items():
        write_text(repo / rel, content)
    target_file = case['target_file_template'].format(provider=provider)
    schema_path = repo / '.tmp' / 'real-harness-output-schema.json'
    write_text(schema_path, json.dumps(case['output_schema'], ensure_ascii=False, indent=2) + '\n')
    tracked_paths = sorted(
        {
            assertion.get('path_template', '').format(provider=provider)
            for assertion in case.get('assertions', [])
            if assertion.get('type') == 'file-unchanged' and assertion.get('path_template')
        }
        | {
            assertion.get('path')
            for assertion in case.get('assertions', [])
            if assertion.get('type') == 'file-unchanged' and assertion.get('path')
        }
    )
    metadata = {
        'target_file': target_file,
        'schema_path': str(schema_path),
        'file_hashes_before': snapshot_file_hashes(repo, [path for path in tracked_paths if path]),
    }
    return repo, metadata


def build_prompt(case: dict, metadata: dict) -> str:
    return case['prompt_template'].format(target_file=metadata['target_file'])


def build_command(provider: str, repo: Path, case: dict, metadata: dict) -> tuple[list[str], Path | None]:
    prompt = build_prompt(case, metadata)
    if provider == 'codex':
        last_message_path = repo / '.tmp' / 'codex-last-message.json'
        cmd = [
            'codex',
            'exec',
            '--sandbox',
            'workspace-write',
            '-c',
            'approval_policy="never"',
            '--skip-git-repo-check',
            '--output-schema',
            metadata['schema_path'],
            '--output-last-message',
            str(last_message_path),
            '-C',
            str(repo),
            prompt,
        ]
        return cmd, last_message_path
    if provider == 'claude':
        cmd = [
            'claude',
            '-p',
            '--dangerously-skip-permissions',
            '--output-format',
            'json',
            '--json-schema',
            json.dumps(case['output_schema'], ensure_ascii=False),
            prompt,
        ]
        return cmd, None
    raise ValueError(f'unsupported provider: {provider}')


def parse_provider_output(provider: str, stdout: str, last_message_path: Path | None) -> tuple[dict | None, str | None]:
    try:
        if provider == 'codex':
            if last_message_path is None or not last_message_path.exists():
                return None, 'missing_codex_output_last_message'
            return json.loads(last_message_path.read_text(encoding='utf-8')), None
        if provider == 'claude':
            payload = json.loads(stdout)
            structured = payload.get('structured_output')
            if structured is None:
                return None, 'missing_claude_structured_output'
            return structured, None
    except json.JSONDecodeError as exc:
        return None, f'json_decode_error:{exc}'
    return None, 'unknown_provider'


def render_value(template: str | None, metadata: dict) -> str | None:
    if template is None:
        return None
    return template.format(target_file=metadata['target_file'])


def is_retryable_provider_failure(process: subprocess.CompletedProcess[str]) -> bool:
    haystack = f'{process.stdout}\n{process.stderr}'.lower()
    return any(marker.lower() in haystack for marker in RETRYABLE_ERROR_MARKERS)


def read_json_path(data: object, key_path: str) -> tuple[bool, object]:
    current = data
    for part in key_path.split('.'):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def evaluate_assertion(assertion: dict, repo: Path, output_json: dict | None, process: subprocess.CompletedProcess[str], metadata: dict) -> str | None:
    assertion_type = assertion['type']
    if assertion_type == 'exit-code':
        expected = assertion['value']
        if process.returncode != expected:
            return f'exit_code_expected_{expected}_got_{process.returncode}'
        return None

    if assertion_type == 'json-key-exists':
        if output_json is None or assertion['key'] not in output_json:
            return f'json_key_missing:{assertion["key"]}'
        return None

    if assertion_type == 'json-list-contains':
        if output_json is None:
            return f'json_missing_for_list_contains:{assertion["key"]}'
        expected = render_value(assertion.get('value_template'), metadata) or assertion.get('value')
        value = output_json.get(assertion['key'])
        if not isinstance(value, list):
            return f'json_list_missing:{assertion["key"]}:{expected}'
        if expected in value:
            return None
        if any(isinstance(item, str) and path_value_matches(item, expected, repo) for item in value):
            return None
        return f'json_list_missing:{assertion["key"]}:{expected}'

    path_str = render_value(assertion.get('path_template'), metadata) or assertion.get('path')
    if path_str is None:
        return f'assertion_missing_path:{assertion_type}'
    path = repo / path_str

    if assertion_type == 'file-exists':
        if not path.exists():
            return f'file_missing:{path_str}'
        return None

    if assertion_type == 'file-unchanged':
        current_hash = sha256_text(path) if path.exists() else None
        before_hash = metadata.get('file_hashes_before', {}).get(path_str)
        if before_hash != current_hash:
            return f'file_changed:{path_str}'
        return None

    if assertion_type in {'json-file-key-exists', 'json-file-key-equals'}:
        if not path.exists():
            return f'file_missing:{path_str}'
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as exc:
            return f'json_file_decode_error:{path_str}:{exc}'
        exists, current_value = read_json_path(data, assertion['key'])
        if not exists:
            return f'json_file_key_missing:{path_str}:{assertion["key"]}'
        if assertion_type == 'json-file-key-exists':
            return None
        if current_value != assertion.get('value'):
            return f'json_file_key_expected:{path_str}:{assertion["key"]}:{assertion.get("value")}!= {current_value}'
        return None

    if not path.exists():
        return f'file_missing:{path_str}'

    text = path.read_text(encoding='utf-8')
    value = render_value(assertion.get('value_template'), metadata) or assertion.get('value')

    if assertion_type == 'file-contains':
        if value not in text:
            return f'file_missing_text:{path_str}:{value}'
        return None

    if assertion_type == 'file-contains-any':
        values = assertion.get('values', [])
        if not values:
            return f'assertion_missing_values:{assertion_type}'
        if not any(item in text for item in values):
            return f'file_missing_any_text:{path_str}:{values}'
        return None

    if assertion_type == 'file-not-contains':
        if value in text:
            return f'file_unexpected_text:{path_str}:{value}'
        return None

    return f'unsupported_assertion:{assertion_type}'


def run_case(provider: str, case: dict) -> dict:
    repo, metadata = materialize_case_repo(case, provider)
    cmd, last_message_path = build_command(provider, repo, case, metadata)
    stem = f'{provider}-{case["name"]}'
    case_started_at = now_iso()
    log_progress(f'[case] provider={provider} case={case["name"]} repo={repo.relative_to(ROOT)}')

    process: subprocess.CompletedProcess[str] | None = None
    timed_out = False
    output_json: dict | None = None
    parse_error: str | None = None
    failures: list[str] = []
    attempts: list[dict] = []
    case_duration_seconds = 0.0

    for attempt in range(1, MAX_PROVIDER_ATTEMPTS + 1):
        attempt_started_at = now_iso()
        process, timed_out, elapsed = run_with_progress(
            cmd,
            cwd=repo,
            timeout_seconds=case.get('timeout_seconds', 420),
            label=f'{provider}/{case["name"]} attempt={attempt}',
        )
        attempt_finished_at = now_iso()
        case_duration_seconds += elapsed

        write_text(RESULTS / f'{stem}.attempt{attempt}.stdout.txt', process.stdout)
        write_text(RESULTS / f'{stem}.attempt{attempt}.stderr.txt', process.stderr)

        output_json, parse_error = parse_provider_output(provider, process.stdout, last_message_path)
        failures = []
        if parse_error:
            failures.append(parse_error)

        for assertion in case.get('assertions', []):
            failure = evaluate_assertion(assertion, repo, output_json, process, metadata)
            if failure:
                failures.append(failure)

        should_retry = attempt < MAX_PROVIDER_ATTEMPTS and (timed_out or is_retryable_provider_failure(process))
        attempts.append(
            {
                'attempt': attempt,
                'started_at': attempt_started_at,
                'finished_at': attempt_finished_at,
                'duration_seconds': round(elapsed, 2),
                'returncode': process.returncode,
                'timed_out': timed_out,
                'retry_scheduled': should_retry,
            }
        )
        if not should_retry:
            break
        log_progress(f'[retry] {provider}/{case["name"]} attempt={attempt} will retry after transient failure')
        time.sleep(attempt)

    assert process is not None

    write_text(RESULTS / f'{stem}.stdout.txt', process.stdout)
    write_text(RESULTS / f'{stem}.stderr.txt', process.stderr)
    if output_json is not None:
        write_text(RESULTS / f'{stem}.structured-output.json', json.dumps(output_json, ensure_ascii=False, indent=2) + '\n')

    case_finished_at = now_iso()
    result = {
        'provider': provider,
        'case': case['name'],
        'ok': not timed_out and not failures,
        'timed_out': timed_out,
        'returncode': process.returncode,
        'started_at': case_started_at,
        'finished_at': case_finished_at,
        'duration_seconds': round(case_duration_seconds, 2),
        'target_repo': str(repo.relative_to(ROOT)),
        'target_file': metadata['target_file'],
        'attempts': attempts,
        'failed_assertions': failures,
        'manual_review': case.get('manual_review', []),
    }
    write_text(RESULTS / f'{stem}.result.json', json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    status = 'PASS' if result['ok'] else 'FAIL'
    log_progress(f'[result] {provider}/{case["name"]} -> {status}')
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run real Codex/Claude CLI harness against agentwork bootstrap.')
    parser.add_argument('--provider', choices=SUPPORTED_PROVIDERS, action='append', dest='providers', help='provider to run; default runs all available providers')
    parser.add_argument('--case', action='append', dest='cases', help='case name without .json; default runs all cases')
    parser.add_argument('--heartbeat-seconds', type=int, default=DEFAULT_HEARTBEAT_SECONDS, help='progress heartbeat interval while a provider case is running')
    return parser.parse_args()


def main() -> int:
    global HEARTBEAT_SECONDS
    args = parse_args()
    HEARTBEAT_SECONDS = max(1, args.heartbeat_seconds)
    requested_providers = args.providers or list(SUPPORTED_PROVIDERS)
    providers = which_available(requested_providers)
    if not providers:
        raise SystemExit('no supported provider executable found (expected codex and/or claude)')

    requested_case_names = set(args.cases or [])
    case_paths = sorted(CASE_ROOT.glob('*.json'))
    if requested_case_names:
        case_paths = [path for path in case_paths if path.stem in requested_case_names]
    if not case_paths:
        raise SystemExit('no case files selected')

    if TMP.exists():
        shutil.rmtree(TMP)
    REPOS.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)

    case_dicts = [load_case(path) for path in case_paths]
    log_progress(f'[harness] providers={providers} cases={[case["name"] for case in case_dicts]} heartbeat={HEARTBEAT_SECONDS}s')
    results: list[dict] = []
    for provider in providers:
        for case in case_dicts:
            results.append(run_case(provider, case))
            write_summary_reports('summary.latest', summarize_results(providers, case_dicts, results))

    summary = summarize_results(providers, case_dicts, results)
    write_summary_reports('summary', summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if all(result['ok'] for result in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
