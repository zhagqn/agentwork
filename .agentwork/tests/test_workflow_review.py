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
        # 名称须符合 YYYYMMDD-HHMM-slug，否则不参与 latest 选取。
        self.case = self.root / '.shared/case/20260101-0000-test.md'
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

    def test_exec_review_keep_structural_and_content_gates(self):
        plan = next(v for k, v in checker.SELF_TEST_FIXTURES.items() if 'exec-fixture' in k)
        review = next(v for k, v in checker.SELF_TEST_FIXTURES.items() if '/review/' in k)
        path = self.root / 'artifact.md'
        checks = ((plan, checker.check_exec, ('# Plan: fixture', '## 验证策略')),
                  (review, lambda p: checker.check_review(p, True), ('# Review:', '## Findings')))
        for text, check, headings in checks:
            path.write_text(text)
            self.assertEqual(check(path)[1], [])
            for prefix in headings:
                heading = next(line for line in text.splitlines() if line.startswith(prefix.split(':')[0]))
                path.write_text(text.replace(heading, '', 1))
                self.assertTrue(check(path)[1], heading)
            path.write_text(text + '\n{name}\n')
            self.assertTrue(check(path)[1])
        path.write_text(plan.replace('- [x]', '- [ ]'))
        self.assertIn('missing_completed_task_checkbox', checker.check_exec(path)[1])
        path.write_text(review.replace('### Important\n- none', '### Important\n- 保留阻塞问题'))
        self.assertTrue(checker.check_review(path, True)[1])

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

    def latest_case(self):
        return subprocess.run(
            ['python3', str(ROOT / '.shared/scripts/agentwork-check.py'), 'latest', 'case'],
            cwd=self.root, text=True, capture_output=True,
        )

    def test_latest_ignores_nonconforming_names_regardless_of_mtime(self):
        self.case.write_text('# Case: stamped\n')
        stray = self.case.parent / 'scratch-notes.md'
        stray.write_text('# Case: draft\n')
        os.utime(self.case, (1600000000, 1600000000))
        os.utime(stray, (2000000000, 2000000000))

        result = self.latest_case()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(self.case.relative_to(self.root)))

        # case-review.sh 必须与 agentwork-check.py 得到同一结论。
        review = subprocess.run(['bash', str(SCRIPT)], cwd=self.root, text=True, capture_output=True)
        self.assertEqual(review.returncode, 0, review.stderr)
        self.assertIn(f'Case: {self.case.relative_to(self.root)}', review.stdout)
        self.assertNotIn('scratch-notes.md', review.stdout)

    def test_same_timestamp_is_ambiguous_instead_of_mtime_tiebreak(self):
        self.case.write_text('# Case: first\n')
        twin = self.case.parent / '20260101-0000-twin.md'
        twin.write_text('# Case: second\n')

        result = self.latest_case()
        self.assertEqual(result.returncode, 1)
        self.assertIn('ambiguous_latest:case', result.stderr)
        for path in (self.case, twin):
            self.assertIn(str(path.relative_to(self.root)), result.stderr)

        review = subprocess.run(['bash', str(SCRIPT)], cwd=self.root, text=True, capture_output=True)
        self.assertNotEqual(review.returncode, 0)
        self.assertIn('无法确定最新 Case', review.stderr)

    def test_readme_only_is_not_a_case(self):
        (self.case.parent / 'README.md').write_text('not a case')
        result = subprocess.run(['bash', str(SCRIPT)], cwd=self.root, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('暂无 Case 记录', result.stderr)

    def test_literal_bracket_path_does_not_cover_unrelated_file(self):
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Fixture')
        (self.root / 'src').mkdir()
        literal = self.root / 'src/[id].tsx'
        other = self.root / 'src/i.tsx'
        literal.write_text('before')
        other.write_text('before')
        self.case.write_text('## 当前批次工作集（可选）\n- 范围: `src/[id].tsx` | 主题: fixture\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        other.write_text('after')
        for state in ('modified', 'deleted', 'renamed'):
            with self.subTest(state=state):
                if state == 'modified':
                    literal.write_text('after')
                elif state == 'deleted':
                    literal.unlink()
                else:
                    literal.write_text('before')
                    self.git('mv', 'src/[id].tsx', 'src/new.tsx')
                before_index = self.git('diff', '--cached', '--binary').stdout
                result = subprocess.run(['bash', str(SCRIPT), str(self.case)], cwd=self.root, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                uncovered = result.stdout.split('工作区有改动但未被“当前批次工作集”覆盖：', 1)[1].split('\n\n', 1)[0]
                self.assertIn('`src/i.tsx`', uncovered)
                self.assertNotIn('`src/[id].tsx`', uncovered)
                self.assertNotIn('记录但当前工作区未体现', result.stdout)
                self.assertEqual(self.git('diff', '--cached', '--binary').stdout, before_index)
