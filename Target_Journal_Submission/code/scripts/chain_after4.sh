#!/bin/bash
cd "$(dirname "$0")/.."
sleep 30
while pgrep -f "run_all.py --mode full --stage robustness" >/dev/null; do sleep 60; done
PYTHONWARNINGS=ignore python3 run_all.py --mode full --stage temporal,main,analysis >> results/logs/full_run.log 2>&1
echo "CHAIN4 DONE" >> results/logs/full_run.log
