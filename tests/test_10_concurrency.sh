#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/utils.sh"

info "Testing Multi-Worker Concurrency and Parallel Job Execution"
clean_env

# ------------------------------------------------------------
# Enqueue multiple jobs
# ------------------------------------------------------------
info "Enqueuing 5 jobs for concurrency test..."
for i in {1..5}; do
  queuectl enqueue "{\"command\": \"echo job $i\"}" >/dev/null
done

# ------------------------------------------------------------
# Start multiple workers simultaneously
# ------------------------------------------------------------
info "Starting 3 concurrent workers..."
stdbuf -oL -eL queuectl worker-start --count 3 > concurrent.log 2>&1 &
PID=$!

sleep 6  # allow processing
queuectl worker-stop >/dev/null 2>&1 || true
sleep 1

# ------------------------------------------------------------
# Verify all jobs completed
# ------------------------------------------------------------
completed_jobs=$(grep -ci "completed successfully" concurrent.log || true)
if [[ "$completed_jobs" -ge 5 ]]; then
    pass "All 5 jobs processed successfully by multiple workers"
else
    echo "--------------------------------------------------"
    echo "Worker Log (last 25 lines):"
    tail -n 25 concurrent.log || true
    echo "--------------------------------------------------"
    fail "Not all jobs were completed (found $completed_jobs/5 completions)"
fi

# ------------------------------------------------------------
# Improved concurrency detection logic
# ------------------------------------------------------------
# Count how many jobs finished per timestamp second
concurrency_hint=$(grep -Eo '^[0-9]{2}:[0-9]{2}:[0-9]{2}' concurrent.log | sort | uniq -c | awk '$1 >= 2 {print}' | wc -l)

if [[ "$concurrency_hint" -ge 1 ]]; then
    pass "Detected overlapping job completions — concurrency confirmed"
else
    echo "--------------------------------------------------"
    echo "Worker Log (last 25 lines):"
    tail -n 25 concurrent.log || true
    echo "--------------------------------------------------"
    fail "No evidence of overlapping job completions — concurrency not confirmed"
fi

# ------------------------------------------------------------
# Cleanup background process
# ------------------------------------------------------------
if ps -p "$PID" >/dev/null 2>&1; then
    kill "$PID" >/dev/null 2>&1 || true
fi

pass "Multi-worker concurrency test completed successfully"
