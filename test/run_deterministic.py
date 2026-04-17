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
TOOLS_ROOT = ROOT / '.agentwork' / 'tools'
REGISTRY = TOOLS_ROOT / 'registry.json'
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
            'project 轻量索引与本地 project 文档保留使用脚本硬校验，不做评分。',
            'tools 的安装/卸载路径与 bootstrap 隔离使用脚本硬校验。',
            'tools 的真实可用性仍保留人工审查入口，不在 deterministic harness 中自动评分。',
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


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding='utf-8'))


def tool_targets(tool_name: str) -> list[str]:
    registry = load_registry()
    for tool in registry.get('tools', []):
        if tool.get('name') != tool_name:
            continue
        tool_meta_path = TOOLS_ROOT / tool['dir'] / 'tool.json'
        tool_meta = json.loads(tool_meta_path.read_text(encoding='utf-8'))
        return [entry['to'] for entry in tool_meta.get('entries', [])]
    raise ValueError(f'unknown tool: {tool_name}')


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
    (existing / '.shared/project/sample.md').write_text('# Project: sample\n\n- local keep\n', encoding='utf-8')
    (existing / '.shared/session/README.md').write_text('# Session 目录说明\n\n## 本项目补充说明\n- local keep\n', encoding='utf-8')
    (existing / '.gitignore').write_text('node_modules/\n.local-cache/\n', encoding='utf-8')
    existing_install = run(['python3', str(ROOT / 'install-bootstrap.py'), '-p', str(existing)])
    write_process_logs('existing-bootstrap', existing_install)
    existing_reinstall = run(['python3', str(ROOT / 'install-bootstrap.py'), '-p', str(existing)])
    write_process_logs('existing-bootstrap-reinstall', existing_reinstall)
    existing_contract = run(['python3', str(ROOT / 'test/check_bootstrap_contract.py'), str(existing)])
    write_process_logs('existing-bootstrap-contract', existing_contract)
    existing_project_doc = (existing / '.shared/project/sample.md').read_text(encoding='utf-8')
    existing_project_doc_ok = 'local keep' in existing_project_doc
    existing_gitignore = (existing / '.gitignore').read_text(encoding='utf-8')
    existing_gitignore_ok = (
        'node_modules/' in existing_gitignore
        and '.local-cache/' in existing_gitignore
        and existing_gitignore.count('.tmp/') == 1
    )

    details = {
        'ok': (
            fresh_contract.returncode == 0
            and existing_contract.returncode == 0
            and existing_project_doc_ok
            and existing_gitignore_ok
            and existing_reinstall.returncode == 0
        ),
        'fresh_install_contract_stdout': fresh_contract.stdout.strip(),
        'fresh_install_contract_stderr': fresh_contract.stderr.strip(),
        'existing_reinstall_contract_stdout': existing_contract.stdout.strip(),
        'existing_reinstall_contract_stderr': existing_contract.stderr.strip(),
        'existing_reinstall_stdout': existing_reinstall.stdout.strip(),
        'existing_reinstall_stderr': existing_reinstall.stderr.strip(),
        'existing_project_doc_ok': existing_project_doc_ok,
        'existing_gitignore_ok': existing_gitignore_ok,
    }
    results.append(
        scenario_result(
            'bootstrap_contract',
            [
                ('fresh-bootstrap', fresh_install),
                ('existing-bootstrap', existing_install),
                ('existing-bootstrap-reinstall', existing_reinstall),
            ],
            details,
        )
    )

    figma_targets = tool_targets('figma')
    architecture_targets = tool_targets('architecture')

    tool_seeded_source = REPOS / 'tool-seeded-source'
    shutil.copytree(ROOT, tool_seeded_source, ignore=SELF_SOURCE_COPY_IGNORE)
    tool_seed_install = run(['python3', str(tool_seeded_source / 'install-tool.py'), 'install', 'figma', '-p', str(tool_seeded_source)])
    write_process_logs('tool-seeded-source-install-figma', tool_seed_install)
    tool_seeded_ok = all((tool_seeded_source / rel).exists() for rel in figma_targets)

    isolated = REPOS / 'isolated-from-tool-seeded-source'
    ensure_git_repo(isolated)
    isolated_install = run(['python3', str(tool_seeded_source / 'install-bootstrap.py'), '-p', str(isolated)])
    write_process_logs('isolated-bootstrap-from-tool-seeded-source', isolated_install)
    leaked_targets = [rel for rel in figma_targets if (isolated / rel).exists()]
    details = {
        'ok': tool_seed_install.returncode == 0 and isolated_install.returncode == 0 and tool_seeded_ok and not leaked_targets,
        'tool_seeded_ok': tool_seeded_ok,
        'leaked_targets': leaked_targets,
        'stdout': isolated_install.stdout.strip(),
        'stderr': isolated_install.stderr.strip(),
    }
    results.append(
        scenario_result(
            'bootstrap_optional_tool_isolation',
            [
                ('tool-seeded-source-install-figma', tool_seed_install),
                ('isolated-bootstrap-from-tool-seeded-source', isolated_install),
            ],
            details,
        )
    )

    tool_lifecycle = REPOS / 'tool-lifecycle'
    ensure_git_repo(tool_lifecycle)
    tool_lifecycle_bootstrap = run(['python3', str(ROOT / 'install-bootstrap.py'), '-p', str(tool_lifecycle)])
    write_process_logs('tool-lifecycle-bootstrap', tool_lifecycle_bootstrap)
    legacy_tool_install = run(['python3', str(ROOT / 'install-tool.py'), 'figma', '-p', str(tool_lifecycle)])
    write_process_logs('tool-lifecycle-legacy-install-figma', legacy_tool_install)
    legacy_short_tool_install = run(['python3', str(ROOT / 'install-tool.py'), 'i', 'figma', '-p', str(tool_lifecycle)])
    write_process_logs('tool-lifecycle-legacy-short-install-figma', legacy_short_tool_install)
    legacy_long_flag_install = run(['python3', str(ROOT / 'install-tool.py'), '--install', 'figma', '-p', str(tool_lifecycle)])
    write_process_logs('tool-lifecycle-legacy-long-flag-install-figma', legacy_long_flag_install)
    tool_install = run(['python3', str(ROOT / 'install-tool.py'), '-i', 'figma', '-p', str(tool_lifecycle)])
    write_process_logs('tool-lifecycle-install-figma', tool_install)
    installed_targets = [rel for rel in figma_targets if (tool_lifecycle / rel).exists()]
    tool_uninstall = run(['python3', str(ROOT / 'install-tool.py'), '-u', 'figma', '-p', str(tool_lifecycle)])
    write_process_logs('tool-lifecycle-uninstall-figma', tool_uninstall)
    tool_list = run(['python3', str(ROOT / 'install-tool.py'), '-l'])
    write_process_logs('tool-list-short', tool_list)
    remaining_targets = [rel for rel in figma_targets if (tool_lifecycle / rel).exists()]
    core_files_preserved = all(
        (tool_lifecycle / rel).exists()
        for rel in [
            '.shared/commands/session.md',
            '.shared/project/index.md',
            '.shared/session/README.md',
        ]
    )
    details = {
        'ok': (
            tool_lifecycle_bootstrap.returncode == 0
            and legacy_tool_install.returncode != 0
            and legacy_short_tool_install.returncode != 0
            and legacy_long_flag_install.returncode != 0
            and tool_install.returncode == 0
            and tool_uninstall.returncode == 0
            and tool_list.returncode == 0
            and 'figma' in tool_list.stdout
            and len(installed_targets) == len(figma_targets)
            and not remaining_targets
            and core_files_preserved
        ),
        'legacy_install_stdout': legacy_tool_install.stdout.strip(),
        'legacy_install_stderr': legacy_tool_install.stderr.strip(),
        'legacy_short_install_stdout': legacy_short_tool_install.stdout.strip(),
        'legacy_short_install_stderr': legacy_short_tool_install.stderr.strip(),
        'legacy_long_flag_install_stdout': legacy_long_flag_install.stdout.strip(),
        'legacy_long_flag_install_stderr': legacy_long_flag_install.stderr.strip(),
        'installed_targets': installed_targets,
        'remaining_targets': remaining_targets,
        'core_files_preserved': core_files_preserved,
        'list_stdout': tool_list.stdout.strip(),
        'list_stderr': tool_list.stderr.strip(),
        'install_stdout': tool_install.stdout.strip(),
        'install_stderr': tool_install.stderr.strip(),
        'uninstall_stdout': tool_uninstall.stdout.strip(),
        'uninstall_stderr': tool_uninstall.stderr.strip(),
    }
    results.append(
        scenario_result(
            'tool_install_uninstall',
            [
                ('tool-lifecycle-bootstrap', tool_lifecycle_bootstrap),
                ('tool-lifecycle-install-figma', tool_install),
                ('tool-lifecycle-uninstall-figma', tool_uninstall),
                ('tool-list-short', tool_list),
            ],
            details,
        )
    )

    architecture_smoke = REPOS / 'architecture-smoke'
    ensure_git_repo(architecture_smoke)
    architecture_bootstrap = run(['python3', str(ROOT / 'install-bootstrap.py'), '-p', str(architecture_smoke)])
    write_process_logs('architecture-smoke-bootstrap', architecture_bootstrap)
    architecture_install = run(['python3', str(ROOT / 'install-tool.py'), '-i', 'architecture', '-p', str(architecture_smoke)])
    write_process_logs('architecture-smoke-install', architecture_install)
    architecture_installed = all((architecture_smoke / rel).exists() for rel in architecture_targets)
    example_src = architecture_smoke / '.shared/templates/architecture/examples/architecture-tool'
    example_dst = architecture_smoke / 'docs/architecture'
    shutil.copytree(example_src, example_dst)
    architecture_render = run(
        [
            'python3',
            str(architecture_smoke / '.shared/scripts/architecture-render.py'),
            str(example_dst),
            '--recursive',
        ],
        cwd=architecture_smoke,
    )
    write_process_logs('architecture-smoke-render', architecture_render)
    root_html = example_dst / 'index.html'
    child_html = example_dst / 'nodes/renderer-runtime/index.html'
    root_html_text = root_html.read_text(encoding='utf-8') if root_html.exists() else ''
    child_html_text = child_html.read_text(encoding='utf-8') if child_html.exists() else ''
    root_html_ok = root_html.exists() and 'nodes/renderer-runtime/index.html' in root_html_text and 'Architecture Tool Overview' in root_html_text
    child_html_ok = child_html.exists() and '../../index.html' in child_html_text and 'Renderer Runtime Detail' in child_html_text
    auto_canvas = architecture_smoke / 'docs/architecture-auto'
    auto_canvas.mkdir(parents=True, exist_ok=True)
    (auto_canvas / 'diagram.arch.json').write_text(
        json.dumps(
            {
                'id': 'auto-canvas',
                'title': 'Auto Canvas',
                'summary': 'viewport width/height act as minimum values',
                'viewport': {
                    'width': 400,
                    'height': 280,
                },
                'nodes': [
                    {
                        'id': 'wide-node',
                        'label': 'Wide Node',
                        'kind': 'backend',
                        'x': 520,
                        'y': 220,
                        'w': 180,
                        'h': 110,
                        'lines': ['forces canvas expansion'],
                    }
                ],
                'edges': [],
                'cards': [],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding='utf-8',
    )
    auto_canvas_render = run(
        [
            'python3',
            str(architecture_smoke / '.shared/scripts/architecture-render.py'),
            str(auto_canvas),
        ],
        cwd=architecture_smoke,
    )
    write_process_logs('architecture-auto-canvas-render', auto_canvas_render)
    auto_canvas_html = auto_canvas / 'index.html'
    auto_canvas_text = auto_canvas_html.read_text(encoding='utf-8') if auto_canvas_html.exists() else ''
    auto_canvas_ok = (
        auto_canvas_render.returncode == 0
        and auto_canvas_html.exists()
        and '<svg width="730" height="360"' in auto_canvas_text
    )
    details = {
        'ok': (
            architecture_bootstrap.returncode == 0
            and architecture_install.returncode == 0
            and architecture_render.returncode == 0
            and auto_canvas_render.returncode == 0
            and architecture_installed
            and root_html_ok
            and child_html_ok
            and auto_canvas_ok
        ),
        'architecture_installed': architecture_installed,
        'root_html_ok': root_html_ok,
        'child_html_ok': child_html_ok,
        'auto_canvas_ok': auto_canvas_ok,
        'render_stdout': architecture_render.stdout.strip(),
        'render_stderr': architecture_render.stderr.strip(),
        'auto_canvas_render_stdout': auto_canvas_render.stdout.strip(),
        'auto_canvas_render_stderr': auto_canvas_render.stderr.strip(),
    }
    results.append(
        scenario_result(
            'architecture_render_smoke',
            [
                ('architecture-smoke-bootstrap', architecture_bootstrap),
                ('architecture-smoke-install', architecture_install),
                ('architecture-smoke-render', architecture_render),
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
        '.shared/project/agentwork.md',
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
    self_source_agents = (self_source / 'AGENTS.md').read_text(encoding='utf-8')
    self_source_root_ok = (
        'source repo 的安装入口：`install-bootstrap.py`、`install-tool.py`' in self_source_agents
        and '这是目标项目的启动说明版本。' not in self_source_agents
    )
    details = {
        'ok': self_source_install.returncode == 0 and not self_source_missing and self_source_root_ok,
        'stdout': self_source_install.stdout.strip(),
        'stderr': self_source_install.stderr.strip(),
        'missing': self_source_missing,
        'source_root_agents_ok': self_source_root_ok,
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
