"""Executes experiment runs and caches each (experiment, task, protocol, seed, variant) result, so interrupted
runs resume where they stopped. Per-point bounds are kept in results/cache (not versioned); metrics go to CSV."""
import json, os, pickle, time, hashlib
from pathlib import Path
import numpy as np
import pandas as pd

from fcp.preprocessing.features import build_task
from fcp.evaluation.protocol import run_protocol
from fcp.evaluation.metrics import interval_metrics, point_metrics

ROOT = Path(__file__).resolve().parents[1]
# The results directory is passed through the environment (set by run_all.py) so that joblib worker processes, which
# re-import this module, use the same cache as the parent (quick mode must never write into the full-run cache).
CACHE = Path(os.environ.get("FCP_RESULTS_DIR", ROOT / "results")) / "cache"


def load_task(name, cfg):
    t = build_task(name, k_clusters=cfg["k_clusters"])
    if name in ("mpea_hv", "mpea_ys", "mpea_uts", "mpea_elong"):
        from fcp.data.datasets import load_years
        yrs = load_years(name)
        assert len(yrs) == len(t["y"])
        t = dict(t, year=yrs)
    if name in ("supercon_tc", "expt_gap") and len(t["y"]) > cfg["supercon_max_rows"]:
        rng = np.random.default_rng(0)
        fams = rng.permutation(np.unique(t["fam_system"]))
        keep, n = [], 0
        sizes = pd.Series(t["fam_system"]).value_counts()
        for f in fams:
            if n >= cfg["supercon_max_rows"]:
                break
            keep.append(f); n += sizes[f]
        m = np.isin(t["fam_system"], keep)
        t = {k: (v[m] if isinstance(v, np.ndarray) and len(v) == len(m) else v) for k, v in t.items()}
        # recompute composition clusters on the retained subset so that k clusters exist
        from fcp.preprocessing.features import cluster_families
        t["fam_cluster"] = cluster_families(t["frac"], k=cfg["k_clusters"])
    return t


def _key(*parts):
    return "_".join(str(p) for p in parts)


def run_one(exp, task_name, protocol, seed, cfg, variant="default", n_jobs=4, **kw):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{_key(exp, task_name, protocol, seed, variant)}.pkl"
    if f.exists():
        return pickle.loads(f.read_bytes())
    task = load_task(task_name, cfg)
    t0 = time.perf_counter()
    r = run_protocol(task, protocol, seed, cfg, n_jobs=n_jobs, **kw)
    r["wall"] = time.perf_counter() - t0
    r["meta"] = {"exp": exp, "task": task_name, "protocol": protocol, "seed": seed, "variant": variant}
    f.write_bytes(pickle.dumps(r))
    return r


def metrics_rows(r, families_for_metrics=None):
    meta = r["meta"]
    y = r["y"]
    sd = np.std(y)
    fam = r["families"] if families_for_metrics is None else families_for_metrics
    pm = point_metrics(y, r["mu"])
    rows = []
    for (m, a) in r["lo"]:
        im = interval_metrics(y, r["lo"][(m, a)], r["hi"][(m, a)], a, fam, r["novelty"], sd)
        t = r["time"].get(m, [np.nan])
        rows.append({**meta, "method": m, "alpha": a, **im, **{f"point_{k}": v for k, v in pm.items()},
                     "fit_time_s_per_fold": float(np.mean(t))})
    return rows
