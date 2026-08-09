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


class ToolCatalogTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix='agentwork-tool-catalog-')
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'
        self.project.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.project)], check=True)
        boundary = self.project / 'staged-boundary.txt'
        boundary.write_text('keep staged\n')
        subprocess.run(['git', '-C', str(self.project), 'add', boundary.name], check=True)
        registry = json.loads(REGISTRY.read_text())
        self.tools = registry['tools']
        self.names = [tool['name'] for tool in self.tools]

    def run_installer(self, command: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ['python3', str(INSTALLER), command, *self.names, '-p', str(self.project)],
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

    def manifest_entries(self):
        for tool in self.tools:
            tool_root = TOOLS_ROOT / tool['dir']
            manifest = json.loads((tool_root / 'tool.json').read_text())
            self.assertEqual(manifest['name'], tool['name'])
            self.assertEqual(manifest['kind'], tool['kind'])
            for entry in manifest['entries']:
                yield tool_root / entry['from'], self.project / entry['to']

    def assert_manifest_exact(self) -> None:
        for source, target in self.manifest_entries():
            with self.subTest(target=target.relative_to(self.project)):
                self.assertTrue(target.exists() or target.is_symlink())
                self.assertEqual(tree_snapshot(target), tree_snapshot(source))

    def test_full_catalog_install_reinstall_and_uninstall_round_trip(self) -> None:
        staged_before = self.staged_hash()
        self.run_installer('install')
        self.assert_manifest_exact()
        first_install = self.project_snapshot()
        self.run_installer('install')
        self.assert_manifest_exact()
        self.assertEqual(self.project_snapshot(), first_install)
        self.assertEqual(self.staged_hash(), staged_before)

        self.run_installer('uninstall')
        for _, target in self.manifest_entries():
            self.assertFalse(target.exists() or target.is_symlink())
        after_uninstall = self.project_snapshot()
        self.run_installer('uninstall')
        self.assertEqual(self.project_snapshot(), after_uninstall)
        self.assertEqual(self.staged_hash(), staged_before)
        self.assertEqual((self.project / '.env').read_bytes(), b'')
        self.assertEqual((self.project / '.gitignore').read_text(), '.env\n')


if __name__ == '__main__':
    unittest.main(verbosity=2)
