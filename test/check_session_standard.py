#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BASE_REQUIRED_TEXT = [
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

STRICT_FLOW_REQUIRED_TEXT = [
    '## 计划摘要（可选）',
    '### 关键文件 / 边界',
    '### 执行批次 / 优先级',
    '### 验证策略',
    '### 完成标准（可选）',
    '## 当前批次工作集（可选）',
    '## 产出批次（提交锚点）',
]

BANNED_STANDALONE_HEADINGS = [
    '## Goal',
    '## Scope',
    '## Findings',
    '## Review Basis',
    '## Verification Status',
    '## Next Recommendation',
    '## Blockers / Risks',
    '## Execution Log',
]

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
    '{下一步要做的事}',
    '{当前任务目标}',
    '{本轮纳入范围}',
    '{本轮不做什么}',
    '{约束 1}',
    '{当前已确认方案}',
    '{仅保留继续推进所必需的定义或流程}',
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

WORKSET_HEADING = '## 当前批次工作集'
DELIVERABLE_HEADING = '## 产出批次'


def extract_section(text: str, heading_prefix: str) -> list[str]:
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


def check_session(path: Path, strict_flow: bool) -> list[str]:
    failures: list[str] = []
    if not path.exists():
        return [f'missing:{path}']

    text = path.read_text(encoding='utf-8')
    required = BASE_REQUIRED_TEXT + (STRICT_FLOW_REQUIRED_TEXT if strict_flow else [])
    for item in required:
        if item not in text:
            failures.append(f'missing_text:{item}')

    for heading in BANNED_STANDALONE_HEADINGS:
        if re.search(rf'^{re.escape(heading)}(?:\s|[（(/]|$)', text, flags=re.MULTILINE):
            failures.append(f'standalone_heading_leak:{heading}')

    for placeholder in TEMPLATE_PLACEHOLDERS:
        if placeholder in text:
            failures.append(f'template_placeholder_leak:{placeholder}')

    if not re.search(r'^- \[[ x]\] .+', text, flags=re.MULTILINE):
        failures.append('missing_task_checkbox')

    workset_lines = [line for line in extract_section(text, WORKSET_HEADING) if line.startswith('- ')]
    if strict_flow and not workset_lines:
        failures.append('missing_workset_entries')
    for line in workset_lines:
        if not re.match(r'^- 范围: `[^`]+`(?:, `[^`]+`)* \| 主题: .+', line):
            failures.append(f'bad_workset_entry:{line}')

    deliverable_lines = [line for line in extract_section(text, DELIVERABLE_HEADING) if line.startswith('- ')]
    if strict_flow and not deliverable_lines:
        failures.append('missing_deliverable_entries')
    for line in deliverable_lines:
        if not re.match(r'^- 提交: `[^`]+` \| 范围: .+', line) and not re.match(r'^- 历史: `[^`]+` \| 范围: .+', line):
            failures.append(f'bad_deliverable_entry:{line}')

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description='Check whether a session file still follows the standard session shape.')
    parser.add_argument('session_file')
    parser.add_argument('--strict-flow', action='store_true', help='require plan/workset/deliverable sections for full-flow tests, including sections marked optional in the template')
    args = parser.parse_args()

    failures = check_session(Path(args.session_file), args.strict_flow)
    if failures:
        print('\n'.join(failures))
        return 1

    print('session_standard:PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
