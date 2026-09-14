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
    'case': '.shared/case/*.md',
}

TEMPLATE_PLACEHOLDERS = [
    '{name}',
    '{YYYY-MM-DD HH:MM}',
    '{desc}',
    '{brain-topic-summary}',
    '{case-desc}',
    '{plan-source}',
    '{review-source}',
    '{exec-source}',
    '{case-or-plan-ref}',
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
    '{如果需要 Case 快照，确认后使用哪个 brain/plan 工件作为来源}',
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
    '{如果不写入 Case，说明执行入口}',
    '{如果需要 Case，说明要写入的 plan-source}',
    '{严重问题；如无可写 none}',
    '{重要问题；如无可写 none}',
    '{次要问题；如无可写 none}',
    '{采纳了什么，为什么}',
    '{拒绝了什么，为什么}',
    '{当前验证状态}',
    '{建议回到 /brain /plan /exec /case 中哪一步}',
    '{当前任务目标}',
    '{本轮纳入范围}',
    '{本轮不做什么}',
    '{约束 1}',
    '{当前已确认方案}',
    '{只记录会影响后续恢复的已否决方案、兼容取舍或迁移前提；重复讨论留在 brain/review 工件}',
    '{尚未确认的推荐方案；确认前不要写成已选方案}',
    '{需要用户确认后才能进入 /plan 或 /case exec 的关键问题}',
    '{需要用户确认后才能进入 /case plan 或 /case exec 的关键问题}',
    '{仅保留继续推进所必需的定义或流程}',
    '{下一步要做的事}',
    '{会修改哪些文件、哪些边界不能碰}',
    '{当前批次应先做什么}',
    '{standard}',
    '{本轮最小验证方式}',
    '{何时可认为这一轮真正完成}',
    '{为什么属于当前批次}',
    '{小批次或关键文件可精确列出}',
    '{必要时可用 glob；精确路径由 review 脚本/git 取证}',
    '{阶段摘要}',
    '{提交区间或主题范围}',
    '{结果结论}',
    '{当前风险或阻塞}',
    '{本次里程碑完成项}',
    '{检查结果（写结论，不写命令流水）}',
    '{剩余风险或下一步}',
    '{历史审查时间范围}',
    '{审查日期或主题}',
    '{历史审查一句话摘要；含验证状态、未闭环风险或来源锚点}',
    '{如果出现长期稳定事实，列在这里等待确认}',
]

CASE_BASE_REQUIRED = [
    '# Case:',
    '## 任务列表（按优先级）',
    '## 已确认结论（工作快照）',
    '### 目标',
    '### 边界',
    '### 约束',
    '### 已选方案',
    '## 风险 / 阻塞',
    '## 审查记录',
]

CASE_STRICT_REQUIRED = [
    '## 计划摘要（可选）',
    '### 关键文件 / 边界',
    '### 执行批次 / 优先级',
    '### 验证策略',
    '### 完成标准（可选）',
    '## 当前批次工作集（可选）',
    '## 产出批次（提交锚点）',
]

BANNED_CASE_HEADINGS = [
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
    '.shared/case/20260101-0000-fixture.md': """# Case: fixture

> 创建: 2026-01-01 00:00
> 简述: command harness fixture

## 任务列表（按优先级）
- [x] 验证 Case 自检。

## 已确认结论（工作快照）
### 目标
- 验证 Case 工件形态。
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
- 验证 strict-flow Case。
### 验证策略
- 运行 `.shared/scripts/agentwork-check.py case --strict-flow`。
### 完成标准（可选）
- Case strict-flow 检查通过。

## 当前批次工作集（可选）
- 范围: `.shared/scripts/agentwork-check.py` | 主题: 命令自检入口

## 产出批次（提交锚点）
- 提交: `-` | 范围: `.shared/scripts/agentwork-check.py` | 验证: Case strict-flow 检查通过。

## 风险 / 阻塞
- 无。

## 审查记录
### 2026-01-01 00:00
- 变更：创建 fixture Case。
- 验证：本地 harness 检查通过。
- 风险/待办：无。
""",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8')


ARTIFACT_NAME_RE = re.compile(r'^(\d{8}-\d{4})-.+\.md$')


class AmbiguousLatest(Exception):
    """同一时间戳下存在多个候选，需由调用方显式指定。"""

    def __init__(self, kind: str, paths: list[Path]) -> None:
        self.kind = kind
        self.paths = paths
        super().__init__(kind)


def latest_path(kind: str) -> Path | None:
    """按 `YYYYMMDD-HHMM-slug.md` 命名选取最新工件；不依赖 mtime。"""
    pattern = TEXT_GLOBS[kind]
    stamped: dict[str, list[Path]] = {}
    # 相对 glob：输出保持仓库相对路径，与 case-review.sh 的历史输出一致。
    for path in Path().glob(pattern):
        if not path.is_file():
            continue
        match = ARTIFACT_NAME_RE.match(path.name)
        if match is None:
            continue
        stamped.setdefault(match.group(1), []).append(path)
    if not stamped:
        return None
    newest = max(stamped)
    candidates = sorted(stamped[newest], key=lambda path: str(path))
    if len(candidates) > 1:
        raise AmbiguousLatest(kind, candidates)
    return candidates[0]


def resolve_path(kind: str, value: str | None) -> Path | None:
    if value:
        path = Path(value)
        if kind == 'case' and not path.exists() and path.suffix != '.md' and '/' not in value:
            return Path('.shared/case') / f'{value}.md'
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
    if re.search(r'^# Case:', text, flags=re.MULTILINE):
        add_once(failures, 'case_heading_leak:# Case:')
    if re.search(r'^## 已确认结论（工作快照）', text, flags=re.MULTILINE):
        add_once(failures, 'case_heading_leak:## 已确认结论（工作快照）')
    if not re.search(r'^- \[[ x]\] .+', text, flags=re.MULTILINE):
        add_once(failures, 'missing_task_checkbox')
    return path, failures


def check_exec(path: Path | None) -> tuple[Path | None, list[str]]:
    path, failures = check_plan(path)
    if path is None:
        return None, failures
    text = read_text(path)
    if not re.search(r'^- \[x\] .+', text, flags=re.MULTILINE):
        add_once(failures, 'missing_completed_task_checkbox')
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
    if fail_on_major:
        failures.extend(parse_review_major_findings(text))
    return path, failures


def deliverable_commit_anchors(line: str) -> list[str]:
    anchor_text = ''
    if line.startswith('- 提交:'):
        anchor_text = line.split(' | 范围:', maxsplit=1)[0]
    elif line.startswith('- 历史:') and ' | 提交:' in line:
        anchor_text = line.split(' | 提交:', maxsplit=1)[1].split(' | 范围:', maxsplit=1)[0]
    return [match.group(0).lower() for match in re.finditer(r'\b[0-9a-fA-F]{7,40}\b', anchor_text)]


def report_duplicate_commit_anchors(deliverable_lines: list[str]) -> None:
    counts: dict[str, int] = {}
    for line in deliverable_lines:
        for anchor in deliverable_commit_anchors(line):
            counts[anchor] = counts.get(anchor, 0) + 1
    for anchor, count in counts.items():
        if count > 1:
            print(f'warning:duplicate_commit_anchor:{anchor}:{count}:review 独立验证或边界后决定是否合并', file=sys.stderr)


def latest_review_date(title: str) -> tuple[int, int, int, int | None, int | None] | None:
    dates: list[tuple[int, int, int, int | None, int | None]] = []
    pattern = r'(?<!\d)(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2}))?'
    for match in re.finditer(pattern, title):
        year, month, day = (int(match.group(index)) for index in range(1, 4))
        hour = int(match.group(4)) if match.group(4) is not None else None
        minute = int(match.group(5)) if match.group(5) is not None else None
        try:
            datetime(year, month, day, hour or 0, minute or 0)
        except ValueError:
            continue
        dates.append((year, month, day, hour, minute))
    if not dates:
        return None
    return max(dates, key=lambda value: (*value[:3], value[3] or 0, value[4] or 0))


def parse_review_events(review_lines: list[str]) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    current: dict[str, object] | None = None

    def finish_current() -> None:
        nonlocal current
        if current is not None:
            events.append(current)
            current = None

    for raw in review_lines:
        line = raw.strip()
        if line.startswith('### '):
            finish_current()
            title = line[4:].strip()
            date = latest_review_date(title)
            if date is not None:
                current = {
                    'title': title,
                    'date': date,
                    'history': '历史' in title and '摘要' in title,
                    'body': [],
                }
            continue
        if current is not None:
            body = current['body']
            assert isinstance(body, list)
            body.append(raw)
            continue
        if line.startswith('- ') and latest_review_date(line) is not None:
            events.append(
                {
                    'title': line,
                    'date': latest_review_date(line),
                    'history': '历史' in line and '摘要' in line,
                    'body': [line],
                }
            )
    finish_current()
    return events


def review_dates_out_of_order(
    previous: tuple[int, int, int, int | None, int | None],
    current: tuple[int, int, int, int | None, int | None],
) -> bool:
    if previous[:3] != current[:3]:
        return previous[:3] < current[:3]
    previous_time = previous[3:]
    current_time = current[3:]
    if None in previous_time or None in current_time:
        return False
    return previous_time < current_time


def review_detail_fields(body: str) -> set[str]:
    fields: set[str] = set()
    if re.search(r'(?:变更|结论|收敛|修正|结果)\s*[:：]', body):
        fields.add('change')
    if re.search(r'(?:验证|证据)\s*[:：]', body):
        fields.add('verification')
    if re.search(r'(?:风险\s*(?:[/／]\s*待办)?|待办|后续|阻塞)\s*[:：]', body):
        fields.add('risk')
    return fields


def check_review_history(review_lines: list[str], failures: list[str]) -> None:
    for raw in review_lines:
        line = raw.strip()
        heading_match = re.match(r'^###(?:\s+(.*))?$', line)
        if heading_match is None:
            continue
        title = (heading_match.group(1) or '').strip()
        if latest_review_date(title) is None:
            add_once(failures, f'missing_valid_review_date:{title or "<empty>"}')

    events = parse_review_events(review_lines)
    for previous, current in zip(events, events[1:]):
        previous_date = previous['date']
        current_date = current['date']
        assert isinstance(previous_date, tuple) and isinstance(current_date, tuple)
        if review_dates_out_of_order(previous_date, current_date):
            add_once(failures, f'review_events_out_of_order:{previous["title"]}->{current["title"]}')

    history_seen = False
    detailed_events: list[dict[str, object]] = []
    for event in events:
        if event['history']:
            history_seen = True
            body = event['body']
            assert isinstance(body, list)
            if not any(line.strip() for line in body):
                add_once(failures, f'empty_review_history:{event["title"]}')
        else:
            if history_seen:
                add_once(failures, f'review_detail_after_history:{event["title"]}')
            detailed_events.append(event)

    for event in detailed_events[:3]:
        body_lines = event['body']
        assert isinstance(body_lines, list)
        fields = review_detail_fields('\n'.join(body_lines))
        missing = sorted({'change', 'verification', 'risk'} - fields)
        if missing:
            add_once(failures, f'incomplete_recent_review:{event["title"]}:{",".join(missing)}')


def check_case(path: Path | None, strict_flow: bool) -> tuple[Path | None, list[str]]:
    failures: list[str] = []
    path = check_exists(path, 'case', failures)
    if path is None:
        return None, failures
    text = read_text(path)
    check_no_placeholders(text, failures)
    check_required_headings(text, CASE_BASE_REQUIRED + (CASE_STRICT_REQUIRED if strict_flow else []), failures)
    for heading in BANNED_CASE_HEADINGS:
        if re.search(rf'^{re.escape(heading)}(?:\s|[（(/]|$)', text, flags=re.MULTILINE):
            add_once(failures, f'temporary_heading_leak:{heading}')
    if not re.search(r'^- \[[ x]\] .+', text, flags=re.MULTILINE):
        add_once(failures, 'missing_task_checkbox')

    workset_lines = [line for line in section_lines(text, '## 当前批次工作集') if line.startswith('- ')]
    active_tasks = any(re.match(r'^- \[ \] .+', line) for line in section_lines(text, '## 任务列表'))
    explicitly_empty = '当前无工作集。' in section_lines(text, '## 当前批次工作集')
    if strict_flow and not workset_lines and active_tasks and not explicitly_empty:
        add_once(failures, 'missing_workset_entries')
    for line in workset_lines:
        if not re.match(r'^- 范围: `[^`]+`(?:, `[^`]+`)* \| 主题: .+', line):
            add_once(failures, f'bad_workset_entry:{line}')

    deliverable_lines = [line for line in section_lines(text, '## 产出批次') if line.startswith('- ')]
    if strict_flow and not deliverable_lines:
        add_once(failures, 'missing_deliverable_entries')
    for line in deliverable_lines:
        if line.startswith('- 提交:'):
            commit_match = re.match(r'^- 提交: `([^`]+)` \| 范围: .+ \| 验证: .+', line)
            if not commit_match:
                add_once(failures, f'incomplete_deliverable_entry:{line}')
            else:
                anchor_text = commit_match.group(1).strip()
                no_commit_marker = re.match(r'^(?:不适用|未提交|无)(?:[（(]|$)', anchor_text)
                if anchor_text != '-' and not no_commit_marker and not re.search(r'\b[0-9a-fA-F]{7,40}\b', anchor_text):
                    add_once(failures, f'missing_commit_anchor:{line}')
        elif line.startswith('- 历史:') and not re.match(r'^- 历史: `[^`]+`(?: \| 提交: .+)? \| 范围: .+', line):
            add_once(failures, f'bad_deliverable_entry:{line}')
        elif not line.startswith(('- 提交:', '- 历史:')):
            add_once(failures, f'bad_deliverable_entry:{line}')
    report_duplicate_commit_anchors(deliverable_lines)
    check_review_history(section_lines(text, '## 审查记录'), failures)
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

    case_path = root / '.shared/case/20260101-0000-fixture.md'
    case_text = read_text(case_path)
    deliverable = '- 提交: `-` | 范围: `.shared/scripts/agentwork-check.py` | 验证: Case strict-flow 检查通过。'
    duplicate_text = case_text.replace(
        deliverable,
        '- 提交: `abcdef1 feat: first` | 范围: `.shared/scripts/agentwork-check.py` | 验证: first。\n'
        '- 提交: `abcdef1 fix: second` | 范围: `.shared/scripts/agentwork-check.py` | 验证: second。',
    )

    def case_with_reviews(review_text: str) -> str:
        return case_text.split('## 审查记录', maxsplit=1)[0] + '## 审查记录\n' + review_text

    complete_review = (
        '- 变更：更新 Case。\n'
        '- 验证：本地检查通过。\n'
        '- 风险/待办：无。\n'
    )
    out_of_order_text = case_with_reviews(
        '### 2026-01-01 first\n'
        f'{complete_review}\n'
        '### 2026-01-02 second\n'
        f'{complete_review}'
    )
    incomplete_review_text = case_with_reviews(
        '### 2026-01-02 incomplete\n'
        '- 变更：更新 Case。\n'
        '- 验证：本地检查通过。\n'
    )
    undated_review_text = case_with_reviews(
        '### review without date\n'
        f'{complete_review}'
    )
    invalid_review_date_text = case_with_reviews(
        '### 2026-02-30 invalid date\n'
        f'{complete_review}'
    )
    history_before_detail_text = case_with_reviews(
        '### 历史审查摘要（2025-01-01—2025-12-31）\n'
        '- 2025：历史摘要。\n\n'
        '### 2025-01-01 detail\n'
        f'{complete_review}'
    )
    empty_history_text = case_with_reviews(
        '### 2026-01-01 detail\n'
        f'{complete_review}\n'
        '### 历史审查摘要（2025-01-01—2025-12-31）\n'
    )
    many_reviews_text = case_with_reviews(
        ''.join(f'### 2026-01-0{day} review {day}\n{complete_review}\n' for day in range(4, 0, -1))
    )
    same_day_text = case_with_reviews(
        '### 2026-01-01 review A\n'
        f'{complete_review}\n'
        '### 2026-01-01 review B\n'
        f'{complete_review}'
    )

    case_fixtures = {
        'duplicate-anchor': duplicate_text,
        'out-of-order': out_of_order_text,
        'incomplete-review': incomplete_review_text,
        'undated-review': undated_review_text,
        'invalid-review-date': invalid_review_date_text,
        'history-before-detail': history_before_detail_text,
        'empty-history': empty_history_text,
        'many-reviews': many_reviews_text,
        'same-day': same_day_text,
    }
    for name, content in case_fixtures.items():
        write_text(root / f'.shared/case/20260101-0000-{name}.md', content)

    checks = [
        ('brain', check_brain(root / '.tmp/agentwork/brain/20260101-0000-fixture.md'), None),
        ('plan', check_plan(root / '.tmp/agentwork/plan/20260101-0000-fixture.md'), None),
        ('exec', check_exec(root / '.tmp/agentwork/plan/20260101-0001-exec-fixture.md'), None),
        ('review', check_review(root / '.tmp/agentwork/review/20260101-0000-fixture.md', True), None),
        ('case', check_case(case_path, True), None),
        ('case-many-reviews', check_case(root / '.shared/case/20260101-0000-many-reviews.md', True), None),
        ('case-same-day', check_case(root / '.shared/case/20260101-0000-same-day.md', True), None),
        (
            'review-important',
            check_review(root / '.tmp/agentwork/review/20260101-0001-important-fixture.md', True),
            'review_has_important_findings',
        ),
        (
            'case-duplicate-anchor',
            check_case(root / '.shared/case/20260101-0000-duplicate-anchor.md', True),
            None,
        ),
        (
            'case-out-of-order',
            check_case(root / '.shared/case/20260101-0000-out-of-order.md', True),
            'review_events_out_of_order',
        ),
        (
            'case-incomplete-review',
            check_case(root / '.shared/case/20260101-0000-incomplete-review.md', True),
            'incomplete_recent_review',
        ),
        (
            'case-undated-review',
            check_case(root / '.shared/case/20260101-0000-undated-review.md', True),
            'missing_valid_review_date',
        ),
        (
            'case-invalid-review-date',
            check_case(root / '.shared/case/20260101-0000-invalid-review-date.md', True),
            'missing_valid_review_date',
        ),
        (
            'case-history-before-detail',
            check_case(root / '.shared/case/20260101-0000-history-before-detail.md', True),
            'review_detail_after_history',
        ),
        (
            'case-empty-history',
            check_case(root / '.shared/case/20260101-0000-empty-history.md', True),
            'empty_review_history',
        ),
    ]

    failures: list[str] = []
    for name, (_path, check_failures), expected_failure in checks:
        if expected_failure:
            if not any(failure.startswith(expected_failure) for failure in check_failures):
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

    case = subparsers.add_parser('case', help='check a Case snapshot')
    case.add_argument('path', nargs='?')
    case.add_argument('--strict-flow', action='store_true', help='require plan/workset/deliverable sections')

    self_test = subparsers.add_parser('self-test', help='run deterministic built-in fixture checks')
    self_test.add_argument('--root', help='write fixture files under this root; default uses .tmp/agentwork-check-self-test/<timestamp>')

    args = parser.parse_args()

    if args.command == 'self-test':
        root = self_test_root(args.root)
        failures = run_self_test(root)
        if failures:
            for failure in failures:
                print(failure)
            return 1
        print(f'agentwork_check:PASS:self-test:{root}')
        return 0

    try:
        if args.command == 'latest':
            path = latest_path(args.kind)
            if path is None:
                print(f'missing_latest:{args.kind}:{TEXT_GLOBS[args.kind]}')
                return 1
            print(path)
            return 0

        if args.command == 'brain':
            path, failures = check_brain(resolve_path('brain', args.path))
        elif args.command == 'plan':
            path, failures = check_plan(resolve_path('plan', args.path))
        elif args.command == 'exec':
            path, failures = check_exec(resolve_path('plan', args.path))
        elif args.command == 'review':
            path, failures = check_review(resolve_path('review', args.path), args.fail_on_major)
        elif args.command == 'case':
            path, failures = check_case(resolve_path('case', args.path), args.strict_flow)
        else:
            raise AssertionError(args.command)
    except AmbiguousLatest as exc:
        names = ', '.join(str(path) for path in exc.paths)
        print(f'ambiguous_latest:{exc.kind}:{names}', file=sys.stderr)
        return 1

    if failures:
        for failure in failures:
            print(failure)
        return 1

    print(f'agentwork_check:PASS:{args.command}:{path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
