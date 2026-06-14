#!/bin/bash
# start_dashboard.sh
# Launch the Wi-Fi Monitor web dashboard.
# Host, port, debug mode all read from config/default.json.

set -euo pipefail

cd "$(dirname "$0")/.."

if [ -z "${VIRTUAL_ENV:-}" ] && [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

python -m wifi_monitor.main dashboard "$@"