"""Unit tests for the interval machinery (run: python -m pytest tests -q)."""
import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fcp.models import conformal as C
from fcp.models.base import ScaleModel, FamilyBaggedLGBM, NoveltyScorer
from fcp.evaluation.metrics import interval_metrics
from fcp.statistics import tests as T


def test_weighted_quantiles_match_cvplus_order_statistics():
    rng = np.random.default_rng(0)
    V = rng.normal(size=(3, 99))
    w = np.ones(99)
    k = int(np.ceil(0.9 * 100))
    up = C.weighted_upper(V, w, 1.0, 0.9)
    lo = C.weighted_lower(V, w, 1.0, 0.1)
    for j in range(3):
        assert up[j] == np.sort(V[j])[k - 1]
        assert lo[j] == -np.sort(-V[j])[k - 1]


def test_weighted_upper_infinite_when_too_few_units():
    # 8 families of unit mass + test mass 1 => max attainable level 8/9 < 0.9 => +inf
    V = np.arange(8, dtype=float)[None, :]
    assert np.isinf(C.weighted_upper(V, np.ones(8), 1.0, 0.9))[0]


def test_grouped_folds_never_split_a_family():
    g = np.repeat(np.arange(30), 7).astype(str)
    f = C.assign_folds(len(g), 5, g, seed=3)
    for fam in np.unique(g):
        assert len(np.unique(f[g == fam])) == 1
    assert len(np.unique(f)) == 5


def test_split_conformal_coverage_exchangeable():
    rng = np.random.default_rng(1)
    covs = []
    for _ in range(200):
        y = rng.normal(size=201)
        lo, hi = C.split_conformal(np.zeros(100), y[:100], np.zeros(101), 0.1)
        covs.append(np.mean((y[100:] >= lo) & (y[100:] <= hi)))
    assert 0.88 <= np.mean(covs) <= 0.93


def test_cvplus_coverage_iid_synthetic():
    rng = np.random.default_rng(2)
    n = 400
    X = rng.normal(size=(n, 4)).astype(np.float32); y = X[:, 0] + rng.normal(0, 0.3, n)
    Xt = rng.normal(size=(400, 4)).astype(np.float32); yt = Xt[:, 0] + rng.normal(0, 0.3, 400)
    g = rng.integers(0, 40, n).astype(str)
    cf = C.CrossFit(K=5, grouped=True, n_members=3, lgbm_params={"n_estimators": 60}).fit(X, y, g, Xt)
    for mode in ("none", "both"):
        lo, hi = cf.intervals(0.1, mode, False)
        assert np.mean((yt >= lo) & (yt <= hi)) >= 0.85


def test_scale_model_monotone_and_fallback():
    rng = np.random.default_rng(3)
    s = rng.uniform(0.1, 2, 500); d = rng.uniform(0.1, 2, 500)
    r = np.abs(rng.normal(0, s * d))
    m = ScaleModel("both").fit(r, s, d)
    assert m.coef_[1] >= 0 and m.coef_[2] >= 0
    assert m.predict(np.array([2.0]), np.array([2.0]))[0] > m.predict(np.array([0.2]), np.array([0.2]))[0]
    fb = ScaleModel("both").fit(np.full(5, np.nan), np.ones(5), np.ones(5))
    assert fb.fallback_ and np.allclose(fb.predict(np.ones(3), np.ones(3)), 1.0)


def test_family_out_of_bag_only_uses_unseen_members():
    rng = np.random.default_rng(4)
    X = rng.normal(size=(300, 3)).astype(np.float32); y = X[:, 0]
    g = rng.integers(0, 20, 300).astype(str)
    b = FamilyBaggedLGBM(n_members=5, family_frac=0.6, lgbm_params={"n_estimators": 20}, seed=0).fit(X, y, g)
    mu, sd = b.foob(X, g)
    P = b.member_predictions(X)
    i = int(np.where(np.isfinite(mu))[0][0])
    excl = [m for m, fams in enumerate(b.bag_fams) if g[i] not in fams]
    assert np.isclose(mu[i], P[excl, i].mean())


def test_novelty_foob_excludes_own_family():
    X = np.vstack([np.zeros((5, 3)), np.ones((5, 3)) * 10]).astype(np.float32)
    g = np.array(["a"] * 5 + ["b"] * 5)
    nv = NoveltyScorer(n_components=2, k=2).fit(X, g)
    d = nv.foob_score()
    assert np.all(d > 1.0)  # nearest other-family rows are far away


def test_metrics_and_stats():
    y = np.array([0., 1, 2, 3]); lo = y - 1; hi = y + 1; hi[0] = -0.5
    m = interval_metrics(y, lo, hi, 0.1, np.array(["a", "a", "b", "b"]), np.arange(4.), 1.0)
    assert m["coverage"] == 0.75 and m["family_coverage"] == 0.75
    assert np.allclose(T.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
    r = T.paired_wilcoxon(np.arange(10.), np.arange(10.) + 1)
    assert r["median_diff"] == -1 and r["rank_biserial"] == -1


def test_scale_model_clamps_inputs_v2():
    rng = np.random.default_rng(5)
    s = rng.uniform(1, 2, 300); d = rng.uniform(1, 2, 300)
    r = np.abs(rng.normal(0, s * d))
    m = ScaleModel("both", clip=True).fit(r, s, d)
    far = m.predict(np.array([1e6]), np.array([1e6]))[0]
    edge = m.predict(np.array([2.0]), np.array([2.0]))[0]
    assert np.isclose(far, m.predict(np.array([s.max()]), np.array([d.max()]))[0])
    assert far <= edge * 1.01
    m1 = ScaleModel("both", clip=False).fit(r, s, d)
    assert m1.predict(np.array([1e6]), np.array([1e6]))[0] > far  # v1 extrapolates


def test_unbalanced_assignment_varies_with_seed():
    g = np.repeat([f"c{i}" for i in range(10)], np.arange(10, 20))
    parts = {tuple(C.assign_folds(len(g), 5, g, seed=s, balanced=False)) for s in range(5)}
    balanced = {tuple(C.assign_folds(len(g), 5, g, seed=s, balanced=True)) for s in range(5)}
    assert len(parts) > 1
    assert len(balanced) >= 1


def test_inverted_interval_counts_as_empty():
    y = np.array([0.0, 1.0]); lo = np.array([0.5, 0.0]); hi = np.array([-0.5, 2.0])  # first interval inverted
    m = interval_metrics(y, lo, hi, 0.1, np.array(["a", "b"]), np.array([0.0, 1.0]), 1.0)
    assert m["coverage"] == 0.5 and m["empty_rate"] == 0.5
    assert m["width_sd"] == 1.0  # (0 + 2) / 2


def test_family_subsample_weights():
    g = np.repeat(["a", "b", "c", "d"], [1, 5, 20, 3])
    w = C.calibration_weights(g, "subsample", seed=3)
    assert set(np.unique(w)) <= {0.0, 1.0}
    for f in "abcd":
        assert w[g == f].sum() == 1.0                   # exactly one alloy per family
    assert np.isclose(C.calibration_weights(g, True).sum(), 4.0)  # FCP-W: unit mass per family
    assert C.calibration_weights(g, False).sum() == len(g)
    picks = np.array([np.argmax(C.calibration_weights(g, "subsample", seed=s)[g == "c"]) for s in range(400)])
    assert len(np.unique(picks)) > 15                   # the draw is (approximately) uniform within a family
