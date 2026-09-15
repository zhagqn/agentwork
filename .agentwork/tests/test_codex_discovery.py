from __future__ import annotations

import json
import os
from pathlib import Path
import selectors
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

from test_adapter_contracts import EXPECTED_CAPABILITIES, EXPECTED_COMMANDS
from test_pi_adapter import REPO_ROOT


@unittest.skipUnless(os.environ.get('AGENTWORK_CODEX_DISCOVERY') == '1',
                     'opt in with AGENTWORK_CODEX_DISCOVERY=1; requires Codex 0.154.0')
class CodexDiscoveryTest(unittest.TestCase):
    def test_installed_skills_and_duplicate_paths(self) -> None:
        executable = shutil.which('codex')
        self.assertIsNotNone(executable, 'Codex 0.154.0 is required for this explicit smoke test')
        scratch = REPO_ROOT / '.tmp'
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='codex-discovery-', dir=scratch) as directory:
            root = Path(directory)
            home = root / 'codex-home'
            home.mkdir()
            env = {key: os.environ[key] for key in ('PATH', 'HOME', 'TMPDIR') if key in os.environ}
            env['CODEX_HOME'] = str(home)
            version = subprocess.run([executable, '--version'], env=env, capture_output=True,
                                     text=True, check=True, timeout=10)
            self.assertEqual(version.stdout.strip(), 'codex-cli 0.154.0')
            project = root / 'installed'
            install = subprocess.run([sys.executable, str(REPO_ROOT / 'install-bootstrap.py'),
                                      '-p', str(project)], capture_output=True, text=True, timeout=30)
            self.assertEqual(install.returncode, 0, install.stdout + install.stderr)
            subprocess.run(['git', 'init', '-q', str(project)], check=True, timeout=10)
            cases = [(project, EXPECTED_COMMANDS | EXPECTED_CAPABILITIES, 1)]
            for label, paths in (
                ('old', [('.codex', 'old')]), ('new', [('.agents', 'new')]),
                ('same', [('.codex', 'same'), ('.agents', 'same')]),
                ('different', [('.codex', 'old'), ('.agents', 'new')]),
            ):
                folder = root / label
                folder.mkdir()
                subprocess.run(['git', 'init', '-q', str(folder)], check=True, timeout=10)
                for path, description in paths:
                    skill = folder / path / 'skills/path-probe/SKILL.md'
                    skill.parent.mkdir(parents=True)
                    skill.write_text(f'---\nname: path-probe\ndescription: {description}\n---\nProbe.\n')
                cases.append((folder, {'path-probe'}, len(paths)))
            with (root / 'server.log').open('w') as log:
                proc = subprocess.Popen([executable, 'app-server', '--stdio'], cwd=root, env=env,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log)
                with selectors.DefaultSelector() as selector:
                    selector.register(proc.stdout, selectors.EVENT_READ)
                    buffer = b''

                    def send(message):
                        proc.stdin.write(json.dumps(message).encode() + b'\n')
                        proc.stdin.flush()

                    def response(request_id):
                        nonlocal buffer
                        deadline = time.monotonic() + 15
                        while time.monotonic() < deadline:
                            while b'\n' in buffer:
                                line, buffer = buffer.split(b'\n', 1)
                                message = json.loads(line)
                                if message.get('id') == request_id:
                                    self.assertNotIn('error', message)
                                    return message['result']
                            if selector.select(max(0, deadline - time.monotonic())):
                                data = os.read(proc.stdout.fileno(), 65536)
                                self.assertTrue(data, 'app-server closed before response')
                                buffer += data
                        self.fail('app-server response timed out')

                    try:
                        send({'id': 1, 'method': 'initialize', 'params': {
                            'clientInfo': {'name': 'agentwork_test', 'version': '1'}}})
                        response(1)
                        send({'method': 'initialized'})
                        request_id = 1
                        for folder, names, count in cases:
                            child = folder / 'nested'
                            child.mkdir()
                            for cwd in (folder, child):
                                with self.subTest(layout=folder.name, cwd=cwd.name):
                                    request_id += 1
                                    send({'id': request_id, 'method': 'skills/list', 'params': {
                                        'cwds': [str(cwd)], 'forceReload': True}})
                                    result = response(request_id)['data']
                                    self.assertEqual(len(result), 1)
                                    self.assertEqual(result[0]['errors'], [])
                                    skills = [s for s in result[0]['skills'] if s['scope'] == 'repo']
                                    self.assertEqual({s['name'] for s in skills}, names)
                                    for name in names:
                                        matching = [s for s in skills if s['name'] == name]
                                        self.assertEqual(len(matching), count)
                                        for skill in matching:
                                            self.assertTrue(skill['enabled'])
                                            self.assertTrue(Path(skill['path']).is_relative_to(folder))
                                    actual_paths = {Path(s['path']).resolve() for s in skills}
                                    expected_paths = {p.resolve() for prefix in ('.codex', '.agents')
                                                      for p in (folder / prefix / 'skills').glob('*/SKILL.md')}
                                    self.assertEqual(actual_paths, expected_paths)
                    finally:
                        proc.terminate()
                        try:
                            proc.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                            proc.wait(timeout=5)
                        proc.stdin.close()
                        proc.stdout.close()


if __name__ == '__main__':
    unittest.main()
