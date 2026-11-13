#!/bin/bash
# Resumable driver (every run is cached; safe to re-launch after a restart).
cd "$(dirname "$0")/.."
pgrep -f "run_all.py --mode full" >/dev/null && { echo "already running"; exit 0; }
PYTHONWARNINGS=ignore nohup python3 run_all.py --mode full --stage confirm,fcps,analysis >> results/logs/full_run.log 2>&1 &
echo launched
