from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER = REPO_ROOT / 'install-tool.py'
TOOLS_ROOT = REPO_ROOT / '.agentwork/tools'
REGISTRY = TOOLS_ROOT / 'registry.json'
PI_OPTIONAL_TOOLS = ('browser', 'research', 'codegraph')
PI_SKILL_REFERENCES = {
    'browser': '../../../.shared/skills/browser/SKILL.md',
    'research': '../../../.shared/skills/research/SKILL.md',
    'codegraph': '../../../.shared/mcp/codegraph.md',
}
PI_PATH = shutil.which('pi')


def pi_version() -> str | None:
    if PI_PATH is None:
        return None
    result = subprocess.run(
        [PI_PATH, '--version'],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


PI_VERSION = pi_version()


def load_manifest(name: str) -> dict:
    return json.loads(
        (TOOLS_ROOT / name / 'tool.json').read_text(encoding='utf-8')
    )


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


class PiOptionalToolSurfaceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(
            prefix='agentwork-pi-optional-tools-'
        )
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / 'project'
        self.project.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.project)], check=True)
        boundary = self.project / 'staged-boundary.txt'
        boundary.write_text('keep staged\n', encoding='utf-8')
        subprocess.run(
            ['git', '-C', str(self.project), 'add', boundary.name],
            check=True,
        )

    def run_installer(
        self,
        action: str,
        *names: str,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [
                'python3',
                str(INSTALLER),
                action,
                *names,
                '-p',
                str(self.project),
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return result

    def staged_hash(self) -> str:
        diff = subprocess.run(
            ['git', '-C', str(self.project), 'diff', '--cached', '--binary'],
            check=True,
            capture_output=True,
        ).stdout
        return hashlib.sha256(diff).hexdigest()

    def project_snapshot(self) -> dict[str, tuple[str, bytes | str | None]]:
        return {
            key: value
            for key, value in tree_snapshot(self.project).items()
            if key != '.git' and not key.startswith('.git/')
        }

    def pi_entry(self, name: str) -> dict:
        entries = [
            entry
            for entry in load_manifest(name)['entries']
            if entry['surface'] == 'pi'
        ]
        self.assertEqual(len(entries), 1, name)
        return entries[0]

    def assert_manifest_exact(self) -> None:
        for name in PI_OPTIONAL_TOOLS:
            manifest = load_manifest(name)
            tool_root = TOOLS_ROOT / name
            for entry in manifest['entries']:
                source = tool_root / entry['from']
                target = self.project / entry['to']
                with self.subTest(name=name, target=entry['to']):
                    self.assertTrue(target.exists() or target.is_symlink())
                    self.assertEqual(tree_snapshot(target), tree_snapshot(source))

    def test_manifests_define_thin_settings_free_pi_skills(self) -> None:
        registry = json.loads(REGISTRY.read_text(encoding='utf-8'))
        registry_tools = {
            item['name']: item
            for item in registry['tools']
            if item['name'] in PI_OPTIONAL_TOOLS
        }
        self.assertEqual(set(registry_tools), set(PI_OPTIONAL_TOOLS))

        for name in PI_OPTIONAL_TOOLS:
            manifest = load_manifest(name)
            entry = self.pi_entry(name)
            source = TOOLS_ROOT / name / entry['from']
            skill = source / 'SKILL.md'
            with self.subTest(name=name):
                self.assertEqual(registry_tools[name]['kind'], manifest['kind'])
                self.assertEqual(entry['from'], f'pi/skills/{name}')
                self.assertEqual(entry['to'], f'.pi/skills/{name}')
                self.assertTrue(skill.is_file())
                content = skill.read_text(encoding='utf-8')
                self.assertIn(f'name: {name}', content)
                self.assertIn('description:', content)
                self.assertIn(PI_SKILL_REFERENCES[name], content)
                self.assertFalse(
                    any(
                        item['to'] == '.pi/settings.json'
                        for item in manifest['entries']
                    )
                )

        self.assertEqual(load_manifest('codegraph')['kind'], ['mcp', 'skill'])

    def test_install_reinstall_uninstall_and_restore_are_exact(self) -> None:
        staged_before = self.staged_hash()
        neighbor = self.project / '.pi/skills/project-owned/SKILL.md'
        neighbor.parent.mkdir(parents=True)
        neighbor.write_text(
            '---\nname: project-owned\ndescription: keep\n---\n',
            encoding='utf-8',
        )

        self.run_installer('install', *PI_OPTIONAL_TOOLS)
        self.assert_manifest_exact()
        for name in PI_OPTIONAL_TOOLS:
            skill_dir = self.project / f'.pi/skills/{name}'
            with self.subTest(name=name, reference='installed'):
                self.assertTrue(
                    (skill_dir / PI_SKILL_REFERENCES[name]).resolve().is_file()
                )
        self.assertFalse((self.project / '.pi/settings.json').exists())
        installed = self.project_snapshot()
        self.run_installer('install', *PI_OPTIONAL_TOOLS)
        self.assert_manifest_exact()
        self.assertEqual(self.project_snapshot(), installed)

        browser_skill = self.project / '.pi/skills/browser/SKILL.md'
        browser_skill.write_text('drifted\n', encoding='utf-8')
        self.run_installer('install', *PI_OPTIONAL_TOOLS)
        self.assert_manifest_exact()
        self.assertEqual(self.project_snapshot(), installed)
        self.assertEqual(self.staged_hash(), staged_before)

        self.run_installer('uninstall', *PI_OPTIONAL_TOOLS)
        for name in PI_OPTIONAL_TOOLS:
            entry = self.pi_entry(name)
            self.assertFalse((self.project / entry['to']).exists())
        self.assertTrue(neighbor.is_file())
        self.assertFalse((self.project / '.pi/settings.json').exists())

        self.run_installer('install', *PI_OPTIONAL_TOOLS)
        self.assert_manifest_exact()
        self.assertTrue(neighbor.is_file())
        self.assertFalse((self.project / '.pi/settings.json').exists())
        self.assertEqual(self.staged_hash(), staged_before)

    def test_existing_pi_settings_remain_project_owned(self) -> None:
        settings = self.project / '.pi/settings.json'
        settings.parent.mkdir(parents=True)
        before = b'{"projectOwned": true}\n'
        settings.write_bytes(before)

        self.run_installer('install', *PI_OPTIONAL_TOOLS)
        self.assertEqual(settings.read_bytes(), before)
        self.run_installer('uninstall', *PI_OPTIONAL_TOOLS)
        self.assertEqual(settings.read_bytes(), before)

    @unittest.skipUnless(
        PI_PATH is not None and PI_VERSION == '0.84.4',
        'requires the Pi 0.84.4 compatibility baseline',
    )
    def test_pi_0844_rpc_discovers_only_trusted_project_skills(self) -> None:
        self.run_installer('install', *PI_OPTIONAL_TOOLS)
        approved = self.rpc_skill_commands('--approve', 'approved')
        denied = self.rpc_skill_commands('--no-approve', 'denied')

        expected = {f'skill:{name}' for name in PI_OPTIONAL_TOOLS}
        self.assertEqual(set(approved), expected)
        self.assertEqual(set(denied), set())
        for name, command in approved.items():
            tool_name = name.removeprefix('skill:')
            source_info = command['sourceInfo']
            with self.subTest(name=name):
                self.assertEqual(command['source'], 'skill')
                self.assertEqual(source_info['scope'], 'project')
                self.assertEqual(
                    Path(source_info['path']).resolve(),
                    (
                        self.project
                        / f'.pi/skills/{tool_name}/SKILL.md'
                    ).resolve(),
                )

        self.assertFalse((self.project / '.pi/settings.json').exists())
        for label in ('approved', 'denied'):
            config_dir = self.root / f'pi-config-{label}'
            self.assertEqual(list(config_dir.rglob('settings.json')), [])
            self.assertEqual(list(config_dir.rglob('trust.json')), [])

    def rpc_skill_commands(self, trust_flag: str, label: str) -> dict[str, dict]:
        if PI_PATH is None:
            self.fail('Pi executable disappeared during the test')
        config_dir = self.root / f'pi-config-{label}'
        env = os.environ.copy()
        env.update(
            {
                'PI_CODING_AGENT_DIR': str(config_dir),
                'PI_OFFLINE': '1',
            }
        )
        result = subprocess.run(
            [
                PI_PATH,
                '--mode',
                'rpc',
                trust_flag,
                '--no-session',
                '--offline',
                '--no-tools',
                '--no-extensions',
                '--no-prompt-templates',
                '--no-themes',
                '--no-context-files',
            ],
            cwd=self.project,
            env=env,
            input='{"type":"get_commands"}\n',
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        responses = [
            json.loads(line)
            for line in result.stdout.splitlines()
            if line.strip()
        ]
        matching = [
            item
            for item in responses
            if item.get('type') == 'response'
            and item.get('command') == 'get_commands'
        ]
        self.assertEqual(len(matching), 1, result.stdout)
        commands = matching[0]['data']['commands']
        return {
            item['name']: item
            for item in commands
            if item['source'] == 'skill'
        }


if __name__ == '__main__':
    unittest.main(verbosity=2)
