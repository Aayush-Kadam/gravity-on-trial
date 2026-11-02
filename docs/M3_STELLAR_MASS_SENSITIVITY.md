# M3 stellar-mass sensitivity

Six frozen fixed stellar perturbations per galaxy: disk-only, bulge-only, joint +/-0.1 dex around 0.5/0.7 solar M/L. Same 175 galaxies, observed radii/errors, halo bounds/starts, H0 and fixed RAR acceleration scale. No unrelated nuisance parameter was refit; only the halo's two free parameters remain fitted. Signed gas always preserved.

Named stellar scenario outcomes among 107 decisive M2 baselines (each row denominator 107):

| Scenario | Retained | Different preference | Inconclusive | Unavailable | Invalid proposal | Not applicable |
|---|---:|---:|---:|---:|---:|---:|
| ML_disk_minus01dex | 98 | 3 | 6 | 0 | 0 | 0 |
| ML_disk_plus01dex | 86 | 2 | 6 | 13 | 0 | 0 |
| ML_bulge_minus01dex | 19 | 2 | 1 | 0 | 0 | 85 |
| ML_bulge_plus01dex | 16 | 4 | 0 | 2 | 0 | 85 |
| ML_joint_minus01dex | 94 | 5 | 8 | 0 | 0 | 0 |
| ML_joint_plus01dex | 79 | 6 | 6 | 16 | 0 | 0 |

Null bulge-only shifts are explicitly NOT_APPLICABLE, not artificial support for persistence. Joint and disk-only shifts coincide when the bulge is absent; primary fractions retain the frozen named-grid weights, not independent-sample weights. Such overlap and every invalid/unavailable state are saved. This grid does not exhaust stellar-population uncertainties.

Per-model before/after parameter values, prediction changes in km/s, catalog-frame data likelihood, AICc/BIC applicability, conditioning and bounds are in model_evaluations.csv and full per-galaxy JSON. Ranges use log10 physical units encoded in parameter names. They are scenario spans, not confidence/credible intervals. M3 physical cases do not alter model complexity to make an assumption perturbation look like an extra fitted parameter. Static figures 02 and 05 and selected galaxy before/after curves derive from these actual arrays.
