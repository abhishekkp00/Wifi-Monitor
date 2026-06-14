#!/bin/bash
# run_suite.sh — All defaults from config. Pass args to override.
# Usage: ./scripts/run_suite.sh [host] [server] [count] [duration] [protocol]

set -euo pipefail

cd "$(dirname "$0")/.."

[ -z "${VIRTUAL_ENV:-}" ] && [ -f "venv/bin/activate" ] && source venv/bin/activate

HOST="${1:-}"; SERVER="${2:-}"; COUNT="${3:-}"; DURATION="${4:-}"; PROTOCOL="${5:-}"

H=""; S=""; C=""; D=""; P=""
[ -n "$HOST" ]     && H="--host $HOST"
[ -n "$SERVER" ]   && S="--server $SERVER"
[ -n "$COUNT" ]    && C="--count $COUNT"
[ -n "$DURATION" ] && D="--duration $DURATION"
[ -n "$PROTOCOL" ] && P="--protocol $PROTOCOL"

LOG_DIR="$(python -c "from wifi_monitor.config import get_cfg; print(get_cfg('logging','log_dir','data/logs'))")"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/suite_$(date +%Y%m%d_%H%M%S).log"

{
  echo "=== Suite Run: $(date) ==="
  python -m wifi_monitor.main wifi-info
  # shellcheck disable=SC2086
  python -m wifi_monitor.main ping $H $C
  # shellcheck disable=SC2086
  python -m wifi_monitor.main throughput $S $D $P
  python -m wifi_monitor.main report
  python -m wifi_monitor.main export --format csv
  echo "=== Done: $(date) ==="
} 2>&1 | tee "$LOG"

echo "Log → $LOG"