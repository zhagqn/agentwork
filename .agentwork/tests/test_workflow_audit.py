import importlib.util
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / '.shared/scripts/case-audit.sh'
spec = importlib.util.spec_from_file_location('workflow_check', ROOT / '.shared/scripts/agentwork-check.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class WorkflowAuditTest(unittest.TestCase):
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

    def test_all_brain_spec_headings_are_required(self):
        for kind in ('brain', 'spec'):
            content = next(v for k, v in checker.SELF_TEST_FIXTURES.items() if f'/{kind}/' in k)
            path = self.root / f'{kind}.md'
            check = getattr(checker, f'check_{kind}')
            for heading in (x for x in content.splitlines() if x.startswith(('## ', '# ', '> 来源:'))):
                path.write_text(content.replace(heading, '', 1))
                # Only required headings are a gate; the fixture may include optional headings.
                if heading.startswith(('## 约束', '## Blockers', '## 完成标准', '## 下一步（', '## 执行记录')):
                    continue
                self.assertTrue(check(path)[1], (kind, heading))

    def test_task_line_format_variants(self):
        text = next(v for k, v in checker.SELF_TEST_FIXTURES.items() if 'exec-fixture' in k)
        path = self.root / 'spec.md'
        accepted = (
            text.replace(' | 覆盖: D1 | 验证: 运行', ' ｜ 覆盖：D1 ｜ 验证：运行', 1),
            text.replace(' | 覆盖: D1 | 依赖: T1 | ', '|覆盖: D1|依赖: T1|'),
        )
        for value in accepted:
            path.write_text(value)
            self.assertEqual(checker.check_spec(path)[1], [])
            self.assertEqual(checker.check_exec(path)[1], [])
        t2 = next(line for line in text.splitlines() if line.startswith('- [ ] T2'))
        rejected = [
            (text.replace(t2, '- [X] T2 缺字段'), checker.check_spec, 'task_missing_field:T2:覆盖'),
            (text.replace('- [x] T1', '- [ ] T1').replace('- [ ] T2', '- [X] T2'), checker.check_exec,
             'task_done_before_dependency:T2:T1'),
            (text.replace('- [ ] T2', '- [-] T2'), checker.check_spec, 'task_unknown_checkbox'),
        ]
        for placeholder in ('待确认', '（待定）', '...', '—', '暂无'):
            rejected.append((text.replace('验证: 运行 agentwork-check exec', f'验证: {placeholder}', 1),
                             checker.check_spec, 'task_placeholder_field:T1:验证'))
        for value, check, expected in rejected:
            with self.subTest(expected=expected, value=value[-60:]):
                path.write_text(value)
                self.assertTrue(any(e.startswith(expected) for e in check(path)[1]))
        path.write_text(text.replace('覆盖: D1 | 验证:', '覆盖: D1 | 依赖: T1 | 验证:', 1))
        failures = checker.check_spec(path)[1]
        self.assertIn('task_self_dependency:T1', failures)
        self.assertFalse(any(e.startswith('task_dependency_cycle') for e in failures))

    def test_explicit_completion_must_not_be_placeholder(self):
        text = next(v for k, v in checker.SELF_TEST_FIXTURES.items() if 'exec-fixture' in k)
        path = self.root / 'spec.md'
        for value in ('', '待定', '（待确认）', '...', 'TBD'):
            with self.subTest(value=value):
                path.write_text(text.replace(' | 验证:', f' | 完成: {value} | 验证:', 1))
                for check in (checker.check_spec, checker.check_exec):
                    self.assertIn('task_placeholder_field:T1:完成', check(path)[1])
                self.assertTrue(self.check_case(self.fixture.replace('完成: 验证通过', f'完成: {value}')))
        for content in (text, text.replace(' | 验证:', ' | 完成: 检查通过 | 验证:', 1)):
            path.write_text(content)
            self.assertEqual(checker.check_spec(path)[1], [])
            self.assertEqual(checker.check_exec(path)[1], [])
        self.assertIn('task_missing_field:T1:完成', self.check_case(self.fixture.replace(' | 完成: 验证通过', '')))

    def test_duplicate_task_fields_are_rejected(self):
        text = next(v for k, v in checker.SELF_TEST_FIXTURES.items() if 'exec-fixture' in k)
        path = self.root / 'spec.md'
        for name, first, second in (
            ('依赖', 'T999', '无'), ('依赖', '无', 'T999'),
            ('覆盖', 'D999', 'D1'), ('完成', '待定', '检查通过'),
            ('验证', '待定', '运行检查'),
        ):
            with self.subTest(name=name, first=first):
                # 混用全角与半角字段分隔符仍须识别重复字段。
                suffix = f' ｜ {name}：{first} | {name}: {second}'
                for content, check in (
                    (text, checker.check_spec), (text, checker.check_exec),
                    (self.fixture, lambda p: checker.check_case(p, True)),
                ):
                    lines = content.splitlines()
                    index = next(i for i, line in enumerate(lines) if line.startswith('- [x] T1 '))
                    lines[index] += suffix
                    path.write_text('\n'.join(lines) + '\n')
                    self.assertIn(f'task_duplicate_field:T1:{name}', check(path)[1])

    def test_coverage_requires_explicit_id_list(self):
        text = next(v for k, v in checker.SELF_TEST_FIXTURES.items() if 'exec-fixture' in k)
        path = self.root / 'spec.md'
        for content, check in (
            (text, checker.check_spec), (text, checker.check_exec),
            (self.fixture, lambda p: checker.check_case(p, True)),
        ):
            for value in ('D1-D1', 'D1-D3', 'D1?', 'D1 and D2'):
                with self.subTest(check=check, value=value):
                    path.write_text(content.replace('覆盖: D1', f'覆盖: {value}'))
                    self.assertTrue(any(e.startswith('task_invalid_coverage:T1:') for e in check(path)[1]))
            for value in ('D1', 'D1, D2', 'D1，D2', 'D1、D2'):
                path.write_text(content.replace('- D1 ', '- D2 第二项决策\n- D1 ', 1)
                                .replace('覆盖: D1', f'覆盖: {value}'))
                failures = check(path)[1]
                self.assertEqual(failures, ['decision_not_covered:D2'] if value == 'D1' else [])

    def test_bold_nested_findings_need_their_own_disposition(self):
        text = next(v for k, v in checker.SELF_TEST_FIXTURES.items() if '/audit/' in k and 'important' not in k)
        path = self.root / 'audit.md'
        for label in ('[规格]', '**[规格]**', '**[质量]**'):
            for prefix in ('### Minor\n- ', '- Minor: '):
                finding = f'{prefix}[质量] 父问题 | 处置: 本轮修复\n  - {label} 子问题'
                path.write_text(text.replace('### Minor\n- none', finding))
                for gate in (False, True):
                    self.assertTrue(any(e.startswith('audit_finding_missing_disposition:minor:')
                                        for e in checker.check_audit(path, gate)[1]))
                path.write_text(text.replace('### Minor\n- none', finding +
                                            '\n    | 处置: 转后续\n    - 证据：file:1'))
                self.assertEqual(checker.check_audit(path, True)[1], [])

    def test_audit_nested_items_and_fullwidth_separators(self):
        text = next(v for k, v in checker.SELF_TEST_FIXTURES.items() if '/audit/' in k and 'important' not in k)
        path = self.root / 'audit.md'
        for minor in (
            '### Minor\n- [质量] 问题 | 处置: 本轮修复\n  - 证据：file:1',
            '- Minor: [质量] 问题 | 处置: 本轮修复\n  - 证据：file:1',
            '### Minor\n- [质量] 问题 ｜ 处置：转后续',
            '### Minor\n- N/A',
        ):
            with self.subTest(minor=minor):
                path.write_text(text.replace('### Minor\n- none', minor))
                self.assertEqual(checker.check_audit(path, True)[1], [])
        path.write_text(text.replace('### Minor\n- none', '### Minor\n- [质量] 问题 | 处置: 拒绝（待确认）'))
        self.assertTrue(any(e.startswith('audit_finding_invalid_disposition') for e in checker.check_audit(path, False)[1]))
        # 带类别标签的嵌套项是独立问题，不能借上一条问题的处置通过。
        path.write_text(text.replace('### Minor\n- none', '### Minor\n- [质量] a | 处置: 本轮修复\n  - [规格] b 嵌套的独立问题'))
        self.assertTrue(any(e.startswith('audit_finding_missing_disposition:minor:[规格] b')
                            for e in checker.check_audit(path, False)[1]))

    def test_dependency_values_must_be_none_or_task_ids(self):
        spec_text = next(v for k, v in checker.SELF_TEST_FIXTURES.items() if 'exec-fixture' in k)
        path = self.root / 'spec.md'
        for value in ('T1', 'T1, T2', 'T1、T2', 'T1，T2'):
            with self.subTest(value=value):
                path.write_text(spec_text.replace('依赖: T1', f'依赖: {value}'))
                failures = checker.check_spec(path)[1]
                self.assertFalse(any(e.startswith(('task_invalid_dependency', 'task_placeholder_field')) for e in failures), failures)
        for value, expected in (
            ('待定', 'task_placeholder_field:T2:依赖'), ('TBD', 'task_placeholder_field:T2:依赖'),
            ('-', 'task_placeholder_field:T2:依赖'), ('不存在的前置任务', 'task_invalid_dependency:T2'),
            ('见上', 'task_invalid_dependency:T2'), ('T1?', 'task_invalid_dependency:T2'),
        ):
            with self.subTest(value=value):
                path.write_text(spec_text.replace('依赖: T1', f'依赖: {value}'))
                for check in (checker.check_spec, checker.check_exec):
                    self.assertTrue(any(e.startswith(expected) for e in check(path)[1]))
                case = self.fixture.replace('依赖: 无', f'依赖: {value}')
                self.assertTrue(any(e.startswith(expected.replace('T2', 'T1')) for e in self.check_case(case)))
        self.assertEqual(self.check_case(self.fixture), [])

    def test_audit_findings_require_category(self):
        text = next(v for k, v in checker.SELF_TEST_FIXTURES.items() if '/audit/' in k and 'important' not in k)
        path = self.root / 'audit.md'
        for minor in (
            '### Minor\n- 问题没有类别 | 处置: 转后续',
            '- Minor: 问题没有类别 | 处置: 转后续',
            '### Minor\n- [质量] a | 处置: 本轮修复\n- b 没有类别 | 处置: 本轮修复',
        ):
            with self.subTest(minor=minor):
                path.write_text(text.replace('### Minor\n- none', minor))
                self.assertTrue(any(e.startswith('audit_finding_missing_category') for e in checker.check_audit(path, False)[1]))
        for minor in (
            '### Minor\n- [质量] 问题 | 处置: 本轮修复\n  - 证据：file:1',
            '- Minor: **[规格]** 问题 | 处置: 转后续',
        ):
            with self.subTest(minor=minor):
                path.write_text(text.replace('### Minor\n- none', minor))
                self.assertEqual(checker.check_audit(path, True)[1], [])

    def test_audit_label_variants(self):
        text = next(v for k, v in checker.SELF_TEST_FIXTURES.items() if '/audit/' in k and 'important' not in k)
        path = self.root / 'audit.md'
        variants = (
            text.replace('- 规格符合：通过', '- **规格符合**：通过'),
            text.replace('- 质量规范：通过', '- **质量规范：** 通过'),
            text.replace('### Minor\n- none', '#### Minor\n- [质量] 问题 | 处置: 本轮修复'),
            text.replace('### Minor\n- none', '### Minor（外部审查）\n- [质量] 问题 | 处置: 本轮修复'),
            text.replace('### Minor\n- none', '**Minor**\n- [质量] 问题 | 处置: 本轮修复'),
        )
        for value in variants:
            with self.subTest(value=value[-80:]):
                path.write_text(value)
                self.assertEqual(checker.check_audit(path, True)[1], [])
        path.write_text(text.replace('### Important\n- none', '#### Important\n- [规格] 阻塞 | 处置: 待决策'))
        self.assertIn('audit_has_important_findings:1', checker.check_audit(path, True)[1])
        path.write_text(text.replace('- 规格符合：通过', '- **规格符合**：不通过'))
        self.assertIn('audit_not_passed:规格符合', checker.check_audit(path, True)[1])

    def test_template_placeholders_stay_in_sync(self):
        known = set(checker.TEMPLATE_PLACEHOLDERS)
        found = set()
        for template in (ROOT / '.shared/templates').glob('*.md'):
            # `{n}` 是编号说明，不是待填占位。
            found.update(t for t in re.findall(r'\{[^{}\n]+\}', template.read_text()) if t != '{n}')
        self.assertEqual(found - known, set())
        self.assertEqual(known - found, set())

    def test_case_decisions_come_from_selected_plan(self):
        goal_decision = self.fixture.replace('- 验证 Case 工件形态。', '- 验证 Case 工件形态。\n- D5 目标中的编号不是决策')
        self.assertEqual(self.check_case(goal_decision), [])
        self.assertIn('task_missing_field:T1:覆盖', self.check_case(self.fixture.replace('- [x] T1 验证 Case 自检 | 覆盖: D1 | 依赖: 无 | 完成: 验证通过 | 验证: 运行自检', '- [X] T1 验证 Case 自检')))

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True)

    def test_task_identity_and_dependency_graph(self):
        text = next(v for k, v in checker.SELF_TEST_FIXTURES.items() if 'exec-fixture' in k)
        variants = (
            (text.replace('- D1 ', '- D1 First decision\n- D1 ', 1), 'duplicate_decision_id'),
            (text.replace('- [ ] T2 ', '- [ ] T1 '), 'duplicate_task_id'),
            (text.replace('覆盖: D1 | 验证:', '覆盖: D1 | 依赖: T1 | 验证:', 1), 'task_self_dependency'),
            (text.replace('覆盖: D1 | 验证:', '覆盖: D1 | 依赖: T2 | 验证:', 1), 'task_dependency_cycle'),
        )
        path = self.root / 'spec.md'
        for value, expected in variants:
            with self.subTest(expected=expected):
                path.write_text(value)
                self.assertTrue(any(e.startswith(expected) for e in checker.check_spec(path)[1]))
                self.assertTrue(any(e.startswith(expected) for e in checker.check_exec(path)[1]))
        path.write_text(text)
        self.assertEqual(checker.check_spec(path)[1], [])
        self.assertEqual(checker.check_exec(path)[1], [])

    def test_case_contract_applies_to_every_case(self):
        text = self.fixture.replace('- [x] T1 验证 Case 自检 | 覆盖: D1 | 依赖: 无 | 完成: 验证通过 | 验证: 运行自检', '- [x] T1 验证 Case 自检 | 覆盖: D1 | 依赖: 无 | 完成: 验证通过 | 验证: 运行自检\n- [x] T2 后续任务 | 覆盖: D1 | 依赖: T1 | 完成: 验证通过 | 验证: 运行自检')
        self.assertEqual(self.check_case(text), [])
        variants = (
            (text.replace('- D1 使用命令内建 harness。', ''), 'missing_decisions'),
            (re.sub(r'(^- \[x\] )T\d+ ', r'\1', text, flags=re.M), 'task_missing_id'),
            (text.replace(' | 覆盖: D1', ''), 'task_missing_field:T1:覆盖'),
            (text.replace(' | 完成: 验证通过', ''), 'task_missing_field:T1:完成'),
            (text.replace(' | 依赖: 无', ''), 'task_missing_field:T1:依赖'),
            (text.replace(' | 验证: 运行自检', ''), 'task_missing_field:T1:验证'),
            (text.replace('- [x] T1 ', '- [ ] T1 '), 'task_done_before_dependency:T2:T1'),
        )
        for value, expected in variants:
            with self.subTest(expected=expected):
                self.assertTrue(any(e.startswith(expected) for e in self.check_case(value)))
        # 不再兼容未编号的旧 Case：没有规格来源行也一样校验。
        legacy = self.fixture.replace('- [x] T1 验证 Case 自检 | 覆盖: D1 | 依赖: 无 | 完成: 验证通过 | 验证: 运行自检', '- [x] 验证 Case 自检。').replace('- D1 使用命令内建 harness。', '- 使用命令内建 harness。')
        failures = self.check_case(legacy)
        self.assertIn('missing_decisions', failures)
        self.assertTrue(any(e.startswith('task_missing_id') for e in failures))

    def test_audit_verdicts_and_completion_gate(self):
        text = next(v for k, v in checker.SELF_TEST_FIXTURES.items() if '/audit/' in k and 'important' not in k)
        path = self.root / 'audit.md'
        for value in ('待定', '通过不了', 'TBD'):
            path.write_text(re.sub(r'^- 规格符合：.*$', f'- 规格符合：{value}', text, flags=re.M))
            for gate in (False, True):
                self.assertIn('invalid_audit_conclusion:规格符合', checker.check_audit(path, gate)[1])
        path.write_text(text.replace('规格符合：通过', '规格符合：不通过'))
        self.assertEqual(checker.check_audit(path, False)[1], [])
        self.assertIn('audit_not_passed:规格符合', checker.check_audit(path, True)[1])
        path.write_text(text.replace('## 结论', '## 结论\n- 规格符合：通过'))
        self.assertIn('duplicate_audit_conclusion:规格符合', checker.check_audit(path, True)[1])

    def test_audit_dispositions_share_one_parser(self):
        text = next(v for k, v in checker.SELF_TEST_FIXTURES.items() if '/audit/' in k and 'important' not in k)
        path = self.root / 'audit.md'
        formats = (
            '### Minor\n- [质量] 问题{suffix}',
            '### Minor\n1. [质量] 问题{suffix}',
            '- Minor: [质量] 问题{suffix}',
            '1. **Minor**: [质量] 问题{suffix}',
        )
        for form in formats:
            for disposition in ('', ' | 处置: ...', ' | 处置: 拒绝', ' | 处置: 拒绝（TBD）'):
                with self.subTest(form=form, disposition=disposition):
                    path.write_text(text.replace('### Minor\n- none', form.format(suffix=disposition)))
                    self.assertTrue(checker.check_audit(path, False)[1])
            for disposition in ('本轮修复', '转后续任务', '待用户决策', '拒绝（已有回归覆盖）'):
                path.write_text(text.replace('### Minor\n- none', form.format(suffix=f' | 处置: {disposition}')))
                self.assertEqual(checker.check_audit(path, True)[1], [])
        path.write_text(text.replace('### Minor\n- none', '### Minor\n- [质量] 问题\n  | 处置: 转后续'))
        self.assertEqual(checker.check_audit(path, True)[1], [])
        path.write_text(text.replace('### Important\n- none', '- Important: [质量] 阻塞 | 处置: 待决策'))
        self.assertIn('audit_has_important_findings:1', checker.check_audit(path, True)[1])
        path.write_text(text.replace('### Critical\n- none', '- Critical: none').replace('### Important\n- none', '- Important: none'))
        self.assertEqual(checker.check_audit(path, True)[1], [])

    def test_exec_audit_keep_structural_and_content_gates(self):
        spec = next(v for k, v in checker.SELF_TEST_FIXTURES.items() if 'exec-fixture' in k)
        audit = next(v for k, v in checker.SELF_TEST_FIXTURES.items() if '/audit/' in k and 'important' not in k)
        path = self.root / 'artifact.md'
        checks = ((spec, checker.check_exec, ('# Spec: exec-fixture', '## 验证策略', '## 决策')),
                  (audit, lambda p: checker.check_audit(p, True), ('# Audit:', '## Findings', '## 结论')))
        for text, check, headings in checks:
            path.write_text(text)
            self.assertEqual(check(path)[1], [])
            for prefix in headings:
                heading = next(line for line in text.splitlines() if line.startswith(prefix.split(':')[0]))
                path.write_text(text.replace(heading, '', 1))
                self.assertTrue(check(path)[1], heading)
            path.write_text(text + '\n{name}\n')
            self.assertTrue(check(path)[1])
        path.write_text(spec.replace('- [x]', '- [ ]'))
        self.assertIn('missing_completed_task_checkbox', checker.check_exec(path)[1])
        path.write_text(audit.replace('### Important\n- none', '### Important\n- 保留阻塞问题'))
        self.assertTrue(checker.check_audit(path, True)[1])

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

        # case-audit.sh 必须与 agentwork-check.py 得到同一结论。
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
