#!/bin/bash
# Shared utilities for all QueueCTL tests

RED="\e[31m"; GREEN="\e[32m"; YELLOW="\e[33m"; CYAN="\e[36m"; RESET="\e[0m"

info()  { echo -e "${CYAN}[INFO]${RESET} $1"; }
pass()  { echo -e "${GREEN}[PASS]${RESET} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${RESET} $1"; }
fail()  { echo -e "${RED}[FAIL]${RESET} $1"; exit 1; }

command -v queuectl >/dev/null 2>&1 || fail "queuectl command not found. Run 'pip install -e .' first."

clean_env() {
  rm -f store.db worker_threads.json stop_signal.json 2>/dev/null
  rm -rf logs 2>/dev/null
  echo '{}' > config.json
  info "Clean environment ready."
}
