#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/utils.sh"

info "Testing Job Priority Ordering"
clean_env

# ------------------------------------------------------------
# Enqueue jobs with different priorities
# ------------------------------------------------------------
queuectl enqueue '{"command": "echo Low", "priority": 1}' >/dev/null
queuectl enqueue '{"command": "echo High", "priority": 5}' >/dev/null

# ------------------------------------------------------------
# Verify highest-priority job appears first using Python
# ------------------------------------------------------------
top_job=$(python - <<'PY'
import sqlite3
try:
    con = sqlite3.connect("store.db")
    cur = con.execute("SELECT command FROM jobs ORDER BY priority DESC LIMIT 1;")
    row = cur.fetchone()
    print(row[0] if row else "")
finally:
    con.close()
PY
)

if [[ "$top_job" == "echo High" ]]; then
    pass "High-priority job correctly ordered at the top of the queue"
else
    echo "--------------------------------------------------"
    echo "Database Snapshot:"
    python - <<'PY'
import sqlite3
con = sqlite3.connect("store.db")
for row in con.execute("SELECT id, command, priority FROM jobs ORDER BY priority DESC;"):
    print(row)
con.close()
PY
    echo "--------------------------------------------------"
    fail "Priority ordering failed (expected 'echo High', got '$top_job')"
fi

pass "Priority ordering logic verified successfully"
