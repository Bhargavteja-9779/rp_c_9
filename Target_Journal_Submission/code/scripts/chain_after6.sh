#!/bin/bash
# After the running confirm stage finishes: theory check (FCP-S, Proposition 1), then re-run the analysis.
cd "$(dirname "$0")/.."
while pgrep -f "run_all.py --mode full --stage confirm" >/dev/null; do sleep 60; done
PYTHONWARNINGS=ignore python3 run_all.py --mode full --stage fcps,analysis >> results/logs/full_run.log 2>&1
echo "CHAIN6 DONE" >> results/logs/full_run.log
