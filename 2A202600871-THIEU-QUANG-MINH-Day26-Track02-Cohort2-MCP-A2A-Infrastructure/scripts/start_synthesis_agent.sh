#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source "$ROOT/scripts/_lab_env.sh"
setup_lab_env "$ROOT"
echo "→ Synthesis agent: http://localhost:8003/.well-known/agent-card.json"
exec "${LAB_UVICORN[@]}" agents.synthesis_agent.agent:a2a_app --host localhost --port 8003 --reload
