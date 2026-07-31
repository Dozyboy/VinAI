#!/usr/bin/env bash
# Dừng A2A specialist servers
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

for name in search_agent database_agent synthesis_agent; do
  pid_file="logs/${name}.pid"
  if [[ -f "$pid_file" ]]; then
    pid=$(cat "$pid_file")
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" && echo "✓ Đã dừng $name (pid $pid)"
    fi
    rm -f "$pid_file"
  fi
done

# Fallback: kill theo cổng
for port in 8001 8002 8003; do
  pids=$(lsof -ti :"$port" 2>/dev/null || true)
  if [[ -n "$pids" ]]; then
    echo "$pids" | xargs kill 2>/dev/null && echo "✓ Đã giải phóng cổng $port" || true
  fi
done
