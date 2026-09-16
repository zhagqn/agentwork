#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
if ! command -v pi >/dev/null 2>&1; then echo 'pi-mcp: pi CLI not found; install Pi first.' >&2; exit 1; fi
exec pi install -l --approve npm:pi-mcp-extension@1.5.0
