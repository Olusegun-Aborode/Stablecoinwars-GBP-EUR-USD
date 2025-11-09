#!/bin/bash

# Load environment variables
export NEON_DB_URL=$(grep "^NEON_DB_URL=" ../.env | cut -d= -f2- )
export ALCHEMY_SOL_URL=$(grep "^ALCHEMY_SOL_URL=" ../.env | cut -d= -f2-)
export ALCHEMY_ETH_URL=$(grep "^ALCHEMY_ETH_URL=" ../.env | cut -d= -f2-)
export ALCHEMY_BASE_URL=$(grep "^ALCHEMY_BASE_URL=" ../.env | cut -d= -f2-)

# Verify env vars are set
echo "=== Environment Check ==="
echo "NEON_DB_URL: ${NEON_DB_URL:0:30}..."
echo "ALCHEMY_ETH_URL: ${ALCHEMY_ETH_URL:0:40}..."
echo "ALCHEMY_BASE_URL: ${ALCHEMY_BASE_URL:0:40}..."
echo "ALCHEMY_SOL_URL: ${ALCHEMY_SOL_URL:0:40}..."
echo ""

MODE=${1:-test}

if [ "$MODE" = "full" ]; then
  DAYS=${2:-90}
  LOG="backfill_full.log"
  echo "=== Starting FULL backfill for ${DAYS} day(s) ===" | tee -a "$LOG"
  start_ts=$(date '+%Y-%m-%d %H:%M:%S')
  echo "Start: $start_ts" | tee -a "$LOG"

  successes=0
  failures=0

  for day in $(seq 1 "$DAYS"); do
    echo "\n=== Day $day/$DAYS ===" | tee -a "$LOG"
    attempt=1
    day_success=0
  while [ $attempt -le 3 ]; do
      echo "Attempt $attempt..." | tee -a "$LOG"
      # Run and capture python exit code even with tee
      python3 -u backfill_v2.py --days 1 2>&1 | tee -a "$LOG"
      rc=${PIPESTATUS[0]}
      if [ $rc -eq 0 ]; then
        echo "✓ Day $day succeeded (attempt $attempt)" | tee -a "$LOG"
        day_success=1
        successes=$((successes+1))
        break
      else
        echo "✗ Day $day failed (attempt $attempt, rc=$rc)" | tee -a "$LOG"
        sleep 5
        attempt=$((attempt+1))
      fi
    done

    if [ $day_success -eq 0 ]; then
      echo "⚠ Day $day failed after 3 attempts" | tee -a "$LOG"
      failures=$((failures+1))
    fi
  done

  end_ts=$(date '+%Y-%m-%d %H:%M:%S')
  echo "\n=== FULL backfill complete ===" | tee -a "$LOG"
  echo "Start: $start_ts" | tee -a "$LOG"
  echo "End:   $end_ts" | tee -a "$LOG"
  echo "Summary: ${successes} succeeded, ${failures} failed" | tee -a "$LOG"
  echo "Log file: $LOG"
  exit 0
fi

# Default: test with 1 day first
echo "=== Testing 1-day backfill ==="
python3 -u backfill_v2.py --days 1 2>&1 | tee backfill_test.log

# Check result
if [ ${PIPESTATUS[0]} -eq 0 ]; then
  echo ""
  echo "✓ Test successful!"
  echo ""
  echo "Ready to run full backfill. Run:"
  echo "  nohup ./backfill_safe.sh full &"
else
  echo ""
  echo "✗ Test failed. Check backfill_test.log"
  exit 1
fi
