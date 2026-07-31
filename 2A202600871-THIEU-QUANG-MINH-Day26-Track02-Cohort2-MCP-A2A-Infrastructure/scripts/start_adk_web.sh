#!/usr/bin/env bash
# Khởi động ADK Web UI cho orchestrator
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# shellcheck source=_lab_env.sh
source "$ROOT/scripts/_lab_env.sh"
setup_lab_env "$ROOT"

AGENT_DIR="agents/orchestrator"
if [[ ! -f "$AGENT_DIR/agent.py" ]]; then
  echo "✗ Không tìm thấy $AGENT_DIR/agent.py"
  exit 1
fi

echo "→ ADK Web UI: http://localhost:8000"
echo "  Agent: $AGENT_DIR"
echo "  (Cần A2A servers :8001, :8002 và :8003 đang chạy)"

exec "$LAB_ADK" web "$AGENT_DIR" "$@"
