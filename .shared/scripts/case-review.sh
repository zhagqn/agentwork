#!/usr/bin/env bash
# Case 审查工具 - 对照 Case 的“当前批次工作集”范围与工作区改动，并检查聚合后的“产出批次”锚点

set -euo pipefail

CASE_DIR=".shared/case"

usage() {
    cat >&2 << 'EOF'
用法:
  .shared/scripts/case-review.sh            # 审查最新 Case
  .shared/scripts/case-review.sh <case-ref> # 审查指定 Case id 或文件路径
EOF
}

pick_latest_case() {
    if [[ ! -d "$CASE_DIR" ]]; then
        echo "暂无 Case 记录（目录不存在）" >&2
        return 1
    fi

    # 统一走 agentwork-check.py latest，避免第二条独立的选取规则。
    local checker
    checker="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/agentwork-check.py"

    # 只捕获 stdout；stderr（含 ambiguous_latest 诊断）直接透传，避免混入路径。
    local latest
    if ! latest=$(python3 "$checker" latest case); then
        if [[ "$latest" == missing_latest:* ]]; then
            echo "暂无 Case 记录" >&2
        else
            echo "无法确定最新 Case，请显式指定 case id 或文件路径" >&2
        fi
        return 1
    fi

    echo "$latest"
}

resolve_case_file() {
    if [[ $# -eq 0 ]]; then
        pick_latest_case
        return
    fi

    if [[ $# -ne 1 ]]; then
        usage
        return 2
    fi

    local arg="$1"
    if [[ "$arg" == *.md || "$arg" == */* ]]; then
        echo "$arg"
        return
    fi

    echo "$CASE_DIR/$arg.md"
}

git_root() {
    git rev-parse --show-toplevel 2>/dev/null || true
}

extract_current_workset() {
    local case_file="$1"
    local section

    section=$(awk '
        BEGIN { in_section=0 }
        /^##[[:space:]]+当前批次工作集([（(].*[)）])?[[:space:]]*$/ { in_section=1; next }
        /^##[[:space:]]+/ { if (in_section) exit }
        { if (in_section) print }
    ' "$case_file")

    if [[ -n "$section" ]]; then
        local range_entries
        range_entries=$(echo "$section" | \
            sed -nE '/^- 范围:/ { s/^.*范围:[[:space:]]*//; s/[[:space:]]*\|[[:space:]]*主题:.*$//; p; }' | \
            grep -oE '`[^`]+`' | \
            tr -d '`' | \
            sed 's/^[[:space:]]*//; s/[[:space:]]*$//' | \
            sed '/^$/d' || true)

        if [[ -n "$range_entries" ]]; then
            echo "$range_entries" | sort -u
            return
        fi

        echo "$section" | \
            grep -oE '`[^`]+`' | \
            tr -d '`' | \
            sed 's/^[[:space:]]*//; s/[[:space:]]*$//' | \
            sed '/^$/d' | \
            sort -u
        return
    fi

}

extract_deliverable_section() {
    local case_file="$1"
    local section

    section=$(awk '
        BEGIN { in_section=0 }
        /^##[[:space:]]+产出批次([（(].*[)）])?[[:space:]]*$/ { in_section=1; next }
        /^##[[:space:]]+/ { if (in_section) exit }
        { if (in_section) print }
    ' "$case_file")

    printf '%s\n' "$section"
}

extract_commit_hashes() {
    local case_file="$1"
    extract_commit_hash_occurrences "$case_file" | sort -u
}

extract_commit_hash_occurrences() {
    local case_file="$1"
    local section
    section="$(extract_deliverable_section "$case_file")"

    # 一个“提交:”字段可以聚合多个相关 hash；只解析字段本身，避免把日期或文件名当成 hash。
    printf '%s\n' "$section" |
        sed -nE 's/^.*提交:[[:space:]]*([^|]+).*/\1/p' |
        grep -oE '[0-9a-fA-F]{7,40}' |
        tr 'A-F' 'a-f' |
        sed '/^$/d' || true
}

extract_duplicate_commit_hashes() {
    local case_file="$1"
    extract_commit_hash_occurrences "$case_file" | sort | uniq -d
}

extract_external_commit_hashes() {
    local case_file="$1"
    local section
    section="$(extract_deliverable_section "$case_file")"

    # 独立仓/外部仓锚点不在当前仓 Git object database 中，仍保留但不误报为无效。
    # 混合记录只把来源标记之后的 hash 视为外部；范围中标记为外部仓时整条均视为外部。
    local candidates
    candidates="$(printf '%s\n' "$section" | awk '
        /^- (提交|历史):/ {
            line = $0
            commit = line
            sub(/^.*提交:[[:space:]]*/, "", commit)
            sub(/[[:space:]]*\|.*/, "", commit)
            if (match(commit, /(独立前端仓|独立仓|外部仓|其他仓)/)) {
                print substr(commit, RSTART + RLENGTH)
            } else if (line ~ /(独立前端仓|独立仓|外部仓|其他仓)/) {
                print commit
            }
        }
    ' | grep -oE '[0-9a-fA-F]{7,40}' || true)"
    printf '%s\n' "$candidates" | tr 'A-F' 'a-f' | sed '/^$/d' | sort -u
}

main() {
    local case_file
    case_file="$(resolve_case_file "$@")" || exit $?

    if [[ ! -f "$case_file" ]]; then
        echo "Case 文件不存在: $case_file"
        echo ""
        usage
        exit 1
    fi

    local root
    root="$(git_root)"

    echo "Case Review（脚本辅助）"
    echo ""
    echo "Case: $case_file"

    if [[ -n "$root" ]]; then
        echo "Git Root: $root"
    else
        echo "Git Root: （未检测到 git 仓库）"
    fi

    echo ""

    local workset
    workset="$(extract_current_workset "$case_file" || true)"

    local workset_count=0
    if [[ -n "$workset" ]]; then
        workset_count=$(echo "$workset" | wc -l | tr -d ' ')
    fi

    echo "当前批次工作集条目（可为精确路径、目录范围或 glob）：$workset_count"

    if [[ -n "$workset" ]]; then
        echo "$workset" | sed 's/.*/- `&`/'
    else
        echo "- （无）"
    fi

    echo ""

    local commit_hashes
    commit_hashes="$(extract_commit_hashes "$case_file" || true)"

    local external_commit_hashes
    external_commit_hashes="$(extract_external_commit_hashes "$case_file" || true)"

    local duplicate_commit_hashes
    duplicate_commit_hashes="$(extract_duplicate_commit_hashes "$case_file" || true)"

    local commit_hash_count=0
    if [[ -n "$commit_hashes" ]]; then
        commit_hash_count=$(echo "$commit_hashes" | wc -l | tr -d ' ')
    fi

    echo "产出批次锚点（从“## 产出批次（提交锚点）”解析）：$commit_hash_count"
    if [[ -n "$commit_hashes" ]]; then
        echo "$commit_hashes" | sed 's/.*/- &/'
    else
        echo "- （未解析到 commit hash；未提交时可写“提交: -”）"
    fi

    echo ""

    if [[ -z "$root" ]]; then
        if [[ -n "$commit_hashes" ]]; then
            echo "提示：不在 git 仓库中，无法校验提交 hash 有效性。"
        fi
        echo "提示：不在 git 仓库中，无法对照工作区改动。"
        exit 0
    fi

    # 提交锚点可验证性检查。不可见的历史 hash 不能据此删除，可能来自旧分支、历史重写或其他仓。
    local unavailable_hashes=()
    if [[ -n "$commit_hashes" ]]; then
        while IFS= read -r hash; do
            [[ -z "$hash" ]] && continue
            if ! git cat-file -e "${hash}^{commit}" 2>/dev/null; then
                if [[ -z "$external_commit_hashes" ]] || ! grep -qxF "$hash" <<< "$external_commit_hashes"; then
                    unavailable_hashes+=("$hash")
                fi
            fi
        done <<< "$commit_hashes"
    fi

    if [[ ${#unavailable_hashes[@]} -gt 0 ]]; then
        echo "当前仓不可验证的历史提交锚点（保留原记录，不自动删除）："
        printf '%s\n' "${unavailable_hashes[@]}" | sort -u | sed 's/.*/- &/'
        echo ""
    fi

    if [[ -n "$external_commit_hashes" ]]; then
        echo "外部仓提交锚点（当前仓不做 object 校验）："
        printf '%s\n' "$external_commit_hashes" | sed 's/.*/- &/'
        echo ""
    fi

    if [[ -n "$duplicate_commit_hashes" ]]; then
        echo "重复提交锚点（默认应合并；仅在验证或边界明显不同时保留多处）："
        printf '%s\n' "$duplicate_commit_hashes" | sed 's/.*/- &/'
        echo ""
    fi

    # Git 路径从 NUL 记录到范围比较始终保留边界；转义仅用于展示。
    python3 - "$case_file" "$root" <<'PY'
import fnmatch
import os
from pathlib import Path
import re
import subprocess
import sys

case_file, root = sys.argv[1:]
text = Path(case_file).read_text(encoding='utf-8')
section = re.search(r'^## 当前批次工作集[^\n]*\n(.*?)(?=^## |\Z)', text, re.M | re.S)
scopes = []
if section:
    for line in section.group(1).splitlines():
        if line.startswith('- 范围:'):
            scopes.extend(re.findall(r'`([^`]+)`', line.split(' | 主题:', 1)[0]))
scopes = sorted(set(scopes))
raw = subprocess.run(
    ['git', '-C', root, 'status', '--porcelain=v1', '-z', '--untracked-files=all'],
    check=True, stdout=subprocess.PIPE,
).stdout
records = iter(raw.split(b'\0'))
changed, status_paths = set(), set()
for record in records:
    if not record:
        continue
    status = record[:2]
    path = os.fsdecode(record[3:])
    changed.add(path)
    status_paths.add(path)
    if b'R' in status or b'C' in status:
        # -z 下目标在前，来源是下一条独立 NUL 记录。
        origin = next(records)
        if not origin:
            raise ValueError('incomplete Git rename/copy record')
        status_paths.add(os.fsdecode(origin))

literal_scopes = {
    scope for scope in scopes if not scope.endswith('/')
    and (scope in status_paths or os.path.lexists(os.path.join(root, scope)))
}

def matches(path, scope):
    if scope in literal_scopes:
        return path == scope
    if any(char in scope for char in '*?['):
        return fnmatch.fnmatchcase(path, scope)
    return path.startswith(scope) if scope.endswith('/') else path == scope

def display(path):
    return path.replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

def report(title, paths, always=False):
    paths = sorted(paths)
    if paths or always:
        print(title)
        for path in paths:
            print(f'- `{display(path)}`')
        if not paths:
            print('- （无）')
        print()

report(f'工作区改动（git status --porcelain）：{len(changed)}', changed, True)
missing = [
    scope for scope in scopes
    if not os.path.isabs(scope) and not any(c in scope for c in '*?[')
    and not os.path.lexists(os.path.join(root, scope))
    and not any(matches(path, scope) for path in status_paths)
]
report('缺失/疑似过期的当前批次工作集条目（路径不存在，且未在 git status 中体现）：', missing)
report('工作区有改动但未被“当前批次工作集”覆盖：',
       [path for path in changed if not any(matches(path, scope) for scope in scopes)])
report('“当前批次工作集”中记录但当前工作区未体现（可能已提交/已还原）：',
       [scope for scope in scopes if not any(matches(path, scope) for path in status_paths)])
PY

    echo "下一步建议："
    echo "- 在对话中执行：/review  # 让助手先做双层 review，再整理 Case 文档"
}

main "$@"
