from __future__ import annotations

import hashlib
import json
import sys
import unittest

from test_pi_adapter import BOOTSTRAP, REPO_ROOT, load_renderer


# Independent of the renderer metadata and installer file list.
EXPECTED_DSH_COMMANDS = {'brain', 'spec', 'exec', 'audit', 'case', 'commit'}
EXPECTED_DSH_CAPABILITIES = {'anydoc', 'research'}
EXPECTED_DSH_SKILLS = EXPECTED_DSH_COMMANDS | EXPECTED_DSH_CAPABILITIES


def assert_dsh_skill(test: unittest.TestCase, text: str, name: str) -> None:
    lines = text.splitlines()
    test.assertEqual(lines[0], '---')
    end = lines.index('---', 1)
    fields = dict(line.split(': ', 1) for line in lines[1:end])
    test.assertEqual(len(fields), end - 1, 'duplicate frontmatter fields')
    test.assertEqual(set(fields), {'name', 'description'})
    test.assertEqual(fields['name'], name)
    test.assertTrue(json.loads(fields['description']).strip())
    target = (
        f'.shared/commands/{name}.md' if name in EXPECTED_DSH_COMMANDS
        else f'.shared/skills/{name}/SKILL.md'
    )
    test.assertEqual(text.count(target), 1)
    test.assertIn(f'`{target}`', text)
    test.assertTrue((REPO_ROOT / target).is_file())
    test.assertIn(f'`.dsh/skills/{name}/`', text)
    test.assertIn('向上三级', text)
    test.assertIn('`AGENTS.md`', text)
    test.assertIn('启动必读', text)
    test.assertIn('原始参数、子命令、引号和带空格路径', text)
    test.assertIn('不构成额外执行或提交许可', text)
    test.assertIn('标准模式', text)
    test.assertIn('原生计划模式关闭', text)
    for foreign_contract in ('request_user_input', '$ARGUMENTS', '@.shared/'):
        test.assertNotIn(foreign_contract, text)
    # Full workflow/capability bodies stay in .shared/.
    test.assertNotIn('## 当前核心子命令', text)
    test.assertNotIn('npm install', text)
    test.assertNotIn('## Goal', text)


class DshAdapterTest(unittest.TestCase):
    def test_source_self_host_skills_match_canonical_sources_and_receipt(self) -> None:
        receipt = json.loads((REPO_ROOT / '.agentwork/bootstrap-install-state.json').read_text())
        records = {entry['path']: entry['sha256'] for entry in receipt['files']}
        self.assertEqual(
            {path for path in records if path.startswith('.dsh/')},
            {f'.dsh/skills/{name}/SKILL.md' for name in EXPECTED_DSH_SKILLS},
        )
        for name in EXPECTED_DSH_SKILLS:
            with self.subTest(skill=name):
                relative = f'.dsh/skills/{name}/SKILL.md'
                content = (REPO_ROOT / relative).read_bytes()
                self.assertEqual(content, (BOOTSTRAP / f'dsh/skills/{name}/SKILL.md').read_bytes())
                self.assertEqual(records[relative], hashlib.sha256(content).hexdigest())

    def test_distributable_sources_have_exact_thin_skill_contract(self) -> None:
        root = BOOTSTRAP / 'dsh/skills'
        self.assertEqual(
            {path.relative_to(root).as_posix() for path in root.rglob('SKILL.md')},
            {f'{name}/SKILL.md' for name in EXPECTED_DSH_SKILLS},
        )
        for name in sorted(EXPECTED_DSH_SKILLS):
            with self.subTest(skill=name):
                assert_dsh_skill(self, (root / name / 'SKILL.md').read_text(encoding='utf-8'), name)

    def test_rendered_sources_reuse_metadata_and_leave_research_handwritten(self) -> None:
        module_name = f'agentwork_dsh_renderer_{id(self)}'
        renderer = load_renderer(BOOTSTRAP / 'render_bootstrap.py', module_name)
        self.addCleanup(sys.modules.pop, module_name, None)
        self.assertEqual(renderer.SPEC['dsh'], {
            'mechanism_baseline': '0.2.1-rc.2',
            'tag_commit': '687f282e8625c6b8d11ff58211a90524be2e4317',
        })
        root = BOOTSTRAP / 'dsh/skills'
        outputs = {
            item.path.relative_to(root).as_posix(): item.content
            for item in renderer.prepare_rendered_bootstrap()
            if item.path.is_relative_to(root)
        }
        self.assertEqual(
            set(outputs), {f'{name}/SKILL.md' for name in EXPECTED_DSH_SKILLS - {'research'}},
        )
        for wrapper in renderer.validated_wrapper_specs():
            text = outputs[f"{wrapper['name']}/SKILL.md"].decode('utf-8')
            self.assertIn(f"# {wrapper['title']}\n", text)
            self.assertIn(f"description: {json.dumps(wrapper['description'], ensure_ascii=False)}\n", text)
        for relative, content in outputs.items():
            self.assertEqual((root / relative).read_bytes(), content)
            self.assertIn(renderer.AUTO, content.decode('utf-8'))
        self.assertNotIn(renderer.AUTO, (root / 'research/SKILL.md').read_text(encoding='utf-8'))
        # Existing anydoc mirrors keep the complete canonical body.
        for capability in renderer.validated_default_capabilities():
            for mirror in capability['mirror_to']:
                self.assertEqual(
                    (BOOTSTRAP / mirror).read_bytes(),
                    (REPO_ROOT / capability['canonical']).read_bytes(),
                )


if __name__ == '__main__':
    unittest.main()
