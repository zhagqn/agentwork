import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('verify_checker', ROOT / '.shared/scripts/agentwork-check.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class VerifyTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        scripts = self.root / '.shared/scripts'
        scripts.mkdir(parents=True)
        for name in ('verify.sh', 'agentwork-check.py'):
            shutil.copy2(ROOT / '.shared/scripts' / name, scripts)
        self.script = scripts / 'verify.sh'
        self.checker = scripts / 'agentwork-check.py'
        (self.root / '.agentwork/tests').mkdir(parents=True)
        (self.root / '.agentwork/tests/test_fixture.py').write_text(
            'import unittest\nclass GateFixture(unittest.TestCase):\n'
            '    def test_pass(self):\n        self.assertTrue(True)\n'
        )
        self.renderer = self.root / '.agentwork/bootstrap/render_bootstrap.py'
        self.renderer.parent.mkdir()
        # 聚合器夹具仅隔离源码测试与渲染，Case resolver 和 self-test 用真实脚本。
        self.renderer.write_text('raise SystemExit(0)\n')
        self.cases = self.root / '.shared/case'
        self.cases.mkdir()
        self.fixture = next(v for k, v in checker.SELF_TEST_FIXTURES.items() if k.startswith('.shared/case/'))

    def run_verify(self):
        return subprocess.run(['bash', str(self.script)], capture_output=True, text=True)

    def test_no_case_and_unique_case(self):
        result = self.run_verify()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('跳过', result.stdout)
        (self.cases / '20260914-2200-one.md').write_text(self.fixture)
        result = self.run_verify()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('PASS:case:', result.stdout)

    def test_ambiguous_latest_fails(self):
        for name in ('one', 'two'):
            (self.cases / f'20260914-2200-{name}.md').write_text(self.fixture)
        result = self.run_verify()
        self.assertEqual(result.returncode, 1)
        self.assertIn('ambiguous_latest', result.stderr)
        self.assertIn('失败：latest case', result.stdout)
        self.assertNotIn('跳过', result.stdout)

    def test_checker_failure_is_not_absent_case(self):
        self.checker.write_text('raise RuntimeError("checker failure")\n')
        result = self.run_verify()
        self.assertEqual(result.returncode, 1)
        self.assertIn('workflow self-test; latest case', result.stdout)
        self.assertNotIn('跳过', result.stdout)

    def test_all_gate_failures_are_reported(self):
        self.renderer.write_text('raise SystemExit(7)\n')
        (self.cases / '20260914-2200-one.md').write_text('# invalid\n')
        result = self.run_verify()
        self.assertEqual(result.returncode, 1)
        self.assertIn('失败：bootstrap render --check; case strict-flow', result.stdout)
        self.assertIn('PASS:self-test:', result.stdout)

    def test_target_project_is_rejected_explicitly(self):
        self.renderer.unlink()
        result = self.run_verify()
        self.assertEqual(result.returncode, 2)
        self.assertIn('source repo', result.stderr)
        self.assertNotIn('全部通过', result.stdout)
