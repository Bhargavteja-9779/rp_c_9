"""Interval methods.

Notation: alpha = miscoverage level; target coverage 1 - alpha.

Cross-fitted family (CV+ form, Barber et al., Ann. Stat. 2021):
    K folds over the training data (assigned by *family* for grouped variants, by row for random variants).
    For fold k a FamilyBaggedLGBM mu_k is fitted on D_{-k}, together with its own NoveltyScorer d_k and ScaleModel
    sigma_k (fitted on family-out-of-bag residuals inside D_{-k} only).
    Score of calibration row i (in fold k(i)):  S_i = |y_i - mu_{k(i)}(x_i)| / sigma_{k(i)}(x_i)
    Interval for test x:
        lower = weighted alpha-quantile of { mu_{k(i)}(x) - S_i sigma_{k(i)}(x) } with an extra mass w_inf at -inf
        upper = weighted (1-alpha)-quantile of { mu_{k(i)}(x) + S_i sigma_{k(i)}(x) } with mass w_inf at +inf
    Unweighted: w_i = 1, w_inf = 1  -> standard (normalized) CV+.
    Family-weighted (proposed): w_i = 1 / n_{g(i)}, w_inf = 1, i.e. every training family carries unit mass and
    the test point is treated as one new family (pooled-CDF construction of Dunn, Wasserman & Ramdas, JASA 2023).
"""
import numpy as np
import lightgbm as lgb
from scipy.stats import norm
from sklearn.ensemble import RandomForestRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF, WhiteKernel
from sklearn.linear_model import LogisticRegression

from .base import FamilyBaggedLGBM, NoveltyScorer, ScaleModel, DEFAULT_LGBM

SIGMA_MODES = ("none", "spread", "novelty", "both")


# ----------------------------------------------------------------------------------------------- utilities
def weighted_upper(V, w, w_inf, level):
    """Row-wise smallest v such that sum_{V_i <= v} w_i / (sum w + w_inf) >= level; +inf if never reached.
    V: (t, n) values, w: (n,) weights."""
    idx = np.argsort(V, axis=1)
    Vs = np.take_along_axis(V, idx, axis=1)
    cw = np.cumsum(w[idx], axis=1) / (w.sum() + w_inf)
    pos = (cw < level - 1e-12).sum(axis=1)
    out = np.full(V.shape[0], np.inf)
    ok = pos < V.shape[1]
    out[ok] = Vs[np.where(ok)[0], pos[ok]]
    return out


def weighted_lower(V, w, w_inf, level):
    """Row-wise lower bound at miscoverage `level` (e.g. alpha): largest v such that the weighted mass of
    {V_i >= v} plus w_inf (a point mass at -inf) is at least 1 - level. Equals -weighted_upper(-V, ., 1 - level)."""
    return -weighted_upper(-V, w, w_inf, 1 - level)


def assign_folds(n, K, groups=None, seed=0, balanced=True):
    """Random fold assignment. If groups is given, whole groups are assigned, so no family is split across folds.
    balanced=True : greedy size balancing after a seeded shuffle (deterministic when all group sizes differ, e.g.
                    10 composition clusters -> identical partition for every seed).
    balanced=False: seeded random permutation of groups dealt round-robin (equal number of groups per fold)."""
    rng = np.random.default_rng(seed)
    folds = np.empty(n, dtype=int)
    if groups is None:
        perm = rng.permutation(n)
        folds[perm] = np.arange(n) % K
        return folds
    groups = np.asarray(groups)
    fams, counts = np.unique(groups, return_counts=True)
    if not balanced:
        perm = rng.permutation(len(fams))
        fam_fold = {fams[j]: r % K for r, j in enumerate(perm)}
        return np.array([fam_fold[g] for g in groups])
    order = rng.permutation(len(fams))
    # shuffle, then largest-first greedy (ties broken by the shuffle) to balance fold sizes
    order = order[np.argsort(-counts[order], kind="stable")]
    load = np.zeros(K)
    fam_fold = {}
    for j in order:
        k = int(np.argmin(load + rng.random(K) * 1e-9))
        fam_fold[fams[j]] = k
        load[k] += counts[j]
    for i, g in enumerate(groups):
        folds[i] = fam_fold[g]
    return folds


# ----------------------------------------------------------------------------------------- cross-fitting
class CrossFit:
    """Fits the K fold models once; intervals for any (sigma mode, weighting, alpha) are then derived cheaply."""

    def __init__(self, K=5, grouped=True, n_members=8, family_frac=0.7, lgbm_params=None, novelty_k=5,
                 novelty_pcs=16, seed=0, clip_scale=False, member="lgbm", rf_trees=50):
        self.K, self.grouped, self.clip = K, grouped, clip_scale
        self.kw = dict(n_members=n_members, family_frac=family_frac, lgbm_params=lgbm_params, member=member,
                       rf_trees=rf_trees)
        self.nk, self.npc, self.seed = novelty_k, novelty_pcs, seed

    def fit(self, X, y, groups, X_test):
        n = len(y)
        self.folds = assign_folds(n, self.K, groups if self.grouped else None, seed=self.seed)
        self.groups = np.asarray(groups)
        self.y = y
        self.cal = {"mu": np.empty(n), "s": np.empty(n), "d": np.empty(n)}
        self.test = []
        self.scale_models = {m: [] for m in SIGMA_MODES}
        for k in range(self.K):
            tr, ca = self.folds != k, self.folds == k
            if ca.sum() == 0:
                raise ValueError("empty fold")
            base = FamilyBaggedLGBM(seed=self.seed * 1000 + k, **self.kw).fit(X[tr], y[tr], self.groups[tr])
            nov = NoveltyScorer(self.npc, self.nk).fit(X[tr], self.groups[tr])
            # family-out-of-bag quantities inside D_{-k} (for fitting the scale model only)
            fmu, fsd = base.foob(X[tr], self.groups[tr])
            fd = nov.foob_score()
            r = np.abs(y[tr] - fmu)
            for m in SIGMA_MODES:
                self.scale_models[m].append(ScaleModel(m, clip=self.clip).fit(r, fsd, fd))
            mu, sd = base.predict(X[ca])
            self.cal["mu"][ca], self.cal["s"][ca], self.cal["d"][ca] = mu, sd, nov.score(X[ca])
            tmu, tsd = base.predict(X_test)
            self.test.append({"mu": tmu, "s": tsd, "d": nov.score(X_test)})
        return self

    def point_prediction(self):
        return np.mean([t["mu"] for t in self.test], axis=0)

    def intervals(self, alpha, sigma_mode="none", family_weights=False, chunk=400):
        n = len(self.y)
        sig_cal = np.empty(n)
        for k in range(self.K):
            ca = self.folds == k
            sig_cal[ca] = self.scale_models[sigma_mode][k].predict(self.cal["s"][ca], self.cal["d"][ca])
        S = np.abs(self.y - self.cal["mu"]) / sig_cal
        if family_weights:
            _, inv, cnt = np.unique(self.groups, return_inverse=True, return_counts=True)
            w = 1.0 / cnt[inv]
        else:
            w = np.ones(n)
        w_inf = 1.0
        nt = len(self.test[0]["mu"])
        mu_t = np.stack([t["mu"] for t in self.test])          # (K, nt)
        sig_t = np.stack([self.scale_models[sigma_mode][k].predict(self.test[k]["s"], self.test[k]["d"])
                          for k in range(self.K)])            # (K, nt)
        lo, hi = np.empty(nt), np.empty(nt)
        for a in range(0, nt, chunk):
            b = min(nt, a + chunk)
            M = mu_t[self.folds, a:b].T                        # (t, n): mu_{k(i)}(x_j)
            Sg = sig_t[self.folds, a:b].T * S[None, :]
            lo[a:b] = weighted_lower(M - Sg, w, w_inf, alpha)
            hi[a:b] = weighted_upper(M + Sg, w, w_inf, 1 - alpha)
        return lo, hi


# ------------------------------------------------------------------------------------------ split methods
def split_conformal(base_mu_cal, y_cal, base_mu_test, alpha):
    S = np.abs(y_cal - base_mu_cal)
    n = len(S)
    q = np.inf if np.ceil((n + 1) * (1 - alpha)) > n else np.sort(S)[int(np.ceil((n + 1) * (1 - alpha))) - 1]
    return base_mu_test - q, base_mu_test + q


def weighted_split_conformal(mu_cal, y_cal, mu_test, ratio_cal, ratio_test, alpha):
    """Tibshirani et al. (NeurIPS 2019): weights proportional to estimated density ratio dP_test/dP_train."""
    S = np.abs(y_cal - mu_cal)
    o = np.argsort(S)
    Ss, cw = S[o], np.cumsum(ratio_cal[o])
    tot = cw[-1] + ratio_test
    pos = np.searchsorted(cw, (1 - alpha) * tot - 1e-12, side="left")
    q = np.where(pos < len(S), Ss[np.minimum(pos, len(S) - 1)], np.inf)
    return mu_test - q, mu_test + q


def density_ratio(Z_cal, Z_test, seed=0):
    """Probabilistic classifier estimate of dP_test/dP_cal (logistic regression on PCA features)."""
    Z = np.vstack([Z_cal, Z_test])
    lab = np.r_[np.zeros(len(Z_cal)), np.ones(len(Z_test))]
    clf = LogisticRegression(C=1.0, max_iter=2000, random_state=seed).fit(Z, lab)
    p_c = np.clip(clf.predict_proba(Z_cal)[:, 1], 0.01, 0.99)
    p_t = np.clip(clf.predict_proba(Z_test)[:, 1], 0.01, 0.99)
    c = len(Z_cal) / len(Z_test)
    return p_c / (1 - p_c) * c, p_t / (1 - p_t) * c


def cqr(X_tr, y_tr, X_cal, y_cal, X_test, alpha, lgbm_params=None, seed=0):
    """Conformalized quantile regression (Romano et al., NeurIPS 2019) with LightGBM quantile models."""
    p = dict(DEFAULT_LGBM, **(lgbm_params or {}))
    p.pop("objective", None)
    lo_m = lgb.LGBMRegressor(objective="quantile", alpha=alpha / 2, random_state=seed, **p).fit(X_tr, y_tr)
    hi_m = lgb.LGBMRegressor(objective="quantile", alpha=1 - alpha / 2, random_state=seed, **p).fit(X_tr, y_tr)
    E = np.maximum(lo_m.predict(X_cal) - y_cal, y_cal - hi_m.predict(X_cal))
    n = len(E)
    kk = int(np.ceil((n + 1) * (1 - alpha)))
    q = np.inf if kk > n else np.sort(E)[kk - 1]
    return lo_m.predict(X_test) - q, hi_m.predict(X_test) + q


def gaussian_interval(mu, sd, alpha):
    z = norm.ppf(1 - alpha / 2)
    return mu - z * sd, mu + z * sd


def gp_fit_predict(Z_tr, y_tr, Z_test, max_train=1500, seed=0):
    rng = np.random.default_rng(seed)
    if len(y_tr) > max_train:
        idx = rng.choice(len(y_tr), max_train, replace=False)
        Z_tr, y_tr = Z_tr[idx], y_tr[idx]
    kern = ConstantKernel(1.0, (1e-3, 1e3)) * RBF(np.ones(Z_tr.shape[1]), (1e-2, 1e3)) + WhiteKernel(0.1, (1e-6, 1e1))
    gp = GaussianProcessRegressor(kern, normalize_y=True, random_state=seed, n_restarts_optimizer=0).fit(Z_tr, y_tr)
    return gp.predict(Z_test, return_std=True)


def rf_fit_predict(X_tr, y_tr, X_test, seed=0):
    rf = RandomForestRegressor(n_estimators=300, max_features=0.33, min_samples_leaf=1, n_jobs=1,
                               random_state=seed).fit(X_tr, y_tr)
    P = np.stack([t.predict(X_test) for t in rf.estimators_])
    return P.mean(0), P.std(0, ddof=1)


class CrossFitRFSigma:
    """Iteration 2 (Reviewer-8 hypothesis): CV+ normalized directly by random-forest tree spread.
    For fold k a RandomForest (300 trees, max_features 1/3) is fitted on D_{-k}; s_k(x) = SD over trees;
    sigma_k(x) = s_k(x) + beta_k with beta_k = 0.1 * median s_k over the calibration fold (features only, no labels).
    Folds grouped by family (FCP-RFsigma) or random (CV+-RFsigma); unit weights."""

    def __init__(self, K=5, grouped=True, seed=0, n_trees=300):
        self.K, self.grouped, self.seed, self.n_trees = K, grouped, seed, n_trees

    def fit(self, X, y, groups, X_test):
        n = len(y)
        self.folds = assign_folds(n, self.K, groups if self.grouped else None, seed=self.seed)
        self.y = y
        mu_c, sig_c = np.empty(n), np.empty(n)
        self.mu_t, self.sig_t = [], []
        for k in range(self.K):
            tr, ca = self.folds != k, self.folds == k
            mu, sd = rf_fit_predict(X[tr], y[tr], np.vstack([X[ca], X_test]), seed=self.seed * 1000 + k)
            nc = int(ca.sum())
            beta = 0.1 * np.median(sd[:nc]) + 1e-12
            mu_c[ca], sig_c[ca] = mu[:nc], sd[:nc] + beta
            self.mu_t.append(mu[nc:]); self.sig_t.append(sd[nc:] + beta)
        self.S = np.abs(y - mu_c) / sig_c
        return self

    def intervals(self, alpha, chunk=400):
        n = len(self.y); w = np.ones(n)
        mu_t, sig_t = np.stack(self.mu_t), np.stack(self.sig_t)
        nt = mu_t.shape[1]
        lo, hi = np.empty(nt), np.empty(nt)
        for a in range(0, nt, chunk):
            b = min(nt, a + chunk)
            M = mu_t[self.folds, a:b].T
            Sg = sig_t[self.folds, a:b].T * self.S[None, :]
            lo[a:b] = weighted_lower(M - Sg, w, 1.0, alpha)
            hi[a:b] = weighted_upper(M + Sg, w, 1.0, 1 - alpha)
        return lo, hi
