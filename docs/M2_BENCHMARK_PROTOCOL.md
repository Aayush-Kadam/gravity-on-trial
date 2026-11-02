# M2 frozen benchmark protocol

Run sparc175_m2_v1, configuration configs/m2_v1.json; exact SHA-256 checked before execution. This is M2 only. All existing Gate 0/M1 artifacts remain unchanged. M1 physics, halo bounds, four declared starts, three nuisance-only starts, tolerances, stellar priors, catalog error likelihood, log-coordinate MAP density and geometry conventions are inherited without changes; their full definitions and units are in M1_SCIENTIFIC_METHOD.md and baseline_freeze.json. No prior objective is used for ML information criteria.

Main inventory: all 175 IDs, 3391 radii, signed gas unchanged. Main F0/F1 use every original point; models that cannot evaluate a full mask retain explicit failure/domain records. No per-model hidden clipping. Fixed negative/nonpositive bar cases get a separately labeled common-positive-bar F0 experiment with all models refit to the identical subset and original indices recorded. This never substitutes for the full inventory record. All successes and failures retain n_inventory and attempted/accepted/excluded masks, source identity, units, bounds, priors, optimizer starts, diagnostics, time and memory.

Primary comparison: F0 AICc, all four converged on exactly the same mask, n>k+1, no boundary, data Jacobian rank=k and condition<=1e8. A high-correlation warning alone is not rank deficiency; retain it visibly. If eligible, runner-up gap >=2 gives an operational preference; gap<2 is INCONCLUSIVE. If ineligible, NO_VALID_COMPARISON and no winner. NFW/Burkert pairwise comparisons are separately counted. No posterior-theory probabilities. F1 MAP has no AIC/AICc/BIC, no posterior-evidence ranking; report nuisance shifts/data residual changes separately.

Report full inventory, Q<=2 & i>=30 prespecified higher-quality sample, and eligible/successful subsets with explicit denominators. Population median/distribution summaries disclose their valid count and missing count; no successful-only statement implies whole-sample performance. Warning classes distinguish high correlation, numerical rank/conditioning, boundary, n<=k, and unsupported domains. Exploratory property associations use Spearman coefficient with valid pair count, no p-values or causal claims.

Pilot: 20 deterministic metadata-selected IDs below, chosen before M2 fits; complete all 8 model/config evaluations and fresh-process reruns. GO requires immutable data, valid status/mask/statistics handling, independent controls, consistent warnings, no unresolved correctness bug and measured safe resources. Poor fits are not failures of software acceptance. Full campaign may begin only with saved pilot GO. Batches of five serial galaxies, one controlled child; monitored preflight and 512 MiB floor/180 MiB cap remain unchanged. Checkpoint every galaxy atomically, content identity guards reuse. Sampling safety is measured, not a continuous guarantee.

Fresh-process plan: all 20 pilot cases rerun, then full 175 rerun if measured estimate for a sweep <=600 seconds; otherwise use the 35 frozen evenly spaced IDs. Identity requires canonical parameters, masks and diagnostic arrays equal within 1e-10 rtol/atol; timing/memory fields excluded. Independent halo quadrature, signed gas, synthetic negative controls and statistical edge tests are mandatory. No full-rerun claim based on subset.

Predictive pilot: first five frozen pilot IDs with n>=10 and positive bar throughout, F0 inner 70% training and outer 30% test, same masks for every model. This is radial extrapolation with correlated neighboring measurements, not independent random test data. No global parameter calibration. This bounded pilot is not M3.

Scientific visualizations are standalone PNG/SVG alongside these Markdown reports, from saved numerical arrays, with source, sample, units/configuration and caveats. Data and code are local; no publication, external contact, new hypothesis or paid service.

## Pilot identities and selection

- NGC3198: Retained M1 implementation-validation case
- NGC2403: Retained M1 implementation-validation case
- NGC3741: Retained M1 implementation-validation case; Maximum catalog gas_to_light_proxy
- DDO154: Retained M1 implementation-validation case
- NGC2841: Retained M1 implementation-validation case
- UGC00731: Retained M1 implementation-validation case
- NGC4157: Retained M1 implementation-validation case; Maximum catalog SBdisk
- F567-2: Retained M1 implementation-validation case
- UGCA281: Minimum catalog SBdisk
- UGC11914: Minimum catalog gas_to_light_proxy
- D512-2: Minimum catalog n
- UGC02953: Maximum catalog n; Most negative gas rows
- NGC6789: Minimum catalog radius_max_kpc
- UGC09133: Maximum catalog radius_max_kpc
- NGC4214: Minimum catalog Inc
- UGC11455: Maximum catalog Inc
- CamB: Minimum catalog bulge_max_squared; Lexicographic first Q=2
- UGC03546: Maximum catalog bulge_max_squared
- D631-7: Lexicographic first Q=1
- UGC01281: Fixed-baryon nonpositive domain edge case