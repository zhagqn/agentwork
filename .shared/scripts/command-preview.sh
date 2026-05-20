#!/usr/bin/env bash

set -u

usage() {
  cat <<'EOF'
Usage:
  .shared/scripts/command-preview.sh [--max-bytes N] [--head-bytes N] [--tail-bytes N] -- COMMAND [ARG...]

Default strategy:
  - capture stdout+stderr
  - preserve the command exit status
  - print full output when total bytes <= max-bytes
  - otherwise print head/tail samples within the byte budget
EOF
}

require_int() {
  local value="$1"
  local name="$2"
  if [[ ! "$value" =~ ^[0-9]+$ ]]; then
    printf 'command-preview.sh: %s must be a non-negative integer\n' "$name" >&2
    exit 2
  fi
}

max_bytes=4000
head_bytes=''
tail_bytes=''

while (($#)); do
  case "$1" in
    --max-bytes)
      shift
      if (($# == 0)); then
        printf 'command-preview.sh: missing value for --max-bytes\n' >&2
        exit 2
      fi
      require_int "$1" '--max-bytes'
      max_bytes="$1"
      ;;
    --head-bytes)
      shift
      if (($# == 0)); then
        printf 'command-preview.sh: missing value for --head-bytes\n' >&2
        exit 2
      fi
      require_int "$1" '--head-bytes'
      head_bytes="$1"
      ;;
    --tail-bytes)
      shift
      if (($# == 0)); then
        printf 'command-preview.sh: missing value for --tail-bytes\n' >&2
        exit 2
      fi
      require_int "$1" '--tail-bytes'
      tail_bytes="$1"
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    *)
      printf 'command-preview.sh: expected -- before COMMAND, got %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if (($# == 0)); then
  usage >&2
  exit 2
fi

if [[ -z "$head_bytes" && -z "$tail_bytes" ]]; then
  head_bytes=$((max_bytes / 2))
  tail_bytes=$((max_bytes - head_bytes))
elif [[ -z "$head_bytes" ]]; then
  if ((tail_bytes > max_bytes)); then
    printf 'command-preview.sh: --tail-bytes cannot exceed --max-bytes\n' >&2
    exit 2
  fi
  head_bytes=$((max_bytes - tail_bytes))
elif [[ -z "$tail_bytes" ]]; then
  if ((head_bytes > max_bytes)); then
    printf 'command-preview.sh: --head-bytes cannot exceed --max-bytes\n' >&2
    exit 2
  fi
  tail_bytes=$((max_bytes - head_bytes))
fi

if ((head_bytes + tail_bytes > max_bytes)); then
  printf 'command-preview.sh: head/tail bytes exceed max preview budget\n' >&2
  exit 2
fi

tmp_output="$(mktemp "${TMPDIR:-/tmp}/command-preview.XXXXXX")"
trap 'rm -f "$tmp_output"' EXIT

"$@" >"$tmp_output" 2>&1
status=$?

bytes="$(wc -c <"$tmp_output" | tr -d '[:space:]')"
lines="$(wc -l <"$tmp_output" | tr -d '[:space:]')"

if ((bytes <= max_bytes)); then
  printf '[command-preview] exit=%s bytes=%s lines=%s mode=full\n' "$status" "$bytes" "$lines"
  cat "$tmp_output"
  exit "$status"
fi

omitted_bytes=$((bytes - head_bytes - tail_bytes))
printf '[command-preview] exit=%s bytes=%s lines=%s mode=head-tail omitted_bytes=%s\n' \
  "$status" "$bytes" "$lines" "$omitted_bytes"
printf -- '--- head %s bytes ---\n' "$head_bytes"
head -c "$head_bytes" "$tmp_output"
printf '\n'
printf -- '--- tail %s bytes ---\n' "$tail_bytes"
tail -c "$tail_bytes" "$tmp_output"
printf '\n'

exit "$status"
