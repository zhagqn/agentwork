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
BROWSER_CDP_PREFER="${BROWSER_CDP_PREFER:-1}"
BROWSER_CDP_TARGET="${BROWSER_CDP_TARGET:-9222}"
OS_NAME="$(uname -s)"

PROJECT_KEY="$(python3 - "${PROJECT_ROOT}" <<'PY'
import hashlib
import sys

print(hashlib.sha256(sys.argv[1].encode()).hexdigest()[:16])
PY
)"
DEFAULT_RUNTIME_ROOT="/tmp/agentwork-browser-$(id -u)"
SESSION="${AGENT_BROWSER_SESSION:-default}"
PREVIOUS_SOCKET_DIR="${BROWSER_TMP_ROOT}/agent-browser"
LEGACY_SOCKET_DIR="${BROWSER_TMP_ROOT}"

session_runtime_is_live() {
  local socket_dir="$1"
  local session="$2"

  [[ -S "${socket_dir}/${session}.sock" ]] || return 1

  ps eww -ax -o command= | awk \
    -v project_root="${PROJECT_ROOT}" \
    -v project_key="${PROJECT_KEY}" \
    -v socket_dir="${socket_dir}" \
    -v session="${session}" '
      function has_env(line, name, value,    needle, start, suffix) {
        needle = name "=" value
        start = index(line, needle)
        while (start > 0) {
          suffix = start + length(needle)
          if ((start == 1 || substr(line, start - 1, 1) == " ") &&
              (suffix > length(line) || substr(line, suffix, 1) == " ")) {
            return 1
          }
          line = substr(line, start + 1)
          start = index(line, needle)
        }
        return 0
      }

      {
        has_daemon = has_env($0, "AGENT_BROWSER_DAEMON", "1")
        has_project_marker = index($0, "AGENTWORK_BROWSER_PROJECT_KEY=") > 0
        marked_project = has_env($0, "AGENTWORK_BROWSER_PROJECT_KEY", project_key)
        legacy_project = !has_project_marker && has_env($0, "PWD", project_root)
        same_socket_dir = has_env($0, "AGENT_BROWSER_SOCKET_DIR", socket_dir)
        has_session = index($0, "AGENT_BROWSER_SESSION=") > 0
        same_session = has_env($0, "AGENT_BROWSER_SESSION", session)

        if (session == "default" && !has_session) {
          same_session = 1
        }

        if (has_daemon && (marked_project || legacy_project) && same_session && same_socket_dir) {
          found = 1
        }
      }
      END { exit found ? 0 : 1 }
    '
}

if [[ -n "${AGENT_BROWSER_SOCKET_DIR:-}" ]]; then
  SOCKET_DIR="${AGENT_BROWSER_SOCKET_DIR}"
elif session_runtime_is_live "${PREVIOUS_SOCKET_DIR}" "${SESSION}"; then
  SOCKET_DIR="${PREVIOUS_SOCKET_DIR}"
elif session_runtime_is_live "${LEGACY_SOCKET_DIR}" "${SESSION}"; then
  SOCKET_DIR="${LEGACY_SOCKET_DIR}"
else
  SOCKET_DIR="${DEFAULT_RUNTIME_ROOT}/${PROJECT_KEY}"
fi

if [[ "${SOCKET_DIR}" == "${DEFAULT_RUNTIME_ROOT}/${PROJECT_KEY}" ]]; then
  if [[ -e "${DEFAULT_RUNTIME_ROOT}" && \
    (! -d "${DEFAULT_RUNTIME_ROOT}" || -L "${DEFAULT_RUNTIME_ROOT}" || ! -O "${DEFAULT_RUNTIME_ROOT}") ]]; then
    echo "错误: browser runtime 根目录不安全: ${DEFAULT_RUNTIME_ROOT}" >&2
    exit 1
  fi

  mkdir -p "${DEFAULT_RUNTIME_ROOT}"
  chmod 700 "${DEFAULT_RUNTIME_ROOT}" 2>/dev/null || true
fi

if [[ -e "${SOCKET_DIR}" && \
  (! -d "${SOCKET_DIR}" || -L "${SOCKET_DIR}" || ! -O "${SOCKET_DIR}") ]]; then
  echo "错误: browser socket 目录不安全: ${SOCKET_DIR}" >&2
  exit 1
fi

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
export AGENTWORK_BROWSER_PROJECT_KEY="${PROJECT_KEY}"

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
  local session="${SESSION}"
  local pids

  if session_runtime_is_live "${SOCKET_DIR}" "${session}"; then
    return
  fi

  pids="$(
    ps eww -ax -o pid=,command= | awk \
      -v project_root="${PROJECT_ROOT}" \
      -v project_key="${PROJECT_KEY}" \
      -v socket_dir="${SOCKET_DIR}" \
      -v previous_socket_dir="${PREVIOUS_SOCKET_DIR}" \
      -v legacy_socket_dir="${LEGACY_SOCKET_DIR}" \
      -v session="${session}" '
        function has_env(line, name, value,    needle, start, suffix) {
          needle = name "=" value
          start = index(line, needle)
          while (start > 0) {
            suffix = start + length(needle)
            if ((start == 1 || substr(line, start - 1, 1) == " ") &&
                (suffix > length(line) || substr(line, suffix, 1) == " ")) {
              return 1
            }
            line = substr(line, start + 1)
            start = index(line, needle)
          }
          return 0
        }

        {
          has_daemon = has_env($0, "AGENT_BROWSER_DAEMON", "1")
          has_project_marker = index($0, "AGENTWORK_BROWSER_PROJECT_KEY=") > 0
          marked_project = has_env($0, "AGENTWORK_BROWSER_PROJECT_KEY", project_key)
          legacy_project = !has_project_marker && has_env($0, "PWD", project_root)
          has_session = index($0, "AGENT_BROWSER_SESSION=") > 0
          same_session = has_env($0, "AGENT_BROWSER_SESSION", session)
          same_socket_dir = has_env($0, "AGENT_BROWSER_SOCKET_DIR", socket_dir)
          previous_socket = has_env($0, "AGENT_BROWSER_SOCKET_DIR", previous_socket_dir)
          legacy_socket = has_env($0, "AGENT_BROWSER_SOCKET_DIR", legacy_socket_dir)
          legacy_xdg_only = has_env($0, "XDG_RUNTIME_DIR", legacy_socket_dir) &&
            index($0, "AGENT_BROWSER_SOCKET_DIR=") == 0

          if (session == "default" && !has_session) {
            same_session = 1
          }

          if (has_daemon && (marked_project || legacy_project) && same_session && (same_socket_dir || previous_socket || legacy_socket || legacy_xdg_only)) {
            print $1
          }
        }
      '
  )"

  if [[ -n "${pids}" ]]; then
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
  fi

  rm -f -- \
    "${SOCKET_DIR}/${session}.sock" \
    "${SOCKET_DIR}/${session}.pid" \
    "${SOCKET_DIR}/${session}.port" \
    "${SOCKET_DIR}/${session}.stream" \
    "${SOCKET_DIR}/${session}.target" \
    "${SOCKET_DIR}/${session}.version" \
    "${SOCKET_DIR}/${session}.engine" \
    "${SOCKET_DIR}/${session}.config" \
    "${PREVIOUS_SOCKET_DIR}/${session}.sock" \
    "${PREVIOUS_SOCKET_DIR}/${session}.pid" \
    "${PREVIOUS_SOCKET_DIR}/${session}.port" \
    "${PREVIOUS_SOCKET_DIR}/${session}.stream" \
    "${PREVIOUS_SOCKET_DIR}/${session}.target" \
    "${PREVIOUS_SOCKET_DIR}/${session}.version" \
    "${PREVIOUS_SOCKET_DIR}/${session}.engine" \
    "${PREVIOUS_SOCKET_DIR}/${session}.config" \
    "${LEGACY_SOCKET_DIR}/${session}.sock" \
    "${LEGACY_SOCKET_DIR}/${session}.pid" \
    "${LEGACY_SOCKET_DIR}/${session}.port" \
    "${LEGACY_SOCKET_DIR}/${session}.stream" \
    "${LEGACY_SOCKET_DIR}/${session}.target" \
    "${LEGACY_SOCKET_DIR}/${session}.version" \
    "${LEGACY_SOCKET_DIR}/${session}.engine" \
    "${LEGACY_SOCKET_DIR}/${session}.config"
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
  install | paths | skills | help | --help | -h | --version | -V)
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
    connect | install | paths | skills | help | --help | -h | --version | -V)
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
