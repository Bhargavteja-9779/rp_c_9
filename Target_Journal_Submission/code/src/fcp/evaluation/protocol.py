"""Outer evaluation protocol.

For a task, an outer protocol and a seed:
  * the data are split into 5 outer folds; each outer fold is a test set never used for fitting or calibration;
      - 'random'  : rows grouped by exact formula (in-distribution control; one alloy never on both sides)
      - 'system'  : whole chemical systems held out (F1 families)
      - 'cluster' : whole k-means composition clusters held out (F2 families, harder extrapolation)
  * every interval method is fitted on the outer training part only.
  * the families used *inside* grouped methods are those of the protocol ('system' for the random protocol),
    unless `inner_family` overrides it (robustness experiment on mis-specified family definitions).
Per-point lower/upper bounds for every method and alpha are returned for downstream metrics.
"""
import time
import numpy as np
from joblib import Parallel, delayed

from fcp.models.base import FamilyBaggedLGBM, NoveltyScorer
from fcp.models import conformal as C

ALPHAS = (0.05, 0.1, 0.2)

# variant name -> (folds grouped?, sigma mode, family weights?)
CV_VARIANTS = {
    "CV+": (False, "none", False),
    "NCV+": (False, "both", False),
    "GCV+": (True, "none", False),
    "GCV+[spread]": (True, "spread", False),
    "GCV+[novelty]": (True, "novelty", False),
    "FCP": (True, "both", False),
    "GCV+-W": (True, "none", True),
    "FCP-W": (True, "both", True),
    "FCP-W[spread]": (True, "spread", True),
    "FCP-W[novelty]": (True, "novelty", True),
}


def outer_groups(task, protocol):
    if protocol == "random":
        return task["formula"]
    if protocol == "system":
        return task["fam_system"]
    if protocol == "cluster":
        return task["fam_cluster"]
    raise KeyError(protocol)


def _fold_job(task, protocol, seed, k, tr, te, cfg, inner_family):
    t0 = time.perf_counter()
    X, y = task["X"], task["y"]
    Xtr, ytr, Xte = X[tr], y[tr], X[te]
    fam_key = {"system": "fam_system", "cluster": "fam_cluster"}[inner_family or ("system" if protocol == "random" else protocol)]
    gtr = task[fam_key][tr]
    alphas = cfg.get("alphas", ALPHAS)
    kw = dict(n_members=cfg["n_members"], family_frac=cfg["family_frac"], lgbm_params=cfg.get("lgbm_params"))
    if cfg.get("member", "lgbm") != "lgbm":
        kw.update(member=cfg["member"], rf_trees=cfg.get("rf_trees", 50))
    rs = seed * 100 + k
    out = {"idx": te, "lo": {}, "hi": {}, "time": {}}
    methods = cfg.get("methods", "all")

    def want(name):
        return methods == "all" or name in methods

    # full-train base model: point accuracy + naive ensemble interval + test novelty (for analysis)
    tt = time.perf_counter()
    base = FamilyBaggedLGBM(seed=rs, **kw).fit(Xtr, ytr, gtr)
    mu, sd = base.predict(Xte)
    out["mu"] = mu
    nov = NoveltyScorer(cfg["novelty_pcs"], cfg["novelty_k"]).fit(Xtr, gtr)
    out["novelty"] = nov.score(Xte)
    out["time"]["base"] = time.perf_counter() - tt
    if want("Ens-z"):
        for a in alphas:
            out["lo"][("Ens-z", a)], out["hi"][("Ens-z", a)] = C.gaussian_interval(mu, sd, a)
    # random split (75/25 rows)
    rng = np.random.default_rng(rs)
    if want("SCP") or want("WCP") or want("CQR"):
        tt = time.perf_counter()
        perm = rng.permutation(len(ytr))
        ncal = int(round(0.25 * len(ytr)))
        ca, pr = perm[:ncal], perm[ncal:]
        b2 = FamilyBaggedLGBM(seed=rs + 7, **kw).fit(Xtr[pr], ytr[pr], gtr[pr])
        mcal, _ = b2.predict(Xtr[ca]); mte, _ = b2.predict(Xte)
        for a in alphas:
            out["lo"][("SCP", a)], out["hi"][("SCP", a)] = C.split_conformal(mcal, ytr[ca], mte, a)
        out["time"]["SCP"] = time.perf_counter() - tt
        if want("WCP"):
            tt = time.perf_counter()
            nv = NoveltyScorer(cfg["novelty_pcs"], cfg["novelty_k"]).fit(Xtr[pr], gtr[pr])
            rc, rt = C.density_ratio(nv.transform(Xtr[ca]), nv.transform(Xte), seed=rs)
            for a in alphas:
                out["lo"][("WCP", a)], out["hi"][("WCP", a)] = C.weighted_split_conformal(mcal, ytr[ca], mte, rc, rt, a)
            out["time"]["WCP"] = out["time"]["SCP"] + time.perf_counter() - tt
        if want("CQR"):
            tt = time.perf_counter()
            for a in alphas:
                out["lo"][("CQR", a)], out["hi"][("CQR", a)] = C.cqr(Xtr[pr], ytr[pr], Xtr[ca], ytr[ca], Xte, a,
                                                                      cfg.get("lgbm_params"), seed=rs)
            out["time"]["CQR"] = time.perf_counter() - tt
    # group split (25% of families held out for calibration)
    if want("GSCP"):
        tt = time.perf_counter()
        fams = np.unique(gtr)
        calf = rng.choice(fams, size=max(1, int(round(0.25 * len(fams)))), replace=False)
        cm = np.isin(gtr, calf)
        b3 = FamilyBaggedLGBM(seed=rs + 11, **kw).fit(Xtr[~cm], ytr[~cm], gtr[~cm])
        mcal, _ = b3.predict(Xtr[cm]); mte, _ = b3.predict(Xte)
        for a in alphas:
            out["lo"][("GSCP", a)], out["hi"][("GSCP", a)] = C.split_conformal(mcal, ytr[cm], mte, a)
        out["time"]["GSCP"] = time.perf_counter() - tt
    # cross-fitted CV+ variants (random folds and family-grouped folds)
    for grouped in (False, True):
        names = [n for n, v in CV_VARIANTS.items() if v[0] == grouped and want(n)]
        if not names:
            continue
        tt = time.perf_counter()
        cf = C.CrossFit(K=cfg["K"], grouped=grouped, novelty_k=cfg["novelty_k"], novelty_pcs=cfg["novelty_pcs"],
                        seed=rs, clip_scale=cfg.get("clip_scale", False), **kw).fit(Xtr, ytr, gtr, Xte)
        fit_t = time.perf_counter() - tt
        for n in names:
            _, mode, wts = CV_VARIANTS[n]
            t1 = time.perf_counter()
            for a in alphas:
                out["lo"][(n, a)], out["hi"][(n, a)] = cf.intervals(a, mode, wts)
            out["time"][n] = fit_t + (time.perf_counter() - t1) / len(alphas)
    # Gaussian process and random forest (common materials-informatics practice)
    if want("GP"):
        tt = time.perf_counter()
        gmu, gsd = C.gp_fit_predict(nov.transform(Xtr), ytr, nov.transform(Xte), max_train=cfg.get("gp_max_train", 1500), seed=rs)
        for a in alphas:
            out["lo"][("GP", a)], out["hi"][("GP", a)] = C.gaussian_interval(gmu, gsd, a)
        out["time"]["GP"] = time.perf_counter() - tt
    if want("RF-z"):
        tt = time.perf_counter()
        rmu, rsd = C.rf_fit_predict(Xtr, ytr, Xte, seed=rs)
        for a in alphas:
            out["lo"][("RF-z", a)], out["hi"][("RF-z", a)] = C.gaussian_interval(rmu, rsd, a)
        out["time"]["RF-z"] = time.perf_counter() - tt
    out["time"]["fold_total"] = time.perf_counter() - t0
    return out


def run_protocol(task, protocol, seed, cfg, inner_family=None, n_jobs=4, train_fraction=1.0, label_noise=0.0):
    """Returns dict with per-point arrays aligned to task rows that were tested (each row tested exactly once)."""
    y_orig = task["y"]
    task = dict(task)
    rng = np.random.default_rng(10_000 + seed)
    if label_noise > 0:  # robustness: Gaussian noise on training AND test labels as a fraction of target SD
        task["y"] = y_orig + rng.normal(0, label_noise * y_orig.std(), size=len(y_orig))
    groups = outer_groups(task, protocol)
    folds = C.assign_folds(len(groups), cfg["outer_folds"], groups, seed=seed)
    jobs = []
    for k in range(cfg["outer_folds"]):
        tr, te = np.where(folds != k)[0], np.where(folds == k)[0]
        if train_fraction < 1.0:  # robustness: reduced training data (subsample whole training families)
            fam_key = "fam_system" if protocol in ("random", "system") else "fam_cluster"
            tf = np.unique(task[fam_key][tr])
            keep = rng.choice(tf, size=max(2, int(round(train_fraction * len(tf)))), replace=False)
            tr = tr[np.isin(task[fam_key][tr], keep)]
        jobs.append((k, tr, te))
    res = Parallel(n_jobs=n_jobs)(delayed(_fold_job)(task, protocol, seed, k, tr, te, cfg, inner_family)
                                  for k, tr, te in jobs)
    n = len(task["y"])
    keys = sorted({kk for r in res for kk in r["lo"]})
    out = {"y": task["y"], "fold": folds, "mu": np.full(n, np.nan), "novelty": np.full(n, np.nan),
           "lo": {kk: np.full(n, np.nan) for kk in keys}, "hi": {kk: np.full(n, np.nan) for kk in keys},
           "time": {}}
    for r in res:
        i = r["idx"]
        out["mu"][i], out["novelty"][i] = r["mu"], r["novelty"]
        for kk in keys:
            out["lo"][kk][i], out["hi"][kk][i] = r["lo"][kk], r["hi"][kk]
        for m, t in r["time"].items():
            out["time"].setdefault(m, []).append(t)
    out["families"] = groups
    return out
