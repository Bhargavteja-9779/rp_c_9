# Family-calibrated conformal prediction (FCP) for alloy property models

Code and data pipeline for the manuscript *"Prediction intervals that remain valid for unseen alloy families: family-calibrated conformal prediction for machine-learned alloy properties"* (submitted to *Journal of Materials Research and Technology*).

Every number, table and figure in the manuscript is produced by `run_all.py` from public data. Nothing is typed in by hand.

## 1. Installation
CPU only; no GPU needed. The code was tested with Python 3.13 on Linux (4 cores, 16 GB RAM).
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # or: conda env create -f environment.yml
```
`run_all.py` reports detected hardware (CPU / CUDA / Apple MPS) in `results/logs/run_info.json`. All models are CPU tree ensembles and kernel methods, so accelerators are not used.

## 2. Data
```bash
python scripts/download_data.py
```
This downloads the six public datasets into `data/raw/` and writes `SHA256SUMS.txt`:

| Task key | Property | Source |
|---|---|---|
| `mpea_hv`, `mpea_ys` | Vickers hardness; yield strength of multi-principal-element alloys | Borg et al., *Sci. Data* 7 (2020) 430, GitHub `CitrineInformatics/MPEA_dataset` |
| `steel_ys` | Yield strength of steels | Matbench `matbench_steels` (Dunn et al., *npj Comput. Mater.* 6 (2020) 138) via matminer |
| `superhard_k` | Bulk modulus | Mansouri Tehrani et al., *JACS* 140 (2018) 9844, via matminer |
| `expt_hf` | Experimental formation enthalpy | Kingsbury et al., *npj Comput. Mater.* 8 (2022) 195, via matminer |
| `supercon_tc` | Superconducting Tc | Hamidieh, *Comput. Mater. Sci.* 154 (2018) 346; UCI ML repository id 464 (CC BY 4.0) |

Cleaning (`src/fcp/data/datasets.py`): identical inputs are merged by median target. Featurization and families: `src/fcp/preprocessing/features.py`. Processed tasks are cached in `data/processed/`.

## 3. Reproduce everything
```bash
python run_all.py --mode quick   # ~1 min pipeline check, writes results_quick/ (NOT the paper's numbers)
python run_all.py --mode full    # full study, roughly 8–10 h on 4 cores; writes results/
```
Stages can be run separately and are resumable, because each run is cached in `results/cache/`:
```bash
python run_all.py --mode full --stage data
python run_all.py --mode full --stage main            # Exp 1–3 (main, baselines, ablation): 6 tasks x 3 protocols x 10 seeds
python run_all.py --mode full --stage robustness      # Exp 4: label noise, reduced training data
python run_all.py --mode full --stage generalization  # Exp 5: mis-specified family definition
python run_all.py --mode full --stage sensitivity     # Exp 7: hyper-parameters
python run_all.py --mode full --stage efficiency      # Exp 6: wall time / memory
python run_all.py --mode full --stage analysis        # statistics, tables, figures from cached runs
```
Then build the manuscript (DOCX) from the generated results:
```bash
cd ../manuscript/tools && python build_manuscript.py && node build_docx.js spec.json ../Final_Manuscript.docx
```

## 4. Outputs
| Path | Content |
|---|---|
| `results/raw_results.csv` | one row per task × protocol × seed × method × α (all metrics) |
| `results/metrics.json`, `results/statistics.json` | summary metrics; hypothesis tests (Wilcoxon, Holm, effect sizes, bootstrap CIs) |
| `results/{robustness,generalization,sensitivity,efficiency}_results.csv` | Experiments 4–7 |
| `results/tables/*.csv / *.md` | every manuscript table |
| `results/figures/*.png / *.pdf` | every manuscript figure |
| `results/logs/` | run log and hardware/config record |

## 5. Code map
```
config/default.yaml          pre-specified configuration (full); config/quick.yaml (pipeline check)
src/fcp/data/datasets.py     loaders and cleaning
src/fcp/preprocessing/       Magpie features, element fractions, alloy families (F1 system, F2 cluster)
src/fcp/models/base.py       family-bagged LightGBM, novelty scorer, scale model (log-linear, monotone)
src/fcp/models/conformal.py  CrossFit (CV+ with grouped/random folds, normalization, weights), SCP, WCP, CQR, GP, RF
src/fcp/evaluation/          outer protocol (random/system/cluster), metrics
src/fcp/statistics/tests.py  Wilcoxon, Holm, rank-biserial, bootstrap
experiments/                 stages, runner (caching), analysis (tables, figures)
tests/                       unit tests:  python -m pytest tests -q
scripts/                     data download, citation audit
```

## 6. Using FCP on your own data
```python
from fcp.models.conformal import CrossFit
cf = CrossFit(K=5, grouped=True, n_members=6, family_frac=0.7).fit(X_train, y_train, families_train, X_new)
lo, hi = cf.intervals(alpha=0.1, sigma_mode="both", family_weights=False)   # FCP
lo_w, hi_w = cf.intervals(alpha=0.1, sigma_mode="both", family_weights=True) # FCP-W (needs >= 9 families at alpha=0.1)
```
`families_train` should encode what "new" means in your application, for example the chemical system (`fam_system`).

## 7. Determinism
Seeds are fixed in `config/default.yaml` (0–9). All randomness (folds, bagging, LightGBM, k-means, GP) derives from them. Results are bit-reproducible on the same library versions; across platforms, LightGBM may differ in the last digits.

## Licence
Code: MIT. Data: see the original sources.
