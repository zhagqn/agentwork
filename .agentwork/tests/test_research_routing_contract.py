#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER = REPO_ROOT / 'install-tool.py'
TOOLS_ROOT = REPO_ROOT / '.agentwork/tools'
REGISTRY = TOOLS_ROOT / 'registry.json'
ROUTING_CASES = TOOLS_ROOT / 'research/evals/routing-cases.json'
STACK = ('research', 'exa', 'octocode')
PROVIDERS = STACK[1:]
MCP_CONFIG_PATHS = (
    '.mcp.json',
    '.cursor/mcp.json',
    '.codex/config.toml',
    '.claude/settings.json',
    'opencode.jsonc',
)


def load_manifest(name: str) -> dict:
    return json.loads((TOOLS_ROOT / name / 'tool.json').read_text(encoding='utf-8'))


def tree_snapshot(path: Path) -> dict[str, tuple[str, bytes | str | None]]:
    paths = [path]
    if path.is_dir() and not path.is_symlink():
        paths.extend(sorted(path.rglob('*')))
    snapshot: dict[str, tuple[str, bytes | str | None]] = {}
    for item in paths:
        relative = '.' if item == path else item.relative_to(path).as_posix()
        if item.is_symlink():
            snapshot[relative] = ('symlink', os.readlink(item))
        elif item.is_dir():
            snapshot[relative] = ('directory', None)
        else:
            snapshot[relative] = ('file', item.read_bytes())
    return snapshot


class ResearchRoutingContractTest(unittest.TestCase):
    def test_source_has_one_research_skill_and_independent_providers(self) -> None:
        registry = json.loads(REGISTRY.read_text(encoding='utf-8'))
        stack_entries = {
            item['name']: item
            for item in registry['tools']
            if item['name'] in STACK
        }
        self.assertEqual(set(stack_entries), set(STACK))
        self.assertEqual(stack_entries['research']['kind'], ['skill'])

        research = load_manifest('research')
        self.assertNotIn('env_keys', research)
        self.assertEqual(research['kind'], ['skill'])
        self.assertEqual(
            {entry['surface'] for entry in research['entries']},
            {'shared', 'codex', 'claude', 'pi', 'cursor'},
        )
        self.assertFalse(any('/mcp/' in entry['to'] for entry in research['entries']))
        self.assertFalse(any('/scripts/' in entry['to'] for entry in research['entries']))

        provider_targets: dict[str, set[str]] = {}
        for provider in PROVIDERS:
            manifest = load_manifest(provider)
            with self.subTest(provider=provider):
                self.assertNotIn('skill', manifest['kind'])
                self.assertNotIn('command', manifest['kind'])
                self.assertTrue(manifest['entries'])
                self.assertTrue(all(entry['surface'] == 'shared' for entry in manifest['entries']))
                self.assertTrue(all(
                    entry['to'].startswith(('.shared/mcp/', '.shared/scripts/'))
                    for entry in manifest['entries']
                ))
                self.assertEqual(list((TOOLS_ROOT / provider).rglob('SKILL.md')), [])
                provider_targets[provider] = {entry['to'] for entry in manifest['entries']}

        self.assertEqual(
            [key['name'] for key in load_manifest('exa')['env_keys']],
            ['EXA_API_KEY'],
        )
        self.assertNotIn('env_keys', load_manifest('octocode'))
        all_provider_targets = set().union(*provider_targets.values())
        self.assertEqual(
            len(all_provider_targets),
            sum(len(targets) for targets in provider_targets.values()),
        )
        self.assertTrue(all(
            entry['to'] not in all_provider_targets for entry in research['entries']
        ))

        routing = json.loads(ROUTING_CASES.read_text(encoding='utf-8'))
        forbidden = tuple(routing['prompt_forbidden_provider_names'])
        self.assertEqual(set(forbidden), set(routing['remote_providers']))
        self.assertEqual(len(routing['cases']), 12)
        self.assertEqual(len(routing['hard_gate_case_ids']), 7)
        self.assertEqual(len(routing['fallback_case_ids']), 2)
        for case in routing['cases']:
            with self.subTest(case=case['id']):
                prompt = case['prompt'].lower()
                self.assertFalse(any(name in prompt for name in forbidden))

        cases = {case['id']: case for case in routing['cases']}
        for case_id in ('exact-version-docs', 'missing-version-docs'):
            with self.subTest(case=case_id):
                self.assertEqual(cases[case_id]['remote_provider_limit'], 0)

        self.assertIn('- provisional', (TOOLS_ROOT / 'research/README.md').read_text())
        self.assertIn('- provisional', (TOOLS_ROOT / 'exa/README.md').read_text())
        for provider in PROVIDERS:
            reference = (TOOLS_ROOT / provider / 'shared/mcp' / f'{provider}.md').read_text()
            with self.subTest(provider=provider):
                self.assertIn('.codex/config.toml', reference)
                self.assertNotIn(f'codex mcp add {provider}', reference)
                self.assertIn(f'claude mcp add --scope local {provider}', reference)

    def test_isolated_install_keeps_one_skill_and_provider_lifecycles_independent(self) -> None:
        with tempfile.TemporaryDirectory(prefix='agentwork-research-routing-') as temp:
            project = Path(temp) / 'project'
            project.mkdir()
            subprocess.run(['git', 'init', '-q', str(project)], check=True)
            boundary = project / 'staged-boundary.txt'
            boundary.write_text('keep staged\n')
            subprocess.run(['git', '-C', str(project), 'add', boundary.name], check=True)
            staged_before = self.staged_hash(project)

            self.run_installer(project, 'install', 'research')
            self.assert_manifest_exact(project, ('research',))
            research_only = self.project_snapshot(project)
            self.run_installer(project, 'install', 'research')
            self.assertEqual(self.project_snapshot(project), research_only)
            self.assertFalse((project / '.env').exists())
            self.assertFalse((project / '.gitignore').exists())
            self.assertFalse((project / '.shared/mcp').exists())
            self.assert_no_platform_mcp_config(project)

            self.run_installer(project, 'install', *PROVIDERS)
            self.assert_manifest_exact(project, STACK)
            self.assertEqual(
                {
                    path.relative_to(project).as_posix()
                    for path in project.rglob('SKILL.md')
                },
                {
                    '.shared/skills/research/SKILL.md',
                    '.codex/skills/research/SKILL.md',
                    '.claude/skills/research/SKILL.md',
                    '.pi/skills/research/SKILL.md',
                },
            )
            self.assertEqual(
                {
                    path.relative_to(project).as_posix()
                    for path in (project / '.cursor/rules').glob('*')
                },
                {'.cursor/rules/research.mdc'},
            )
            self.assertEqual(
                (project / '.env').read_text(),
                '# agentwork:env:exa\n'
                'EXA_API_KEY=\n',
            )
            ignored = subprocess.run(
                ['git', '-C', str(project), 'check-ignore', '--quiet', '.env'],
                check=False,
            )
            self.assertEqual(ignored.returncode, 0)
            self.assert_no_platform_mcp_config(project)
            installed = self.project_snapshot(project)
            self.run_installer(project, 'install', *STACK)
            self.assert_manifest_exact(project, STACK)
            self.assertEqual(self.project_snapshot(project), installed)
            self.assertEqual(self.staged_hash(project), staged_before)

            secret = 'configured-test-value-not-for-output'
            env_path = project / '.env'
            env_path.write_text(env_path.read_text().replace(
                'EXA_API_KEY=',
                f'EXA_API_KEY={secret}',
            ))
            uninstall = self.run_installer(project, 'uninstall', *STACK)
            self.assertNotIn(secret, uninstall.stdout + uninstall.stderr)
            self.assertEqual(env_path.read_text(), f'EXA_API_KEY={secret}\n')
            for name in STACK:
                for entry in load_manifest(name)['entries']:
                    target = project / entry['to']
                    self.assertFalse(target.exists() or target.is_symlink())
            self.assert_no_platform_mcp_config(project)
            after_uninstall = self.project_snapshot(project)
            self.run_installer(project, 'uninstall', *STACK)
            self.assertEqual(self.project_snapshot(project), after_uninstall)
            self.assertEqual(self.staged_hash(project), staged_before)

    def run_installer(
        self,
        project: Path,
        action: str,
        *names: str,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ['python3', str(INSTALLER), action, *names, '-p', str(project)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return result

    def assert_manifest_exact(self, project: Path, names: tuple[str, ...]) -> None:
        for name in names:
            tool_root = TOOLS_ROOT / name
            manifest = load_manifest(name)
            for entry in manifest['entries']:
                source = tool_root / entry['from']
                target = project / entry['to']
                with self.subTest(name=name, target=entry['to']):
                    self.assertTrue(target.exists() or target.is_symlink())
                    self.assertEqual(tree_snapshot(target), tree_snapshot(source))

    def assert_no_platform_mcp_config(self, project: Path) -> None:
        for relative in MCP_CONFIG_PATHS:
            with self.subTest(config=relative):
                self.assertFalse((project / relative).exists())

    def staged_hash(self, project: Path) -> str:
        diff = subprocess.run(
            ['git', '-C', str(project), 'diff', '--cached', '--binary'],
            check=True,
            capture_output=True,
        ).stdout
        return hashlib.sha256(diff).hexdigest()

    def project_snapshot(self, project: Path) -> dict[str, tuple[str, bytes | str | None]]:
        return {
            key: value
            for key, value in tree_snapshot(project).items()
            if key != '.git' and not key.startswith('.git/')
        }


if __name__ == '__main__':
    unittest.main(verbosity=2)
