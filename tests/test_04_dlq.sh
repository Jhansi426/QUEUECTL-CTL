#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/utils.sh"

info "Testing Dead Letter Queue (DLQ) Management"
clean_env

# ------------------------------------------------------------
# 1. Enqueue a deliberately failing job
# ------------------------------------------------------------
queuectl enqueue '{"command": "nonexistent"}' >/dev/null || fail "Failed to enqueue bad job"
pass "Enqueued failing job for DLQ test"

# ------------------------------------------------------------
# 2. Start worker and wait for retries to complete
# ------------------------------------------------------------
stdbuf -oL -eL queuectl worker-start --count 1 > dlq_test.log 2>&1 &
PID=$!
sleep 15
queuectl worker-stop >/dev/null 2>&1
sleep 1

# ------------------------------------------------------------
# 3. Confirm job is in DLQ
# ------------------------------------------------------------
if queuectl dlq-list | grep -q "nonexistent"; then
    pass "Job successfully moved to DLQ"
else
    echo "--------------------------------------------------"
    echo "DLQ contents:"
    queuectl dlq-list || true
    echo "--------------------------------------------------"
    fail "Job missing in DLQ after retries"
fi

# ------------------------------------------------------------
# 4. Extract job ID directly using Python
# ------------------------------------------------------------
job_id=$(python - <<'PYCODE'
import sqlite3, json
try:
    con = sqlite3.connect("store.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT id FROM jobs WHERE status='dead' LIMIT 1;")
    row = cur.fetchone()
    if row:
        print(row["id"], end="")
except Exception as e:
    pass
PYCODE
)

if [ -z "$job_id" ]; then
    fail "Could not find DLQ job ID from database (via Python fallback)"
fi

info "Retrying DLQ job ID: $job_id"

# ------------------------------------------------------------
# 5. Retry job from DLQ and verify it’s pending again
# ------------------------------------------------------------
queuectl dlq-retry "$job_id" >/dev/null || fail "DLQ retry command failed"
if queuectl list --status pending | grep -q "$job_id"; then
    pass "DLQ retry successfully moved job to pending"
else
    fail "DLQ retry did not move job to pending"
fi

# ------------------------------------------------------------
# 6. Cleanup
# ------------------------------------------------------------
if ps -p "$PID" >/dev/null 2>&1; then
    kill "$PID" >/dev/null 2>&1 || true
fi

pass "DLQ management (list + retry) verified successfully"
