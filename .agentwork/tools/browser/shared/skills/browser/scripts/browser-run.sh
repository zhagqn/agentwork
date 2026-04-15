#!/usr/bin/env bash
set -euo pipefail

if ! command -v agent-browser >/dev/null 2>&1; then
  echo "错误: 未找到 agent-browser，请先安装。" >&2
  exit 127
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

BROWSER_TMP_ROOT="${BROWSER_TMP_ROOT:-${PROJECT_ROOT}/.tmp/browser}"
PROFILE_DIR="${BROWSER_TMP_ROOT}/profile"
DOWNLOAD_DIR="${BROWSER_TMP_ROOT}/downloads"
SOCKET_DIR="${BROWSER_TMP_ROOT}/agent-browser"
BROWSER_CDP_PREFER="${BROWSER_CDP_PREFER:-1}"
BROWSER_CDP_TARGET="${BROWSER_CDP_TARGET:-9222}"
OS_NAME="$(uname -s)"

case "${OS_NAME}" in
  Darwin)
    BROWSER_EXPORT_TMPDIR="${BROWSER_EXPORT_TMPDIR:-0}"
    BROWSER_EXPORT_XDG_RUNTIME_DIR="${BROWSER_EXPORT_XDG_RUNTIME_DIR:-0}"
    ;;
  *)
    BROWSER_EXPORT_TMPDIR="${BROWSER_EXPORT_TMPDIR:-1}"
    BROWSER_EXPORT_XDG_RUNTIME_DIR="${BROWSER_EXPORT_XDG_RUNTIME_DIR:-1}"
    ;;
esac

mkdir -p \
  "${BROWSER_TMP_ROOT}" \
  "${PROFILE_DIR}" \
  "${DOWNLOAD_DIR}" \
  "${SOCKET_DIR}"

chmod 700 "${SOCKET_DIR}" 2>/dev/null || true

export AGENT_BROWSER_SOCKET_DIR="${SOCKET_DIR}"
export AGENT_BROWSER_DOWNLOAD_PATH="${AGENT_BROWSER_DOWNLOAD_PATH:-${DOWNLOAD_DIR}}"

# macOS 下强改 XDG/TMPDIR 会把 Playwright 内部 runtime/socket 也带到项目目录，
# 这会放大 agent-browser 的 daemon/socket 冲突概率；默认只显式固定 agent-browser 自己的 socket 目录。
if [[ "${BROWSER_EXPORT_TMPDIR}" == "1" ]]; then
  export TMPDIR="${BROWSER_TMP_ROOT}"
fi

if [[ "${BROWSER_EXPORT_XDG_RUNTIME_DIR}" == "1" ]]; then
  export XDG_RUNTIME_DIR="${BROWSER_TMP_ROOT}"
fi

now() {
  date '+%Y%m%d-%H%M%S'
}

cleanup_orphaned_daemons() {
  local session="${AGENT_BROWSER_SESSION:-default}"
  local current_socket="${SOCKET_DIR}/${session}.sock"
  local legacy_socket="${BROWSER_TMP_ROOT}/${session}.sock"
  local pids

  if [[ -S "${current_socket}" || -S "${legacy_socket}" ]]; then
    return
  fi

  pids="$(
    ps eww -ax -o pid=,command= | awk \
      -v project_root="${PROJECT_ROOT}" \
      -v socket_dir="${SOCKET_DIR}" \
      -v browser_tmp_root="${BROWSER_TMP_ROOT}" '
        {
          has_daemon = index($0, "AGENT_BROWSER_DAEMON=1")
          in_project = index($0, "PWD=" project_root)
          same_socket_dir = index($0, "AGENT_BROWSER_SOCKET_DIR=" socket_dir)
          legacy_socket_dir = index($0, "AGENT_BROWSER_SOCKET_DIR=" browser_tmp_root)
          legacy_xdg_only = index($0, "XDG_RUNTIME_DIR=" browser_tmp_root) && !index($0, "AGENT_BROWSER_SOCKET_DIR=")

          if (has_daemon && in_project && (same_socket_dir || legacy_socket_dir || legacy_xdg_only)) {
          print $1
          }
        }
      '
  )"

  if [[ -z "${pids}" ]]; then
    return
  fi

  while IFS= read -r pid; do
    [[ -n "${pid}" ]] || continue
    kill "${pid}" 2>/dev/null || true
  done <<< "${pids}"

  sleep 0.2

  while IFS= read -r pid; do
    [[ -n "${pid}" ]] || continue
    if kill -0 "${pid}" 2>/dev/null; then
      kill -9 "${pid}" 2>/dev/null || true
    fi
  done <<< "${pids}"

  rm -f -- \
    "${SOCKET_DIR}/${session}.sock" \
    "${SOCKET_DIR}/${session}.pid" \
    "${SOCKET_DIR}/${session}.port" \
    "${SOCKET_DIR}/${session}.stream" \
    "${legacy_socket}" \
    "${BROWSER_TMP_ROOT}/${session}.pid" \
    "${BROWSER_TMP_ROOT}/${session}.port" \
    "${BROWSER_TMP_ROOT}/${session}.stream"
}

if [[ $# -eq 0 ]]; then
  cat <<'EOF'
用法:
  .shared/skills/browser/scripts/browser-run.sh <agent-browser-command> [args...]

默认目录:
  .tmp/browser
EOF
  exit 1
fi

if [[ "$1" == "paths" ]]; then
  cat <<EOF
BROWSER_TMP_ROOT=${BROWSER_TMP_ROOT}
BROWSER_CDP_PREFER=${BROWSER_CDP_PREFER}
BROWSER_CDP_TARGET=${BROWSER_CDP_TARGET}
PROFILE_DIR=${PROFILE_DIR}
DOWNLOAD_DIR=${DOWNLOAD_DIR}
SOCKET_DIR=${SOCKET_DIR}
AGENT_BROWSER_SOCKET_DIR=${AGENT_BROWSER_SOCKET_DIR}
AGENT_BROWSER_DOWNLOAD_PATH=${AGENT_BROWSER_DOWNLOAD_PATH}
BROWSER_EXPORT_TMPDIR=${BROWSER_EXPORT_TMPDIR}
BROWSER_EXPORT_XDG_RUNTIME_DIR=${BROWSER_EXPORT_XDG_RUNTIME_DIR}
TMPDIR=${TMPDIR:-}
XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-}
EOF
  exit 0
fi

if [[ "$1" == "screenshot" ]]; then
  if [[ $# -lt 2 || "$2" == -* ]]; then
    set -- "screenshot" "${BROWSER_TMP_ROOT}/screenshot-$(now).png" "${@:2}"
  fi
fi

if [[ "$1" == "pdf" ]]; then
  if [[ $# -lt 2 || "$2" == -* ]]; then
    set -- "pdf" "${BROWSER_TMP_ROOT}/page-$(now).pdf" "${@:2}"
  fi
fi

if [[ "$1" == "record" && "${2-}" == "start" ]]; then
  if [[ -z "${3-}" || "${3-}" == -* ]]; then
    set -- "record" "start" "${BROWSER_TMP_ROOT}/record-$(now).webm" "${@:3}"
  fi
fi

if [[ "$1" == "trace" && "${2-}" == "stop" ]]; then
  if [[ -z "${3-}" || "${3-}" == -* ]]; then
    set -- "trace" "stop" "${BROWSER_TMP_ROOT}/trace-$(now).zip" "${@:3}"
  fi
fi

if [[ "$1" == "state" && "${2-}" == "save" ]]; then
  if [[ -z "${3-}" || "${3-}" == -* ]]; then
    set -- "state" "save" "${BROWSER_TMP_ROOT}/state-$(now).json" "${@:3}"
  fi
fi

has_explicit_cdp=0
for arg in "$@"; do
  if [[ "$arg" == "--cdp" ]]; then
    has_explicit_cdp=1
    break
  fi
done

case "$1" in
  install | paths | help | --help | -h | --version | -V)
    ;;
  *)
    cleanup_orphaned_daemons
    ;;
esac

resolve_cdp_target() {
  local target="$1"
  if [[ "$target" =~ ^[0-9]+$ ]]; then
    # 端口模式下优先解析 127.0.0.1 的 websocket 地址，避免 localhost 解析差异。
    python3 - "$target" <<'PY'
import json
import sys
import urllib.request

port = sys.argv[1]
url = f"http://127.0.0.1:{port}/json/version"
with urllib.request.urlopen(url, timeout=1.2) as resp:
    data = json.load(resp)
print(data["webSocketDebuggerUrl"])
PY
    return $?
  fi

  printf '%s\n' "$target"
}

if [[ "${has_explicit_cdp}" == "1" ]]; then
  exec env -u AGENT_BROWSER_PROFILE agent-browser "$@"
fi

if [[ "${BROWSER_CDP_PREFER}" == "1" ]]; then
  case "$1" in
    connect | install | paths | help | --help | -h | --version | -V)
      ;;
    *)
      # 临时测试默认优先尝试 CDP，失败时自动回退到本地模式。
      if cdp_endpoint="$(resolve_cdp_target "${BROWSER_CDP_TARGET}" 2>/dev/null)"; then
        exec env -u AGENT_BROWSER_PROFILE agent-browser --cdp "${cdp_endpoint}" "$@"
      fi
      ;;
  esac
fi

if [[ "$1" == "connect" ]]; then
  exec env -u AGENT_BROWSER_PROFILE agent-browser "$@"
fi

exec env AGENT_BROWSER_PROFILE="${AGENT_BROWSER_PROFILE:-${PROFILE_DIR}}" agent-browser "$@"
