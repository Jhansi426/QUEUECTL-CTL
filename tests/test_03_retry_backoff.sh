#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/utils.sh"

info "Testing Retry Mechanism and Exponential Backoff Handling"
clean_env

# ------------------------------------------------------------
# 1. Configure retry parameters
# ------------------------------------------------------------
queuectl config-set max_retries 2 >/dev/null || fail "Failed to update max_retries"
queuectl config-set backoff_base 2 >/dev/null || fail "Failed to update backoff_base"
pass "Configuration updated successfully"

# ------------------------------------------------------------
# 2. Enqueue a deliberately failing job
# ------------------------------------------------------------
queuectl enqueue '{"command": "invalid_command"}' >/dev/null || fail "Failed to enqueue invalid job"
pass "Invalid job enqueued for retry test"

# ------------------------------------------------------------
# 3. Start worker and observe retry + DLQ transitions
# ------------------------------------------------------------
stdbuf -oL -eL queuectl worker-start --count 1 > retry.log 2>&1 &
PID=$!
sleep 8  # allow time for retries
queuectl worker-stop >/dev/null 2>&1
sleep 1

# ------------------------------------------------------------
# 4. Validate behavior
# ------------------------------------------------------------
if grep -Eiq "moved to DLQ|Dead Letter Queue|status='dead'" retry.log; then
    pass "Retry + DLQ handling verified successfully"
else
    echo "--------------------------------------------------"
    echo "Worker Log (last 25 lines):"
    echo "--------------------------------------------------"
    tail -n 25 retry.log || true
    echo "--------------------------------------------------"
    fail "Retry or DLQ flow failed (no DLQ evidence found)"
fi

# ------------------------------------------------------------
# 5. Cleanup
# ------------------------------------------------------------
if ps -p "$PID" >/dev/null 2>&1; then
    kill "$PID" >/dev/null 2>&1 || true
fi

pass "Retry and exponential backoff test completed successfully"
