from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_pi_adapter import EXPECTED_PI_COMMANDS, REPO_ROOT
from test_pi_optional_tools import PI_PATH, PI_VERSION


@unittest.skipUnless(PI_PATH is not None and PI_VERSION in ('0.84.4', '0.85.1'),
                     'requires Pi 0.84.4 or 0.85.1; set AGENTWORK_PI_EXECUTABLE if needed')
class PiPromptDiscoveryTest(unittest.TestCase):
    def test_core_prompts_follow_trust_cwd_and_disable_flag(self) -> None:
        scratch = REPO_ROOT / '.tmp'
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='pi-discovery-', dir=scratch) as directory:
            root = Path(directory)
            project = root / 'project'
            result = subprocess.run(
                [sys.executable, str(REPO_ROOT / 'install-bootstrap.py'), '-p', str(project)],
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            subprocess.run(['git', 'init', '-q', str(project)], check=True, timeout=10)
            child = project / 'nested'
            child.mkdir()
            spec = json.loads((REPO_ROOT / '.agentwork/bootstrap/spec.json').read_text())
            descriptions = {w['name']: w['description'] for w in spec['wrappers']}
            for label, cwd, flags, expected in (
                ('trusted', project, ['--approve'], set(EXPECTED_PI_COMMANDS)),
                ('untrusted', project, ['--no-approve'], set()),
                ('nested', child, ['--approve'], set()),
                ('disabled', project, ['--approve', '--no-prompt-templates'], set()),
            ):
                with self.subTest(version=PI_VERSION, scenario=label):
                    config = root / f'config-{label}'
                    env = {k: os.environ[k] for k in ('PATH', 'HOME', 'TMPDIR') if k in os.environ}
                    env.update(PI_CODING_AGENT_DIR=str(config), PI_OFFLINE='1', PI_TELEMETRY='0')
                    result = subprocess.run(
                        [PI_PATH, '--mode', 'rpc', '--no-session', '--offline', '--no-tools',
                         '--no-extensions', '--no-skills', '--no-themes', '--no-context-files', *flags],
                        cwd=cwd, env=env, input='{"type":"get_commands"}\n',
                        capture_output=True, text=True, timeout=15,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                    responses = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
                    matching = [r for r in responses if r.get('command') == 'get_commands']
                    self.assertEqual(len(matching), 1, result.stdout)
                    self.assertTrue(matching[0]['success'])
                    prompts = [c for c in matching[0]['data']['commands'] if c['source'] == 'prompt']
                    self.assertEqual({p['name'] for p in prompts}, expected)
                    self.assertEqual(len(prompts), len(expected))
                    for prompt in prompts:
                        info = prompt['sourceInfo']
                        self.assertEqual(info['scope'], 'project')
                        self.assertEqual(Path(info['path']).resolve(),
                                         (project / '.pi/prompts' / f"{prompt['name']}.md").resolve())
                        self.assertEqual(prompt['description'], descriptions[prompt['name']])
                    self.assertEqual(list(config.rglob('settings.json')), [])
                    self.assertEqual(list(config.rglob('trust.json')), [])
                    self.assertFalse((project / '.pi/settings.json').exists())


if __name__ == '__main__':
    unittest.main()
