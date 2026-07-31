#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source "$ROOT/scripts/_lab_env.sh"
setup_lab_env "$ROOT"
export PYTHONPATH="${PYTHONPATH:-}:$ROOT"
echo "→ Search agent: http://localhost:8001/.well-known/agent-card.json"
exec "${LAB_UVICORN[@]}" agents.search_agent.agent:a2a_app --host localhost --port 8001 --reload
