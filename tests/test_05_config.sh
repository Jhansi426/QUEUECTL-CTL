#!/bin/bash
set -e
source "$(dirname "$0")/utils.sh"

info "Testing Config CLI..."
clean_env
queuectl config-set worker_count 3
queuectl config-get worker_count | grep -q "3" || fail "Config get/set failed"
pass "Config set/get works"

queuectl config-reset
queuectl config-show | grep -q "max_retries" || fail "Config reset failed"
pass "Config reset and show works"
