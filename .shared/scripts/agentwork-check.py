#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import re
import sys
from pathlib import Path


TEXT_GLOBS = {
    'brain': '.tmp/agentwork/brain/*.md',
    'plan': '.tmp/agentwork/plan/*.md',
    'review': '.tmp/agentwork/review/*.md',
    'session': '.shared/session/*.md',
}

TEMPLATE_PLACEHOLDERS = [
    '{name}',
    '{YYYY-MM-DD HH:MM}',
    '{desc}',
    '{brain-topic-summary}',
    '{session-desc}',
    '{plan-source}',
    '{review-source}',
    '{exec-source}',
    '{session-or-plan-ref}',
    '{brain-note-or-other-source}',
    '{已经明确的目标/事实/约束/成功标准/非目标}',
    '{当前最需要确认的问题；若没有可写“无”}',
    '{在未阻塞且可继续时采用的假设}',
    '{若任务跨多个子系统/目标/交付物，列出 2-4 个问题域；否则写“无”}',
    '{优先收敛的问题域}',
    '{什么情况算这一轮收敛完成}',
    '{一句话}',
    '{最终推荐项}',
    '{为什么不选其余方案}',
    '{最终确认方案}',
    '{为什么这样选}',
    '{必要的定义或流程}',
    '{如仍存在}',
    '{交给 plan 的已确认设计、非目标、验收标准和仍待确认事项}',
    '{如果需要 session 快照，确认后使用哪个 brain/plan 工件作为来源}',
    '{一句话目标}',
    '{范围}',
    '{非目标}',
    '{关键文件或模块}',
    '{不能碰的边界}',
    '{bite-sized task 1}',
    '{bite-sized task 2}',
    '{最小验证方式}',
    '{达到什么状态才算完成这一轮}',
    '{当前阻塞或风险}',
    '{执行时可补充简短状态}',
    '{如果不写入 session，说明执行入口}',
    '{如果需要 session，说明要写入的 plan-source}',
    '{严重问题；如无可写 none}',
    '{重要问题；如无可写 none}',
    '{次要问题；如无可写 none}',
    '{采纳了什么，为什么}',
    '{拒绝了什么，为什么}',
    '{当前验证状态}',
    '{建议回到 /brain /plan /exec /session 中哪一步}',
    '{当前任务目标}',
    '{本轮纳入范围}',
    '{本轮不做什么}',
    '{约束 1}',
    '{当前已确认方案}',
    '{尚未确认的推荐方案；确认前不要写成已选方案}',
    '{需要用户确认后才能进入 /plan 或 /session exec 的关键问题}',
    '{需要用户确认后才能进入 /session plan 或 /session exec 的关键问题}',
    '{仅保留继续推进所必需的定义或流程}',
    '{下一步要做的事}',
    '{会修改哪些文件、哪些边界不能碰}',
    '{当前批次应先做什么}',
    '{standard | ralph}',
    '{本轮最小验证方式}',
    '{何时可认为这一轮真正完成}',
    '{为什么属于当前批次}',
    '{小批次或关键文件可精确列出}',
    '{必要时可用 glob；精确路径由 review 脚本/git 取证}',
    '{阶段摘要}',
    '{提交区间或主题范围}',
    '{当前风险或阻塞}',
    '{本次里程碑完成项}',
    '{检查结果（写结论，不写命令流水）}',
    '{剩余风险或下一步}',
    '{如果出现长期稳定事实，列在这里等待确认}',
]

SESSION_BASE_REQUIRED = [
    '# Session:',
    '## 任务列表（按优先级）',
    '## 已确认结论（工作快照）',
    '### 目标',
    '### 边界',
    '### 约束',
    '### 已选方案',
    '## 风险 / 阻塞',
    '## 审查记录',
]

SESSION_STRICT_REQUIRED = [
    '## 计划摘要（可选）',
    '### 关键文件 / 边界',
    '### 执行批次 / 优先级',
    '### 验证策略',
    '### 完成标准（可选）',
    '## 当前批次工作集（可选）',
    '## 产出批次（提交锚点）',
]

BANNED_SESSION_HEADINGS = [
    '## Goal',
    '## Scope',
    '## Findings',
    '## Review Basis',
    '## Verification Status',
    '## Next Recommendation',
    '## Blockers / Risks',
    '## Execution Log',
]


SELF_TEST_FIXTURES = {
    '.tmp/agentwork/brain/20260101-0000-fixture.md': """# Brain Note: fixture

> 创建: 2026-01-01 00:00
> 简述: fixture

## 目标
- 验证命令 harness 可检查 brain 工件。

## 澄清结果
### 已确认
- 目标、边界、成功标准和非目标已明确。

### 关键缺口
- 无。

## 边界
- In Scope: harness fixture
- Out of Scope: provider E2E

## 约束
- 使用本地确定性检查。

## 成功标准
- agentwork-check 能识别方案、成功标准和下一步。

## 方案对比
- 方案 A：做法 本地 fixture | 适用边界 命令自检 | 成本/复杂度 低 | 风险 低 | 验证 运行脚本。
- 方案 B：做法 provider smoke | 适用边界 人工诊断 | 成本/复杂度 高 | 风险 不稳定 | 验证 人工查看。
- 推荐：方案 A。

## 最终决策
- 已选方案：方案 A。
- 决策依据：本地可重复。

## 下一步建议
- `/plan`：继续验证 plan 自检。
""",
    '.tmp/agentwork/plan/20260101-0000-fixture.md': """# Plan: fixture

> 创建: 2026-01-01 00:00
> 来源: .tmp/agentwork/brain/20260101-0000-fixture.md

## Goal
- 验证 plan 自检。

## Scope
- In Scope: `.shared/scripts/agentwork-check.py`
- Out of Scope: provider E2E

## 关键文件 / 边界
- `.shared/scripts/agentwork-check.py`

## 任务列表（按优先级）
- [ ] 覆盖 plan 工件检查。

## 验证策略
- 运行 `.shared/scripts/agentwork-check.py plan`。

## 完成标准（可选）
- plan 检查通过。

## Blockers / Risks
- 无。
""",
    '.tmp/agentwork/plan/20260101-0001-exec-fixture.md': """# Plan: exec-fixture

> 创建: 2026-01-01 00:01
> 来源: .tmp/agentwork/brain/20260101-0000-fixture.md

## Goal
- 验证 exec 后 plan 自检。

## Scope
- In Scope: `.shared/scripts/agentwork-check.py`
- Out of Scope: provider E2E

## 关键文件 / 边界
- `.shared/scripts/agentwork-check.py`

## 任务列表（按优先级）
- [x] 覆盖 exec 工件检查。

## 验证策略
- 运行 `.shared/scripts/agentwork-check.py exec`。

## 完成标准（可选）
- exec 检查通过。

## Blockers / Risks
- 无。

## 执行记录（可选）
- 已验证 exec 自检能识别完成任务。
""",
    '.tmp/agentwork/review/20260101-0000-fixture.md': """# Review: fixture

> 创建: 2026-01-01 00:00
> 审查对象: .tmp/agentwork/plan/20260101-0001-exec-fixture.md

## Review Basis
- 目标 / 范围
- 当前计划 / 任务列表
- 当前工作区事实

## Findings

### Critical
- none

### Important
- none

### Minor
- none

## Accepted / Rejected Feedback
- 接受：无。
- 拒绝：无。

## Verification Status
- 已运行本地检查，未发现阻塞问题。

## Next Recommendation
- 结束当前 fixture 检查。
""",
    '.tmp/agentwork/review/20260101-0001-important-fixture.md': """# Review: important-fixture

> 创建: 2026-01-01 00:01
> 审查对象: .tmp/agentwork/plan/20260101-0001-exec-fixture.md

## Findings

### Critical
- none

### Important
- 缺少关键验证证据。
""",
    '.shared/session/20260101-0000-fixture.md': """# Session: fixture

> 创建: 2026-01-01 00:00
> 简述: command harness fixture

## 任务列表（按优先级）
- [x] 验证 session 自检。

## 已确认结论（工作快照）
### 目标
- 验证 session 工件形态。
### 边界
- In Scope: `.shared/scripts/agentwork-check.py`
- Out of Scope: provider E2E
### 约束
- 本地确定性执行。
### 已选方案
- 使用命令内建 harness。

## 计划摘要（可选）
### 关键文件 / 边界
- `.shared/scripts/agentwork-check.py`
### 执行批次 / 优先级
- 验证 strict-flow session。
### 验证策略
- 运行 `.shared/scripts/agentwork-check.py session --strict-flow`。
### 完成标准（可选）
- session strict-flow 检查通过。

## 当前批次工作集（可选）
- 范围: `.shared/scripts/agentwork-check.py` | 主题: 命令自检入口

## 产出批次（提交锚点）
- 提交: `-` | 范围: `.shared/scripts/agentwork-check.py`

## 风险 / 阻塞
- 无。

## 审查记录
### 2026-01-01 00:00
- 变更：创建 fixture session。
- 验证：本地 harness 检查通过。
- 风险/待办：无。
""",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def latest_path(kind: str) -> Path | None:
    pattern = TEXT_GLOBS[kind]
    paths = [path for path in Path.cwd().glob(pattern) if path.is_file()]
    if kind == 'session':
        paths = [path for path in paths if path.name != 'README.md']
    if not paths:
        return None
    return max(paths, key=lambda path: (path.stat().st_mtime_ns, str(path)))


def resolve_path(kind: str, value: str | None) -> Path | None:
    if value:
        path = Path(value)
        if kind == 'session' and not path.exists() and path.suffix != '.md' and '/' not in value:
            return Path('.shared/session') / f'{value}.md'
        return path
    return latest_path(kind)


def add_once(failures: list[str], failure: str) -> None:
    if failure not in failures:
        failures.append(failure)


def heading_present(text: str, heading: str) -> bool:
    base = re.split(r'[（(]', heading, maxsplit=1)[0].rstrip()
    return bool(re.search(rf'^{re.escape(base)}(?:$|[（(\s])', text, flags=re.MULTILINE))


def section_lines(text: str, heading_prefix: str) -> list[str]:
    lines = text.splitlines()
    in_section = False
    section: list[str] = []
    for line in lines:
        if line.startswith('## '):
            if in_section:
                break
            if line.startswith(heading_prefix):
                in_section = True
                continue
        elif in_section:
            section.append(line)
    return section


def check_exists(path: Path | None, kind: str, failures: list[str]) -> Path | None:
    if path is None:
        add_once(failures, f'missing_latest:{kind}:{TEXT_GLOBS[kind]}')
        return None
    if not path.exists():
        add_once(failures, f'missing:{path}')
        return None
    return path


def check_no_placeholders(text: str, failures: list[str]) -> None:
    for placeholder in TEMPLATE_PLACEHOLDERS:
        if placeholder in text:
            add_once(failures, f'template_placeholder_leak:{placeholder}')


def check_required_headings(text: str, headings: list[str], failures: list[str]) -> None:
    for heading in headings:
        if not heading_present(text, heading):
            add_once(failures, f'missing_heading:{heading}')


def check_any_group(text: str, groups: list[list[str]], failures: list[str], label: str) -> None:
    lowered = text.lower()
    for group in groups:
        if not any(item.lower() in lowered for item in group):
            add_once(failures, f'missing_text_group:{label}:{"/".join(group)}')


def check_brain(path: Path | None) -> tuple[Path | None, list[str]]:
    failures: list[str] = []
    path = check_exists(path, 'brain', failures)
    if path is None:
        return None, failures
    text = read_text(path)
    check_no_placeholders(text, failures)
    check_required_headings(
        text,
        [
            '# Brain Note:',
            '## 目标',
            '## 澄清结果',
            '## 边界',
            '## 成功标准',
            '## 方案对比',
            '## 最终决策',
            '## 下一步建议',
        ],
        failures,
    )
    check_any_group(
        text,
        [
            ['方案', '选项', 'recommendation', 'options'],
            ['验收', '完成标准', '成功标准', '最小验收', 'acceptance', 'success criteria'],
        ],
        failures,
        'brain',
    )
    return path, failures


def check_plan(path: Path | None) -> tuple[Path | None, list[str]]:
    failures: list[str] = []
    path = check_exists(path, 'plan', failures)
    if path is None:
        return None, failures
    text = read_text(path)
    check_no_placeholders(text, failures)
    check_required_headings(
        text,
        [
            '# Plan:',
            '> 来源:',
            '## Goal',
            '## Scope',
            '## 关键文件 / 边界',
            '## 任务列表（按优先级）',
            '## 验证策略',
        ],
        failures,
    )
    if re.search(r'^# Session:', text, flags=re.MULTILINE):
        add_once(failures, 'session_heading_leak:# Session:')
    if re.search(r'^## 已确认结论（工作快照）', text, flags=re.MULTILINE):
        add_once(failures, 'session_heading_leak:## 已确认结论（工作快照）')
    if not re.search(r'^- \[[ x]\] .+', text, flags=re.MULTILINE):
        add_once(failures, 'missing_task_checkbox')
    check_any_group(
        text,
        [
            ['任务', 'steps', 'tasks'],
            ['验证', '验收', 'verification', 'acceptance'],
        ],
        failures,
        'plan',
    )
    return path, failures


def check_exec(path: Path | None) -> tuple[Path | None, list[str]]:
    path, failures = check_plan(path)
    if path is None:
        return None, failures
    text = read_text(path)
    if not re.search(r'^- \[x\] .+', text, flags=re.MULTILINE):
        add_once(failures, 'missing_completed_task_checkbox')
    if '## 执行记录' in text:
        check_any_group(text, [['验证', 'verification', 'checked', '确认']], failures, 'exec_record')
    return path, failures


def parse_review_major_findings(text: str) -> list[str]:
    failures: list[str] = []
    lines = text.splitlines()
    sections: dict[str, list[str]] = {'critical': [], 'important': []}
    current: str | None = None
    for raw in lines:
        line = raw.strip()
        lower = line.lower()
        if lower == '### critical':
            current = 'critical'
            continue
        if lower == '### important':
            current = 'important'
            continue
        if line.startswith('### '):
            current = None
            continue
        if current is None or not line:
            continue
        normalized = line.lstrip('-* ').strip().rstrip('.。').lower()
        if normalized not in {'none', '无'}:
            sections[current].append(line)

    for level, items in sections.items():
        if items:
            add_once(failures, f'review_has_{level}_findings:{len(items)}')
    if any(sections.values()):
        return failures

    bullet_findings: dict[str, list[str]] = {'critical': [], 'important': []}
    for raw in lines:
        line = raw.strip()
        lower = line.lower()
        if lower.startswith(('- `critical`', '* `critical`', '- critical', '* critical')):
            bullet_findings['critical'].append(line)
        elif lower.startswith(('- `important`', '* `important`', '- important', '* important')):
            bullet_findings['important'].append(line)
        numbered = re.match(
            r'^\d+\.\s+(?:\*\*|`)?(critical|important)(?:\*\*|`)?\b',
            line,
            flags=re.IGNORECASE,
        )
        if numbered:
            bullet_findings[numbered.group(1).lower()].append(line)

    if not any(bullet_findings.values()):
        for level in ('critical', 'important'):
            match = re.search(rf'有\s*(\d+)\s*个\s*`?{level}`?', text, flags=re.IGNORECASE)
            if match and int(match.group(1)) > 0:
                bullet_findings[level].append(match.group(0))

    for level, items in bullet_findings.items():
        if items:
            add_once(failures, f'review_has_{level}_findings:{len(items)}')
    return failures


def check_review(path: Path | None, fail_on_major: bool) -> tuple[Path | None, list[str]]:
    failures: list[str] = []
    path = check_exists(path, 'review', failures)
    if path is None:
        return None, failures
    text = read_text(path)
    check_no_placeholders(text, failures)
    check_required_headings(text, ['# Review:'], failures)
    if not (heading_present(text, '## Findings') or heading_present(text, '## Findings Summary')):
        add_once(failures, 'missing_heading:## Findings')
    check_any_group(
        text,
        [['发现', '问题', '风险', 'findings', 'issues', 'no issues', '未发现', '无问题']],
        failures,
        'review',
    )
    if fail_on_major:
        failures.extend(parse_review_major_findings(text))
    return path, failures


def check_session(path: Path | None, strict_flow: bool) -> tuple[Path | None, list[str]]:
    failures: list[str] = []
    path = check_exists(path, 'session', failures)
    if path is None:
        return None, failures
    text = read_text(path)
    check_no_placeholders(text, failures)
    check_required_headings(text, SESSION_BASE_REQUIRED + (SESSION_STRICT_REQUIRED if strict_flow else []), failures)
    for heading in BANNED_SESSION_HEADINGS:
        if re.search(rf'^{re.escape(heading)}(?:\s|[（(/]|$)', text, flags=re.MULTILINE):
            add_once(failures, f'temporary_heading_leak:{heading}')
    if not re.search(r'^- \[[ x]\] .+', text, flags=re.MULTILINE):
        add_once(failures, 'missing_task_checkbox')

    workset_lines = [line for line in section_lines(text, '## 当前批次工作集') if line.startswith('- ')]
    if strict_flow and not workset_lines:
        add_once(failures, 'missing_workset_entries')
    for line in workset_lines:
        if not re.match(r'^- 范围: `[^`]+`(?:, `[^`]+`)* \| 主题: .+', line):
            add_once(failures, f'bad_workset_entry:{line}')

    deliverable_lines = [line for line in section_lines(text, '## 产出批次') if line.startswith('- ')]
    if strict_flow and not deliverable_lines:
        add_once(failures, 'missing_deliverable_entries')
    for line in deliverable_lines:
        if not re.match(r'^- 提交: `[^`]+` \| 范围: .+', line) and not re.match(r'^- 历史: `[^`]+` \| 范围: .+', line):
            add_once(failures, f'bad_deliverable_entry:{line}')
    return path, failures


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def self_test_root(explicit_root: str | None) -> Path:
    if explicit_root:
        return Path(explicit_root)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    return Path('.tmp/agentwork-check-self-test') / stamp


def run_self_test(root: Path) -> list[str]:
    for rel, content in SELF_TEST_FIXTURES.items():
        write_text(root / rel, content)

    checks = [
        ('brain', check_brain(root / '.tmp/agentwork/brain/20260101-0000-fixture.md'), False),
        ('plan', check_plan(root / '.tmp/agentwork/plan/20260101-0000-fixture.md'), False),
        ('exec', check_exec(root / '.tmp/agentwork/plan/20260101-0001-exec-fixture.md'), False),
        ('review', check_review(root / '.tmp/agentwork/review/20260101-0000-fixture.md', True), False),
        ('session', check_session(root / '.shared/session/20260101-0000-fixture.md', True), False),
        ('review-important', check_review(root / '.tmp/agentwork/review/20260101-0001-important-fixture.md', True), True),
    ]

    failures: list[str] = []
    for name, (_path, check_failures), expect_failure in checks:
        if expect_failure:
            if not any(failure.startswith('review_has_important_findings') for failure in check_failures):
                failures.append(f'self_test_negative_missed:{name}:{check_failures}')
        elif check_failures:
            failures.append(f'self_test_failed:{name}:{check_failures}')
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description='Check agentwork command artifacts.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    latest = subparsers.add_parser('latest', help='print the latest artifact path for a kind')
    latest.add_argument('kind', choices=sorted(TEXT_GLOBS))

    brain = subparsers.add_parser('brain', help='check a brain note')
    brain.add_argument('path', nargs='?')

    plan = subparsers.add_parser('plan', help='check a plan')
    plan.add_argument('path', nargs='?')

    exec_parser = subparsers.add_parser('exec', help='check a plan after /exec updated it')
    exec_parser.add_argument('path', nargs='?')

    review = subparsers.add_parser('review', help='check a review note')
    review.add_argument('path', nargs='?')
    review.add_argument('--fail-on-major', action='store_true', help='fail when Critical or Important findings are present')

    session = subparsers.add_parser('session', help='check a session snapshot')
    session.add_argument('path', nargs='?')
    session.add_argument('--strict-flow', action='store_true', help='require plan/workset/deliverable sections')

    self_test = subparsers.add_parser('self-test', help='run deterministic built-in fixture checks')
    self_test.add_argument('--root', help='write fixture files under this root; default uses .tmp/agentwork-check-self-test/<timestamp>')

    args = parser.parse_args()

    if args.command == 'latest':
        path = latest_path(args.kind)
        if path is None:
            print(f'missing_latest:{args.kind}:{TEXT_GLOBS[args.kind]}')
            return 1
        print(path)
        return 0

    if args.command == 'self-test':
        root = self_test_root(args.root)
        failures = run_self_test(root)
        if failures:
            for failure in failures:
                print(failure)
            return 1
        print(f'agentwork_check:PASS:self-test:{root}')
        return 0

    if args.command == 'brain':
        path, failures = check_brain(resolve_path('brain', args.path))
    elif args.command == 'plan':
        path, failures = check_plan(resolve_path('plan', args.path))
    elif args.command == 'exec':
        path, failures = check_exec(resolve_path('plan', args.path))
    elif args.command == 'review':
        path, failures = check_review(resolve_path('review', args.path), args.fail_on_major)
    elif args.command == 'session':
        path, failures = check_session(resolve_path('session', args.path), args.strict_flow)
    else:
        raise AssertionError(args.command)

    if failures:
        for failure in failures:
            print(failure)
        return 1

    print(f'agentwork_check:PASS:{args.command}:{path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
