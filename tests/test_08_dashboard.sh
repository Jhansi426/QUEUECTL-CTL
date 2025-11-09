#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/utils.sh"

info "Testing Dashboard HTTP Server and Template Rendering"
clean_env

# ------------------------------------------------------------
# Start the dashboard in background
# ------------------------------------------------------------
python web/dashboard.py > dashboard.log 2>&1 &
PID=$!
sleep 4  # give Flask enough time to start

# ------------------------------------------------------------
# Health check
# ------------------------------------------------------------
if curl -fs http://127.0.0.1:5000 | grep -q "QueueCTL Dashboard"; then
    pass "Dashboard started successfully and rendered expected HTML"
else
    echo "--------------------------------------------------"
    echo "Dashboard Log (last 20 lines):"
    echo "--------------------------------------------------"
    tail -n 20 dashboard.log || true
    echo "--------------------------------------------------"
    fail "Dashboard failed to start or respond correctly"
fi

# ------------------------------------------------------------
# Cleanup
# ------------------------------------------------------------
kill "$PID" >/dev/null 2>&1 || true
rm -f dashboard.log
pass "Dashboard process stopped cleanly"
