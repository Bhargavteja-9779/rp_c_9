#!/bin/bash
cd "$(dirname "$0")/.."
until grep -q "CHAIN DONE" results/logs/full_run.log; do sleep 60; done
PYTHONWARNINGS=ignore python3 run_all.py --mode full --stage randfolds,analysis >> results/logs/full_run.log 2>&1
echo "CHAIN2 DONE" >> results/logs/full_run.log
