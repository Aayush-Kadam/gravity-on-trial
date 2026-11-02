# M3 frozen experiment protocol

Run sparc175_fragility_m3_v1. M3 only; M4 forbidden. Exact scenarios, pilot IDs, thresholds, units, masks, budgets and reproduction tolerances are frozen in configs/m3_v1.json before fitting. M2's 107 preferred / 24 inconclusive / 44 unavailable states, all 988 warnings and 278 boundary contacts are preserved, not reinterpreted as theory probabilities.

## Scenario matrix and scientific boundaries

Twelve physical cases per original galaxy: disk-only, bulge-only and joint stellar ML shifts +/-0.1 dex around 0.5/0.7; D +/-eD; inclination +/-eI; joint geometry +/-eD and +/-eI. All four models use the same original radii/observations and catalog-frame velocity likelihood. Only explicitly changed fixed quantities change; halo parameters are refit using unchanged bounds/four M2 starts. RAR a0 stays universal 1.2e-10 SI. Signed gas preserved. No radial cuts. Zero-sensitivity scenarios are NOT_APPLICABLE, not artificial persistence support. D<=0 or invalid inclination proposals are rejected, counted and never clipped.

The +/-sigma shifts are deterministic stress cases, not draws from a posterior or an empirical covariance. Joint diagonal cases assume no measured covariance and do not exhaust uncertainty. A computation view may rescale component arrays/radii and correct both observations/errors, but saved predictions/log-likelihood are returned to the immutable catalog frame and independently checked. No source file or observation is changed.

Two separate MAP cases vary the log10 stellar ML prior width to 0.05 and 0.2 dex, around unchanged fiducials. Geometry priors, positive bounds and deterministic M2 starting points remain identical. This tests prior strength relative to the 0.1 dex fiducial, not a new measured stellar population. No cosmological halo prior or concentration-mass hypothesis is introduced. MAP prior objectives have no AIC/BIC ranking and never enter primary physical persistence fractions.

Quality cuts all175, Q<=2, Q=1, i>=30 and Q<=2&i>=30 change population composition only. They never change individual observed masks or count as individual preference flips. No unplanned radial uncertainty filtering. AIC and BIC are evaluated separately on the same MLE/common eligible masks as AICc; no mixing of incomparable objectives.

## Primary operational metrics and categories

Baseline decisive galaxies: retained, different decisive preference, inconclusive, unavailable, failed/domain, invalid physical proposal and not-applicable outcomes all recorded. Valid comparable scenarios include decisive or inconclusive; unavailable outcomes never support the original preference. Retained+flipped+inconclusive=valid. Persistence=retained/valid and flip frequency=flipped/valid; report the numerator/denominator and also all outcomes over 12 planned slots and 12-minus-null meaningful slots. Neither fraction is a posterior probability or calibrated sampling probability.

Baseline unavailable -> UNASSESSABLE. Baseline inconclusive -> INCONCLUSIVE; no baseline winner or flip probability invented. Baseline decisive: valid>=6 and valid/(12-null)>=0.6 required, otherwise UNASSESSABLE. Then inconclusive/valid>=0.5 -> INCONCLUSIVE; otherwise persistence>=0.8 and flip fraction<=0.1 -> STABLE; else SENSITIVE. Continuous counts/fractions always accompany labels. Frozen lenient/strict alternative thresholds in the JSON quantify classification-definition sensitivity without changing the primary rule.

Parameter ranges/medians use optimization log coordinates and physical units; scenario ranges are not confidence intervals. Boundary and identifiability frequencies show successful and unknown/failure counts with explicit denominators. Data-only and prior-inclusive curvature remain distinct. Multistart objective ranges and parameter ranges among solutions within delta objective<=1 are saved; >0.1 dex is a descriptive material-variation flag, not a proof of multimodality. Bounded dogbox cross-check: six frozen galaxies, baseline/joint-ML-plus/distance-plus, two declared starts and unchanged bounds; objective agreement target relative 1e-6. Distinct minima are reported rather than hidden.

## Pilot, scaling, resources and reproducibility

20 deterministic galaxies below span all three M2 outcome categories, quality levels, correlation/boundary behavior, gas/stellar/bulge components, negative gas and geometry uncertainty. No M3 sensitivity outcome was used in selection. Pilot must pass physical transforms, normalized likelihood, prior separation, failure bookkeeping, independent predictions, classification tests and fresh-process rerun. Poor fits, fragile preferences and valid rejected proposals do not fail the gate.

14 scenario records and 56 planned model slots per galaxy: 2,450 full galaxy-scenario records / 9,800 model slots, including explicit null/invalid slots. No combinatorial expansion. Pilot runtime projects full sweeps; if >900 seconds, stop with partial results rather than silently shrink scope. Otherwise attempt full campaign and full independent rerun, serial batches of five, unchanged 768 MiB stable preflight / 512 MiB floor / 180 MiB child cap. Checkpoint per galaxy, guard exact content identity, one BLAS thread, no GPU/MCMC/browser/dashboard. Numerical rerun tolerances 1e-10 rtol/atol; identities/quadrature 1e-9; synthetic recovery 1e-5 dex. No tuning thresholds after full results.

## Frozen pilot selection

- NGC3198: Retained real validation / signed-force edge case
- NGC2403: Retained real validation / signed-force edge case
- NGC3741: Retained real validation / signed-force edge case; max catalog gas_to_light_proxy
- DDO154: Retained real validation / signed-force edge case
- NGC2841: Retained real validation / signed-force edge case
- UGC01281: Retained real validation / signed-force edge case
- D512-2: Lexicographic first baseline PREFERENCE; min catalog n
- F561-1: Lexicographic first baseline INCONCLUSIVE; Lexicographic first Q=3
- CamB: Lexicographic first baseline NO_VALID_COMPARISON; Lexicographic first Q=2
- D631-7: Lexicographic first Q=1
- UGC11914: min catalog gas_to_light_proxy
- UGC02953: max catalog negative_gas_rows; max catalog n
- UGC03546: max catalog bulge_max_squared
- UGC00891: Largest fractional distance uncertainty
- UGC11820: Largest inclination uncertainty
- UGC08837: Most M2 boundary contacts
- ESO563-G021: Fixed NFW fit without an identifiability warning
- D564-8: Deterministic lexicographic fill
- DDO064: Deterministic lexicographic fill
- DDO161: Deterministic lexicographic fill