"""Statistical procedures (pre-specified before the main results were inspected).

Unit of analysis for cross-dataset claims: one *cell* = (task, shift protocol). Its value is the mean over the
10 outer-split seeds. Seeds re-partition the SAME data, so seed-level values are not independent replicates; they
are only used to describe split-to-split variability (mean, SD, 95% percentile interval).
Cells from different tasks are treated as independent; the two shift protocols of one task share data. This
dependence is acknowledged in the manuscript, and every test is also reported per protocol (6 cells each).

Tests
  * paired_wilcoxon(a, b): two-sided Wilcoxon signed-rank (exact for n <= 25, scipy 'auto'), matched-pairs
    rank-biserial correlation as effect size, Hodges-Lehmann-style median of differences with a bootstrap 95% CI.
  * one_sample_wilcoxon(x, mu0, alternative): signed-rank test of the location of x against mu0.
  * holm(pvals): Holm-Bonferroni step-down adjustment (family = all baselines compared with the proposed method).
"""
import numpy as np
from scipy import stats


def rank_biserial(d):
    d = np.asarray(d, float)
    d = d[d != 0]
    if len(d) == 0:
        return 0.0
    r = stats.rankdata(np.abs(d))
    return float((r[d > 0].sum() - r[d < 0].sum()) / r.sum())


def bootstrap_ci(x, fn=np.median, n_boot=10000, seed=0, level=0.95):
    x = np.asarray(x, float)
    rng = np.random.default_rng(seed)
    bs = np.array([fn(x[rng.integers(0, len(x), len(x))]) for _ in range(n_boot)])
    lo, hi = np.quantile(bs, [(1 - level) / 2, 1 - (1 - level) / 2])
    return float(lo), float(hi)


def paired_wilcoxon(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ok = np.isfinite(a) & np.isfinite(b)
    a, b = a[ok], b[ok]
    d = a - b
    if len(d) < 3 or np.all(d == 0):
        return {"n": len(d), "statistic": np.nan, "p": np.nan, "rank_biserial": rank_biserial(d),
                "median_diff": float(np.median(d)) if len(d) else np.nan, "ci_lo": np.nan, "ci_hi": np.nan}
    res = stats.wilcoxon(a, b, alternative="two-sided", zero_method="wilcox")
    lo, hi = bootstrap_ci(d)
    return {"n": len(d), "statistic": float(res.statistic), "p": float(res.pvalue), "rank_biserial": rank_biserial(d),
            "median_diff": float(np.median(d)), "ci_lo": lo, "ci_hi": hi}


def one_sample_wilcoxon(x, mu0, alternative="less"):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    d = x - mu0
    res = stats.wilcoxon(d, alternative=alternative, zero_method="wilcox")
    lo, hi = bootstrap_ci(x)
    return {"n": len(x), "statistic": float(res.statistic), "p": float(res.pvalue), "median": float(np.median(x)),
            "ci_lo": lo, "ci_hi": hi, "rank_biserial": rank_biserial(d)}


def holm(pvals):
    p = np.asarray(pvals, float)
    out = np.full_like(p, np.nan)
    ok = np.isfinite(p)
    idx = np.argsort(p[ok])
    m = ok.sum()
    adj = np.empty(m)
    run = 0.0
    for rank, i in enumerate(idx):
        run = max(run, min(1.0, (m - rank) * p[ok][i]))
        adj[i] = run
    out[ok] = adj
    return out


def seed_summary(x):
    x = np.asarray(x, float)
    return {"mean": float(np.mean(x)), "sd": float(np.std(x, ddof=1)) if len(x) > 1 else 0.0,
            "p2.5": float(np.quantile(x, 0.025)), "p97.5": float(np.quantile(x, 0.975)), "n_seeds": len(x)}
