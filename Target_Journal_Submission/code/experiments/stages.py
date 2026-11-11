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
    from fcp.evaluation.protocol import CV_VARIANTS
    jobs = [(t, p, s) for t in cfg["tasks"] for p in cfg["protocols"] for s in cfg["seeds"]]
    # (a) non-CV+ methods (baselines). Runs cached before the v2 revision also contain v1 CV+ variants; those rows
    #     are relabelled '<name> (v1)' and reported only in the iteration log.
    c_base = copy.deepcopy(cfg); c_base["methods"] = ["Ens-z", "SCP", "WCP", "CQR", "GSCP", "GP", "RF-z"]
    _parallel_runs("main", jobs, c_base, n_jobs)
    # (b) all CV+ variants with the v2 scale model, for every task / protocol / seed
    c_cv = copy.deepcopy(cfg); c_cv["methods"] = list(CV_VARIANTS)
    _parallel_runs("main", jobs, c_cv, n_jobs, variant="cvplus_v2")
    rows = []
    for t, p, s in jobs:
        for x in R.metrics_rows(R.run_one("main", t, p, s, c_base)):
            if x["method"] in CV_VARIANTS:
                x["method"] = x["method"] + " (v1)"
            rows.append(x)
        rows += R.metrics_rows(R.run_one("main", t, p, s, c_cv, variant="cvplus_v2"))
    _save_rows(rows, out / "raw_results.csv")


def _one(exp, t, p, s, cfg, variant, kw):
    t0 = time.time()
    r = R.run_one(exp, t, p, s, cfg, variant=variant, n_jobs=1, **kw)
    print(f"  {exp} {t} {p} seed={s} {variant} wall={r['wall']:.0f}s (call {time.time() - t0:.0f}s)", flush=True)
    return None


def _parallel_runs(exp, jobs, cfg, n_jobs, variant="default", kw=None):
    """Runs (task, protocol, seed) jobs concurrently, one process per run (single-threaded inside), so all cores
    stay busy. Results are cached per run; already cached runs return immediately."""
    from joblib import Parallel, delayed
    Parallel(n_jobs=n_jobs, verbose=0)(delayed(_one)(exp, t, p, s, cfg, variant, kw or {}) for t, p, s in jobs)


def robustness(cfg, out, n_jobs):
    """RQ4: label noise and reduced training data (system-holdout protocol)."""
    rc = cfg["robustness"]
    c2 = copy.deepcopy(cfg); c2["methods"] = rc["methods"]
    from joblib import Parallel, delayed
    todo = [(t, s, "noise", ln) for t in rc["tasks"] for s in rc["seeds"] for ln in rc["label_noise"]] + \
           [(t, s, "frac", tf) for t in rc["tasks"] for s in rc["seeds"] for tf in rc["train_fraction"]]
    Parallel(n_jobs=n_jobs)(delayed(_one)("robust", t, "system", s, c2, f"noise{v}" if k == "noise" else f"trainfrac{v}",
                                          {"label_noise": v} if k == "noise" else {"train_fraction": v}) for t, s, k, v in todo)
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
    from joblib import Parallel, delayed
    Parallel(n_jobs=n_jobs)(delayed(_one)("general", t, "cluster", s, c2, "inner_system", {"inner_family": "system"})
                            for t in cfg["tasks"] for s in rc["seeds"])
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
    from joblib import Parallel, delayed
    todo = []
    for t in sc["tasks"]:
        for s in sc["seeds"]:
            for par, vals in sc["grid"].items():
                for v in vals:
                    c2 = copy.deepcopy(cfg); c2["methods"] = sc["methods"]; c2[par] = v
                    todo.append((t, s, c2, f"{par}={v}"))
    Parallel(n_jobs=n_jobs)(delayed(_one)("sens", t, "system", s, c2, var, {}) for t, s, c2, var in todo)
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


def basemodel(cfg, out, n_jobs):
    """Base-learner swap: FCP and random-fold CV+ with random-forest members (50 trees each, M members), to test
    whether the family-level calibration principle composes with a different point predictor (compare with RF-z)."""
    c2 = copy.deepcopy(cfg); c2["member"] = "rf"; c2["rf_trees"] = 50
    c2["methods"] = ["CV+", "NCV+", "GCV+", "GCV+[spread]", "FCP", "SCP", "GSCP"]
    seeds = cfg["robustness"]["seeds"]
    jobs = [(t, p, s) for t in cfg["tasks"] for p in ["system", "cluster", "random"] for s in seeds]
    from joblib import Parallel, delayed
    Parallel(n_jobs=n_jobs)(delayed(_one)("basemodel", t, p, s, c2, "rf_members", {}) for t, p, s in jobs)
    rows = []
    for t, p, s in jobs:
        rows += [dict(x, base="RF members") for x in R.metrics_rows(R.run_one("basemodel", t, p, s, c2, variant="rf_members"))]
    _save_rows(rows, out / "basemodel_results.csv")


def randfolds(cfg, out, n_jobs):
    """Statistics check: cluster protocol with fully random (unbalanced) assignment of clusters to outer folds, so
    that every seed uses a different outer partition (the balanced assignment is identical across seeds)."""
    c2 = copy.deepcopy(cfg); c2["outer_assign"] = "random"
    c2["methods"] = ["SCP", "CV+", "CQR", "WCP", "RF-z", "GSCP", "GCV+", "GCV+[spread]", "FCP", "FCP-W"]  # GP omitted (cost)
    jobs = [(t, "cluster", s) for t in cfg["tasks"] for s in cfg["seeds"]]
    from joblib import Parallel, delayed
    Parallel(n_jobs=n_jobs)(delayed(_one)("randfolds", t, p, s, c2, "random_assign", {}) for t, p, s in jobs)
    rows = []
    for t, p, s in jobs:
        rows += [dict(x, assignment="random") for x in R.metrics_rows(R.run_one("randfolds", t, p, s, c2, variant="random_assign"))]
    _save_rows(rows, out / "randfolds_results.csv")


def mondrian(cfg, out, n_jobs):
    """Reviewer-2 request: Mondrian (novelty-tertile) split conformal with random calibration, all tasks/protocols/seeds."""
    c2 = copy.deepcopy(cfg); c2["methods"] = ["SCP", "MCP"]
    jobs = [(t, p, s) for t in cfg["tasks"] for p in cfg["protocols"] for s in cfg["seeds"]]
    from joblib import Parallel, delayed
    Parallel(n_jobs=n_jobs)(delayed(_one)("mondrian", t, p, s, c2, "mcp", {}) for t, p, s in jobs)
    rows = []
    for t, p, s in jobs:
        rows += R.metrics_rows(R.run_one("mondrian", t, p, s, c2, variant="mcp"))
    _save_rows(rows, out / "mondrian_results.csv")


def temporal(cfg, out, n_jobs):
    """Reviewer-5 request: chronological deployment test on MPEA data (train: publications before 2019; test: 2019)."""
    c2 = copy.deepcopy(cfg)
    jobs = [(t, "temporal", s) for t in ["mpea_hv", "mpea_ys"] for s in cfg["seeds"]]
    from joblib import Parallel, delayed
    Parallel(n_jobs=n_jobs)(delayed(_one)("temporal", t, p, s, c2, "y2019", {}) for t, p, s in jobs)
    rows = []
    for t, p, s in jobs:
        rows += R.metrics_rows(R.run_one("temporal", t, p, s, c2, variant="y2019"))
    _save_rows(rows, out / "temporal_results.csv")


def rfsigma(cfg, out, n_jobs):
    """Iteration 2: family-grouped CV+ normalized by random-forest tree spread (FCP-RFsigma) vs random-fold version and RF-z."""
    c2 = copy.deepcopy(cfg); c2["methods"] = ["FCP-RFsigma", "CV+-RFsigma", "RF-z"]
    seeds = cfg["robustness"]["seeds"]
    jobs = [(t, p, s) for t in cfg["tasks"] for p in cfg["protocols"] for s in seeds]
    from joblib import Parallel, delayed
    Parallel(n_jobs=n_jobs)(delayed(_one)("rfsigma", t, p, s, c2, "rfsigma", {}) for t, p, s in jobs)
    rows = []
    for t, p, s in jobs:
        rows += R.metrics_rows(R.run_one("rfsigma", t, p, s, c2, variant="rfsigma"))
    _save_rows(rows, out / "rfsigma_results.csv")


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
