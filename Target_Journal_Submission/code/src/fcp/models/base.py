"""Base predictor, novelty scorer and difficulty (scale) model.

FamilyBaggedLGBM
    An ensemble of M LightGBM regressors, each trained on a random subset (fraction `family_frac`) of the
    *families* present in the training data. Two by-products are used for uncertainty:
      * spread s(x): standard deviation of member predictions (family-level model disagreement);
      * family-out-of-bag (FOOB) predictions for training rows: each row is predicted only by members that did
        not see its family, which mimics the error made on an unseen family.
    All interval methods in the study share this base predictor, so they differ only in how they calibrate.

NoveltyScorer
    d(x) = mean Euclidean distance to the k nearest training rows in a standardized, PCA-reduced feature space.
    For training rows, `foob_score` excludes rows of the same family (distance to *other* families).

ScaleModel
    log sigma(x) = a + b log s(x) + c log d(x), with b, c >= 0, fitted by bounded least squares to log|FOOB residual|.
    Fitted only on the training data that the corresponding point model saw, so calibration labels never leak.
"""
import numpy as np
import lightgbm as lgb
from scipy.optimize import lsq_linear
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

DEFAULT_LGBM = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=5, subsample=0.8,
                    subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, n_jobs=1, verbose=-1)
EPS = 1e-12


class FamilyBaggedLGBM:
    def __init__(self, n_members=8, family_frac=0.7, lgbm_params=None, seed=0, member="lgbm", rf_trees=50):
        self.M, self.frac = int(n_members), float(family_frac)
        self.params = dict(DEFAULT_LGBM, **(lgbm_params or {}))
        self.seed, self.member, self.rf_trees = seed, member, rf_trees

    def _new_member(self, rs):
        if self.member == "rf":  # random-forest members (base-learner swap experiment)
            from sklearn.ensemble import RandomForestRegressor
            return RandomForestRegressor(n_estimators=self.rf_trees, max_features=0.33, min_samples_leaf=1, n_jobs=1,
                                         random_state=rs)
        return lgb.LGBMRegressor(random_state=rs, **self.params)

    def fit(self, X, y, groups):
        rng = np.random.default_rng(self.seed)
        groups = np.asarray(groups)
        fams = np.unique(groups)
        self.members, self.bag_fams = [], []
        for m in range(self.M):
            if len(fams) >= 3:
                k = max(1, int(np.ceil(self.frac * len(fams))))
                chosen = rng.choice(fams, size=k, replace=False)
                mask = np.isin(groups, chosen)
            else:  # degenerate case: too few families -> row subsampling
                chosen = fams
                mask = rng.random(len(y)) < self.frac
            mdl = self._new_member(int(rng.integers(1 << 31)))
            mdl.fit(X[mask], y[mask])
            self.members.append(mdl)
            self.bag_fams.append(set(chosen.tolist()))
        return self

    def member_predictions(self, X):
        return np.stack([m.predict(X) for m in self.members], axis=0)  # (M, n)

    def predict(self, X):
        P = self.member_predictions(X)
        return P.mean(0), P.std(0, ddof=1)

    def foob(self, X, groups):
        """Family-out-of-bag mean/std for training rows (NaN where fewer than 2 members excluded the family)."""
        P = self.member_predictions(X)
        excl = np.stack([~np.isin(groups, list(b)) for b in self.bag_fams], axis=0)  # (M, n) True = unseen family
        cnt = excl.sum(0)
        Pm = np.where(excl, P, 0.0)
        c1 = np.maximum(cnt, 1)
        mu = Pm.sum(0) / c1
        sd = np.sqrt(np.maximum(((Pm - mu) ** 2 * excl).sum(0), 0) / np.maximum(cnt - 1, 1))
        mu[cnt < 1] = np.nan
        sd[cnt < 2] = np.nan
        return mu, sd


class NoveltyScorer:
    def __init__(self, n_components=16, k=5):
        self.nc, self.k = n_components, k

    def fit(self, X, groups):
        self.scaler = StandardScaler().fit(X)
        Z = self.scaler.transform(X)
        self.pca = PCA(n_components=min(self.nc, Z.shape[1], Z.shape[0] - 1), random_state=0).fit(Z)
        self.Ztr = self.pca.transform(Z)
        self.groups = np.asarray(groups)
        self.nn = NearestNeighbors().fit(self.Ztr)
        return self

    def transform(self, X):
        return self.pca.transform(self.scaler.transform(X))

    def score(self, X):
        k = min(self.k, len(self.Ztr))
        d, _ = self.nn.kneighbors(self.transform(X), n_neighbors=k)
        return d.mean(1) + EPS

    def foob_score(self):
        """Distance of each training row to the k nearest rows of OTHER families."""
        out = np.empty(len(self.Ztr))
        n = len(self.Ztr)
        for g in np.unique(self.groups):
            idx = np.where(self.groups == g)[0]
            m = min(n, self.k + len(idx))
            d, j = self.nn.kneighbors(self.Ztr[idx], n_neighbors=m)
            other = self.groups[j] != g
            for r in range(len(idx)):
                dd = d[r][other[r]][: self.k]
                out[idx[r]] = dd.mean() if len(dd) else np.nan
        return out + EPS


class ScaleModel:
    """sigma(x) = exp(a + b*log s + c*log d), b,c >= 0. mode in {'none','spread','novelty','both'}.
    clip=True (v2): log s and log d are clamped to the range observed in the fitting data before prediction, so the
    log-linear scale is never extrapolated (v1, clip=False, produced a few unbounded intervals for extreme novelty)."""

    def __init__(self, mode="both", clip=False):
        self.mode, self.clip = mode, clip

    def _design(self, s, d):
        s = np.asarray(s, float); d = np.asarray(d, float)
        if self.clip and getattr(self, "lims_", None) is not None:
            (s0, s1), (d0, d1) = self.lims_
            s = np.clip(s, s0, s1); d = np.clip(d, d0, d1)
        cols = [np.ones_like(s)]
        if self.mode in ("spread", "both"):
            cols.append(np.log(np.maximum(s, EPS)))
        if self.mode in ("novelty", "both"):
            cols.append(np.log(np.maximum(d, EPS)))
        return np.stack(cols, 1)

    def fit(self, abs_resid, s, d):
        if self.mode == "none":
            return self
        ok = np.isfinite(abs_resid) & np.isfinite(s) & np.isfinite(d) & (s > 0)
        self.lims_ = None
        A = self._design(s[ok], d[ok])
        if ok.any():
            self.lims_ = ((s[ok].min(), s[ok].max()), (d[ok].min(), d[ok].max()))
        t = np.log(abs_resid[ok] + 1e-6 * (np.median(abs_resid[ok]) + EPS))
        lb = np.r_[-np.inf, np.zeros(A.shape[1] - 1)]
        self.fallback_ = ok.sum() <= max(10, A.shape[1] + 2)
        if not self.fallback_:
            self.coef_ = lsq_linear(A, t, bounds=(lb, np.full(A.shape[1], np.inf))).x
            self.floor_ = np.quantile(np.exp(A @ self.coef_), 0.05)  # guards against degenerate tiny scales
        else:  # too few family-out-of-bag rows: constant scale (equivalent to mode 'none')
            self.coef_ = np.zeros(A.shape[1])
            self.floor_ = 1.0
        return self

    def predict(self, s, d):
        if self.mode == "none":
            return np.ones_like(np.asarray(s, dtype=float))
        sig = np.exp(self._design(np.asarray(s, float), np.asarray(d, float)) @ self.coef_)
        return np.maximum(sig, self.floor_)
