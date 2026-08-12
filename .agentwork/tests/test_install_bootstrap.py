#!/usr/bin/env python3
from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER = REPO_ROOT / 'install-bootstrap.py'
BOOTSTRAP = REPO_ROOT / '.agentwork/bootstrap'
CONFIG_START = '# >>> AGENTWORK bootstrap: Codex agents >>>'
CONFIG_END = '# <<< AGENTWORK bootstrap: Codex agents <<<'
PROJECT_START = '<!-- AGENTWORK:PROJECT-INDEX:START -->'
PROJECT_END = '<!-- AGENTWORK:PROJECT-INDEX:END -->'
SESSION_START = '<!-- AGENTWORK:SESSION-README:START -->'
SESSION_END = '<!-- AGENTWORK:SESSION-README:END -->'
GITIGNORE_START = '# >>> AGENTWORK bootstrap: tmp artifacts >>>'
GITIGNORE_END = '# <<< AGENTWORK bootstrap: tmp artifacts <<<'
RECEIPT_REL = Path('.agentwork/bootstrap-install-state.json')


def tree_snapshot(path: Path) -> dict[str, tuple[str, bytes | str | None]]:
    snapshot: dict[str, tuple[str, bytes | str | None]] = {}
    for item in [path, *sorted(path.rglob('*'))]:
        relative = '.' if item == path else item.relative_to(path).as_posix()
        if item.is_symlink():
            snapshot[relative] = ('symlink', os.readlink(item))
        elif item.is_dir():
            snapshot[relative] = ('directory', None)
        else:
            snapshot[relative] = ('file', item.read_bytes())
    return snapshot


class InstallBootstrapCodexAgentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix='agentwork-bootstrap-')
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'
        self.project.mkdir()

    def run_installer(
        self,
        *,
        project: Path | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        project = project or self.project
        result = subprocess.run(
            ['python3', str(INSTALLER), '-p', str(project)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if check and result.returncode != 0:
            self.fail(f'installer failed: {result.stderr}{result.stdout}')
        return result

    def receipt(self, project: Path | None = None) -> dict:
        return json.loads(((project or self.project) / RECEIPT_REL).read_text(encoding='utf-8'))

    def load_installer(self):
        module_name = f'agentwork_install_bootstrap_{id(self)}'
        spec = importlib.util.spec_from_file_location(module_name, INSTALLER)
        if spec is None or spec.loader is None:
            self.fail('cannot load bootstrap installer module')
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        self.addCleanup(sys.modules.pop, module_name, None)
        spec.loader.exec_module(module)
        return module

    def prepared_plan(self, module):
        return module.prepare_bootstrap_plan(self.project.resolve())

    def assert_plan_rollback(self, module, plan, pattern: str = 'failed and rolled back') -> None:
        before = tree_snapshot(self.project)
        with redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(SystemExit, pattern):
                module.run_transaction(
                    plan.target,
                    plan.transaction_paths,
                    lambda: module.apply_bootstrap_plan(plan),
                )
        self.assertEqual(tree_snapshot(self.project), before)

    def test_fresh_install_registers_generated_codex_agent(self) -> None:
        self.run_installer()

        installed_agent = self.project / '.codex/agents/luna-worker.toml'
        source_agent = BOOTSTRAP / 'codex/agents/luna-worker.toml'
        self.assertEqual(installed_agent.read_bytes(), source_agent.read_bytes())
        agent = tomllib.loads(installed_agent.read_text(encoding='utf-8'))
        self.assertEqual(agent['model'], 'gpt-5.6-luna')
        self.assertEqual(agent['model_reasoning_effort'], 'max')
        self.assertIn('只负责完成父代理委派', agent['developer_instructions'])
        self.assertNotIn('name', agent)
        self.assertNotIn('description', agent)

        config_text = (self.project / '.codex/config.toml').read_text(encoding='utf-8')
        self.assertEqual(config_text, (BOOTSTRAP / 'codex/config.block.toml').read_text(encoding='utf-8'))
        config = tomllib.loads(config_text)
        role = config['agents']['luna_worker']
        self.assertEqual(role['config_file'], 'agents/luna-worker.toml')
        self.assertIn('范围明确', role['description'])
        self.assertEqual(config_text.count(CONFIG_START), 1)
        self.assertEqual(config_text.count(CONFIG_END), 1)

        receipt = self.receipt()
        self.assertEqual(receipt['schema_version'], 1)
        records = {entry['path']: entry for entry in receipt['files']}
        source_command = REPO_ROOT / '.shared/commands/brain.md'
        self.assertEqual(records['.shared/commands/brain.md']['type'], 'file')
        self.assertEqual(
            records['.shared/commands/brain.md']['sha256'],
            hashlib.sha256(source_command.read_bytes()).hexdigest(),
        )
        self.assertNotIn(str(self.project), (self.project / RECEIPT_REL).read_text())

    def test_reinstall_preserves_other_config_and_agents(self) -> None:
        codex = self.project / '.codex'
        (codex / 'agents').mkdir(parents=True)
        custom_agent = codex / 'agents/reviewer.toml'
        custom_agent.write_bytes(b'model = "custom-model"\n')
        custom_config = (
            b'model = "project-model"\r\n\r\n'
            b'[agents.reviewer]\r\n'
            b'description = "project role"\r\n'
            b'config_file = "agents/reviewer.toml"\r\n'
        )
        (codex / 'config.toml').write_bytes(custom_config)

        self.run_installer()
        first_config = (codex / 'config.toml').read_bytes()
        self.run_installer()

        self.assertEqual((codex / 'config.toml').read_bytes(), first_config)
        self.assertTrue(first_config.startswith(custom_config))
        self.assertEqual(custom_agent.read_bytes(), b'model = "custom-model"\n')
        config = tomllib.loads(first_config.decode('utf-8'))
        self.assertIn('reviewer', config['agents'])
        self.assertIn('luna_worker', config['agents'])

    def test_receipt_is_stable_across_reinstall(self) -> None:
        self.run_installer()
        first = (self.project / RECEIPT_REL).read_bytes()
        self.run_installer()
        self.assertEqual((self.project / RECEIPT_REL).read_bytes(), first)

    def test_reinstall_preserves_managed_block_context_and_unmanaged_files(self) -> None:
        project_index = self.project / '.shared/project/index.md'
        session_readme = self.project / '.shared/session/README.md'
        project_index.parent.mkdir(parents=True)
        session_readme.parent.mkdir(parents=True)
        project_index.write_text('# Project-owned prefix\n', encoding='utf-8')
        session_readme.write_text('# Session-owned prefix\n', encoding='utf-8')
        (self.project / '.gitignore').write_text('node_modules/\n/.tmp/\n', encoding='utf-8')
        self.run_installer()

        for path in (project_index, session_readme):
            path.write_text(path.read_text(encoding='utf-8') + '\nProject-owned suffix\n', encoding='utf-8')
        optional_file = self.project / '.shared/skills/browser/SKILL.md'
        optional_file.parent.mkdir(parents=True)
        optional_file.write_text('project optional tool\n', encoding='utf-8')
        receipt_outside_file = self.project / '.codex/skills/brain/project-notes.md'
        receipt_outside_file.write_text('project notes\n', encoding='utf-8')

        self.run_installer()
        after_second = tree_snapshot(self.project)
        self.run_installer()

        self.assertEqual(tree_snapshot(self.project), after_second)
        for path, prefix in (
            (project_index, '# Project-owned prefix\n'),
            (session_readme, '# Session-owned prefix\n'),
        ):
            text = path.read_text(encoding='utf-8')
            self.assertTrue(text.startswith(prefix))
            self.assertTrue(text.endswith('Project-owned suffix\n'))
        self.assertEqual((self.project / '.gitignore').read_text(encoding='utf-8'), 'node_modules/\n/.tmp/\n')
        self.assertEqual(optional_file.read_text(encoding='utf-8'), 'project optional tool\n')
        self.assertEqual(receipt_outside_file.read_text(encoding='utf-8'), 'project notes\n')

    def test_malformed_managed_blocks_fail_without_writes(self) -> None:
        targets = (
            ('.shared/project/index.md', PROJECT_START, PROJECT_END),
            ('.shared/session/README.md', SESSION_START, SESSION_END),
            ('.gitignore', GITIGNORE_START, GITIGNORE_END),
        )
        variants = (
            ('start-only', lambda start, end: f'prefix\n{start}\nproject data\n'),
            ('end-only', lambda start, end: f'prefix\n{end}\nproject data\n'),
            ('reversed', lambda start, end: f'prefix\n{end}\nproject data\n{start}\n'),
            ('duplicate', lambda start, end: f'{start}\none\n{end}\n{start}\ntwo\n{end}\n'),
        )
        for target_index, (rel, start, end) in enumerate(targets):
            for variant_index, (name, content) in enumerate(variants):
                with self.subTest(path=rel, variant=name):
                    project = Path(self.temp.name) / f'malformed-{target_index}-{variant_index}'
                    path = project / rel
                    path.parent.mkdir(parents=True)
                    path.write_text(content(start, end), encoding='utf-8')
                    before = tree_snapshot(project)

                    result = self.run_installer(project=project, check=False)

                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(rel, result.stderr)
                    self.assertIn('agentwork managed block', result.stderr)
                    self.assertNotIn('Traceback (most recent call last)', result.stderr)
                    self.assertEqual(tree_snapshot(project), before)

    def test_non_utf8_managed_files_fail_without_writes_or_traceback(self) -> None:
        for index, rel in enumerate(('.shared/project/index.md', '.shared/session/README.md', '.gitignore')):
            with self.subTest(path=rel):
                project = Path(self.temp.name) / f'non-utf8-{index}'
                path = project / rel
                path.parent.mkdir(parents=True)
                path.write_bytes(b'\xff\xfe')
                before = tree_snapshot(project)

                result = self.run_installer(project=project, check=False)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(rel, result.stderr)
                self.assertIn('non-UTF-8', result.stderr)
                self.assertNotIn('Traceback (most recent call last)', result.stderr)
                self.assertEqual(tree_snapshot(project), before)

    def test_renderer_rejects_unsafe_source_blocks_before_source_writes(self) -> None:
        variants = (
            ('malformed', f'{PROJECT_START}\nproject data\n'.encode()),
            ('non-utf8', b'\xff\xfe'),
        )
        for index, (name, content) in enumerate(variants):
            with self.subTest(variant=name):
                source = Path(self.temp.name) / f'renderer-source-{index}'
                bootstrap = source / '.agentwork/bootstrap'
                shutil.copytree(BOOTSTRAP, bootstrap)
                project_index = source / '.shared/project/index.md'
                project_index.parent.mkdir(parents=True)
                project_index.write_bytes(content)
                agents = source / 'AGENTS.md'
                agents.write_text('source-owned agents\n', encoding='utf-8')
                before = tree_snapshot(source)

                result = subprocess.run(
                    ['python3', str(bootstrap / 'render_bootstrap.py')],
                    cwd=source,
                    text=True,
                    capture_output=True,
                    check=False,
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn('.shared/project/index.md', result.stderr)
                self.assertNotIn('Traceback (most recent call last)', result.stderr)
                self.assertEqual(tree_snapshot(source), before)

    def test_external_install_does_not_refresh_source_checkout(self) -> None:
        module = self.load_installer()

        def unexpected_refresh() -> None:
            raise AssertionError('external install must not refresh the source checkout')

        module.refresh_generated_bootstrap = unexpected_refresh
        with patch.object(sys, 'argv', ['install-bootstrap.py', '-p', str(self.project)]):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(module.main(), 0)

        self.assertTrue((self.project / 'AGENTS.md').is_file())

    def test_receipt_allows_refresh_of_an_unchanged_prior_version(self) -> None:
        self.run_installer()
        target = self.project / '.shared/commands/brain.md'
        prior = b'# prior agentwork-managed version\n'
        target.write_bytes(prior)
        receipt = self.receipt()
        for entry in receipt['files']:
            if entry['path'] == '.shared/commands/brain.md':
                entry['sha256'] = hashlib.sha256(prior).hexdigest()
                break
        (self.project / RECEIPT_REL).write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
            encoding='utf-8',
        )

        self.run_installer()

        self.assertEqual(target.read_bytes(), (REPO_ROOT / '.shared/commands/brain.md').read_bytes())

    def test_modified_managed_file_fails_without_writes(self) -> None:
        self.run_installer()
        target = self.project / '.shared/commands/brain.md'
        target.write_text('# project customization\n', encoding='utf-8')
        before = tree_snapshot(self.project)

        result = self.run_installer(check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('content changed since the last successful bootstrap install', result.stderr)
        self.assertEqual(tree_snapshot(self.project), before)

    def test_custom_managed_paths_fail_before_any_target_changes(self) -> None:
        paths = (
            'AGENTS.md',
            '.claude/CLAUDE.md',
            '.claude/commands/brain.md',
            '.cursor/rules/agentwork-bootstrap.mdc',
            '.opencode/commands/brain.md',
            '.codex/skills/brain/SKILL.md',
            '.codex/agents/luna-worker.toml',
            '.shared/commands/brain.md',
        )
        for index, rel in enumerate(paths):
            with self.subTest(path=rel):
                project = Path(self.temp.name) / f'conflict-{index}'
                path = project / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('project-owned content\n', encoding='utf-8')
                before = tree_snapshot(project)

                result = self.run_installer(project=project, check=False)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(rel, result.stderr)
                self.assertIn('bootstrap ownership conflicts', result.stderr)
                self.assertEqual(tree_snapshot(project), before)

    def test_managed_file_directory_conflict_fails_without_writes(self) -> None:
        conflict = self.project / '.claude/CLAUDE.md'
        conflict.mkdir(parents=True)
        (conflict / 'project-file.md').write_text('keep\n', encoding='utf-8')
        before = tree_snapshot(self.project)

        result = self.run_installer(check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('.claude/CLAUDE.md', result.stderr)
        self.assertIn('target is not a regular file', result.stderr)
        self.assertEqual(tree_snapshot(self.project), before)

    def test_codex_skill_refresh_preserves_extra_files(self) -> None:
        self.run_installer()
        extra = self.project / '.codex/skills/brain/project-notes.md'
        extra.write_text('keep project notes\n', encoding='utf-8')

        self.run_installer()

        self.assertEqual(extra.read_text(encoding='utf-8'), 'keep project notes\n')

    def test_modified_codex_skill_fails_and_preserves_extra_files(self) -> None:
        self.run_installer()
        skill = self.project / '.codex/skills/brain/SKILL.md'
        skill.write_text(skill.read_text() + '\nproject edit\n', encoding='utf-8')
        extra = skill.parent / 'project-notes.md'
        extra.write_text('keep project notes\n', encoding='utf-8')
        before = tree_snapshot(self.project)

        result = self.run_installer(check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('.codex/skills/brain/SKILL.md', result.stderr)
        self.assertEqual(tree_snapshot(self.project), before)

    def test_legacy_equal_content_and_generated_marker_can_refresh(self) -> None:
        shared = self.project / '.shared/commands/brain.md'
        shared.parent.mkdir(parents=True)
        shared.write_bytes((REPO_ROOT / '.shared/commands/brain.md').read_bytes())
        agents = self.project / 'AGENTS.md'
        agents.write_text(
            '<!-- AUTO-GENERATED by agentwork bootstrap -->\n# prior generated version\n',
            encoding='utf-8',
        )

        self.run_installer()

        self.assertEqual(agents.read_bytes(), (BOOTSTRAP / 'root/AGENTS.md').read_bytes())
        self.assertTrue((self.project / RECEIPT_REL).is_file())

    def test_invalid_receipts_fail_before_any_target_changes(self) -> None:
        invalid_receipts = (
            {'schema_version': 2, 'files': []},
            {'schema_version': 1, 'files': [{'path': '../outside', 'type': 'file', 'sha256': '0' * 64}]},
            {
                'schema_version': 1,
                'files': [
                    {'path': 'AGENTS.md', 'type': 'file', 'sha256': '0' * 64},
                    {'path': 'AGENTS.md', 'type': 'file', 'sha256': '1' * 64},
                ],
            },
        )
        for index, receipt in enumerate(invalid_receipts):
            with self.subTest(receipt=receipt):
                project = Path(self.temp.name) / f'invalid-receipt-{index}'
                path = project / RECEIPT_REL
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps(receipt), encoding='utf-8')
                before = tree_snapshot(project)

                result = self.run_installer(project=project, check=False)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn('bootstrap receipt', result.stderr)
                self.assertEqual(tree_snapshot(project), before)

    def test_receipt_entry_symlink_is_rejected_before_writes(self) -> None:
        external = Path(self.temp.name) / 'external-receipt-target'
        external.mkdir()
        managed = self.project / 'managed'
        managed.symlink_to(external, target_is_directory=True)
        receipt = {
            'schema_version': 1,
            'files': [{'path': 'managed/file.md', 'type': 'file', 'sha256': '0' * 64}],
        }
        path = self.project / RECEIPT_REL
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(receipt), encoding='utf-8')
        before = tree_snapshot(self.project)

        result = self.run_installer(check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('bootstrap receipt entry through symlink', result.stderr)
        self.assertEqual(tree_snapshot(self.project), before)
        self.assertEqual(list(external.iterdir()), [])

    def test_existing_same_role_fails_before_installing_files(self) -> None:
        codex = self.project / '.codex'
        codex.mkdir()
        original = (
            '[agents.luna_worker]\n'
            'description = "project role"\n'
            'config_file = "agents/custom.toml"\n'
        )
        (codex / 'config.toml').write_text(original, encoding='utf-8')

        result = self.run_installer(check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('already defines agentwork-managed role', result.stderr)
        self.assertEqual((codex / 'config.toml').read_text(encoding='utf-8'), original)
        self.assertFalse((self.project / 'AGENTS.md').exists())

    def test_existing_custom_agent_file_is_not_overwritten(self) -> None:
        agent = self.project / '.codex/agents/luna-worker.toml'
        agent.parent.mkdir(parents=True)
        agent.write_text('model = "project-model"\n', encoding='utf-8')

        result = self.run_installer(check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('bootstrap ownership conflicts', result.stderr)
        self.assertEqual(agent.read_text(encoding='utf-8'), 'model = "project-model"\n')
        self.assertFalse((self.project / 'AGENTS.md').exists())

    def test_codex_directory_symlink_is_rejected(self) -> None:
        external = Path(self.temp.name) / 'external-codex'
        external.mkdir()
        (self.project / '.codex').symlink_to(external, target_is_directory=True)

        result = self.run_installer(check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('path contains symlink', result.stderr)
        self.assertEqual(list(external.iterdir()), [])
        self.assertFalse((self.project / 'AGENTS.md').exists())

    def test_direct_copy_failure_rolls_back_complete_tree(self) -> None:
        module = self.load_installer()
        plan = self.prepared_plan(module)
        original = module.copy_file
        calls = 0

        def fail_after_copy(src: Path, dst: Path) -> None:
            nonlocal calls
            original(src, dst)
            calls += 1
            if calls == 1:
                raise OSError('injected direct copy failure')

        module.copy_file = fail_after_copy
        self.assert_plan_rollback(module, plan)

    def test_managed_index_failure_rolls_back_complete_tree(self) -> None:
        module = self.load_installer()
        plan = self.prepared_plan(module)
        original = module.write_managed_indexes

        def fail_after_indexes(prepared) -> None:
            original(prepared)
            raise OSError('injected managed index failure')

        module.write_managed_indexes = fail_after_indexes
        self.assert_plan_rollback(module, plan)

    def test_codex_config_failure_rolls_back_complete_tree(self) -> None:
        module = self.load_installer()
        plan = self.prepared_plan(module)
        original = module.write_prepared_file

        def fail_after_codex_config(prepared) -> None:
            original(prepared)
            if prepared.path == plan.codex_config.path:
                raise OSError('injected Codex config failure')

        module.write_prepared_file = fail_after_codex_config
        self.assert_plan_rollback(module, plan)

    def test_gitignore_failure_rolls_back_complete_tree(self) -> None:
        module = self.load_installer()
        plan = self.prepared_plan(module)
        original = module.write_prepared_file

        def fail_after_gitignore(prepared) -> None:
            original(prepared)
            if prepared.path == plan.gitignore.path:
                raise OSError('injected .gitignore failure')

        module.write_prepared_file = fail_after_gitignore
        self.assert_plan_rollback(module, plan)

    def test_receipt_failure_rolls_back_complete_tree(self) -> None:
        module = self.load_installer()
        plan = self.prepared_plan(module)
        original = module.write_receipt

        def fail_after_receipt(target: Path, content: bytes) -> None:
            original(target, content)
            raise OSError('injected receipt failure')

        module.write_receipt = fail_after_receipt
        self.assert_plan_rollback(module, plan)

    def test_keyboard_interrupt_rolls_back_complete_tree(self) -> None:
        module = self.load_installer()
        plan = self.prepared_plan(module)
        original = module.copy_file
        calls = 0

        def interrupt_after_copy(src: Path, dst: Path) -> None:
            nonlocal calls
            original(src, dst)
            calls += 1
            if calls == 1:
                raise KeyboardInterrupt

        module.copy_file = interrupt_after_copy
        self.assert_plan_rollback(module, plan)

    def test_retired_adapter_is_restored_and_custom_adapter_is_preserved(self) -> None:
        owned = self.project / '.agent/workflows/brain.md'
        owned.parent.mkdir(parents=True)
        owned.write_text(
            '<!-- AUTO-GENERATED by agentwork bootstrap -->\n# retired\n',
            encoding='utf-8',
        )
        custom = self.project / '.agent/workflows/plan.md'
        custom.write_text('# project-owned plan\n', encoding='utf-8')
        module = self.load_installer()
        plan = self.prepared_plan(module)
        self.assertIn(Path('.agent/workflows/brain.md'), plan.retired_removed)
        self.assertIn(Path('.agent/workflows/plan.md'), plan.retired_preserved)
        original = module.copy_file
        calls = 0

        def fail_after_copy(src: Path, dst: Path) -> None:
            nonlocal calls
            original(src, dst)
            calls += 1
            if calls == 1:
                raise OSError('injected post-retirement failure')

        module.copy_file = fail_after_copy
        self.assert_plan_rollback(module, plan)

    def test_backup_failure_happens_before_operation_or_target_changes(self) -> None:
        module = self.load_installer()
        plan = self.prepared_plan(module)
        original = module.snapshot_path
        calls = 0
        operated = False

        def fail_during_backup(path: Path, backup: Path):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('injected backup failure')
            return original(path, backup)

        def operation() -> None:
            nonlocal operated
            operated = True

        module.snapshot_path = fail_during_backup
        before = tree_snapshot(self.project)
        with self.assertRaisesRegex(SystemExit, 'cannot prepare bootstrap transaction backup'):
            module.run_transaction(plan.target, plan.transaction_paths, operation)
        self.assertFalse(operated)
        self.assertEqual(tree_snapshot(self.project), before)

    def test_rollback_incomplete_reports_residual_path(self) -> None:
        module = self.load_installer()
        target = self.project.resolve()
        residual = target / 'residual.txt'
        paths = module.collect_transaction_paths(target, [residual])

        def fail_restore(snapshot) -> None:
            raise OSError('injected restore failure')

        def operation() -> None:
            residual.write_text('partial change\n', encoding='utf-8')
            raise OSError('injected operation failure')

        module.restore_snapshot = fail_restore
        with self.assertRaisesRegex(
            SystemExit,
            'rollback incomplete: residual.txt: injected restore failure',
        ):
            module.run_transaction(target, paths, operation)
        self.assertEqual(residual.read_text(encoding='utf-8'), 'partial change\n')

    def test_transaction_paths_are_bounded_and_preserve_existing_empty_dirs(self) -> None:
        module = self.load_installer()
        target = self.project.resolve()
        existing_empty = target / 'existing-empty'
        existing_empty.mkdir()
        managed = existing_empty / 'managed.txt'
        paths = module.collect_transaction_paths(target, [managed])
        before = tree_snapshot(self.project)

        def operation() -> None:
            managed.write_text('partial change\n', encoding='utf-8')
            raise OSError('injected operation failure')

        with self.assertRaisesRegex(SystemExit, 'failed and rolled back'):
            module.run_transaction(target, paths, operation)
        self.assertEqual(tree_snapshot(self.project), before)
        outside = Path(self.temp.name) / 'outside.txt'
        with self.assertRaisesRegex(SystemExit, 'must be below project root'):
            module.collect_transaction_paths(target, [outside])

    def test_transaction_restores_directory_snapshot(self) -> None:
        module = self.load_installer()
        target = self.project.resolve()
        managed = target / 'managed-directory'
        managed.mkdir()
        (managed / 'before.txt').write_text('before\n', encoding='utf-8')
        paths = module.collect_transaction_paths(target, [managed])
        before = tree_snapshot(self.project)

        def operation() -> None:
            module.remove_path(managed)
            managed.mkdir()
            (managed / 'after.txt').write_text('after\n', encoding='utf-8')
            raise OSError('injected directory failure')

        with self.assertRaisesRegex(SystemExit, 'failed and rolled back'):
            module.run_transaction(target, paths, operation)
        self.assertEqual(tree_snapshot(self.project), before)

    def test_transaction_removes_new_project_root_after_failure(self) -> None:
        module = self.load_installer()
        target = (Path(self.temp.name) / 'new-project').resolve()
        managed = target / '.shared/managed.txt'
        paths = module.collect_transaction_paths(target, [managed])

        def operation() -> None:
            managed.parent.mkdir(parents=True)
            managed.write_text('partial change\n', encoding='utf-8')
            raise OSError('injected new project failure')

        with self.assertRaisesRegex(SystemExit, 'failed and rolled back'):
            module.run_transaction(target, paths, operation)
        self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
