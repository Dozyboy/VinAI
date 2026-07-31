#!/usr/bin/env sh
set -eu

: "${PORT:=8000}"
: "${MCP_PORT:=8001}"
: "${MCP_CLINICAL_URL:=http://127.0.0.1:${MCP_PORT}/mcp}"
export MCP_CLINICAL_URL

python src/agents/mcp/server.py &
MCP_PID="$!"

python -m uvicorn src.main:app --host 0.0.0.0 --port "$PORT" &
API_PID="$!"

cleanup() {
    kill "$API_PID" 2>/dev/null || true
    kill "$MCP_PID" 2>/dev/null || true
    wait "$API_PID" 2>/dev/null || true
    wait "$MCP_PID" 2>/dev/null || true
}

trap cleanup INT TERM EXIT

while true; do
    if ! kill -0 "$MCP_PID" 2>/dev/null; then
        wait "$MCP_PID"
        exit "$?"
    fi

    if ! kill -0 "$API_PID" 2>/dev/null; then
        wait "$API_PID"
        exit "$?"
    fi

    sleep 2
done
