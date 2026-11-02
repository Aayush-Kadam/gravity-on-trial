# M1 statistical comparison

All F0 comparisons share masks, fixed stellar ratios/geometry and normalized velocity likelihood. Halo k=2, baryons/RAR k=0. F1 has model-specific identifiable-input parameter counts and is MAP; all its information criteria are null. Degrees of freedom are nominal n−k, not Bayesian effective degrees of freedom. Boundary contact and data identifiability are reported separately from convergence. Physical admissibility means finite nonnegative speeds and parameters inside physical bounds; it is not external evidence that a parameter is cosmologically plausible.

| Galaxy | Lowest F0 chi² | Lowest F0 BIC | BIC runner-up gap | Lowest data chi² among F1 MAP solutions |
|---|---|---|---:|---|
| NGC3198 | nfw | nfw | 12.904 | nfw |
| NGC2403 | nfw | nfw | 1031.463 | nfw |
| NGC3741 | nfw | nfw | 15.778 | nfw |
| DDO154 | burkert | burkert | 105.276 | burkert |
| NGC2841 | nfw | nfw | 175.365 | nfw |
| UGC00731 | nfw | nfw | 2.306 | nfw |
| NGC4157 | burkert | burkert | 0.349 | burkert |
| F567-2 | burkert | burkert | 0.724 | burkert |

Continuous score gaps are descriptive; no post-hoc significance/probability threshold is imposed. A small gap signals limited separation under the declared likelihood. F1 column describes residual ordering at MAP solutions, not a maximum-likelihood ranking or posterior model probability. Differences across F0/F1 cannot be attributed to more data: they are induced by changed assumptions and nuisance freedom. Eight selected cases do not establish a population rate or preference.

| Galaxy | F0 model | Chi² | Reduced chi² | Boundary |
|---|---|---:|---:|---|
| NGC3198 | baryons | 32639.323 | 759.054 | False |
| NGC3198 | nfw | 57.086 | 1.392 | False |
| NGC3198 | burkert | 69.991 | 1.707 | False |
| NGC3198 | rar | 576.588 | 13.409 | False |
| NGC2403 | baryons | 319317.336 | 4374.21 | False |
| NGC2403 | nfw | 710.891 | 10.013 | False |
| NGC2403 | burkert | 1742.354 | 24.54 | False |
| NGC2403 | rar | 5521.548 | 75.638 | False |
| NGC3741 | baryons | 2576.163 | 122.674 | False |
| NGC3741 | nfw | 6.537 | 0.344 | False |
| NGC3741 | burkert | 23.073 | 1.214 | False |
| NGC3741 | rar | 28.405 | 1.353 | False |
| DDO154 | baryons | 70395.932 | 5866.328 | False |
| DDO154 | nfw | 117.712 | 11.771 | False |
| DDO154 | burkert | 12.436 | 1.244 | False |
| DDO154 | rar | 1069.088 | 89.091 | False |
| NGC2841 | baryons | 37314.688 | 746.294 | False |
| NGC2841 | nfw | 160.330 | 3.34 | False |
| NGC2841 | burkert | 335.696 | 6.994 | False |
| NGC2841 | rar | 4313.601 | 86.272 | False |
| UGC00731 | baryons | 2334.477 | 194.54 | False |
| UGC00731 | nfw | 3.396 | 0.34 | False |
| UGC00731 | burkert | 5.702 | 0.57 | False |
| UGC00731 | rar | 196.268 | 16.356 | False |
| NGC4157 | baryons | 677.400 | 39.847 | False |
| NGC4157 | nfw | 6.016 | 0.401 | False |
| NGC4157 | burkert | 5.667 | 0.378 | False |
| NGC4157 | rar | 154.490 | 9.088 | False |
| F567-2 | baryons | 64.743 | 12.949 | False |
| F567-2 | nfw | 1.894 | 0.631 | False |
| F567-2 | burkert | 1.171 | 0.39 | False |
| F567-2 | rar | 28.218 | 5.644 | False |

Full 64-row table: results/m1/v1/model_comparison.csv. Parameter values/units, local covariance/correlation and per-start diagnostics are in each galaxy JSON. Per-galaxy maximum residuals, neighbor correlations, inner/outer means and complete standardized residual arrays remain available. Large standardized residuals, e.g. NGC2403, persist under nuisance fits: improving an objective is not proving a correct physical model. Coherent radial departures could reflect restricted models, baryonic assumptions or systematic kinematics/errors; this investigation does not identify the cause.

Reference checks: the original components match the official separate SPARC archive from Lelli+2016; Gate 0 per-start regression passes with the documented summation tie-break. Li+2018 uses the same empirical RAR and geometry transformations but reports an acceleration-space statistic and MCMC results. At its rounded NGC3198 values (ML=.77, D=10.4 Mpc, i=71.1°), independent scalar RAR agrees with our prediction to 4.44e-16 relative precision. Its acceleration-error convention gives reduced chi² 2.060854 versus published 2.057 (difference ~0.19%); our velocity chi² is 78.846263. No tolerance was fitted to this comparison: closeness is descriptive; rounded inputs, signed-gas conventions and possible source revisions remain differences. This is not reproducing a published posterior. Li+2020 fits multiple halos while marginalizing nuisance parameters and considering cosmological priors; its parameter/ranking statements cannot be directly equated with our F0 or truncated-coordinate MAP configuration. No unresolved matched halo-numerical discrepancy is concealed, and no numerical agreement with its halo table is claimed.

Sources: https://astroweb.case.edu/SPARC/ ; https://arxiv.org/abs/1606.09251 ; https://arxiv.org/html/1803.00022 (equations 3–6 and NGC3198 table row); https://arxiv.org/abs/2001.10538 . Source comparison is methodological and selected numerical validation, not new astrophysical novelty.
