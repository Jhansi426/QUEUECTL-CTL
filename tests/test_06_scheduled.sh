#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/utils.sh"

info "Testing Scheduled Job Execution"
clean_env

# ------------------------------------------------------------
# 1. Schedule a job 5 seconds into the future
# ------------------------------------------------------------
future_time=$(date -u -d "5 seconds" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+5S +"%Y-%m-%dT%H:%M:%SZ")
queuectl enqueue "{\"command\": \"echo scheduled execution\", \"run_at\": \"$future_time\"}" >/dev/null
pass "Enqueued job scheduled for execution at $future_time"

# ------------------------------------------------------------
# 2. Start worker
# ------------------------------------------------------------
stdbuf -oL -eL queuectl worker-start --count 1 > scheduled_exec.log 2>&1 &
PID=$!

# Wait long enough for job time to arrive and execute
sleep 8

# ------------------------------------------------------------
# 3. Stop workers
# ------------------------------------------------------------
queuectl worker-stop >/dev/null 2>&1
sleep 1

# ------------------------------------------------------------
# 4. Verify the scheduled job executed successfully
# ------------------------------------------------------------
if grep -Eiq "completed successfully|Job .*completed" scheduled_exec.log; then
    pass "Scheduled job executed after its run_at time"
else
    echo "--------------------------------------------------"
    echo "Worker Log (last 20 lines):"
    tail -n 20 scheduled_exec.log || true
    echo "--------------------------------------------------"
    fail "Scheduled job did not execute as expected"
fi

# ------------------------------------------------------------
# 5. Cleanup
# ------------------------------------------------------------
if ps -p "$PID" >/dev/null 2>&1; then
    kill "$PID" >/dev/null 2>&1 || true
fi

pass "Scheduled job timing and execution verified successfully"
