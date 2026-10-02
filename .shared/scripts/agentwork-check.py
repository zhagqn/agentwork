#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from graphlib import CycleError, TopologicalSorter
import re
import sys
from pathlib import Path


TEXT_GLOBS = {
    'brain': '.tmp/agentwork/brain/*.md',
    'spec': '.tmp/agentwork/spec/*.md',
    'audit': '.tmp/agentwork/audit/*.md',
    'case': '.shared/case/*.md',
}

TEMPLATE_PLACEHOLDERS = [
    '{name}',
    '{YYYY-MM-DD HH:MM}',
    '{brain-topic-summary}',
    '{case-desc}',
    '{spec-source}',
    '{audit-source}',
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
    '{交给 spec 的已确认设计、非目标、验收标准和仍待确认事项}',
    '{如果需要 Case 快照，确认后使用哪个 brain/spec 工件作为来源}',
    '{一句话目标}',
    '{范围}',
    '{非目标}',
    '{关键文件或模块}',
    '{不能碰的边界}',
    '{来源中已确认、会约束实现的结论}',
    '{已确认结论}',
    '{纵向切片任务}',
    '{可观察条件}',
    '{可观察完成条件}',
    '{本轮最小验证}',
    '{最小验证}',
    '{本轮在哪一层验证，以及使用的已有验证入口}',
    '{补充验证方式}',
    '{达到什么状态才算完成这一轮}',
    '{当前阻塞或风险}',
    '{执行时可补充简短状态}',
    '{如果不写入 Case，说明执行入口}',
    '{如果需要 Case，说明要写入的 spec-source}',
    '{通过 / 不通过；决策覆盖、完成条件、范围外改动的一句话结论}',
    '{通过 / 不通过；代码与文档质量的一句话结论}',
    '{[规格|质量] 严重问题 | 处置: 本轮修复 / 转后续 / 拒绝（理由）/ 待决策；如无可写 none}',
    '{[规格|质量] 重要问题 | 处置: ...；如无可写 none}',
    '{[规格|质量] 次要问题 | 处置: ...；如无可写 none}',
    '{当前验证状态}',
    '{建议回到 /brain /spec /exec /case 中哪一步}',
    '{当前任务目标}',
    '{本轮纳入范围}',
    '{本轮不做什么}',
    '{约束 1}',
    '{当前已确认方案}',
    '{只记录会影响后续恢复的已否决方案、兼容取舍或迁移前提；重复讨论留在 brain/audit 工件}',
    '{尚未确认的推荐方案；确认前不要写成已选方案}',
    '{需要用户确认后才能进入 /case spec 或 /case exec 的关键问题}',
    '{仅保留继续推进所必需的定义或流程}',
    '{下一步要做的事}',
    '{会修改哪些文件、哪些边界不能碰}',
    '{当前批次应先做什么}',
    '{standard}',
    '{本轮最小验证方式}',
    '{何时可认为这一轮真正完成}',
    '{为什么属于当前批次}',
    '{小批次或关键文件可精确列出}',
    '{必要时可用 glob；精确路径由 audit 脚本/git 取证}',
    '{阶段摘要}',
    '{提交区间或主题范围}',
    '{结果结论}',
    '{当前风险或阻塞}',
    '{本次里程碑完成项}',
    '{检查结果（写结论，不写命令流水）}',
    '{剩余风险或下一步}',
    '{规格符合 通过 / 不通过；质量规范 通过 / 不通过}',
    '{[规格|质量] 严重度 问题 | 处置: 本轮修复 / 转后续 / 拒绝（理由）/ 待决策；如无可写 无}',
    '{历史审查时间范围}',
    '{审查日期或主题}',
    '{历史审查一句话摘要；含验证状态、未闭环风险或来源锚点}',
    '{如果出现长期稳定事实，列在这里等待确认}',
    '{paths/范围}',
    '{3-7 条稳定结论/约束}',
    '{常用命令与最低验证要求}',
    '{命名、边界、生成物策略}',
    '{不应轻易改变的约束}',
    '{关键文件或目录}',
    '{YYYY-MM-DD}',
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
    '## Audit Basis',
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
- `/spec`：继续验证 spec 自检。
""",
    '.tmp/agentwork/spec/20260101-0000-fixture.md': """# Spec: fixture

> 创建: 2026-01-01 00:00
> 来源: .tmp/agentwork/brain/20260101-0000-fixture.md

## Goal
- 验证 spec 自检。

## 决策
- D1 spec 工件由 agentwork-check 校验。

## Scope
- In Scope: `.shared/scripts/agentwork-check.py`
- Out of Scope: provider E2E

## 关键文件 / 边界
- `.shared/scripts/agentwork-check.py`

## 任务列表（按优先级）
- [ ] T1 覆盖 spec 工件检查 | 覆盖: D1 | 依赖: 无 | 完成: spec 检查通过 | 验证: 运行 agentwork-check spec

## 验证策略
- 验证接缝：`.shared/scripts/agentwork-check.py spec`。

## 完成标准（可选）
- spec 检查通过。

## Blockers / Risks
- 无。
""",
    '.tmp/agentwork/spec/20260101-0001-exec-fixture.md': """# Spec: exec-fixture

> 创建: 2026-01-01 00:01
> 来源: .tmp/agentwork/brain/20260101-0000-fixture.md

## Goal
- 验证 exec 后 spec 自检。

## 决策
- D1 exec 后任务状态由 agentwork-check 校验。

## Scope
- In Scope: `.shared/scripts/agentwork-check.py`
- Out of Scope: provider E2E

## 关键文件 / 边界
- `.shared/scripts/agentwork-check.py`

## 任务列表（按优先级）
- [x] T1 覆盖 exec 工件检查 | 覆盖: D1 | 验证: 运行 agentwork-check exec
- [ ] T2 覆盖依赖顺序检查 | 覆盖: D1 | 依赖: T1 | 验证: 运行 agentwork-check exec

## 验证策略
- 验证接缝：`.shared/scripts/agentwork-check.py exec`。

## 完成标准（可选）
- exec 检查通过。

## Blockers / Risks
- 无。

## 执行记录（可选）
- 已验证 exec 自检能识别完成任务。
""",
    '.tmp/agentwork/audit/20260101-0000-fixture.md': """# Audit: fixture

> 创建: 2026-01-01 00:00
> 审查对象: .tmp/agentwork/spec/20260101-0001-exec-fixture.md

## Audit Basis
- 目标 / 范围
- 当前 spec / 决策与任务列表
- 当前工作区事实

## 结论
- 规格符合：通过；D1 已覆盖，T1 完成条件成立，无范围外改动。
- 质量规范：通过；未发现质量问题。

## Findings

### Critical
- none

### Important
- none

### Minor
- none

## Verification Status
- 已运行本地检查，未发现阻塞问题。

## Next Recommendation
- 结束当前 fixture 检查。
""",
    '.tmp/agentwork/audit/20260101-0001-important-fixture.md': """# Audit: important-fixture

> 创建: 2026-01-01 00:01
> 审查对象: .tmp/agentwork/spec/20260101-0001-exec-fixture.md

## 结论
- 规格符合：不通过；缺少验证证据。
- 质量规范：通过。

## Findings

### Critical
- none

### Important
- [规格] 缺少关键验证证据 | 处置: 本轮修复
""",
    '.shared/case/20260101-0000-fixture.md': """# Case: fixture

> 创建: 2026-01-01 00:00
> 简述: command harness fixture

## 任务列表（按优先级）
- [x] T1 验证 Case 自检 | 覆盖: D1 | 依赖: 无 | 完成: 验证通过 | 验证: 运行自检

## 已确认结论（工作快照）
### 目标
- 验证 Case 工件形态。
### 边界
- In Scope: `.shared/scripts/agentwork-check.py`
- Out of Scope: provider E2E
### 约束
- 本地确定性执行。
### 已选方案
- D1 使用命令内建 harness。

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
    # 相对 glob：输出保持仓库相对路径，与 case-audit.sh 的历史输出一致。
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


def subsection_lines(lines: list[str], heading_prefix: str) -> list[str]:
    section: list[str] = []
    in_section = False
    for line in lines:
        if line.startswith('### '):
            in_section = line.startswith(heading_prefix)
            continue
        if in_section:
            section.append(line)
    return section


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


# 只拦截明显的占位写法；验证是否充分仍由 /audit 人工判断。
VERIFY_PLACEHOLDERS = {
    '待定', '待补', '待补充', '待确认', '未定', '暂无', 'tbd', 'todo', '无', 'n/a', 'na', '-', '—', '–', '…', '略',
}
CHECKBOX_RE = re.compile(r'^- \[(.)\] ')
TASK_LINE_RE = re.compile(r'^- \[([ xX])\] (T\d+)\b(.*)$')
DECISION_LINE_RE = re.compile(r'^- (D\d+)\b')
# 半角 / 全角分隔符与冒号等价，避免把格式差异误报为缺字段。
FIELD_SEPARATOR_RE = re.compile(r'\s*[|｜]\s*')
FIELD_RE = re.compile(r'^([^:：]+)[:：]\s*(.*)$')
DEPENDENCY_LIST_RE = re.compile(r'^T\d+(?:\s*[,，、]\s*T\d+)*$')
COVERAGE_LIST_RE = re.compile(r'^D\d+(?:\s*[,，、]\s*D\d+)*$')
FINDING_CATEGORY_RE = re.compile(r'^\**\[(?:规格|质量)\]')


def is_placeholder(value: str) -> bool:
    """去掉括号与句末标点后比对，`（待定）`、`...` 这类写法同样视为占位。"""
    normalized = value.strip().strip('（）()【】[]').strip().rstrip('。.').strip().lower()
    return not normalized or normalized in VERIFY_PLACEHOLDERS


def parse_spec_tasks(text: str) -> list[dict[str, object]]:
    """解析任务行 `- [ ] Tn 任务 | 覆盖: Dx | 依赖: Ty | 完成: ... | 验证: ...`。"""
    tasks: list[dict[str, object]] = []
    for raw in section_lines(text, '## 任务列表'):
        line = raw.strip()
        checkbox = CHECKBOX_RE.match(line)
        if checkbox is None or checkbox.group(1) not in ' xX':
            continue
        match = TASK_LINE_RE.match(line)
        fields: dict[str, str] = {}
        duplicate_fields: set[str] = set()
        if match:
            for part in FIELD_SEPARATOR_RE.split(match.group(3))[1:]:
                field = FIELD_RE.match(part)
                if field:
                    name = field.group(1).strip()
                    if name in fields:
                        duplicate_fields.add(name)
                    fields[name] = field.group(2).strip()
        tasks.append({
            'line': line,
            'id': match.group(2) if match else None,
            'done': checkbox.group(1) in 'xX',
            'fields': fields,
            'duplicate_fields': duplicate_fields,
        })
    return tasks


def check_checkbox_marks(text: str, failures: list[str]) -> None:
    """`[ ]` / `[x]` / `[X]` 之外的标记无法判定完成状态，直接报错而不是静默跳过。"""
    for raw in section_lines(text, '## 任务列表'):
        checkbox = CHECKBOX_RE.match(raw.strip())
        if checkbox and checkbox.group(1) not in ' xX':
            add_once(failures, f'task_unknown_checkbox:{raw.strip()}')


def id_refs(value: str, prefix: str) -> list[str]:
    return re.findall(rf'\b{prefix}\d+\b', value)


def check_task_contract(
    decision_lines: list[str],
    tasks: list[dict[str, object]],
    failures: list[str],
    *,
    require_completion: bool = False,
) -> None:
    decisions = [match.group(1) for line in decision_lines if (match := DECISION_LINE_RE.match(line.strip()))]
    if not decisions:
        add_once(failures, 'missing_decisions')
    for decision in decisions:
        if decisions.count(decision) > 1:
            add_once(failures, f'duplicate_decision_id:{decision}')
    if not tasks:
        add_once(failures, 'missing_task_checkbox')
    task_ids: set[str] = set()
    for task in tasks:
        if task['id'] in task_ids:
            add_once(failures, f'duplicate_task_id:{task["id"]}')
        if task['id']:
            task_ids.add(task['id'])
    covered: set[str] = set()
    dependencies: dict[str, set[str]] = {}
    for task in tasks:
        task_id = task['id']
        if task_id is None:
            add_once(failures, f'task_missing_id:{task["line"]}')
            continue
        fields = task['fields']
        for name in sorted(task['duplicate_fields']):
            add_once(failures, f'task_duplicate_field:{task_id}:{name}')
        coverage = id_refs(fields.get('覆盖', ''), 'D')
        if not coverage:
            add_once(failures, f'task_missing_field:{task_id}:覆盖')
        elif not COVERAGE_LIST_RE.fullmatch(fields['覆盖']):
            add_once(failures, f'task_invalid_coverage:{task_id}:{fields["覆盖"]}')
        verify = fields.get('验证', '')
        if not verify:
            add_once(failures, f'task_missing_field:{task_id}:验证')
        elif is_placeholder(verify):
            add_once(failures, f'task_placeholder_field:{task_id}:验证')
        complete = fields.get('完成', '')
        if require_completion and not complete:
            add_once(failures, f'task_missing_field:{task_id}:完成')
        elif '完成' in fields and is_placeholder(complete):
            add_once(failures, f'task_placeholder_field:{task_id}:完成')
        raw_dependency = fields.get('依赖')
        dependency = (raw_dependency or '').strip().rstrip('。.').strip()
        if raw_dependency is None:
            if require_completion:
                add_once(failures, f'task_missing_field:{task_id}:依赖')
        elif dependency != '无' and not DEPENDENCY_LIST_RE.match(dependency):
            # `无` 本身在占位词表里，须先放行；其余值不能退化成“无依赖”。
            if is_placeholder(dependency):
                add_once(failures, f'task_placeholder_field:{task_id}:依赖')
            else:
                add_once(failures, f'task_invalid_dependency:{task_id}:{dependency}')
        for ref in coverage:
            if ref not in decisions:
                add_once(failures, f'task_unknown_decision:{task_id}:{ref}')
        covered.update(coverage)
        deps = set(id_refs(fields.get('依赖', ''), 'T'))
        dependencies[task_id] = (deps & task_ids) - {task_id}
        for dep in deps:
            if dep not in task_ids:
                add_once(failures, f'task_unknown_dependency:{task_id}:{dep}')
            elif dep == task_id:
                add_once(failures, f'task_self_dependency:{task_id}')
    for decision in decisions:
        if decision not in covered:
            add_once(failures, f'decision_not_covered:{decision}')

    try:
        TopologicalSorter(dependencies).prepare()
    except CycleError as exc:
        add_once(failures, f'task_dependency_cycle:{",".join(exc.args[1])}')


def check_completed_dependencies(tasks: list[dict[str, object]], failures: list[str]) -> None:
    done = {task['id'] for task in tasks if task['done']}
    for task in tasks:
        if not task['done'] or task['id'] is None:
            continue
        for dep in id_refs(task['fields'].get('依赖', ''), 'T'):
            if dep not in done:
                add_once(failures, f'task_done_before_dependency:{task["id"]}:{dep}')


def check_spec(path: Path | None) -> tuple[Path | None, list[str]]:
    failures: list[str] = []
    path = check_exists(path, 'spec', failures)
    if path is None:
        return None, failures
    text = read_text(path)
    check_no_placeholders(text, failures)
    check_required_headings(
        text,
        [
            '# Spec:',
            '> 来源:',
            '## Goal',
            '## 决策',
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

    check_task_contract(section_lines(text, '## 决策'), parse_spec_tasks(text), failures)
    check_checkbox_marks(text, failures)
    return path, failures


def check_exec(path: Path | None) -> tuple[Path | None, list[str]]:
    path, failures = check_spec(path)
    if path is None:
        return None, failures
    tasks = parse_spec_tasks(read_text(path))
    if not any(task['done'] for task in tasks):
        add_once(failures, 'missing_completed_task_checkbox')
    check_completed_dependencies(tasks, failures)
    return path, failures


def finding_sections(text: str) -> dict[str, list[str]]:
    """统一解析 Findings 的严重度分节和带严重度前缀的列表。"""
    sections: dict[str, list[str]] = {'critical': [], 'important': [], 'minor': [], 'unclassified': []}
    current: str | None = None
    last: str | None = None
    for raw in section_lines(text, '## Findings'):
        line = raw.strip()
        if not line:
            continue
        heading = re.match(r'^#{3,4}\s+(.*)$', line) or re.match(r'^(\*\*[^*]+\*\*)\s*(?:[（(][^)）]*[)）])?$', line)
        if heading:
            label = re.match(r'^\**\s*(critical|important|minor)\b', heading.group(1).strip(), re.I)
            current = label.group(1).lower() if label else None
            last = None
            continue
        item = re.sub(r'^(?:[-*+]|\d+[.)])\s+', '', line)
        prefixed = re.match(r'^(?:\*\*|`)?(critical|important|minor)(?:\*\*|`)?(?:\s*[:：]\s*|\s+)(.*)$', item, re.I)
        level = current or 'unclassified'
        if prefixed:
            level, item = prefixed.group(1).lower(), prefixed.group(2)
        if item.strip().rstrip('.。').lower() in {'none', '无', 'n/a'}:
            continue
        # 缩进的续行与证据等子项归入上一条问题；带类别标签的嵌套项仍是独立问题，须单独带处置。
        nested_finding = FINDING_CATEGORY_RE.match(item)
        if raw.startswith((' ', '\t')) and not prefixed and last is not None:
            if not nested_finding:
                sections[last][-1] += ' ' + item
                continue
            level = last
        sections[level].append(item)
        last = level
    return sections


def check_audit(path: Path | None, fail_on_major: bool) -> tuple[Path | None, list[str]]:
    failures: list[str] = []
    path = check_exists(path, 'audit', failures)
    if path is None:
        return None, failures
    text = read_text(path)
    check_no_placeholders(text, failures)
    check_required_headings(text, ['# Audit:', '## 结论'], failures)
    if not (heading_present(text, '## Findings') or heading_present(text, '## Findings Summary')):
        add_once(failures, 'missing_heading:## Findings')
    # 规格符合与质量规范分开给结论，不让一类掩盖另一类。
    conclusion = '\n'.join(section_lines(text, '## 结论'))
    for label in ('规格符合', '质量规范'):
        values = re.findall(rf'^- \*{{0,2}}{label}\*{{0,2}}[:：]\*{{0,2}}\s*([^\n]*)', conclusion, flags=re.MULTILINE)
        if not values:
            add_once(failures, f'missing_audit_conclusion:{label}')
            continue
        if len(values) != 1:
            add_once(failures, f'duplicate_audit_conclusion:{label}')
        for value in values:
            verdict = re.match(r'^(通过|不通过)(?=$|[\s；;，,。.:：*])', value.strip().lstrip('*'))
            if not verdict:
                add_once(failures, f'invalid_audit_conclusion:{label}')
            elif fail_on_major and verdict.group(1) != '通过':
                add_once(failures, f'audit_not_passed:{label}')
    # 每个问题都要带处置，否则审查结论无法接力。
    for level, items in finding_sections(text).items():
        if items and level == 'unclassified':
            add_once(failures, 'audit_finding_missing_severity')
        if items and fail_on_major and level in ('critical', 'important'):
            add_once(failures, f'audit_has_{level}_findings:{len(items)}')
        for item in items:
            if not FINDING_CATEGORY_RE.match(item.strip()):
                add_once(failures, f'audit_finding_missing_category:{level}:{item}')
            disposition = re.search(r'(?:^|[|｜])\s*处置[:：]\s*(.*)', item)
            if disposition is None:
                add_once(failures, f'audit_finding_missing_disposition:{level}:{item}')
                continue
            value = disposition.group(1).strip()
            if not re.match(r'^(?:本轮修复|转后续(?:任务)?|待(?:用户)?决策)(?=$|[\s；;，,。.:：（(])', value):
                rejected = re.fullmatch(r'拒绝\s*[（(](.+)[）)]\s*[。.]?', value)
                if rejected is None or is_placeholder(rejected.group(1)):
                    add_once(failures, f'audit_finding_invalid_disposition:{level}:{item}')
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
            print(f'warning:duplicate_commit_anchor:{anchor}:{count}:audit 独立验证或边界后决定是否合并', file=sys.stderr)


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
    if not re.search(r'^- \[[ xX]\] .+', text, flags=re.MULTILINE):
        add_once(failures, 'missing_task_checkbox')

    # strict-flow 对所有 Case 校验 D/T 契约；不读取临时来源 spec。
    if strict_flow:
        tasks = parse_spec_tasks(text)
        # 决策只从“已选方案”收集，目标或约束里以 `- Dn` 开头的行不算决策。
        decisions = subsection_lines(section_lines(text, '## 已确认结论'), '### 已选方案')
        check_task_contract(decisions, tasks, failures, require_completion=True)
        check_checkbox_marks(text, failures)
        check_completed_dependencies(tasks, failures)

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

    spec_dir = root / '.tmp/agentwork/spec'
    spec_text = read_text(spec_dir / '20260101-0000-fixture.md')
    exec_text = read_text(spec_dir / '20260101-0001-exec-fixture.md')
    spec_uncovered = spec_dir / '20260101-0002-uncovered-decision.md'
    write_text(spec_uncovered, spec_text.replace(
        '- D1 spec 工件由 agentwork-check 校验。',
        '- D1 spec 工件由 agentwork-check 校验。\n- D2 未被任何任务覆盖的决策。',
    ))
    spec_missing_verify = spec_dir / '20260101-0003-missing-verify.md'
    write_text(spec_missing_verify, spec_text.replace(' | 验证: 运行 agentwork-check spec', ''))
    exec_out_of_order = spec_dir / '20260101-0004-done-before-dependency.md'
    write_text(exec_out_of_order, exec_text.replace('- [x] T1', '- [ ] T1').replace('- [ ] T2', '- [x] T2'))
    spec_unknown_decision = spec_dir / '20260101-0005-unknown-decision.md'
    write_text(spec_unknown_decision, spec_text.replace('覆盖: D1', '覆盖: D1, D9'))
    spec_unknown_dependency = spec_dir / '20260101-0006-unknown-dependency.md'
    write_text(spec_unknown_dependency, spec_text.replace('依赖: 无', '依赖: T9'))
    spec_placeholder_verify = spec_dir / '20260101-0007-placeholder-verify.md'
    write_text(spec_placeholder_verify, spec_text.replace('验证: 运行 agentwork-check spec', '验证: 待定'))

    audit_dir = root / '.tmp/agentwork/audit'
    audit_text = read_text(audit_dir / '20260101-0000-fixture.md')
    audit_missing_quality = audit_dir / '20260101-0002-missing-quality.md'
    write_text(audit_missing_quality, re.sub(r'^- 质量规范.*\n', '', audit_text, flags=re.MULTILINE))
    audit_critical = audit_dir / '20260101-0003-critical.md'
    write_text(audit_critical, audit_text.replace(
        '### Critical\n- none', '### Critical\n- [规格] 决策被弱化 | 处置: 本轮修复'))
    audit_missing_disposition = audit_dir / '20260101-0004-missing-disposition.md'
    write_text(audit_missing_disposition, audit_text.replace('### Minor\n- none', '### Minor\n- [质量] 命名不一致'))

    checks = [
        ('brain', check_brain(root / '.tmp/agentwork/brain/20260101-0000-fixture.md'), None),
        ('spec', check_spec(root / '.tmp/agentwork/spec/20260101-0000-fixture.md'), None),
        ('exec', check_exec(root / '.tmp/agentwork/spec/20260101-0001-exec-fixture.md'), None),
        ('audit', check_audit(root / '.tmp/agentwork/audit/20260101-0000-fixture.md', True), None),
        ('spec-uncovered-decision', check_spec(spec_uncovered), 'decision_not_covered:D2'),
        ('spec-missing-verify', check_spec(spec_missing_verify), 'task_missing_field:T1:验证'),
        ('exec-done-before-dependency', check_exec(exec_out_of_order), 'task_done_before_dependency:T2:T1'),
        ('spec-unknown-decision', check_spec(spec_unknown_decision), 'task_unknown_decision:T1:D9'),
        ('spec-unknown-dependency', check_spec(spec_unknown_dependency), 'task_unknown_dependency:T1:T9'),
        ('spec-placeholder-verify', check_spec(spec_placeholder_verify), 'task_placeholder_field:T1:验证'),
        ('audit-missing-quality', check_audit(audit_missing_quality, False), 'missing_audit_conclusion:质量规范'),
        ('audit-critical', check_audit(audit_critical, True), 'audit_has_critical_findings'),
        (
            'audit-missing-disposition',
            check_audit(audit_missing_disposition, False),
            'audit_finding_missing_disposition:minor',
        ),
        ('case', check_case(case_path, True), None),
        ('case-many-reviews', check_case(root / '.shared/case/20260101-0000-many-reviews.md', True), None),
        ('case-same-day', check_case(root / '.shared/case/20260101-0000-same-day.md', True), None),
        (
            'audit-important',
            check_audit(root / '.tmp/agentwork/audit/20260101-0001-important-fixture.md', True),
            'audit_has_important_findings',
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

    spec_case = case_text.replace('- [x] T1 验证 Case 自检 | 覆盖: D1 | 依赖: 无 | 完成: 验证通过 | 验证: 运行自检', '- [x] T1 验证 Case 自检 | 覆盖: D1 | 依赖: 无 | 完成: 验证通过 | 验证: 运行自检\n- [x] T2 后续任务 | 覆盖: D1 | 依赖: T1 | 完成: 验证通过 | 验证: 运行自检')
    contract_fixtures = [
        ('case-contract', spec_case, lambda p: check_case(p, True), None),
        ('case-no-decisions', spec_case.replace('- D1 使用命令内建 harness。', ''), lambda p: check_case(p, True), 'missing_decisions'),
        ('case-no-completion', spec_case.replace(' | 完成: 验证通过', ''), lambda p: check_case(p, True), 'task_missing_field:T1:完成'),
        ('case-unready', spec_case.replace('- [x] T1 ', '- [ ] T1 '), lambda p: check_case(p, True), 'task_done_before_dependency'),
        ('spec-duplicate-task', exec_text.replace('- [ ] T2 ', '- [ ] T1 '), check_spec, 'duplicate_task_id'),
        ('spec-cycle', exec_text.replace('覆盖: D1 | 验证:', '覆盖: D1 | 依赖: T2 | 验证:', 1), check_spec, 'task_dependency_cycle'),
        ('audit-pending', audit_text.replace('规格符合：通过；', '规格符合：待定；'), lambda p: check_audit(p, True), 'invalid_audit_conclusion'),
        ('audit-failed', audit_text.replace('规格符合：通过；', '规格符合：不通过；'), lambda p: check_audit(p, True), 'audit_not_passed'),
        ('audit-invalid-disposition', audit_text.replace('### Minor\n- none', '### Minor\n- [质量] 问题 | 处置: ...'), lambda p: check_audit(p, False), 'audit_finding_invalid_disposition'),
        ('audit-rejected-no-reason', audit_text.replace('### Minor\n- none', '### Minor\n1. [质量] 问题 | 处置: 拒绝'), lambda p: check_audit(p, False), 'audit_finding_invalid_disposition'),
        ('case-pending-dependency', spec_case.replace('依赖: T1 |', '依赖: 待定 |'), lambda p: check_case(p, True), 'task_placeholder_field:T2:依赖'),
        ('case-invalid-dependency', spec_case.replace('依赖: T1 |', '依赖: 不存在的前置任务 |'), lambda p: check_case(p, True), 'task_invalid_dependency:T2'),
        ('audit-missing-category', audit_text.replace('### Minor\n- none', '### Minor\n- 问题 | 处置: 本轮修复'), lambda p: check_audit(p, False), 'audit_finding_missing_category'),
        ('audit-summary-no-disposition', audit_text.replace('### Minor\n- none', '- Minor: [质量] 问题'), lambda p: check_audit(p, False), 'audit_finding_missing_disposition'),
        ('spec-pending-completion', exec_text.replace(' | 验证:', ' | 完成: 待定 | 验证:', 1), check_spec, 'task_placeholder_field:T1:完成'),
        ('exec-pending-completion', exec_text.replace(' | 验证:', ' | 完成: 待定 | 验证:', 1), check_exec, 'task_placeholder_field:T1:完成'),
        ('spec-coverage-range', exec_text.replace('覆盖: D1', '覆盖: D1-D1'), check_spec, 'task_invalid_coverage'),
        ('spec-duplicate-dependency', exec_text.replace('依赖: T1', '依赖: T999 | 依赖: T1'), check_spec, 'task_duplicate_field:T2:依赖'),
        ('audit-bold-nested', audit_text.replace('### Minor\n- none', '### Minor\n- [质量] 父问题 | 处置: 本轮修复\n  - **[规格]** 子问题'), lambda p: check_audit(p, True), 'audit_finding_missing_disposition'),
    ]
    for name, content, check, expected in contract_fixtures:
        fixture_path = root / 'contract-fixtures' / f'{name}.md'
        write_text(fixture_path, content)
        checks.append((name, check(fixture_path), expected))

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

    spec_parser = subparsers.add_parser('spec', help='check a spec')
    spec_parser.add_argument('path', nargs='?')

    exec_parser = subparsers.add_parser('exec', help='check a spec after /exec updated it')
    exec_parser.add_argument('path', nargs='?')

    audit = subparsers.add_parser('audit', help='check an audit note')
    audit.add_argument('path', nargs='?')
    audit.add_argument('--fail-on-major', action='store_true', help='fail when Critical or Important findings are present')

    case = subparsers.add_parser('case', help='check a Case snapshot')
    case.add_argument('path', nargs='?')
    case.add_argument('--strict-flow', action='store_true', help='require 计划摘要/当前批次工作集/产出批次 sections and the spec task contract')

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
        elif args.command == 'spec':
            path, failures = check_spec(resolve_path('spec', args.path))
        elif args.command == 'exec':
            path, failures = check_exec(resolve_path('spec', args.path))
        elif args.command == 'audit':
            path, failures = check_audit(resolve_path('audit', args.path), args.fail_on_major)
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
