#!/usr/bin/env python3
"""Single entry point reproducing every number, table and figure of the study.

    python run_all.py --mode quick     # pipeline check (minutes); writes to results_quick/
    python run_all.py --mode full      # full study (hours on 4 CPU cores)
    python run_all.py --mode full --stage analysis   # re-create statistics/tables/figures from cached runs
Stages: data, main, robustness, generalization, sensitivity, efficiency, basemodel, randfolds, mondrian, temporal,
analysis (default: all)
"""
import argparse, json, os, platform, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT))
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, yaml


def device_report():
    """Hardware detection. All methods are CPU tree ensembles / kernel methods; accelerators are reported only."""
    info = {"platform": platform.platform(), "python": platform.python_version(), "cpu_count": os.cpu_count()}
    try:
        import torch
        info["cuda"] = torch.cuda.is_available()
        info["mps"] = bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())
    except Exception:
        info["cuda"] = info["mps"] = False
    info["device_used"] = "cpu"
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["quick", "full"], default="quick")
    ap.add_argument("--stage", default="all")
    ap.add_argument("--n_jobs", type=int, default=min(4, os.cpu_count() or 1))
    a = ap.parse_args()
    cfg = yaml.safe_load(open(ROOT / "config" / ("quick.yaml" if a.mode == "quick" else "default.yaml")))
    out = ROOT / ("results_quick" if a.mode == "quick" else "results")
    out.mkdir(exist_ok=True)
    os.environ["FCP_RESULTS_DIR"] = str(out)
    import experiments.runner as R
    if a.mode == "quick":
        R.CACHE = out / "cache"
    (out / "logs").mkdir(exist_ok=True)
    json.dump({"device": device_report(), "config": cfg, "mode": a.mode}, open(out / "logs" / "run_info.json", "w"), indent=2)
    stages = ["data", "main", "robustness", "generalization", "sensitivity", "efficiency", "basemodel", "randfolds",
              "mondrian", "temporal", "rfsigma", "fcps", "confirm", "analysis"] if a.stage == "all" else a.stage.split(",")
    from experiments import stages as S
    for st in stages:
        t0 = time.time()
        print(f"=== stage {st} ===", flush=True)
        getattr(S, st)(cfg, out, a.n_jobs)
        print(f"=== stage {st} done in {time.time() - t0:.0f}s ===", flush=True)


if __name__ == "__main__":
    main()
