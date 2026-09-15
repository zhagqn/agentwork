#!/usr/bin/env bash
# 本地门禁聚合入口 - 依次运行核心检查，全部跑完后汇总，有失败则 exit 1
#
# 仅在 agentwork source repo 内可用：它检查的对象（.agentwork/tests、
# 渲染器）不随 bootstrap 分发到目标项目。目标项目误运行时明确报错退出，
# 不伪装成检查通过。
#
# 无 CI，这些检查只有被实际执行才生效。此脚本不引入新的检查逻辑，只把
# 散落各处的命令串起来；单独调试时仍可直接运行其中任意一条。
#
# 不使用 set -e：首个失败不应掩盖其余检查的结果。
# 不使用数组累积失败项：bash 3.2 下 set -u 与空数组展开行为不一致。

set -uo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

CHECKER='.shared/scripts/agentwork-check.py'
RENDERER='.agentwork/bootstrap/render_bootstrap.py'
TESTS='.agentwork/tests'

for required in "$CHECKER" "$RENDERER" "$TESTS"; do
    if [[ ! -e "$required" ]]; then
        echo "verify.sh 只能在 agentwork source repo 内运行：缺少 $required" >&2
        echo '目标项目无需运行本入口；核心工作流检查由 source repo 负责。' >&2
        exit 2
    fi
done

failures=''

note_failure() {
    if [[ -z "$failures" ]]; then
        failures="$1"
    else
        failures="$failures; $1"
    fi
}

run() {
    local label="$1"
    shift
    printf '\n== %s ==\n' "$label"
    "$@" || note_failure "$label"
}

run 'unittest' python3 -m unittest discover -s "$TESTS" -p 'test_*.py'
run 'workflow self-test' python3 "$CHECKER" self-test
run 'bootstrap render --check' python3 "$RENDERER" --check

# Case 是可选的，但只有「确实没有 Case」才跳过。
# latest 的失败必须分辨：无 Case 时 stdout 为 missing_latest:，
# 同戳歧义或 checker 执行失败一律计入失败，不得静默跳过成假绿。
printf '\n== case strict-flow ==\n'
if case_ref="$(python3 "$CHECKER" latest case)"; then
    if [[ -n "$case_ref" ]]; then
        python3 "$CHECKER" case "$case_ref" --strict-flow \
            || note_failure "case strict-flow ($case_ref)"
    else
        note_failure 'latest case 返回空值'
        echo 'latest case 成功退出但未输出路径' >&2
    fi
elif [[ "$case_ref" == missing_latest:* ]]; then
    echo '(无可用 Case，跳过)'
else
    echo 'latest case 解析失败，无法确定要检查的 Case（见上方 stderr）' >&2
    note_failure 'latest case 解析'
fi

printf '\n== verify 汇总 ==\n'
if [[ -n "$failures" ]]; then
    echo "失败：$failures"
    exit 1
fi
echo '全部通过'
