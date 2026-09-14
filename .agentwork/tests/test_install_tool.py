#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER = REPO_ROOT / 'install-tool.py'


class InstallToolEnvTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix='agentwork-install-tool-')
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.source = root / 'source'
        self.project = root / 'project'
        self.source.mkdir()
        self.project.mkdir()
        shutil.copy2(INSTALLER, self.source / 'install-tool.py')
        (self.source / '.agentwork/tools').mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(self.project)], check=True)
        self.registry: list[dict] = []
        self.add_tool('alpha', env_name='TEST_API_KEY')
        self.add_tool('plain')
        self.write_registry()

    def add_tool(
        self,
        name: str,
        *,
        env_name: str | None = None,
        source_exists: bool = True,
        env_override: object | None = None,
    ) -> None:
        tool_root = self.source / '.agentwork/tools' / name
        tool_root.mkdir(parents=True, exist_ok=True)
        manifest: dict = {
            'name': name,
            'kind': ['test'],
            'description': f'{name} test tool',
            'entries': [
                {
                    'surface': 'shared',
                    'from': f'shared/{name}.txt',
                    'to': f'.shared/{name}.txt',
                }
            ],
        }
        if env_override is not None:
            manifest['env_keys'] = env_override
        elif env_name is not None:
            manifest['env_keys'] = [
                {
                    'name': env_name,
                    'required': False,
                    'description': f'Credential for {name}',
                }
            ]
        (tool_root / 'tool.json').write_text(json.dumps(manifest, indent=2) + '\n')
        if source_exists:
            source = tool_root / 'shared' / f'{name}.txt'
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(f'{name}\n')
        self.registry.append({'name': name, 'dir': name, 'kind': ['test']})

    def write_registry(self) -> None:
        path = self.source / '.agentwork/tools/registry.json'
        path.write_text(json.dumps({'schema_version': 1, 'tools': self.registry}, indent=2) + '\n')

    def run_installer(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ['python3', str(self.source / 'install-tool.py'), *args, '-p', str(self.project)],
            cwd=self.source,
            text=True,
            capture_output=True,
            check=False,
        )
        if check and result.returncode != 0:
            self.fail(f'installer failed: {result.stderr}{result.stdout}')
        return result

    def load_installer(self):
        path = self.source / 'install-tool.py'
        module_name = f'agentwork_install_tool_{id(self)}'
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            self.fail('cannot load installer module')
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        self.addCleanup(sys.modules.pop, module_name, None)
        spec.loader.exec_module(module)
        return module

    def project_snapshot(self) -> dict[str, bytes]:
        return {
            str(path.relative_to(self.project)): path.read_bytes()
            for path in self.project.rglob('*')
            if path.is_file() and '.git' not in path.parts
        }

    def test_unowned_file_conflict_stops_all_tools_before_writes(self) -> None:
        path = self.project / '.shared/plain.txt'
        path.parent.mkdir()
        path.write_bytes(b'private\xff')
        before = self.project_snapshot()
        result = self.run_installer('install', 'alpha', 'plain', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.project_snapshot(), before)

    def test_non_git_env_ignore_survives_negation_and_later_git_init(self) -> None:
        for index, original in enumerate((b'.env\n!.env\n', b'.env\r\n!*\r\n', b'.env\n')):
            with self.subTest(ignore=original):
                self.project = Path(self.temp.name) / f'not-yet-git-{index}'
                self.project.mkdir()
                ignore = self.project / '.gitignore'
                ignore.write_bytes(original)
                self.run_installer('install', 'alpha')
                self.assertTrue(ignore.read_bytes().startswith(original))
                self.assertFalse((self.project / '.git').exists())
                first = self.project_snapshot()
                self.run_installer('install', 'alpha')
                self.assertEqual(self.project_snapshot(), first)
                (self.project / '.env').write_text('TEST_API_KEY=synthetic-not-a-secret\n')
                subprocess.run(['git', 'init', '-q', str(self.project)], check=True)
                subprocess.run(['git', '-C', str(self.project), 'add', '--all'], check=True)
                tracked = subprocess.run(['git', '-C', str(self.project), 'ls-files', '-z'], check=True, capture_output=True).stdout
                self.assertNotIn(b'.env', tracked.split(b'\0'))

    def directory_tool(self) -> Path:
        root = self.source / '.agentwork/tools/plain'
        manifest = json.loads((root / 'tool.json').read_text())
        manifest['entries'][0].update({'from': 'shared', 'to': '.pi/skills/plain'})
        (root / 'tool.json').write_text(json.dumps(manifest))
        return self.project / '.pi/skills/plain'

    def test_uninstall_never_installed_preserves_directory(self) -> None:
        target = self.directory_tool()
        target.mkdir(parents=True)
        (target / 'private.txt').write_bytes(b'private\xff')
        before = self.project_snapshot()
        self.run_installer('uninstall', 'plain')
        self.assertEqual(self.project_snapshot(), before)

    def test_directory_reinstall_and_uninstall_preserve_user_additions(self) -> None:
        target = self.directory_tool()
        self.run_installer('install', 'plain')
        (target / 'local-note.md').write_text('keep')
        self.run_installer('install', 'plain')
        self.assertEqual((target / 'local-note.md').read_text(), 'keep')
        before = self.project_snapshot()
        self.run_installer('install', 'plain')
        self.assertEqual(self.project_snapshot(), before)
        self.run_installer('uninstall', 'plain')
        self.assertEqual((target / 'local-note.md').read_text(), 'keep')
        self.assertFalse((target / 'plain.txt').exists())

    def test_modified_managed_file_blocks_update_and_uninstall(self) -> None:
        self.run_installer('install', 'plain')
        (self.project / '.shared/plain.txt').write_text('user edit')
        before = self.project_snapshot()
        for action in ('install', 'uninstall'):
            result = self.run_installer(action, 'plain', check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(self.project_snapshot(), before)

    def test_receipted_file_can_upgrade(self) -> None:
        self.run_installer('install', 'plain')
        (self.source / '.agentwork/tools/plain/shared/plain.txt').write_text('new version')
        self.run_installer('install', 'plain')
        self.assertEqual((self.project / '.shared/plain.txt').read_text(), 'new version')
        self.run_installer('uninstall', 'plain')
        self.assertFalse((self.project / '.shared/plain.txt').exists())

    def test_removed_source_file_stays_accounted_for_until_uninstall(self) -> None:
        target = self.directory_tool()
        self.run_installer('install', 'plain')
        (self.source / '.agentwork/tools/plain/shared/plain.txt').unlink()
        self.run_installer('install', 'plain')
        self.assertTrue((target / 'plain.txt').is_file())
        self.run_installer('uninstall', 'plain')
        self.assertFalse(target.exists())

    def test_empty_directories_install_and_preserve_later_user_files(self) -> None:
        target = self.directory_tool()
        source = self.source / '.agentwork/tools/plain/shared'
        (source / 'empty').mkdir()
        (source / 'user-content').mkdir()
        self.run_installer('install', 'plain')
        self.assertTrue((target / 'empty').is_dir())
        (target / 'user-content/note').write_text('keep')
        self.run_installer('install', 'plain')
        self.run_installer('uninstall', 'plain')
        self.assertFalse((target / 'empty').exists())
        self.assertEqual((target / 'user-content/note').read_text(), 'keep')

    def test_receipt_failure_rolls_back_files_and_receipt(self) -> None:
        self.project = self.project.resolve()
        self.run_installer('install', 'plain')
        (self.source / '.agentwork/tools/plain/shared/plain.txt').write_text('upgrade')
        module = self.load_installer()
        _, tools = module.load_tools()
        entries = module.build_tool_entries(self.project, 'plain', tools['plain'], set())
        grouped, receipts = module.prepare_owned_changes(self.project, 'install', [('plain', entries)])
        env_plan = module.prepare_install_env(self.project, [])
        paths = module.transaction_paths(grouped, env_plan) + tuple(receipts)
        before = self.project_snapshot()

        def operation() -> None:
            module.apply_tool_changes(self.project, 'install', grouped, env_plan)
            module.apply_receipts(receipts, self.project)
            raise OSError('after receipt write')

        with self.assertRaisesRegex(SystemExit, 'rolled back'):
            module.run_transaction(self.project, paths, operation)
        self.assertEqual(self.project_snapshot(), before)

    def test_registry_schema_version_is_validated(self) -> None:
        """registry 的 schema_version 必须被校验，异常形态一律拒绝。"""
        registry = self.source / '.agentwork/tools/registry.json'
        original = json.loads(registry.read_text())
        for label, payload in (
            ('missing', {k: v for k, v in original.items() if k != 'schema_version'}),
            ('future', {**original, 'schema_version': 999}),
            ('string', {**original, 'schema_version': '1'}),
            ('null', {**original, 'schema_version': None}),
            ('list', {**original, 'schema_version': [1]}),
        ):
            with self.subTest(variant=label):
                registry.write_text(json.dumps(payload) + '\n')
                result = self.run_installer('list', check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('unsupported registry schema', result.stderr + result.stdout)
        registry.write_text(json.dumps(original) + '\n')
        self.assertEqual(self.run_installer('list').returncode, 0)

    def test_retired_receipt_path_blocks_install_but_allows_uninstall(self) -> None:
        """源端移除文件后，旧收据路径不得同时堵死 install 与 uninstall。"""
        self.add_tool('twin')
        manifest_path = self.source / '.agentwork/tools/twin/tool.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['entries'].append(
            {'surface': 'shared', 'from': 'shared/extra.txt', 'to': '.shared/twin-extra.txt'}
        )
        (self.source / '.agentwork/tools/twin/shared/extra.txt').write_text('extra\n')
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
        self.write_registry()
        self.run_installer('install', 'twin')
        self.assertTrue((self.project / '.shared/twin-extra.txt').is_file())

        # 源端退役 extra.txt：它成为 manifest 之外的旧收据路径。
        manifest['entries'] = [e for e in manifest['entries'] if e['to'] != '.shared/twin-extra.txt']
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
        (self.source / '.agentwork/tools/twin/shared/extra.txt').unlink()

        blocked = self.run_installer('install', 'twin', check=False)
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn('receipt path outside current manifest', blocked.stderr + blocked.stdout)

        self.run_installer('uninstall', 'twin')
        for relative in ('.shared/twin.txt', '.shared/twin-extra.txt'):
            self.assertFalse((self.project / relative).exists(), relative)
        self.assertFalse((self.project / '.agentwork/tool-receipts/twin.json').exists())

    def test_systemexit_after_second_write_rolls_back(self) -> None:
        """fail() 在事务内抛 SystemExit 时也必须回滚，而不是留下半写状态。"""
        self.project = self.project.resolve()
        self.run_installer('install', 'plain')
        (self.source / '.agentwork/tools/plain/shared/plain.txt').write_text('upgrade')
        module = self.load_installer()
        _, tools = module.load_tools()
        entries = module.build_tool_entries(self.project, 'plain', tools['plain'], set())
        grouped, receipts = module.prepare_owned_changes(self.project, 'install', [('plain', entries)])
        env_plan = module.prepare_install_env(self.project, [])
        paths = module.transaction_paths(grouped, env_plan) + tuple(receipts)
        before = self.project_snapshot()

        def operation() -> None:
            module.apply_tool_changes(self.project, 'install', grouped, env_plan)
            module.apply_receipts(receipts, self.project)
            module.fail('after receipt write')

        with self.assertRaisesRegex(SystemExit, 'rolled back'):
            module.run_transaction(self.project, paths, operation)
        self.assertEqual(self.project_snapshot(), before)

    def test_receipt_and_nested_target_symlinks_fail_without_changes(self) -> None:
        target = self.directory_tool()
        self.run_installer('install', 'plain')
        for rel in ('.agentwork/tool-receipts/plain.json', '.pi/skills/plain/plain.txt'):
            with self.subTest(path=rel):
                path = self.project / rel
                content = path.read_bytes()
                external = Path(self.temp.name) / 'external-link-target'
                external.write_bytes(content)
                path.unlink()
                path.symlink_to(external)
                before = self.project_snapshot()
                for action in ('install', 'uninstall'):
                    result = self.run_installer(action, 'plain', check=False)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertTrue(path.is_symlink())
                    self.assertEqual(self.project_snapshot(), before)
                    self.assertEqual(external.read_bytes(), content)
                path.unlink()
                path.write_bytes(content)

    def test_missing_env_creates_managed_placeholder_and_ignore_rule(self) -> None:
        result = self.run_installer('install', 'alpha')
        self.assertEqual(
            (self.project / '.env').read_text(),
            '# agentwork:env:alpha\nTEST_API_KEY=\n',
        )
        self.assertEqual((self.project / '.gitignore').read_text(), '.env\n')
        self.assertIn('[env:added-empty] TEST_API_KEY', result.stdout)
        self.assertTrue((self.project / '.shared/alpha.txt').is_file())

    def test_existing_env_missing_key_appends_without_changing_existing_bytes(self) -> None:
        original = b'# user comment\r\nOTHER=value\r\n'
        (self.project / '.env').write_bytes(original)
        self.run_installer('install', 'alpha')
        updated = (self.project / '.env').read_bytes()
        self.assertTrue(updated.startswith(original))
        self.assertIn(b'# agentwork:env:alpha\r\nTEST_API_KEY=\r\n', updated)

    def test_existing_empty_key_stays_user_owned(self) -> None:
        original = b'OTHER=1\nTEST_API_KEY=\n'
        (self.project / '.env').write_bytes(original)
        result = self.run_installer('install', 'alpha')
        self.assertEqual((self.project / '.env').read_bytes(), original)
        self.assertNotIn(b'agentwork:env:alpha', original)
        self.assertIn('[env:existing-empty] TEST_API_KEY', result.stdout)
        self.run_installer('uninstall', 'alpha')
        self.assertEqual((self.project / '.env').read_bytes(), original)

    def test_existing_set_key_is_preserved_and_not_printed(self) -> None:
        secret = 'not-for-output'
        original = f'TEST_API_KEY={secret}\n'.encode()
        (self.project / '.env').write_bytes(original)
        result = self.run_installer('install', 'alpha')
        self.assertEqual((self.project / '.env').read_bytes(), original)
        self.assertNotIn(secret, result.stdout + result.stderr)
        self.assertIn('[env:existing-set] TEST_API_KEY', result.stdout)

    def test_duplicate_key_fails_before_target_changes(self) -> None:
        (self.project / '.env').write_text('TEST_API_KEY=one\nTEST_API_KEY=two\n')
        before = self.project_snapshot()
        result = self.run_installer('install', 'alpha', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('duplicate key: TEST_API_KEY', result.stderr)
        self.assertEqual(self.project_snapshot(), before)

    def test_tracked_env_is_rejected_before_target_changes(self) -> None:
        (self.project / '.env').write_text('TEST_API_KEY=\n')
        subprocess.run(['git', '-C', str(self.project), 'add', '.env'], check=True)
        before = self.project_snapshot()
        result = self.run_installer('install', 'alpha', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('tracked project-root .env', result.stderr)
        self.assertEqual(self.project_snapshot(), before)

    def test_existing_ignore_rule_and_reinstall_are_idempotent(self) -> None:
        (self.project / '.gitignore').write_text('.env\n')
        self.run_installer('install', 'alpha')
        first_env = (self.project / '.env').read_bytes()
        self.run_installer('install', 'alpha')
        self.assertEqual((self.project / '.env').read_bytes(), first_env)
        self.assertEqual((self.project / '.gitignore').read_text(), '.env\n')

    def test_reinstall_without_git_is_idempotent(self) -> None:
        shutil.rmtree(self.project / '.git')
        self.run_installer('install', 'alpha')
        first_env = (self.project / '.env').read_bytes()
        self.run_installer('install', 'alpha')
        self.assertEqual((self.project / '.env').read_bytes(), first_env)
        self.assertEqual((self.project / '.gitignore').read_text(), '.env\n')
        self.assertEqual(first_env.count(b'TEST_API_KEY='), 1)
        self.assertEqual(first_env.count(b'# agentwork:env:alpha'), 1)

    def test_hardlinked_entry_env_and_gitignore_are_replaced_without_external_writes(self) -> None:
        self.run_installer('install', 'alpha')
        shared = self.project / '.shared'
        paths = {
            'entry': (shared / 'alpha.txt', b'alpha\n'),
            'env': (self.project / '.env', b'OTHER=1\n'),
            'gitignore': (self.project / '.gitignore', b'# keep\n'),
        }
        external_paths: dict[str, Path] = {}
        for name, (target, content) in paths.items():
            target.unlink()
            external = Path(self.temp.name) / f'external-{name}'
            external.write_bytes(content)
            os.link(external, target)
            external_paths[name] = external

        self.run_installer('install', 'alpha')

        self.assertEqual((shared / 'alpha.txt').read_bytes(), b'alpha\n')
        self.assertEqual((self.project / '.env').read_bytes(), b'OTHER=1\n# agentwork:env:alpha\nTEST_API_KEY=\n')
        self.assertEqual((self.project / '.gitignore').read_bytes(), b'# keep\n.env\n')
        for name, (target, original) in paths.items():
            external = external_paths[name]
            self.assertEqual(external.read_bytes(), original)
            self.assertNotEqual(target.stat().st_ino, external.stat().st_ino)

    def test_reinstall_restores_source_file_mode(self) -> None:
        source = self.source / '.agentwork/tools/alpha/shared/alpha.txt'
        source.chmod(0o755)
        self.run_installer('install', 'alpha')
        target = self.project / '.shared/alpha.txt'
        target.chmod(0o644)

        self.run_installer('install', 'alpha')

        self.assertEqual(target.stat().st_mode & 0o7777, 0o755)

    def test_uninstall_removes_untouched_empty_managed_key_only(self) -> None:
        original = b'# keep\nOTHER=1\n'
        (self.project / '.env').write_bytes(original)
        self.run_installer('install', 'alpha')
        gitignore = (self.project / '.gitignore').read_bytes()
        result = self.run_installer('uninstall', 'alpha')
        self.assertEqual((self.project / '.env').read_bytes(), original)
        self.assertEqual((self.project / '.gitignore').read_bytes(), gitignore)
        self.assertIn('[env:empty-removed] TEST_API_KEY', result.stdout)
        self.assertTrue((self.project / '.env').exists())

    def test_uninstall_preserves_filled_managed_value_without_printing_it(self) -> None:
        self.run_installer('install', 'alpha')
        secret = 'filled-after-install'
        env_path = self.project / '.env'
        env_path.write_text(env_path.read_text().replace('TEST_API_KEY=', f'TEST_API_KEY={secret}'))
        result = self.run_installer('uninstall', 'alpha')
        content = env_path.read_text()
        self.assertEqual(content, f'TEST_API_KEY={secret}\n')
        self.assertNotIn('agentwork:env:alpha', content)
        self.assertNotIn(secret, result.stdout + result.stderr)
        self.assertIn('[env:set-preserved] TEST_API_KEY', result.stdout)

    def test_uninstall_restores_file_without_final_newline(self) -> None:
        original = b'OTHER=1'
        (self.project / '.env').write_bytes(original)
        self.run_installer('install', 'alpha')
        self.assertIn(b'agentwork:env-format:alpha:TEST_API_KEY:no-final-newline', (self.project / '.env').read_bytes())
        self.run_installer('uninstall', 'alpha')
        self.assertEqual((self.project / '.env').read_bytes(), original)

    def test_multi_tool_preflight_failure_leaves_project_unchanged(self) -> None:
        self.add_tool('broken', env_name='BROKEN_KEY', source_exists=False)
        self.write_registry()
        before = self.project_snapshot()
        result = self.run_installer('install', 'alpha', 'broken', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('source does not exist', result.stderr)
        self.assertEqual(self.project_snapshot(), before)

    def test_project_root_target_is_rejected_before_changes(self) -> None:
        manifest_path = self.source / '.agentwork/tools/alpha/tool.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['entries'][0]['to'] = '.'
        manifest_path.write_text(json.dumps(manifest))

        before = self.project_snapshot()
        result = self.run_installer('install', 'alpha', check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('must name a child path', result.stderr)
        self.assertEqual(self.project_snapshot(), before)

    def test_overlapping_targets_are_rejected_before_changes(self) -> None:
        self.add_tool('beta')
        manifest_path = self.source / '.agentwork/tools/beta/tool.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['entries'][0]['to'] = '.shared'
        manifest_path.write_text(json.dumps(manifest))
        self.write_registry()

        before = self.project_snapshot()
        result = self.run_installer('install', 'alpha', 'beta', check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('overlapping install targets', result.stderr)
        self.assertEqual(self.project_snapshot(), before)

    def test_empty_entries_are_rejected_before_changes(self) -> None:
        manifest_path = self.source / '.agentwork/tools/plain/tool.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['entries'] = []
        manifest_path.write_text(json.dumps(manifest))

        before = self.project_snapshot()
        result = self.run_installer('install', 'plain', check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('entries must be a non-empty list', result.stderr)
        self.assertEqual(self.project_snapshot(), before)

    def test_runtime_failure_rolls_back_entries_env_and_gitignore(self) -> None:
        module = self.load_installer()
        _, tools = module.load_tools()
        project_root = self.project.resolve()
        seen_targets: set[Path] = set()
        tool = tools['alpha']
        entries = module.build_tool_entries(project_root, 'alpha', tool, seen_targets)
        grouped = [('alpha', entries)]
        env_keys = [('alpha', env_key) for env_key in tool['env_keys']]
        env_plan = module.prepare_install_env(project_root, env_keys)
        original_apply_env_plan = module.apply_env_plan

        def fail_after_env_write(root: Path, plan) -> None:
            original_apply_env_plan(root, plan)
            raise OSError('injected write failure')

        module.apply_env_plan = fail_after_env_write
        before = self.project_snapshot()
        with self.assertRaisesRegex(SystemExit, 'transaction failed and rolled back'):
            module.run_transaction(
                project_root,
                module.transaction_paths(grouped, env_plan),
                lambda: module.apply_tool_changes(project_root, 'install', grouped, env_plan),
            )
        self.assertEqual(self.project_snapshot(), before)
        self.assertFalse((self.project / '.shared').exists())
        self.assertFalse((self.project / '.env').exists())
        self.assertFalse((self.project / '.gitignore').exists())

    def test_hardlinked_files_stay_external_on_install_rollback(self) -> None:
        shared = self.project / '.shared'
        shared.mkdir()
        paths = {
            'entry': (shared / 'alpha.txt', b'project-owned entry\n'),
            'env': (self.project / '.env', b'OTHER=1\n'),
            'gitignore': (self.project / '.gitignore', b'# keep\n'),
        }
        external_paths: dict[str, Path] = {}
        for name, (target, content) in paths.items():
            external = Path(self.temp.name) / f'external-rollback-{name}'
            external.write_bytes(content)
            os.link(external, target)
            external_paths[name] = external

        module = self.load_installer()
        _, tools = module.load_tools()
        project_root = self.project.resolve()
        seen_targets: set[Path] = set()
        tool = tools['alpha']
        entries = module.build_tool_entries(project_root, 'alpha', tool, seen_targets)
        grouped = [('alpha', entries)]
        env_keys = [('alpha', env_key) for env_key in tool['env_keys']]
        env_plan = module.prepare_install_env(project_root, env_keys)
        original_apply_env_plan = module.apply_env_plan

        def fail_after_env_write(root: Path, plan) -> None:
            original_apply_env_plan(root, plan)
            raise OSError('injected hardlink write failure')

        module.apply_env_plan = fail_after_env_write
        before = self.project_snapshot()
        with self.assertRaisesRegex(SystemExit, 'transaction failed and rolled back'):
            module.run_transaction(
                project_root,
                module.transaction_paths(grouped, env_plan),
                lambda: module.apply_tool_changes(project_root, 'install', grouped, env_plan),
            )

        self.assertEqual(self.project_snapshot(), before)
        for name, (target, original) in paths.items():
            external = external_paths[name]
            self.assertEqual(external.read_bytes(), original)
            self.assertEqual(target.read_bytes(), original)
            self.assertNotEqual(target.stat().st_ino, external.stat().st_ino)

    def test_uninstall_runtime_failure_restores_installed_state(self) -> None:
        self.run_installer('install', 'alpha')
        module = self.load_installer()
        _, tools = module.load_tools()
        project_root = self.project.resolve()
        seen_targets: set[Path] = set()
        tool = tools['alpha']
        entries = module.build_tool_entries(project_root, 'alpha', tool, seen_targets)
        grouped = [('alpha', entries)]
        env_keys = [('alpha', env_key) for env_key in tool['env_keys']]
        env_plan = module.prepare_uninstall_env(project_root, env_keys)
        original_apply_env_plan = module.apply_env_plan

        def fail_after_env_write(root: Path, plan) -> None:
            original_apply_env_plan(root, plan)
            raise OSError('injected uninstall failure')

        module.apply_env_plan = fail_after_env_write
        before = self.project_snapshot()
        with self.assertRaisesRegex(SystemExit, 'transaction failed and rolled back'):
            module.run_transaction(
                project_root,
                module.transaction_paths(grouped, env_plan),
                lambda: module.apply_tool_changes(project_root, 'uninstall', grouped, env_plan),
            )
        self.assertEqual(self.project_snapshot(), before)

    def test_keyboard_interrupt_rolls_back_installed_state(self) -> None:
        module = self.load_installer()
        _, tools = module.load_tools()
        project_root = self.project.resolve()
        seen_targets: set[Path] = set()
        tool = tools['alpha']
        entries = module.build_tool_entries(project_root, 'alpha', tool, seen_targets)
        grouped = [('alpha', entries)]
        env_keys = [('alpha', env_key) for env_key in tool['env_keys']]
        env_plan = module.prepare_install_env(project_root, env_keys)
        original_apply_env_plan = module.apply_env_plan

        def interrupt_after_env_write(root: Path, plan) -> None:
            original_apply_env_plan(root, plan)
            raise KeyboardInterrupt

        module.apply_env_plan = interrupt_after_env_write
        before = self.project_snapshot()
        with self.assertRaisesRegex(SystemExit, 'transaction failed and rolled back'):
            module.run_transaction(
                project_root,
                module.transaction_paths(grouped, env_plan),
                lambda: module.apply_tool_changes(project_root, 'install', grouped, env_plan),
            )
        self.assertEqual(self.project_snapshot(), before)

    def test_invalid_env_manifest_fields_types_and_name_fail(self) -> None:
        manifest_path = self.source / '.agentwork/tools/alpha/tool.json'
        original = json.loads(manifest_path.read_text())
        invalid_values = [
            [{'name': 'TEST_API_KEY', 'required': False, 'description': 'x', 'extra': True}],
            [{'name': 'BAD-NAME', 'required': False, 'description': 'x'}],
            [{'name': 'TEST_API_KEY', 'required': 'false', 'description': 'x'}],
        ]
        for env_keys in invalid_values:
            with self.subTest(env_keys=env_keys):
                changed = {**original, 'env_keys': env_keys}
                manifest_path.write_text(json.dumps(changed))
                before = self.project_snapshot()
                result = self.run_installer('install', 'alpha', check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.project_snapshot(), before)
        manifest_path.write_text(json.dumps(original))

    def test_registry_rejects_duplicate_managed_key(self) -> None:
        self.add_tool('beta', env_name='TEST_API_KEY')
        self.write_registry()
        before = self.project_snapshot()
        result = self.run_installer('install', 'alpha', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('managed by both alpha and beta', result.stderr)
        self.assertEqual(self.project_snapshot(), before)

    def test_shell_syntax_in_existing_value_is_never_executed_or_printed(self) -> None:
        sentinel = Path(self.temp.name) / 'executed'
        value = f'"$(touch {sentinel})`touch {sentinel}`\'quoted\'"'
        (self.project / '.env').write_text(f'TEST_API_KEY={value}\n')
        result = self.run_installer('install', 'alpha')
        self.assertFalse(sentinel.exists())
        self.assertNotIn(value, result.stdout + result.stderr)
        self.assertEqual((self.project / '.env').read_text(), f'TEST_API_KEY={value}\n')

    def test_plain_manifest_keeps_legacy_behavior_without_env_files(self) -> None:
        self.run_installer('install', 'plain')
        self.assertTrue((self.project / '.shared/plain.txt').is_file())
        self.assertFalse((self.project / '.env').exists())
        self.assertFalse((self.project / '.gitignore').exists())

    def test_target_symlink_is_rejected_before_changes(self) -> None:
        shared = self.project / '.shared'
        shared.mkdir()
        user_file = self.project / 'user-owned.txt'
        user_file.write_text('keep\n')
        (shared / 'plain.txt').symlink_to(user_file)
        before = self.project_snapshot()
        result = self.run_installer('install', 'plain', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('target path contains symlink', result.stderr)
        self.assertEqual(self.project_snapshot(), before)
        self.assertEqual(user_file.read_text(), 'keep\n')

    def test_install_does_not_change_existing_staged_diff(self) -> None:
        staged = self.project / 'staged.txt'
        staged.write_text('staged\n')
        subprocess.run(['git', '-C', str(self.project), 'add', 'staged.txt'], check=True)
        before = subprocess.run(
            ['git', '-C', str(self.project), 'diff', '--cached', '--binary'],
            check=True,
            capture_output=True,
        ).stdout
        self.run_installer('install', 'alpha')
        after = subprocess.run(
            ['git', '-C', str(self.project), 'diff', '--cached', '--binary'],
            check=True,
            capture_output=True,
        ).stdout
        self.assertEqual(after, before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
