#!/bin/bash
# waits for the running campaign, then runs the base-model experiment and the analysis
cd "$(dirname "$0")/.."
while pgrep -f "run_all.py --mode full --stage main" >/dev/null; do sleep 30; done
PYTHONWARNINGS=ignore python3 run_all.py --mode full --stage robustness,generalization,sensitivity,efficiency,basemodel,analysis >> results/logs/full_run.log 2>&1
echo "CHAIN DONE" >> results/logs/full_run.log
