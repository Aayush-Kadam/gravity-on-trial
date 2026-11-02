# M2 population results — 3 November 2026

## Population and denominators

All 175 official SPARC galaxies and 3,391 radial measurements are represented, including 361 negative gas contributions in the frozen source. Q counts remain 99/64/12 for high/medium/low. No original radial observations were removed from the main benchmark. The prespecified higher-quality metadata cut Q<=2 and i>=30° contains 153 galaxies; it does not establish independent errors or eliminate astrophysical systematics.

Four physical families under F0 fixed MLE and F1 nuisance MAP yield 1,400 primary records: 1,393 CONVERGED, 2 UNSUPPORTED_DOMAIN and 5 NO_VALID_START. These results were independently rerun for all 175 galaxies in fresh processes. Converged includes 348 fixed-parameter F0 predictions and 1,045 optimized model/configuration problems; 1,050 optimization problems were attempted. All 3,850 declared optimizer starts are retained: 3,831 converged and 19 domain-aborted starts per full sweep. Convergence is not physical adequacy or parameter precision.

## Fit quality and identifiability

| Model/configuration | Inventory denominator | Converged | Warning-bearing | Bound-contact | Defined reduced chi² n | Median defined reduced chi² |
|---|---:|---:|---:|---:|---:|---:|
| MLE_baryons | 175 | 174 | 0 | 0 | 174 | 85.4418 |
| MLE_nfw | 175 | 175 | 134 | 44 | 175 | 1.3316 |
| MLE_burkert | 175 | 174 | 158 | 12 | 174 | 0.7519 |
| MLE_rar | 175 | 174 | 0 | 0 | 174 | 10.8061 |
| MAP_baryons | 175 | 174 | 174 | 115 | 174 | 11.4474 |
| MAP_nfw | 175 | 175 | 175 | 55 | 165 | 1.6027 |
| MAP_burkert | 175 | 174 | 174 | 26 | 164 | 0.8618 |
| MAP_rar | 175 | 173 | 173 | 26 | 173 | 1.9999 |

Medians above condition on valid values; the valid counts disclose missingness. They must not be compared as matched-population effect sizes. Twenty converged MAP halo cases have n<=k, making reduced chi² undefined (10 each for NFW and Burkert). Overall warnings: 988/1,400 evaluations; bound contacts: 278/1,400. These sets overlap and must not be added.

All 696 converged F1 cases have weak data-only directions; local data covariance is withheld. The explicit distance/inclination/halo scaling ridge explains why priors can select an optimum without making its parameters independently identifiable. F0 local covariance is returned for 131/175 NFW and 162/175 Burkert cases; these are known-error local approximations, not posterior intervals. Fixed models have no parameter-error estimation. Full parameter/uncertainty distributions with unavailable counts are in parameter_distributions.json.

## Frozen operational comparisons

All-inventory four-way F0 AICc: 131/175 eligible, 24/175 inconclusive, 44/175 no valid comparison. The 107 eligible operational preferences are {'rar': 3, 'burkert': 59, 'nfw': 42, 'baryons': 3}. These sum to 107, not 175; no winner is assigned to the other 68 galaxies. Runner-up gap>=2 is the frozen operational rule, not a theory probability or calibrated significance threshold.

NFW/Burkert-only comparison: 131/175 eligible; preferences {'burkert': 62, 'nfw': 43}; 26 inconclusive; 44 unavailable. Four-way and pairwise counts answer different questions and are not interchangeable.

Higher-quality sample: 115/153 eligible, 21/153 inconclusive, 38/153 unavailable; preferences {'rar': 3, 'burkert': 51, 'nfw': 40}. Boundary exclusion is a deliberate regularity condition, not removal of inconvenient observations: every bound-limited fit remains in the inventory and distributions. No F1 AIC/BIC or posterior-objective winner is reported.

## Nuisance dependence, residuals and properties

Matched F1/F0 data-chi² ratio medians: baryons 0.128 (174 paired cases), NFW 0.925 (175), Burkert 0.859 (174), RAR 0.162 (173). These are conditional residual changes under more freedom/priors, not ML likelihood-ratio tests or comparisons of physical truth. Raw chi², changing k and MAP penalty remain separate.

NGC4389, NGC2976 and UGC02455 can move NFW log-mass estimates across the entire 8–14 dex allowed box between F0/F1; independent halo integrals still pass and boundaries flag the results. Such shifts are evidence of assumption/bound sensitivity, not new accurate halo-mass measurements. Burkert extremes also span broad prior boxes. The twelve largest inspected cases retain both parameters, bounds and independent checks in parameter_instability_examples.json.

All standardized residual arrays are saved; 26,969 valid residual points across F0/F1 feed descriptive plots. These are repeated/model-dependent uses of the 3,391 observed measurements, not independent observations. Point-weighted radial medians/IQRs reveal conditional structure; neighboring-radius correlation, normalization by Rmax and source-quality mix limit inference. Large residuals are retained (e.g. NGC2403), and reduced chi² below one does not certify a true model.

Exploratory Spearman tables cover luminosity, central surface brightness, HI-to-light proxy, morphology, inclination, ring count, radial coverage and Q. They carry valid-pair n, full inventory denominator and no p-values. For example, NFW warning versus outer radius has rho≈−0.340 (175 successful cases); Burkert's corresponding value is ≈−0.043 (174). These are associations, not causal explanations or controlled multiple-testing discoveries. The constant F1 warning indicator has no defined association coefficient, not a fabricated zero.

## Supplemental checks

UGC01281's two nonpositive fixed baryonic-force radii (indices 0,1) invalidate full-mask baryons/RAR evaluation and make some optimizer trajectories infeasible. A separately labeled common-positive subset uses indices 2–24 (23/25 points) for every model; all four models converge there. It does not replace the full records or join main preference counts. Five prespecified inner-70%/outer-30% F0 experiments produced all 20 training/evaluation results and repeated in fresh processes. They test radial extrapolation with correlated errors, not fully independent predictive validation; saved weighted outer errors are in predictive_pilot.json. No global calibration or M3 campaign ran.

Scientific figures: 12 population/parameter figures and 8 selected full-mask galaxy figures, PNG/SVG, source-linked to saved arrays. See figures/contact_sheet.png and figure_manifest.json. No astronomical photos or synthetic observations are used.
