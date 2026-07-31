#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source "$ROOT/scripts/_lab_env.sh"
setup_lab_env "$ROOT"
echo "→ Database agent: http://localhost:8002/.well-known/agent-card.json"
exec "${LAB_UVICORN[@]}" agents.database_agent.agent:a2a_app --host localhost --port 8002 --reload
