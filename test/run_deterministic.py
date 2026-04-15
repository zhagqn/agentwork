#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / '.tmp' / 'harness'
REPOS = TMP / 'repos'
RESULTS = TMP / 'results'
SELF_SOURCE_COPY_IGNORE = shutil.ignore_patterns('.git', '.tmp', '__pycache__', '*.pyc')


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True)


def ensure_git_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    run(['git', 'init'], cwd=path)


def write_process_logs(stem: str, process: subprocess.CompletedProcess[str]) -> None:
    (RESULTS / f'{stem}.stdout.txt').write_text(process.stdout, encoding='utf-8')
    (RESULTS / f'{stem}.stderr.txt').write_text(process.stderr, encoding='utf-8')


def scenario_result(name: str, process_logs: list[tuple[str, subprocess.CompletedProcess[str]]], details: dict) -> dict:
    install_failures = [stem for stem, process in process_logs if process.returncode != 0]
    return {
        'name': name,
        'ok': not install_failures and details.get('ok', False),
        'install_failures': install_failures,
        'details': details,
    }


def summary_report(results: list[dict]) -> dict:
    return {
        'design_basis': [
            'bootstrap 基础文件、内容 block 与 skill 结构使用脚本硬校验，不做评分。',
            'tools 仅保留人工审查入口，不在 deterministic harness 中自动评分。',
        ],
        'results': results,
        'manual_review': [
            {
                'name': 'tools_manual_review',
                'status': 'manual',
                'reason': '工具安装是否真正可用高度依赖本机环境与外部服务，当前只建议人工验证。',
            }
        ],
    }


def main() -> int:
    if TMP.exists():
        shutil.rmtree(TMP)
    REPOS.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []

    fresh = REPOS / 'fresh'
    ensure_git_repo(fresh)
    fresh_install = run(['python3', str(ROOT / 'install-bootstrap.py'), '-p', str(fresh)])
    write_process_logs('fresh-bootstrap', fresh_install)
    fresh_contract = run(['python3', str(ROOT / 'test/check_bootstrap_contract.py'), str(fresh)])
    write_process_logs('fresh-bootstrap-contract', fresh_contract)

    existing = REPOS / 'existing'
    ensure_git_repo(existing)
    (existing / '.shared/project').mkdir(parents=True, exist_ok=True)
    (existing / '.shared/session').mkdir(parents=True, exist_ok=True)
    (existing / '.shared/project/local.md').write_text('LOCAL\n', encoding='utf-8')
    (existing / '.shared/project/index.md').write_text('# Project 索引\n\n## 本项目自定义内容\n- local keep\n', encoding='utf-8')
    (existing / '.shared/session/README.md').write_text('# Session 目录说明\n\n## 本项目补充说明\n- local keep\n', encoding='utf-8')
    existing_install = run(['python3', str(ROOT / 'install-bootstrap.py'), '-p', str(existing)])
    write_process_logs('existing-bootstrap', existing_install)
    existing_contract = run(['python3', str(ROOT / 'test/check_bootstrap_contract.py'), str(existing)])
    write_process_logs('existing-bootstrap-contract', existing_contract)

    details = {
        'ok': fresh_contract.returncode == 0 and existing_contract.returncode == 0,
        'fresh_install_contract_stdout': fresh_contract.stdout.strip(),
        'fresh_install_contract_stderr': fresh_contract.stderr.strip(),
        'existing_reinstall_contract_stdout': existing_contract.stdout.strip(),
        'existing_reinstall_contract_stderr': existing_contract.stderr.strip(),
    }
    results.append(
        scenario_result(
            'bootstrap_contract',
            [
                ('fresh-bootstrap', fresh_install),
                ('existing-bootstrap', existing_install),
            ],
            details,
        )
    )

    self_source = REPOS / 'self-source'
    shutil.copytree(ROOT, self_source, ignore=SELF_SOURCE_COPY_IGNORE)
    self_source_install = run(['python3', str(self_source / 'install-bootstrap.py'), '-p', str(self_source)])
    write_process_logs('self-source-bootstrap', self_source_install)
    self_source_required = [
        'AGENTS.md',
        '.shared/INDEX.md',
        '.claude/CLAUDE.md',
        '.claude/commands/session.md',
        '.agent/rules/bootstrap.md',
        '.agent/workflows/session.md',
        '.cursor/rules/agentwork-bootstrap.mdc',
        '.github/copilot-instructions.md',
    ]
    self_source_missing = [
        rel for rel in self_source_required if not (self_source / rel).exists()
    ]
    details = {
        'ok': self_source_install.returncode == 0 and not self_source_missing,
        'stdout': self_source_install.stdout.strip(),
        'stderr': self_source_install.stderr.strip(),
        'missing': self_source_missing,
    }
    results.append(
        scenario_result(
            'bootstrap_self_source',
            [('self-source-bootstrap', self_source_install)],
            details,
        )
    )

    report = summary_report(results)
    (RESULTS / 'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all(result['ok'] for result in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
