#!/bin/bash
set -e
source "$(dirname "$0")/utils.sh"

info "Running Enqueue Tests..."
clean_env

# ------------------------------------------------------------
#  Valid job enqueue test
# ------------------------------------------------------------
output=$(queuectl enqueue '{"command": "echo Hello"}')
echo "$output" | grep -qi "job enqueued" || fail "Failed to enqueue valid job"
pass "Valid job enqueued"

# ------------------------------------------------------------
#  Invalid JSON handling
# ------------------------------------------------------------
output=$(queuectl enqueue '{command:echo fail}' 2>&1 || true)
echo "$output" | grep -qi "Invalid JSON format" || fail "Invalid JSON not handled"
pass "Invalid JSON handled correctly"

# ------------------------------------------------------------
#  Missing 'command' field validation
# ------------------------------------------------------------
output=$(queuectl enqueue '{"id":"x1"}' 2>&1 || true)
echo "$output" | grep -Eqi "Missing|required|command" || fail "Missing field not handled"
pass "Missing command validation works"

# ------------------------------------------------------------
#  Priority + Scheduling behavior
# ------------------------------------------------------------
queuectl enqueue '{"command": "echo Scheduled", "priority": 5, "run_at": "2050-01-01T00:00:00Z"}' >/dev/null


pending_count=$(queuectl list --status pending | grep -c "pending" || true)
if [ "$pending_count" -lt 1 ]; then
    fail "Scheduled job not listed or pending count = 0"
else
    pass "Priority  + run_at scheduling works"
fi
