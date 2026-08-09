#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE_ROOT = Path(__file__).resolve().parents[2]
WRAPPER = SOURCE_ROOT / '.agentwork/tools/exa/shared/scripts/exa-mcp.py'


class ExaMcpWrapperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_wrapper(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(WRAPPER), '--project-root', str(self.root), *args],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def test_check_reports_only_safe_statuses(self) -> None:
        missing = self.run_wrapper('--check')
        self.assertEqual(missing.returncode, 1)
        self.assertIn('EXA_API_KEY: missing', missing.stdout)

        (self.root / '.env').write_text('EXA_API_KEY=\n')
        empty = self.run_wrapper('--check')
        self.assertEqual(empty.returncode, 1)
        self.assertIn('EXA_API_KEY: empty', empty.stdout)

        secret = 'not-a-real-secret'
        (self.root / '.env').write_text(f'EXA_API_KEY="{secret}"\n')
        configured = self.run_wrapper('--check')
        self.assertEqual(configured.returncode, 0)
        self.assertIn('EXA_API_KEY: configured', configured.stdout)
        self.assertNotIn(secret, configured.stdout + configured.stderr)

    def test_malicious_syntax_is_passed_literally_via_environment(self) -> None:
        bin_dir = self.root / 'bin'
        bin_dir.mkdir()
        capture = self.root / 'capture.json'
        sentinel = self.root / 'executed'
        fake_npx = bin_dir / 'npx'
        fake_npx.write_text(
            '#!/usr/bin/env python3\n'
            'import json, os, pathlib, sys\n'
            "pathlib.Path(os.environ['CAPTURE_PATH']).write_text(json.dumps({\n"
            "    'argv': sys.argv[1:],\n"
            "    'key': os.environ.get('EXA_API_KEY'),\n"
            "    'tools': os.environ.get('ENABLED_TOOLS'),\n"
            '}))\n'
        )
        fake_npx.chmod(0o755)
        fake_node = bin_dir / 'node'
        fake_node.write_text('#!/bin/sh\nprintf "v20.12.0\\n"\n')
        fake_node.chmod(0o755)
        value = f'$(touch {sentinel})`touch {sentinel}`\'quoted\''
        (self.root / '.env').write_text(f'EXA_API_KEY="{value}"\n')
        child_env = os.environ.copy()
        child_env['PATH'] = f'{bin_dir}{os.pathsep}{child_env["PATH"]}'
        child_env['CAPTURE_PATH'] = str(capture)

        result = self.run_wrapper(env=child_env)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(sentinel.exists())
        self.assertNotIn(value, result.stdout + result.stderr)
        recorded = json.loads(capture.read_text())
        self.assertEqual(recorded['argv'], ['-y', 'exa-mcp-server@3.4.0'])
        self.assertEqual(recorded['key'], value)
        self.assertEqual(recorded['tools'], 'web_search_exa,web_fetch_exa')
        self.assertNotIn(value, recorded['argv'])

    def test_check_requires_compatible_node_and_npx(self) -> None:
        (self.root / '.env').write_text('EXA_API_KEY=configured\n')
        empty_bin = self.root / 'empty-bin'
        empty_bin.mkdir()
        env = os.environ.copy()
        env['PATH'] = str(empty_bin)
        result = self.run_wrapper('--check', env=env)
        self.assertEqual(result.returncode, 1)
        self.assertIn('EXA_API_KEY: configured', result.stdout)
        self.assertIn('node: missing-or-incompatible', result.stdout)
        self.assertIn('npx: missing', result.stdout)

    def test_duplicate_and_unmatched_assignments_fail_before_npx(self) -> None:
        for content in ('EXA_API_KEY=one\nEXA_API_KEY=two\n', 'EXA_API_KEY="open\n'):
            with self.subTest(content=content):
                (self.root / '.env').write_text(content)
                result = self.run_wrapper()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('[exa-mcp]', result.stderr)

    def test_other_assignments_and_export_form_are_supported(self) -> None:
        (self.root / '.env').write_text("OTHER=1\nexport EXA_API_KEY='value with spaces'\n")
        result = self.run_wrapper('--check')
        self.assertEqual(result.returncode, 0)
        self.assertIn('EXA_API_KEY: configured', result.stdout)
        self.assertNotIn('value with spaces', result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
