#!/bin/bash
cd "$(dirname "$0")/.."
until grep -q "CHAIN2 DONE" results/logs/full_run.log; do sleep 60; done
PYTHONWARNINGS=ignore python3 run_all.py --mode full --stage mondrian,analysis >> results/logs/full_run.log 2>&1
echo "CHAIN3 DONE" >> results/logs/full_run.log
