#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER = REPO_ROOT / 'install-bootstrap.py'
BOOTSTRAP = REPO_ROOT / '.agentwork/bootstrap'
CONFIG_START = '# >>> AGENTWORK bootstrap: Codex agents >>>'
CONFIG_END = '# <<< AGENTWORK bootstrap: Codex agents <<<'


class InstallBootstrapCodexAgentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix='agentwork-bootstrap-')
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'
        self.project.mkdir()

    def run_installer(self, *, check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ['python3', str(INSTALLER), '-p', str(self.project)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if check and result.returncode != 0:
            self.fail(f'installer failed: {result.stderr}{result.stdout}')
        return result

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
        self.assertIn('cannot replace non-agentwork Codex agent file', result.stderr)
        self.assertEqual(agent.read_text(encoding='utf-8'), 'model = "project-model"\n')
        self.assertFalse((self.project / 'AGENTS.md').exists())

    def test_codex_directory_symlink_is_rejected(self) -> None:
        external = Path(self.temp.name) / 'external-codex'
        external.mkdir()
        (self.project / '.codex').symlink_to(external, target_is_directory=True)

        result = self.run_installer(check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('cannot manage Codex agent through symlink', result.stderr)
        self.assertEqual(list(external.iterdir()), [])
        self.assertFalse((self.project / 'AGENTS.md').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
