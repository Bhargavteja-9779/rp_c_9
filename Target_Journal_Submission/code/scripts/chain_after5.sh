#!/bin/bash
cd "$(dirname "$0")/.."
until grep -q "CHAIN4 DONE" results/logs/full_run.log; do sleep 60; done
PYTHONWARNINGS=ignore python3 run_all.py --mode full --stage rfsigma,analysis >> results/logs/full_run.log 2>&1
echo "CHAIN5 DONE" >> results/logs/full_run.log
