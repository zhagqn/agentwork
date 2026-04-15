#!/usr/bin/env bash
# Session 审查工具 - 对照 session 的“当前批次工作集”与工作区改动，并检查“产出批次”锚点

set -euo pipefail

SESSION_DIR=".shared/session"

usage() {
    cat >&2 << 'EOF'
用法:
  .shared/scripts/session-review.sh                # 审查最新 session
  .shared/scripts/session-review.sh <session-id>  # 审查指定 session（不含 .md）
  .shared/scripts/session-review.sh <path/to.md>  # 审查指定文件路径
EOF
}

pick_latest_session() {
    if [[ ! -d "$SESSION_DIR" ]]; then
        echo "暂无 Session 记录（目录不存在）" >&2
        return 1
    fi

    local latest
    latest=$(find "$SESSION_DIR" -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort -r | head -n 1 || true)
    if [[ -z "$latest" ]]; then
        echo "暂无 Session 记录" >&2
        return 1
    fi

    echo "$latest"
}

resolve_session_file() {
    if [[ $# -eq 0 ]]; then
        pick_latest_session
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

    echo "$SESSION_DIR/$arg.md"
}

git_root() {
    git rev-parse --show-toplevel 2>/dev/null || true
}

extract_current_workset() {
    local session_file="$1"
    local section

    section=$(awk '
        BEGIN { in_section=0 }
        /^##[[:space:]]+当前批次工作集([（(].*[)）])?[[:space:]]*$/ { in_section=1; next }
        /^##[[:space:]]+/ { if (in_section) exit }
        { if (in_section) print }
    ' "$session_file")

    if [[ -n "$section" ]]; then
        echo "$section" | \
            grep -oE '`[^`]+`' | \
            tr -d '`' | \
            sed 's/^[[:space:]]*//; s/[[:space:]]*$//' | \
            sed '/^$/d' | \
            sort -u
        return
    fi

    # fallback：兼容 legacy 的“产出物（含提交锚点）”逐文件格式
    awk '
        BEGIN { in_deliverables=0 }
        /^##[[:space:]]+产出物([（(].*[)）])?[[:space:]]*$/ { in_deliverables=1; next }
        /^##[[:space:]]+/ { if (in_deliverables) exit }
        { if (in_deliverables) print }
    ' "$session_file" | \
        sed -E 's/^.*文件:[[:space:]]*//; s/[[:space:]]*\|[[:space:]]*提交:.*$//' | \
        grep -oE '`[^`]+`' | \
        tr -d '`' | \
        sed 's/^[[:space:]]*//; s/[[:space:]]*$//' | \
        sed '/^$/d' | \
        sort -u
}

extract_commit_hashes() {
    local session_file="$1"
    local section

    section=$(awk '
        BEGIN { in_section=0 }
        /^##[[:space:]]+产出批次([（(].*[)）])?[[:space:]]*$/ { in_section=1; next }
        /^##[[:space:]]+/ { if (in_section) exit }
        { if (in_section) print }
    ' "$session_file")

    if [[ -z "$section" ]]; then
        # fallback：兼容 legacy 的“产出物（含提交锚点）”
        section=$(awk '
        BEGIN { in_deliverables=0 }
        /^##[[:space:]]+产出物([（(].*[)）])?[[:space:]]*$/ { in_deliverables=1; next }
        /^##[[:space:]]+/ { if (in_deliverables) exit }
        { if (in_deliverables) print }
    ' "$session_file")
    fi

    # 仅解析“提交:”列的首个 token，过滤非 hash 值（如 "-"）
    echo "$section" | \
        sed -nE 's/^.*提交:[[:space:]]*`?([^`|]+)`?.*/\1/p' | \
        awk '{print $1}' | \
        grep -E '^[0-9a-fA-F]{7,40}$' | \
        tr 'A-F' 'a-f' | \
        sort -u
}

extract_git_changed_files() {
    # 解析 git status --porcelain 输出，覆盖新增/修改/重命名/未跟踪
    # 关闭 Git 对非 ASCII 路径的转义输出，避免中文文件名匹配失败
    git -c core.quotepath=false status --porcelain 2>/dev/null | awk '
        {
            path = substr($0, 4)
            # 处理 rename/copy: "old -> new"
            arrow = index(path, " -> ")
            if (arrow > 0) {
                path = substr(path, arrow + 4)
            }
            print path
        }
    ' | sed '/^$/d' | sort -u
}

main() {
    local session_file
    session_file="$(resolve_session_file "$@")" || exit $?

    if [[ ! -f "$session_file" ]]; then
        echo "Session 文件不存在: $session_file"
        echo ""
        usage
        exit 1
    fi

    local root
    root="$(git_root)"

    echo "Session Review（脚本辅助）"
    echo ""
    echo "Session: $session_file"

    if [[ -n "$root" ]]; then
        echo "Git Root: $root"
    else
        echo "Git Root: （未检测到 git 仓库）"
    fi

    echo ""

    local workset
    workset="$(extract_current_workset "$session_file" || true)"

    local workset_count=0
    if [[ -n "$workset" ]]; then
        workset_count=$(echo "$workset" | wc -l | tr -d ' ')
    fi

    echo "当前批次工作集（优先从“## 当前批次工作集”解析；若不存在则回退 legacy 产出物）：$workset_count"

    if [[ -n "$workset" ]]; then
        echo "$workset" | sed 's/.*/- `&`/'
    else
        echo "- （无）"
    fi

    echo ""

    local commit_hashes
    commit_hashes="$(extract_commit_hashes "$session_file" || true)"

    local commit_hash_count=0
    if [[ -n "$commit_hashes" ]]; then
        commit_hash_count=$(echo "$commit_hashes" | wc -l | tr -d ' ')
    fi

    echo "产出批次锚点（优先从“## 产出批次（提交锚点）”解析；若不存在则回退 legacy 产出物）：$commit_hash_count"
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

    local changed
    changed="$(extract_git_changed_files || true)"

    local changed_count=0
    if [[ -n "$changed" ]]; then
        changed_count=$(echo "$changed" | wc -l | tr -d ' ')
    fi

    echo "工作区改动（git status --porcelain）：$changed_count"
    if [[ -n "$changed" ]]; then
        echo "$changed" | sed 's/.*/- `&`/'
    else
        echo "- （无）"
    fi

    echo ""

    # 提交锚点有效性检查
    local invalid_hashes=()
    if [[ -n "$commit_hashes" ]]; then
        while IFS= read -r hash; do
            [[ -z "$hash" ]] && continue
            if ! git cat-file -e "${hash}^{commit}" 2>/dev/null; then
                invalid_hashes+=("$hash")
            fi
        done <<< "$commit_hashes"
    fi

    if [[ ${#invalid_hashes[@]} -gt 0 ]]; then
        echo "无效/不存在的提交锚点："
        printf '%s\n' "${invalid_hashes[@]}" | sort -u | sed 's/.*/- &/'
        echo ""
    fi

    # 当前批次工作集缺失检查（相对 git root）
    local missing=()
    if [[ -n "$workset" ]]; then
        while IFS= read -r path; do
            # 对于绝对路径或不在仓库内的路径，不做存在性检查
            if [[ "$path" == /* ]]; then
                continue
            fi
            if [[ ! -e "$root/$path" ]]; then
                missing+=("$path")
            fi
        done <<< "$workset"
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "缺失/疑似过期的当前批次工作集条目（路径不存在）："
        printf '%s\n' "${missing[@]}" | sort -u | sed 's/.*/- `&`/'
        echo ""
    fi

    # 工作区改动但未记录到当前批次工作集（简单精确匹配）
    local changed_not_listed=()
    if [[ -n "$changed" ]]; then
        while IFS= read -r f; do
            [[ -z "$f" ]] && continue
            if [[ -z "$workset" ]] || ! grep -qxF "$f" <<< "$workset"; then
                changed_not_listed+=("$f")
            fi
        done <<< "$changed"
    fi

    if [[ ${#changed_not_listed[@]} -gt 0 ]]; then
        echo "工作区有改动但未记录到“当前批次工作集”："
        printf '%s\n' "${changed_not_listed[@]}" | sort -u | sed 's/.*/- `&`/'
        echo ""
    fi

    # 当前批次工作集中记录但当前工作区未体现（可能已提交/已还原）
    local listed_but_not_changed=()
    if [[ -n "$workset" ]]; then
        while IFS= read -r f; do
            [[ -z "$f" ]] && continue
            if [[ -z "$changed" ]] || ! grep -qxF "$f" <<< "$changed"; then
                listed_but_not_changed+=("$f")
            fi
        done <<< "$workset"
    fi

    if [[ ${#listed_but_not_changed[@]} -gt 0 ]]; then
        echo "“当前批次工作集”中记录但当前工作区未体现（可能已提交/已还原）："
        printf '%s\n' "${listed_but_not_changed[@]}" | sort -u | sed 's/.*/- `&`/'
        echo ""
    fi

    echo "下一步建议："
    echo "- 在对话中执行：/review  # 让助手先做双层 review，再整理 session 文档"
}

main "$@"
