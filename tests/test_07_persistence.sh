#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/utils.sh"

info "Testing Job Persistence and Database Integrity"
clean_env

# ------------------------------------------------------------
# 1. Enqueue a simple persistent job
# ------------------------------------------------------------
queuectl enqueue '{"command": "echo persist"}' >/dev/null || fail "Failed to enqueue job"
[ -f store.db ] || fail "Database file missing after enqueue"
pass "Database initialized and job persisted successfully"

# ------------------------------------------------------------
# 2. Start a single worker
# ------------------------------------------------------------
stdbuf -oL -eL queuectl worker-start --count 1 > persist.log 2>&1 &
PID=$!
sleep 4  # Give enough time for worker to process the job

# ------------------------------------------------------------
# 3. Stop workers gracefully
# ------------------------------------------------------------
queuectl worker-stop >/dev/null 2>&1
sleep 1

# ------------------------------------------------------------
# 4. Verify the job was completed and persisted correctly
# ------------------------------------------------------------
if grep -Eiq "completed successfully|Job .*completed" persist.log; then
    pass "Job executed and persisted as completed"
else
    echo "--------------------------------------------------"
    echo "Worker Log (last 20 lines):"
    tail -n 20 persist.log || true
    echo "--------------------------------------------------"
    fail "Job execution or persistence verification failed"
fi

# ------------------------------------------------------------
# 5. Cross-check persistence via queuectl status
# ------------------------------------------------------------
if queuectl status | grep -Eiq "Completed|completed"; then
    pass "Queue status reflects completed job (persistent state verified)"
else
    echo "--------------------------------------------------"
    queuectl status || true
    echo "--------------------------------------------------"
    fail "Queue status did not reflect persisted completion"
fi

# ------------------------------------------------------------
# 6. Confirm database still exists and has entries
# ------------------------------------------------------------
if [ -f store.db ]; then
    if python - <<'PYCODE'
import sqlite3
con = sqlite3.connect("store.db")
cur = con.cursor()
cur.execute("SELECT COUNT(*) FROM jobs;")
count = cur.fetchone()[0]
if count < 1:
    exit(1)
PYCODE
    then
        pass "Database integrity check passed (job records exist)"
    else
        fail "Database integrity check failed (no job entries found)"
    fi
else
    fail "Database file missing after processing"
fi

# ------------------------------------------------------------
# 7. Cleanup background processes
# ------------------------------------------------------------
if ps -p "$PID" >/dev/null 2>&1; then
    kill "$PID" >/dev/null 2>&1 || true
fi

pass "Persistence, completion, and database integrity verified successfully"
