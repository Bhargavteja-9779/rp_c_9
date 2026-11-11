"""Interval metrics computed from per-point bounds.

coverage            fraction of test rows with lo <= y <= hi
family_coverage     mean over test families of within-family coverage (each family weighted equally)
undercovered_fams   fraction of test families (with >= 5 rows) whose coverage < 1 - alpha - 0.10
width_sd            mean interval width / SD(y) over finite intervals; inf_rate = fraction of infinite intervals
median_width_sd     median width / SD(y) (robust; infinite intervals included)
interval_score_sd   mean Winkler interval score / SD(y) (Gneiting & Raftery 2007): width + (2/alpha) * miss distance
cov_novelty_{low,mid,high}  coverage within tertiles of test-point novelty (distance to training data)
"""
import numpy as np


def interval_metrics(y, lo, hi, alpha, families, novelty, sd_y):
    cov = (y >= lo) & (y <= hi)
    w = hi - lo
    fin = np.isfinite(w)
    fams = np.unique(families)
    fc = np.array([cov[families == g].mean() for g in fams])
    big = np.array([(families == g).sum() >= 5 for g in fams])
    miss = np.where(y < lo, lo - y, 0) + np.where(y > hi, y - hi, 0)
    with np.errstate(invalid="ignore"):
        score = w + (2 / alpha) * miss
    t1, t2 = np.quantile(novelty, [1 / 3, 2 / 3])
    out = {
        "coverage": cov.mean(),
        "family_coverage": fc.mean(),
        "undercovered_fams": float(np.mean(fc[big] < 1 - alpha - 0.10)) if big.any() else np.nan,
        "width_sd": w[fin].mean() / sd_y if fin.any() else np.inf,
        "median_width_sd": np.median(w) / sd_y,
        "inf_rate": 1 - fin.mean(),
        "interval_score_sd": score.mean() / sd_y,
        "cov_novelty_low": cov[novelty <= t1].mean(),
        "cov_novelty_mid": cov[(novelty > t1) & (novelty <= t2)].mean(),
        "cov_novelty_high": cov[novelty > t2].mean(),
        "n_test": len(y),
        "n_test_families": len(fams),
    }
    return out


def point_metrics(y, mu):
    res = y - mu
    return {"r2": 1 - np.mean(res ** 2) / np.var(y), "mae": np.mean(np.abs(res)), "rmse": np.sqrt(np.mean(res ** 2))}
