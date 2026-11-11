"""Experiment stages (each maps to research questions RQ1-RQ5 described in README / manuscript)."""
import copy, json, os, subprocess, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

from experiments import runner as R


def _save_rows(rows, path):
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    return df


def data(cfg, out, n_jobs):
    """Download (if needed), clean, featurize; write dataset summary table."""
    raw = R.ROOT / "data" / "raw"
    need = [raw / "MPEA_dataset.csv", raw / "superconductivty+data.zip"]
    if not all(p.exists() and p.stat().st_size > 0 for p in need):
        subprocess.check_call([sys.executable, str(R.ROOT / "scripts" / "download_data.py")])
    rows = []
    for t in cfg["tasks"]:
        d = R.load_task(t, cfg)
        rows.append({"task": t, "n": len(d["y"]), "n_features": d["X"].shape[1], "n_elements": len(d["elements"]),
                     "n_systems": len(np.unique(d["fam_system"])), "n_clusters": len(np.unique(d["fam_cluster"])),
                     "largest_system_frac": pd.Series(d["fam_system"]).value_counts(normalize=True).iloc[0],
                     "y_mean": d["y"].mean(), "y_sd": d["y"].std(), "y_min": d["y"].min(), "y_max": d["y"].max(),
                     "n_unparseable": d["n_unparseable"]})
    (out / "tables").mkdir(exist_ok=True)
    _save_rows(rows, out / "tables" / "dataset_summary.csv")


def main(cfg, out, n_jobs):
    """RQ1-RQ3: coverage/efficiency of all methods under random, chemical-system and cluster extrapolation."""
    rows = []
    for t in cfg["tasks"]:
        for p in cfg["protocols"]:
            for s in cfg["seeds"]:
                t0 = time.time()
                r = R.run_one("main", t, p, s, cfg, n_jobs=n_jobs)
                rows += R.metrics_rows(r)
                print(f"  main {t} {p} seed={s} wall={r['wall']:.0f}s (this call {time.time() - t0:.0f}s)", flush=True)
                _save_rows(rows, out / "raw_results.csv")


def robustness(cfg, out, n_jobs):
    """RQ4: label noise and reduced training data (system-holdout protocol)."""
    rc = cfg["robustness"]
    c2 = copy.deepcopy(cfg); c2["methods"] = rc["methods"]
    rows = []
    for t in rc["tasks"]:
        for s in rc["seeds"]:
            for ln in rc["label_noise"]:
                r = R.run_one("robust", t, "system", s, c2, variant=f"noise{ln}", n_jobs=n_jobs, label_noise=ln)
                rows += [dict(x, condition=f"label_noise={ln}") for x in R.metrics_rows(r)]
            for tf in rc["train_fraction"]:
                r = R.run_one("robust", t, "system", s, c2, variant=f"trainfrac{tf}", n_jobs=n_jobs, train_fraction=tf)
                rows += [dict(x, condition=f"train_fraction={tf}") for x in R.metrics_rows(r)]
            print(f"  robustness {t} seed={s}", flush=True)
            _save_rows(rows, out / "robustness_results.csv")


def generalization(cfg, out, n_jobs):
    """RQ5: mis-specified family definition: true shift = composition clusters, FCP calibrates on chemical systems."""
    rc = cfg["robustness"]
    c2 = copy.deepcopy(cfg); c2["methods"] = ["GSCP", "GCV+", "FCP", "FCP-W", "CV+", "SCP"]
    rows = []
    for t in cfg["tasks"]:
        for s in rc["seeds"]:
            r = R.run_one("general", t, "cluster", s, c2, variant="inner_system", n_jobs=n_jobs, inner_family="system")
            rows += [dict(x, condition="inner=system,outer=cluster") for x in R.metrics_rows(r)]
            print(f"  generalization {t} seed={s}", flush=True)
            _save_rows(rows, out / "generalization_results.csv")


def sensitivity(cfg, out, n_jobs):
    """Hyper-parameter sensitivity of FCP (one factor at a time around the pre-specified defaults)."""
    sc = cfg["sensitivity"]
    rows = []
    for t in sc["tasks"]:
        for s in sc["seeds"]:
            for par, vals in sc["grid"].items():
                for v in vals:
                    c2 = copy.deepcopy(cfg); c2["methods"] = sc["methods"]; c2[par] = v
                    r = R.run_one("sens", t, "system", s, c2, variant=f"{par}={v}", n_jobs=n_jobs)
                    rows += [dict(x, parameter=par, value=v) for x in R.metrics_rows(r)]
            print(f"  sensitivity {t} seed={s}", flush=True)
            _save_rows(rows, out / "sensitivity_results.csv")


def efficiency(cfg, out, n_jobs):
    """Wall time and peak resident memory of each method for one outer fold (separate processes)."""
    rows = []
    methods = ["SCP", "WCP", "CQR", "GSCP", "CV+", "FCP", "GP", "RF-z"]
    for t in [x for x in ["mpea_ys", "superhard_k"] if x in cfg["tasks"]] or cfg["tasks"][:1]:
        for m in methods:
            code = (
                "import sys,time,resource,json,warnings;warnings.filterwarnings('ignore');"
                f"sys.path.insert(0,{str(R.ROOT / 'src')!r});sys.path.insert(0,{str(R.ROOT)!r});"
                "import numpy as np, yaml;from experiments import runner as R;from fcp.evaluation.protocol import _fold_job, outer_groups;"
                "from fcp.models.conformal import assign_folds;"
                f"cfg=yaml.safe_load(open({str(R.ROOT / 'config' / 'default.yaml')!r}));cfg['methods']=[{m!r}];cfg['alphas']=[0.1];"
                f"task=R.load_task({t!r},cfg);g=outer_groups(task,'system');f=assign_folds(len(g),5,g,seed=0);"
                "tr,te=np.where(f!=0)[0],np.where(f==0)[0];r0=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;"
                "t0=time.perf_counter();o=_fold_job(task,'system',0,0,tr,te,cfg,None);dt=time.perf_counter()-t0;"
                "print(json.dumps({'wall_s':dt,'base_s':o['time']['base'],'peak_rss_mb':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,'n_train':len(tr),'n_test':len(te)}))"
            )
            res = json.loads(subprocess.check_output([sys.executable, "-c", code]).decode().strip().splitlines()[-1])
            rows.append({"task": t, "method": m, **res})
            print(f"  efficiency {t} {m} {res}", flush=True)
    _save_rows(rows, out / "efficiency_results.csv")


def analysis(cfg, out, n_jobs):
    from experiments import analysis as A
    A.run(cfg, out)
