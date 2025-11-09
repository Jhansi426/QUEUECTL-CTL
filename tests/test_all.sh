#!/bin/bash
set -e
echo "===================================="
echo "🔧 Running Full QueueCTL Test Suite"
echo "===================================="

for test in tests/test_*.sh; do
  echo -e "\n▶️ Running: $test"
  bash "$test"
done

echo
echo " All tests passed successfully!"
