#!/usr/bin/env bash
# 本地门禁聚合入口 - 依次运行核心检查，全部跑完后汇总，有失败则 exit 1
#
# 无 CI，这些检查只有被实际执行才生效。此脚本只是把散落各处的四条命令
# 串起来，不引入新的检查逻辑；单独调试时仍可直接运行其中任意一条。
#
# 不使用 set -e：首个失败不应掩盖其余检查的结果。

set -uo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

failed=()

run() {
    local label="$1"
    shift
    printf '\n== %s ==\n' "$label"
    "$@" || failed+=("$label")
}

run 'unittest' python3 -m unittest discover -s .agentwork/tests -p 'test_*.py'
run 'workflow self-test' python3 .shared/scripts/agentwork-check.py self-test
run 'bootstrap render --check' python3 .agentwork/bootstrap/render_bootstrap.py --check

# Case 是可选的：没有 Case 时跳过而非报错。
if case_ref="$(python3 .shared/scripts/agentwork-check.py latest case 2>/dev/null)" && [[ -n "$case_ref" ]]; then
    run "case strict-flow ($case_ref)" \
        python3 .shared/scripts/agentwork-check.py case "$case_ref" --strict-flow
else
    printf '\n== case strict-flow ==\n(无可用 Case，跳过)\n'
fi

printf '\n== verify 汇总 ==\n'
if [[ ${#failed[@]} -gt 0 ]]; then
    printf '失败：%s\n' "${failed[*]}"
    exit 1
fi
echo '全部通过'
