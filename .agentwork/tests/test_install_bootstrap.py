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
CASE_START = '<!-- AGENTWORK:CASE-README:START -->'
CASE_END = '<!-- AGENTWORK:CASE-README:END -->'
RETIRED_SESSION_START = '<!-- AGENTWORK:SESSION-README:START -->'
RETIRED_SESSION_END = '<!-- AGENTWORK:SESSION-README:END -->'
GITIGNORE_START = '# >>> AGENTWORK bootstrap: tmp artifacts >>>'
GITIGNORE_END = '# <<< AGENTWORK bootstrap: tmp artifacts <<<'
RECEIPT_REL = Path('.agentwork/bootstrap-install-state.json')
PI_PROMPTS = ('brain', 'case', 'commit', 'exec', 'plan', 'review')
RETIRED_SESSION_FILES = (
    '.claude/commands/session.md',
    '.codex/skills/session/SKILL.md',
    '.opencode/commands/session.md',
    '.pi/prompts/aw-session.md',
    '.shared/commands/session.md',
    '.shared/patterns/session-workflow.md',
    '.shared/scripts/session-review.sh',
    '.shared/templates/session.md',
)


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

    def load_installer(self, installer: Path = INSTALLER):
        module_name = f'agentwork_install_bootstrap_{id(self)}_{abs(hash(installer))}'
        spec = importlib.util.spec_from_file_location(module_name, installer)
        if spec is None or spec.loader is None:
            self.fail('cannot load bootstrap installer module')
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        self.addCleanup(sys.modules.pop, module_name, None)
        spec.loader.exec_module(module)
        return module

    def prepared_plan(self, module):
        return module.prepare_bootstrap_plan(self.project.resolve())

    def source_fixture(self, name: str, *, include_pi_source: bool = True) -> Path:
        source = Path(self.temp.name) / name
        source.mkdir()
        shutil.copy2(INSTALLER, source / 'install-bootstrap.py')
        shutil.copytree(BOOTSTRAP, source / '.agentwork/bootstrap')
        tools = source / '.agentwork/tools'
        tools.mkdir(parents=True)
        (tools / 'registry.json').write_text('{"tools": []}\n', encoding='utf-8')
        shutil.copytree(REPO_ROOT / '.shared', source / '.shared')
        shutil.copy2(REPO_ROOT / 'AGENTS.md', source / 'AGENTS.md')
        if not include_pi_source:
            shutil.rmtree(source / '.agentwork/bootstrap/pi')
        return source

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

        default_skills = (
            ('.codex/skills/anydoc/SKILL.md', 'Codex default skill'),
            ('.claude/skills/anydoc/SKILL.md', 'Claude default skill'),
            ('.pi/skills/anydoc/SKILL.md', 'Pi default skill'),
            ('.cursor/rules/anydoc.mdc', 'Cursor default rule'),
            # research 与 anydoc 同为默认能力；其平台入口是手写薄指针，
            # 含唯一的 5 层嵌套资产 agents/openai.yaml。
            ('.codex/skills/research/SKILL.md', 'Codex default skill'),
            ('.codex/skills/research/agents/openai.yaml', 'Codex default skill asset'),
            ('.claude/skills/research/SKILL.md', 'Claude default skill'),
            ('.pi/skills/research/SKILL.md', 'Pi default skill'),
            ('.cursor/rules/research.mdc', 'Cursor default rule'),
        )
        records = {entry['path']: entry for entry in self.receipt()['files']}
        for relative, label in default_skills:
            with self.subTest(path=relative):
                installed = self.project / relative
                self.assertTrue(installed.is_file(), label)
                self.assertEqual(installed.read_bytes(), (REPO_ROOT / relative).read_bytes())
                self.assertIn(relative, records)

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

    def test_fresh_install_registers_exact_pi_prompts_in_receipt(self) -> None:
        self.run_installer()

        installed_dir = self.project / '.pi/prompts'
        self.assertEqual(
            {path.name for path in installed_dir.iterdir()},
            {f'{name}.md' for name in PI_PROMPTS},
        )
        records = {entry['path']: entry for entry in self.receipt()['files']}
        self.assertEqual(
            {path for path in records if path.startswith('.pi/prompts/')},
            {f'.pi/prompts/{name}.md' for name in PI_PROMPTS},
        )
        for name in PI_PROMPTS:
            with self.subTest(prompt=name):
                source = BOOTSTRAP / 'pi/prompts' / f'{name}.md'
                installed = installed_dir / source.name
                receipt_path = f'.pi/prompts/{source.name}'
                self.assertEqual(installed.read_bytes(), source.read_bytes())
                self.assertEqual(
                    records[receipt_path]['sha256'],
                    hashlib.sha256(source.read_bytes()).hexdigest(),
                )
        self.assertNotIn('.pi/prompts/session.md', records)
        self.assertNotIn('.pi/prompts/aw-session.md', records)

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

    def test_source_session_data_is_excluded_from_installs(self) -> None:
        relative = Path('.shared/session/local-task.md')
        source_content = b'source-owned legacy task\n\xff\n'
        project_content = b'project-owned legacy task\n\xfe\n'
        for scenario in ('fresh', 'existing', 'self-host'):
            with self.subTest(scenario=scenario):
                source = self.source_fixture(f'source-session-data-{scenario}')
                source_data = source / relative
                source_data.parent.mkdir(parents=True)
                source_data.write_bytes(source_content)
                target = source if scenario == 'self-host' else self.project / scenario
                target.mkdir(parents=True, exist_ok=True)
                target_data = target / relative
                if scenario == 'existing':
                    target_data.parent.mkdir(parents=True)
                    target_data.write_bytes(project_content)

                after_first = None
                for run in range(2):
                    result = subprocess.run(
                        ['python3', str(source / 'install-bootstrap.py'), '-p', str(target)],
                        cwd=source,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                    self.assertEqual(source_data.read_bytes(), source_content)
                    if scenario == 'fresh':
                        self.assertFalse(target_data.parent.exists())
                    else:
                        expected = source_content if scenario == 'self-host' else project_content
                        self.assertEqual(target_data.read_bytes(), expected)
                    receipt_paths = {entry['path'] for entry in self.receipt(target)['files']}
                    self.assertFalse(any(path.startswith('.shared/session/') for path in receipt_paths))
                    self.assertIn('.shared/commands/case.md', receipt_paths)
                    self.assertIn('.pi/prompts/case.md', receipt_paths)
                    if run == 0:
                        after_first = tree_snapshot(target)
                    else:
                        self.assertEqual(tree_snapshot(target), after_first)

    def test_prior_session_receipt_retires_owned_contract_without_touching_data(self) -> None:
        receipt_files = []
        for index, relative in enumerate(RETIRED_SESSION_FILES):
            path = self.project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            content = f'prior agentwork Session contract {index}\n'.encode()
            path.write_bytes(content)
            receipt_files.append(
                {
                    'path': relative,
                    'type': 'file',
                    'sha256': hashlib.sha256(content).hexdigest(),
                }
            )

        retired_readme = self.project / '.shared/session/README.md'
        retired_readme.parent.mkdir(parents=True, exist_ok=True)
        retired_readme_content = (
            '# Session 目录说明\n\n'
            '## 本项目补充说明\n\n'
            f'{RETIRED_SESSION_START}\n'
            'prior managed instructions\n'
            f'{RETIRED_SESSION_END}\n'
        ).encode()
        retired_readme.write_bytes(retired_readme_content)
        receipt_files.append(
            {
                'path': '.shared/session/README.md',
                'type': 'file',
                'sha256': hashlib.sha256(retired_readme_content).hexdigest(),
            }
        )
        legacy_data = self.project / '.shared/session/keep.md'
        legacy_data.write_bytes(b'project legacy data\n\xff\n')
        legacy_data_before = legacy_data.read_bytes()
        receipt_path = self.project / RECEIPT_REL
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(
            json.dumps(
                {'schema_version': 1, 'files': receipt_files},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + '\n',
            encoding='utf-8',
        )

        self.run_installer()

        for relative in RETIRED_SESSION_FILES:
            self.assertFalse((self.project / relative).exists(), relative)
        self.assertFalse(retired_readme.exists())
        self.assertEqual(legacy_data.read_bytes(), legacy_data_before)
        self.assertTrue((self.project / '.shared/case/README.md').is_file())
        receipt_paths = {entry['path'] for entry in self.receipt()['files']}
        self.assertFalse(set(RETIRED_SESSION_FILES) & receipt_paths)
        self.assertNotIn('.shared/session/README.md', receipt_paths)
        self.assertIn('.shared/commands/case.md', receipt_paths)
        self.assertIn('.pi/prompts/case.md', receipt_paths)

    def test_modified_receipted_retired_wrapper_is_preserved_across_reinstall(self) -> None:
        retired_wrapper = self.project / '.claude/commands/session.md'
        retired_wrapper.parent.mkdir(parents=True, exist_ok=True)
        prior_content = b'<!-- AUTO-GENERATED by agentwork bootstrap -->\n# prior Session wrapper\n'
        customized_content = prior_content + b'\nProject customization\n'
        retired_wrapper.write_bytes(customized_content)
        receipt_path = self.project / RECEIPT_REL
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(
            json.dumps(
                {
                    'schema_version': 1,
                    'files': [
                        {
                            'path': '.claude/commands/session.md',
                            'type': 'file',
                            'sha256': hashlib.sha256(prior_content).hexdigest(),
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + '\n',
            encoding='utf-8',
        )

        first = self.run_installer()
        self.assertEqual(retired_wrapper.read_bytes(), customized_content)
        self.assertIn('- [keep] .claude/commands/session.md', first.stdout)
        self.assertNotIn(
            '.claude/commands/session.md',
            {entry['path'] for entry in self.receipt()['files']},
        )

        second = self.run_installer()
        self.assertEqual(retired_wrapper.read_bytes(), customized_content)
        self.assertIn('- [keep] .claude/commands/session.md', second.stdout)

    def test_retired_session_custom_content_is_preserved_and_block_is_stripped(self) -> None:
        custom_command = self.project / '.shared/commands/session.md'
        custom_command.parent.mkdir(parents=True, exist_ok=True)
        custom_command.write_text('# Project-owned legacy command\n', encoding='utf-8')
        legacy_data = self.project / '.shared/session/keep.md'
        legacy_data.parent.mkdir(parents=True, exist_ok=True)
        legacy_data.write_bytes(b'project-owned legacy data\n')
        retired_readme = self.project / '.shared/session/README.md'
        retired_readme.write_text(
            '# Project legacy notes\n\n'
            f'{RETIRED_SESSION_START}\n'
            'prior managed instructions\n'
            f'{RETIRED_SESSION_END}\n\n'
            'Project legacy suffix\n',
            encoding='utf-8',
        )
        old_pi_prompt = self.project / '.pi/prompts/aw-session.md'
        old_pi_prompt.parent.mkdir(parents=True, exist_ok=True)
        old_pi_prompt.symlink_to('../../.shared/session/keep.md')

        self.run_installer()
        after_first = tree_snapshot(self.project)
        self.run_installer()

        self.assertEqual(tree_snapshot(self.project), after_first)
        self.assertEqual(
            custom_command.read_text(encoding='utf-8'),
            '# Project-owned legacy command\n',
        )
        self.assertTrue(old_pi_prompt.is_symlink())
        self.assertEqual(os.readlink(old_pi_prompt), '../../.shared/session/keep.md')
        self.assertEqual(legacy_data.read_bytes(), b'project-owned legacy data\n')
        readme_text = retired_readme.read_text(encoding='utf-8')
        self.assertIn('# Project legacy notes', readme_text)
        self.assertIn('Project legacy suffix', readme_text)
        self.assertNotIn(RETIRED_SESSION_START, readme_text)
        self.assertNotIn(RETIRED_SESSION_END, readme_text)

    def test_unrecognized_retired_session_readme_is_ignored(self) -> None:
        variants = (
            f'project data\n{RETIRED_SESSION_START}\nincomplete\n'.encode(),
            b'\xff\xfe',
        )
        for index, content in enumerate(variants):
            with self.subTest(variant=index):
                project = Path(self.temp.name) / f'retired-session-readme-{index}'
                readme = project / '.shared/session/README.md'
                readme.parent.mkdir(parents=True)
                readme.write_bytes(content)

                self.run_installer(project=project)

                self.assertEqual(readme.read_bytes(), content)
                self.assertTrue((project / '.shared/case/README.md').is_file())

    def test_reinstall_preserves_managed_block_context_and_unmanaged_files(self) -> None:
        project_index = self.project / '.shared/project/index.md'
        case_readme = self.project / '.shared/case/README.md'
        project_index.parent.mkdir(parents=True)
        case_readme.parent.mkdir(parents=True)
        project_index.write_text('# Project-owned prefix\n', encoding='utf-8')
        case_readme.write_text('# Case-owned prefix\n', encoding='utf-8')
        (self.project / '.gitignore').write_text('node_modules/\n/.tmp/\n', encoding='utf-8')
        self.run_installer()

        for path in (project_index, case_readme):
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
            (case_readme, '# Case-owned prefix\n'),
        ):
            text = path.read_text(encoding='utf-8')
            self.assertTrue(text.startswith(prefix))
            self.assertTrue(text.endswith('Project-owned suffix\n'))
        self.assertEqual((self.project / '.gitignore').read_text(encoding='utf-8'), 'node_modules/\n/.tmp/\n')
        self.assertEqual(optional_file.read_text(encoding='utf-8'), 'project optional tool\n')
        self.assertEqual(receipt_outside_file.read_text(encoding='utf-8'), 'project notes\n')

    def test_tmp_protection_survives_negations_and_git_init(self) -> None:
        cases = {
            'directory': '.tmp/\n!.tmp/\n',
            'children': '.tmp/*\n!.tmp/keep.md\n',
            'leading-space': ' .tmp/\n',
            'managed': f'{GITIGNORE_START}\n.tmp/\n{GITIGNORE_END}\n!.tmp/\n',
        }
        for name, rules in cases.items():
            for initialized in (False, True):
                for newline in ('\n', '\r\n'):
                    with self.subTest(name=name, git=initialized, newline=repr(newline)):
                        project = Path(tempfile.mkdtemp(dir=self.temp.name))
                        original = rules.replace('\n', newline).encode()
                        (project / '.gitignore').write_bytes(original)
                        (project / '.tmp').mkdir()
                        (project / '.tmp/keep.md').write_text('synthetic temporary artifact\n')
                        (project / 'staged.txt').write_text('project-owned\n')
                        if initialized:
                            subprocess.run(['git', 'init', '-q', str(project)], check=True)
                            subprocess.run(['git', '-C', str(project), 'add', 'staged.txt'], check=True)
                            index_before = (project / '.git/index').read_bytes()

                        self.run_installer(project=project)
                        if initialized:
                            self.assertEqual((project / '.git/index').read_bytes(), index_before)
                        else:
                            self.assertFalse((project / '.git').exists())
                            subprocess.run(['git', 'init', '-q', str(project)], check=True)

                        ignore = (project / '.gitignore').read_bytes()
                        if name == 'managed':
                            self.assertEqual(ignore.count(GITIGNORE_START.encode()), 1)
                            self.assertLess(ignore.index(b'!.tmp/'), ignore.index(GITIGNORE_START.encode()))
                        else:
                            self.assertTrue(ignore.startswith(original))
                        if newline == '\r\n':
                            self.assertNotIn(b'\n', ignore.replace(b'\r\n', b''))
                        before_repeat = tree_snapshot(project)
                        self.run_installer(project=project)
                        self.assertEqual(tree_snapshot(project), before_repeat)

                        subprocess.run(['git', '-C', str(project), 'add', '--all'], check=True,
                                       capture_output=True)
                        tracked = subprocess.run(
                            ['git', '-C', str(project), 'ls-files', '--', '.tmp'],
                            check=True, capture_output=True, text=True,
                        )
                        self.assertEqual(tracked.stdout, '')

    def test_tmp_protection_does_not_untrack_existing_artifact(self) -> None:
        subprocess.run(['git', 'init', '-q', str(self.project)], check=True)
        (self.project / '.tmp').mkdir()
        (self.project / '.tmp/retained.md').write_text('explicitly retained evidence\n')
        subprocess.run(['git', '-C', str(self.project), 'add', '-f', '.tmp/retained.md'], check=True)
        index_before = (self.project / '.git/index').read_bytes()
        self.run_installer()
        self.assertEqual((self.project / '.git/index').read_bytes(), index_before)
        self.assertEqual((self.project / '.tmp/retained.md').read_text(), 'explicitly retained evidence\n')

    def test_reinstall_preserves_unmanaged_pi_content_and_receipt(self) -> None:
        settings = self.project / '.pi/settings.json'
        extension = self.project / '.pi/extensions/project-extension.ts'
        native_session = self.project / '.pi/prompts/session.md'
        custom_prompt = self.project / '.pi/prompts/project-command.md'
        for path, content in (
            (settings, '{"project": true}\n'),
            (extension, 'export default function projectExtension() {}\n'),
            (native_session, 'project-owned session prompt\n'),
            (custom_prompt, 'project-owned custom prompt\n'),
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')

        self.run_installer()
        receipt = (self.project / RECEIPT_REL).read_bytes()
        after_first = tree_snapshot(self.project)
        self.run_installer()

        self.assertEqual(tree_snapshot(self.project), after_first)
        self.assertEqual((self.project / RECEIPT_REL).read_bytes(), receipt)
        self.assertEqual(settings.read_text(encoding='utf-8'), '{"project": true}\n')
        self.assertEqual(
            extension.read_text(encoding='utf-8'),
            'export default function projectExtension() {}\n',
        )
        self.assertEqual(
            native_session.read_text(encoding='utf-8'),
            'project-owned session prompt\n',
        )
        self.assertEqual(
            custom_prompt.read_text(encoding='utf-8'),
            'project-owned custom prompt\n',
        )

    def test_malformed_managed_blocks_fail_without_writes(self) -> None:
        targets = (
            ('.shared/project/index.md', PROJECT_START, PROJECT_END),
            ('.shared/case/README.md', CASE_START, CASE_END),
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
        for index, rel in enumerate(('.shared/project/index.md', '.shared/case/README.md', '.gitignore')):
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

    def test_renderer_check_is_read_only_and_rejects_drift(self) -> None:
        source = Path(self.temp.name) / 'renderer-check'
        bootstrap = source / '.agentwork/bootstrap'
        shutil.copytree(BOOTSTRAP, bootstrap)
        shutil.copytree(REPO_ROOT / '.shared/commands', source / '.shared/commands')
        command = ['python3', str(bootstrap / 'render_bootstrap.py')]
        subprocess.run(command, check=True, capture_output=True)
        output = bootstrap / 'root/AGENTS.md'
        original = output.read_bytes()
        for scenario in ('clean', 'missing', 'drift', 'unknown'):
            with self.subTest(scenario=scenario):
                output.write_bytes(original)
                if scenario == 'missing':
                    output.unlink()
                elif scenario == 'drift':
                    output.write_bytes(b'custom content')
                before = tree_snapshot(source)
                result = subprocess.run(command + ['--unknown' if scenario == 'unknown' else '--check'], capture_output=True)
                self.assertEqual(result.returncode == 0, scenario == 'clean')
                self.assertEqual(tree_snapshot(source), before)

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
                shutil.copytree(REPO_ROOT / '.shared/commands', source / '.shared/commands')
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

    def test_source_self_host_preflights_new_pi_target_before_rendering(self) -> None:
        source = self.source_fixture('source-target-conflict', include_pi_source=False)
        custom = source / '.pi/prompts/brain.md'
        custom.parent.mkdir(parents=True)
        custom.write_text('project-owned Pi prompt\n', encoding='utf-8')
        before = tree_snapshot(source)

        result = subprocess.run(
            ['python3', str(source / 'install-bootstrap.py'), '-p', str(source)],
            cwd=source,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('bootstrap ownership conflicts', result.stderr)
        self.assertIn('.pi/prompts/brain.md', result.stderr)
        self.assertEqual(tree_snapshot(source), before)
        self.assertFalse((source / '.agentwork/bootstrap/pi').exists())

    def test_source_self_host_preserves_new_generated_source_conflict(self) -> None:
        source = self.source_fixture('source-generator-conflict', include_pi_source=False)
        custom = source / '.agentwork/bootstrap/pi/prompts/brain.md'
        custom.parent.mkdir(parents=True)
        custom.write_text('project-owned generated source\n', encoding='utf-8')
        before = tree_snapshot(source)

        result = subprocess.run(
            ['python3', str(source / 'install-bootstrap.py'), '-p', str(source)],
            cwd=source,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('bootstrap source ownership conflicts', result.stderr)
        self.assertIn('.agentwork/bootstrap/pi/prompts/brain.md', result.stderr)
        self.assertEqual(tree_snapshot(source), before)
        self.assertEqual(custom.read_text(encoding='utf-8'), 'project-owned generated source\n')

    def test_source_self_host_installs_new_wrapper_on_first_run(self) -> None:
        source = self.source_fixture('source-new-wrapper')
        spec_path = source / '.agentwork/bootstrap/spec.json'
        data = json.loads(spec_path.read_text(encoding='utf-8'))
        data['wrappers'].append(
            {
                'name': 'probe',
                'title': '/probe [args]',
                'target': '.shared/commands/brain.md',
            }
        )
        spec_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8',
        )

        result = subprocess.run(
            ['python3', str(source / 'install-bootstrap.py'), '-p', str(source)],
            cwd=source,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        pairs = (
            (
                '.agentwork/bootstrap/claude/commands/probe.md',
                '.claude/commands/probe.md',
            ),
            (
                '.agentwork/bootstrap/codex/skills/probe/SKILL.md',
                '.codex/skills/probe/SKILL.md',
            ),
            (
                '.agentwork/bootstrap/opencode/commands/probe.md',
                '.opencode/commands/probe.md',
            ),
            (
                '.agentwork/bootstrap/pi/prompts/probe.md',
                '.pi/prompts/probe.md',
            ),
        )
        for canonical, installed in pairs:
            with self.subTest(platform=installed):
                self.assertEqual(
                    (source / installed).read_bytes(),
                    (source / canonical).read_bytes(),
                )
        receipt_paths = {
            entry['path']
            for entry in json.loads(
                (source / RECEIPT_REL).read_text(encoding='utf-8')
            )['files']
        }
        self.assertTrue({installed for _, installed in pairs} <= receipt_paths)

        before_second_run = tree_snapshot(source)
        second = subprocess.run(
            ['python3', str(source / 'install-bootstrap.py'), '-p', str(source)],
            cwd=source,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(second.returncode, 0, second.stderr + second.stdout)
        self.assertEqual(tree_snapshot(source), before_second_run)

    def test_source_self_host_rolls_back_renderer_and_target_writes(self) -> None:
        for index, failure in enumerate((OSError('injected copy failure'), KeyboardInterrupt())):
            with self.subTest(failure=type(failure).__name__):
                source = self.source_fixture(f'source-rollback-{index}')
                module = self.load_installer(source / 'install-bootstrap.py')
                original = module.copy_file
                calls = 0

                def fail_after_copy(src: Path, dst: Path) -> None:
                    nonlocal calls
                    original(src, dst)
                    calls += 1
                    if calls == 1:
                        raise failure

                module.copy_file = fail_after_copy
                before = tree_snapshot(source)
                with redirect_stdout(io.StringIO()):
                    with self.assertRaisesRegex(SystemExit, 'failed and rolled back'):
                        module.run_source_self_host(source.resolve())
                self.assertEqual(tree_snapshot(source), before)

    def test_external_install_does_not_refresh_source_checkout(self) -> None:
        module = self.load_installer()

        def unexpected_renderer_load():
            raise AssertionError('external install must not load the source renderer')

        module.load_bootstrap_renderer = unexpected_renderer_load
        with patch.object(sys, 'argv', ['install-bootstrap.py', '-p', str(self.project)]):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(module.main(), 0)

        self.assertTrue((self.project / 'AGENTS.md').is_file())

    def test_external_install_ignores_stale_generated_source_prompts(self) -> None:
        source = self.source_fixture('external-stale-pi-source')
        stale_dir = source / '.agentwork/bootstrap/pi/prompts'
        (stale_dir / 'aw-session.md').write_text(
            '<!-- AUTO-GENERATED by agentwork bootstrap -->\n# stale aw-session\n',
            encoding='utf-8',
        )
        (stale_dir / 'other.md').write_text(
            '<!-- AUTO-GENERATED by agentwork bootstrap -->\n# stale other\n',
            encoding='utf-8',
        )
        target = Path(self.temp.name) / 'external-stale-target'
        target.mkdir()
        source_before = tree_snapshot(source)

        result = subprocess.run(
            ['python3', str(source / 'install-bootstrap.py'), '-p', str(target)],
            cwd=source,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(tree_snapshot(source), source_before)
        self.assertEqual(
            {path.name for path in (target / '.pi/prompts').iterdir()},
            {f'{name}.md' for name in PI_PROMPTS},
        )
        receipt_paths = {
            entry['path']
            for entry in json.loads(
                (target / RECEIPT_REL).read_text(encoding='utf-8')
            )['files']
        }
        self.assertNotIn('.pi/prompts/aw-session.md', receipt_paths)
        self.assertNotIn('.pi/prompts/other.md', receipt_paths)

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
            '.pi/prompts/brain.md',
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

    def test_pi_prompt_directory_conflict_fails_without_writes(self) -> None:
        conflict = self.project / '.pi/prompts/brain.md'
        conflict.mkdir(parents=True)
        (conflict / 'project-file.md').write_text('keep\n', encoding='utf-8')
        before = tree_snapshot(self.project)

        result = self.run_installer(check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('.pi/prompts/brain.md', result.stderr)
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

    def test_modified_managed_pi_prompt_fails_without_writes(self) -> None:
        self.run_installer()
        prompt = self.project / '.pi/prompts/brain.md'
        prompt.write_text(
            prompt.read_text(encoding='utf-8') + '\nproject edit\n',
            encoding='utf-8',
        )
        before = tree_snapshot(self.project)

        result = self.run_installer(check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('.pi/prompts/brain.md', result.stderr)
        self.assertIn(
            'content changed since the last successful bootstrap install',
            result.stderr,
        )
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

    def test_pi_symlink_boundaries_are_rejected_without_external_writes(self) -> None:
        for index, variant in enumerate(('pi-root', 'prompts-dir', 'prompt-file')):
            with self.subTest(variant=variant):
                project = Path(self.temp.name) / f'pi-symlink-{index}'
                project.mkdir()
                external = Path(self.temp.name) / f'pi-symlink-external-{index}'
                external.mkdir()
                if variant == 'pi-root':
                    (project / '.pi').symlink_to(external, target_is_directory=True)
                elif variant == 'prompts-dir':
                    (project / '.pi').mkdir()
                    (project / '.pi/prompts').symlink_to(
                        external,
                        target_is_directory=True,
                    )
                else:
                    (project / '.pi/prompts').mkdir(parents=True)
                    external_prompt = external / 'brain.md'
                    external_prompt.write_text('external prompt\n', encoding='utf-8')
                    (project / '.pi/prompts/brain.md').symlink_to(external_prompt)
                project_before = tree_snapshot(project)
                external_before = tree_snapshot(external)

                result = self.run_installer(project=project, check=False)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn('.pi/prompts/', result.stderr)
                self.assertIn('path contains symlink', result.stderr)
                self.assertEqual(tree_snapshot(project), project_before)
                self.assertEqual(tree_snapshot(external), external_before)

    def test_pi_symlinks_to_canonical_source_are_rejected_without_writes(self) -> None:
        canonical = BOOTSTRAP / 'pi/prompts'
        for index, variant in enumerate(('prompts-dir', 'prompt-file')):
            with self.subTest(variant=variant):
                project = Path(self.temp.name) / f'pi-canonical-symlink-{index}'
                if variant == 'prompts-dir':
                    (project / '.pi').mkdir(parents=True)
                    (project / '.pi/prompts').symlink_to(
                        canonical,
                        target_is_directory=True,
                    )
                else:
                    (project / '.pi/prompts').mkdir(parents=True)
                    (project / '.pi/prompts/brain.md').symlink_to(
                        canonical / 'brain.md'
                    )
                project_before = tree_snapshot(project)
                canonical_before = tree_snapshot(canonical)

                result = self.run_installer(project=project, check=False)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn('.pi/prompts/', result.stderr)
                self.assertIn('path contains symlink', result.stderr)
                self.assertEqual(tree_snapshot(project), project_before)
                self.assertEqual(tree_snapshot(canonical), canonical_before)
                self.assertFalse((project / 'AGENTS.md').exists())

    def test_hardlinked_managed_file_is_replaced_without_external_write(self) -> None:
        target = (self.project / '.pi/prompts/brain.md').resolve()
        target.parent.mkdir(parents=True)
        canonical = BOOTSTRAP / 'pi/prompts/brain.md'
        external = Path(self.temp.name) / 'external-hardlink.md'
        original = canonical.read_bytes()
        external_content = original.replace(b'# /brain', b'# project-owned brain')
        external.write_bytes(external_content)
        os.link(external, target)

        result = self.run_installer(check=False)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(external.read_bytes(), external_content)
        self.assertEqual(target.read_bytes(), original)
        self.assertNotEqual(target.stat().st_ino, external.stat().st_ino)

    def test_hardlinked_managed_file_stays_external_on_rollback(self) -> None:
        module = self.load_installer()
        target = (self.project / '.pi/prompts/brain.md').resolve()
        target.parent.mkdir(parents=True)
        canonical = BOOTSTRAP / 'pi/prompts/brain.md'
        external = Path(self.temp.name) / 'external-hardlink-rollback.md'
        original = canonical.read_bytes()
        external_content = original.replace(b'# /brain', b'# project-owned brain')
        external.write_bytes(external_content)
        os.link(external, target)
        plan = self.prepared_plan(module)
        original_copy = module.copy_file

        def fail_after_hardlink_copy(src: Path, dst: Path) -> None:
            original_copy(src, dst)
            if dst == target:
                raise OSError('injected hardlink copy failure')

        module.copy_file = fail_after_hardlink_copy
        before = tree_snapshot(self.project)
        with redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(SystemExit, 'failed and rolled back'):
                module.run_transaction(
                    plan.target,
                    plan.transaction_paths,
                    lambda: module.apply_bootstrap_plan(plan),
                )

        self.assertEqual(tree_snapshot(self.project), before)
        self.assertEqual(external.read_bytes(), external_content)
        self.assertEqual(target.read_bytes(), external_content)
        self.assertNotEqual(target.stat().st_ino, external.stat().st_ino)

    def test_hardlinked_managed_config_is_replaced_without_external_write(self) -> None:
        target = (self.project / '.codex/config.toml').resolve()
        target.parent.mkdir(parents=True)
        external = Path(self.temp.name) / 'external-config-hardlink.toml'
        external_content = b'model = "project-model"\n'
        external.write_bytes(external_content)
        os.link(external, target)

        result = self.run_installer(check=False)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(external.read_bytes(), external_content)
        self.assertIn(CONFIG_START.encode('utf-8'), target.read_bytes())
        self.assertNotEqual(target.stat().st_ino, external.stat().st_ino)

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

    def test_pi_prompt_copy_failure_or_interrupt_rolls_back_complete_tree(self) -> None:
        for index, failure in enumerate(
            (OSError('injected Pi prompt copy failure'), KeyboardInterrupt())
        ):
            with self.subTest(failure=type(failure).__name__):
                project = Path(self.temp.name) / f'pi-copy-rollback-{index}'
                project.mkdir()
                module = self.load_installer()
                plan = module.prepare_bootstrap_plan(project.resolve())
                original = module.copy_file

                def fail_after_pi_copy(src: Path, dst: Path) -> None:
                    original(src, dst)
                    if dst == plan.target / '.pi/prompts/brain.md':
                        raise failure

                module.copy_file = fail_after_pi_copy
                before = tree_snapshot(project)
                with redirect_stdout(io.StringIO()):
                    with self.assertRaisesRegex(SystemExit, 'failed and rolled back'):
                        module.run_transaction(
                            plan.target,
                            plan.transaction_paths,
                            lambda: module.apply_bootstrap_plan(plan),
                        )
                self.assertEqual(tree_snapshot(project), before)
                self.assertFalse((project / '.pi').exists())

    def test_retired_adapter_is_restored_and_custom_adapter_is_preserved(self) -> None:
        owned = self.project / '.agent/workflows/brain.md'
        owned.parent.mkdir(parents=True)
        owned.write_text(
            '<!-- AUTO-GENERATED by agentwork bootstrap -->\n# retired\n',
            encoding='utf-8',
        )
        custom = self.project / '.agent/workflows/plan.md'
        custom.write_text('# project-owned plan\n', encoding='utf-8')
        retired_readme = self.project / '.shared/session/README.md'
        retired_readme.parent.mkdir(parents=True)
        retired_readme.write_text(
            '# Project legacy notes\n\n'
            f'{RETIRED_SESSION_START}\nmanaged\n{RETIRED_SESSION_END}\n\n'
            'Project suffix\n',
            encoding='utf-8',
        )
        module = self.load_installer()
        plan = self.prepared_plan(module)
        self.assertIn(Path('.agent/workflows/brain.md'), plan.retired_removed)
        self.assertIn(Path('.agent/workflows/plan.md'), plan.retired_preserved)
        self.assertEqual(
            tuple(item.path for item in plan.retired_managed),
            (retired_readme.resolve(),),
        )
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
