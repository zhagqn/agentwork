#!/usr/bin/env bash
set -euo pipefail

URL="${1:-${FIGMA_MCP_URL:-http://127.0.0.1:3845/mcp}}"
TIMEOUT_SEC="${FIGMA_MCP_CHECK_TIMEOUT_SEC:-2}"

if ! command -v curl >/dev/null 2>&1; then
  echo "[figma-mcp] 缺少 curl，无法做本地 MCP 连通性检查" >&2
  exit 1
fi

HTTP_CODE="$(curl -sS -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT_SEC" "$URL" || true)"

if [ -z "$HTTP_CODE" ] || [ "$HTTP_CODE" = "000" ]; then
  echo "[figma-mcp] check: failed" >&2
  echo "[figma-mcp] 无法连接: $URL" >&2
  echo "[figma-mcp] 请确认 Figma Desktop MCP 已启动，并检查端口/URL" >&2
  exit 1
fi

if [[ "$HTTP_CODE" == 5* ]]; then
  echo "[figma-mcp] check: failed" >&2
  echo "[figma-mcp] 服务已响应但状态异常: $HTTP_CODE" >&2
  exit 1
fi

echo "[figma-mcp] check: reachable"
echo "[figma-mcp] url: $URL"
echo "[figma-mcp] status: $HTTP_CODE"

if [ "$HTTP_CODE" = "400" ] || [ "$HTTP_CODE" = "404" ] || [ "$HTTP_CODE" = "405" ]; then
  echo "[figma-mcp] 提示: 该状态码通常表示服务在线但请求路径/方法不匹配" >&2
fi
