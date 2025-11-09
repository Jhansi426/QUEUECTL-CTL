#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/utils.sh"

info "Testing Worker Start, Processing, and Graceful Shutdown"
clean_env

# ------------------------------------------------------------
# 1. Enqueue a test job
# ------------------------------------------------------------
info "Enqueuing simple worker job..."
queuectl enqueue '{"command": "echo from worker"}' >/dev/null || fail "Failed to enqueue job"

# ------------------------------------------------------------
# 2. Start worker asynchronously
# ------------------------------------------------------------
info "Starting a single worker thread..."
stdbuf -oL -eL queuectl worker-start --count 1 > worker.log 2>&1 &
WORKER_PID=$!
sleep 5

# ------------------------------------------------------------
# 3. Stop all workers
# ------------------------------------------------------------
info "Stopping all workers gracefully..."
queuectl worker-stop >/dev/null 2>&1 || fail "Failed to send stop signal"
sleep 1

# ------------------------------------------------------------
# 4. Validate output
# ------------------------------------------------------------
if grep -Eiq "Job .*completed successfully" worker.log; then
    pass "Worker successfully processed the enqueued job"
else
    echo "--------------------------------------------------"
    echo "Worker Log (last 25 lines):"
    echo "--------------------------------------------------"
    tail -n 25 worker.log || true
    echo "--------------------------------------------------"
    fail "Worker did not complete job execution"
fi

# ------------------------------------------------------------
# 5. Cleanup background worker
# ------------------------------------------------------------
if ps -p "$WORKER_PID" >/dev/null 2>&1; then
    kill "$WORKER_PID" >/dev/null 2>&1 || true
fi

pass "Worker lifecycle (start → process → stop) verified successfully"
