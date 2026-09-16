#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
command -v pi >/dev/null 2>&1 && echo 'pi: available' || echo 'pi: missing'
[[ -f .pi/mcp.json ]] && echo 'project mcp.json: present (not validated)' || echo 'project mcp.json: absent (global servers may still apply)'
[[ -f .pi/npm/node_modules/pi-mcp-extension/package.json ]] && echo 'project extension files: present (registration and loading not verified)' || echo 'project extension files: absent'
