#!/usr/bin/env bash
set -euo pipefail

# Android 通用回退方案：使用 shell + pull 替代 exec-out，提升老设备兼容性
# 用法：
#   .shared/scripts/android-shell-pull-fallback.sh [device_id] [output_root]
# 示例：
#   .shared/scripts/android-shell-pull-fallback.sh emulator-5554
#   .shared/scripts/android-shell-pull-fallback.sh 192.168.31.201:5555 .tmp/android-test/reports

OUTPUT_ROOT="${2:-.tmp/android-test/reports}"
REMOTE_DIR="${ANDROID_REMOTE_TMP_DIR:-/sdcard/Download/mcp-fallback}"
ARTIFACT_PREFIX="${ANDROID_ARTIFACT_PREFIX:-android}"

resolve_device_id() {
    if [ -n "${1:-}" ]; then
        echo "$1"
        return 0
    fi

    if [ -n "${ANDROID_DEVICE_ID:-}" ]; then
        echo "$ANDROID_DEVICE_ID"
        return 0
    fi

    adb devices | awk 'NR > 1 && $2 == "device" { print $1; exit }'
}

if ! command -v adb >/dev/null 2>&1; then
    echo "error: adb not found in PATH" >&2
    exit 1
fi

DEVICE_ID="$(resolve_device_id "${1:-}")"
if [ -z "$DEVICE_ID" ]; then
    echo "error: no available android device, please pass <android-device-id> or set ANDROID_DEVICE_ID" >&2
    exit 1
fi

RUN_DIR="${OUTPUT_ROOT}/${ARTIFACT_PREFIX}-shell-pull-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR"

adb -s "$DEVICE_ID" get-state > "$RUN_DIR/device-state.txt"
adb -s "$DEVICE_ID" wait-for-device
adb -s "$DEVICE_ID" shell mkdir -p "$REMOTE_DIR"

step_ok() {
    local name="$1"
    shift
    if "$@" >"$RUN_DIR/${name}.out" 2>"$RUN_DIR/${name}.err"; then
        echo pass > "$RUN_DIR/${name}.status"
    else
        echo fail > "$RUN_DIR/${name}.status"
        return 1
    fi
}

FAILS=()

# Stage 1: 基础 UI 采集（HOME + dump + screenshot）
step_ok stage1-home adb -s "$DEVICE_ID" shell input keyevent HOME || FAILS+=("stage1-home")
step_ok stage1-ui-dump adb -s "$DEVICE_ID" shell uiautomator dump "$REMOTE_DIR/stage1-window_dump.xml" || FAILS+=("stage1-ui-dump")
step_ok stage1-ui-pull adb -s "$DEVICE_ID" pull "$REMOTE_DIR/stage1-window_dump.xml" "$RUN_DIR/stage1-window_dump.xml" || FAILS+=("stage1-ui-pull")
step_ok stage1-shot-dump adb -s "$DEVICE_ID" shell screencap -p "$REMOTE_DIR/stage1.png" || FAILS+=("stage1-shot-dump")
step_ok stage1-shot-pull adb -s "$DEVICE_ID" pull "$REMOTE_DIR/stage1.png" "$RUN_DIR/stage1.png" || FAILS+=("stage1-shot-pull")

# Stage 2: 带日志的联动采集（清日志 + HOME + dump + screenshot + logcat）
step_ok stage2-prep-logcat-clear adb -s "$DEVICE_ID" logcat -c || FAILS+=("stage2-prep-logcat-clear")
step_ok stage2-home adb -s "$DEVICE_ID" shell input keyevent HOME || FAILS+=("stage2-home")
step_ok stage2-ui-dump adb -s "$DEVICE_ID" shell uiautomator dump "$REMOTE_DIR/stage2-window_dump.xml" || FAILS+=("stage2-ui-dump")
step_ok stage2-ui-pull adb -s "$DEVICE_ID" pull "$REMOTE_DIR/stage2-window_dump.xml" "$RUN_DIR/stage2-window_dump.xml" || FAILS+=("stage2-ui-pull")
step_ok stage2-shot-dump adb -s "$DEVICE_ID" shell screencap -p "$REMOTE_DIR/stage2.png" || FAILS+=("stage2-shot-dump")
step_ok stage2-shot-pull adb -s "$DEVICE_ID" pull "$REMOTE_DIR/stage2.png" "$RUN_DIR/stage2.png" || FAILS+=("stage2-shot-pull")
adb -s "$DEVICE_ID" logcat -d > "$RUN_DIR/stage2-logcat.log" 2> "$RUN_DIR/stage2-logcat.err" || FAILS+=("stage2-logcat")

PASS_COUNT=$(find "$RUN_DIR" -name '*.status' -exec cat {} \; | awk '$0 == "pass" { c++ } END { print c + 0 }')
FAIL_COUNT=$(find "$RUN_DIR" -name '*.status' -exec cat {} \; | awk '$0 == "fail" { c++ } END { print c + 0 }')
TOTAL=$((PASS_COUNT + FAIL_COUNT))
SUCCESS_RATE=$(python3 - <<PY
p=int("$PASS_COUNT")
t=int("$TOTAL")
print(f"{(p/t*100):.1f}" if t else "0.0")
PY
)

{
    echo "run_dir=$RUN_DIR"
    echo "device=$DEVICE_ID"
    echo "mode=shell+pull"
    echo "total_steps=$TOTAL"
    echo "pass_steps=$PASS_COUNT"
    echo "fail_steps=$FAIL_COUNT"
    echo "success_rate=${SUCCESS_RATE}%"
    if [ ${#FAILS[@]} -gt 0 ]; then
        echo "failed_list=$(IFS=';'; echo "${FAILS[*]}")"
    else
        echo "failed_list="
    fi
} | tee "$RUN_DIR/summary.txt"

echo "$RUN_DIR"
