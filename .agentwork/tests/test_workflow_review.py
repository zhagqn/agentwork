import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / '.shared/scripts/case-review.sh'
spec = importlib.util.spec_from_file_location('workflow_check', ROOT / '.shared/scripts/agentwork-check.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class WorkflowReviewTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.case = self.root / '.shared/case/20260101-test.md'
        self.case.parent.mkdir(parents=True)
        self.fixture = next(v for k, v in checker.SELF_TEST_FIXTURES.items() if k.startswith('.shared/case/'))

    def check_case(self, text):
        self.case.write_text(text)
        return checker.check_case(self.case, True)[1]

    def test_empty_workset(self):
        import re
        empty = re.sub(r'(## 当前批次工作集[^\n]*\n).*?(?=\n## )', r'\1\n', self.fixture, flags=re.S)
        self.assertEqual(self.check_case(empty), [])
        active = empty.replace('- [x]', '- [ ]')
        self.assertIn('missing_workset_entries', self.check_case(active))
        self.assertEqual(self.check_case(active.replace('## 当前批次工作集（可选）', '## 当前批次工作集（可选）\n当前无工作集。')), [])
        self.assertTrue(self.check_case(empty.replace('## 当前批次工作集（可选）', '## 其他')))

    def test_independent_duplicate_anchor_is_not_blocking(self):
        text = self.fixture.replace('- 提交: `-`', '- 提交: `abcdef1234`')
        line = next(x for x in text.splitlines() if x.startswith('- 提交:'))
        text = text.replace(line, line + '\n- 提交: `abcdef1234` | 范围: `api/` | 验证: 独立授权边界检查通过。')
        self.assertEqual(self.check_case(text), [])

    def test_all_brain_plan_headings_are_required(self):
        for kind in ('brain', 'plan'):
            content = next(v for k, v in checker.SELF_TEST_FIXTURES.items() if f'/{kind}/' in k)
            path = self.root / f'{kind}.md'
            check = getattr(checker, f'check_{kind}')
            for heading in (x for x in content.splitlines() if x.startswith(('## ', '# ', '> 来源:'))):
                path.write_text(content.replace(heading, '', 1))
                # Only required headings are a gate; the fixture may include optional headings.
                if heading.startswith(('## 约束', '## Blockers', '## 完成标准', '## 下一步（', '## 执行记录')):
                    continue
                self.assertTrue(check(path)[1], (kind, heading))

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True)

    def test_git_paths_and_latest_case(self):
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Fixture')
        names = ['a b.txt', 'a -> b.txt', '中文.txt', 'tab\tfile', 'line\nfile', 'quote"file', 'old.txt']
        (self.root / 'src').mkdir()
        for name in names:
            (self.root / 'src' / name).write_text('before')
        self.case.write_text('## 当前批次工作集（可选）\n- 范围: `src/` | 主题: fixture\n')
        readme = self.case.parent / 'README.md'
        readme.write_text('not a case')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        for name in names[:-1]:
            (self.root / 'src' / name).write_text('after')
        self.git('mv', 'src/old.txt', 'src/new -> name.txt')
        os.utime(readme, (2000000000, 2000000000))
        for args in ([], [str(self.case)]):
            result = subprocess.run(['bash', str(SCRIPT), *args], cwd=self.root, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f'Case: {self.case.relative_to(self.root)}' if not args else f'Case: {self.case}', result.stdout)
            self.assertNotIn('未被“当前批次工作集”覆盖', result.stdout)
            self.assertNotIn('记录但当前工作区未体现', result.stdout)
            self.assertIn('工作区改动（git status --porcelain）：7', result.stdout)

        # 精确路径、rename 来源与 glob 同时覆盖；未覆盖的换行路径不能被拆成两条。
        self.case.write_text('## 当前批次工作集（可选）\n' + '\n'.join(
            f'- 范围: `src/{name}` | 主题: fixture'
            for name in ['a b.txt', 'a -> b.txt', '中文.txt', 'tab\tfile', 'quote"file', 'old.txt', 'new -> name.txt', 'line*']
        ) + '\n')
        self.git('add', str(self.case.relative_to(self.root)))
        self.git('commit', '-qm', 'case ranges', '--', str(self.case.relative_to(self.root)))
        result = subprocess.run(['bash', str(SCRIPT), str(self.case)], cwd=self.root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('未被“当前批次工作集”覆盖', result.stdout)
        self.assertNotIn('缺失/疑似过期', result.stdout)
        self.assertNotIn('记录但当前工作区未体现', result.stdout)

    def test_readme_only_is_not_a_case(self):
        (self.case.parent / 'README.md').write_text('not a case')
        result = subprocess.run(['bash', str(SCRIPT)], cwd=self.root, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('暂无 Case 记录', result.stderr)
