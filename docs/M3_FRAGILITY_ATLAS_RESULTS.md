# M3 Model Fragility Atlas results — 3 November 2026

## Inventory and execution

All 175 original galaxies and 3,391 measurements remain represented. M2's 107 operational preferences, 24 inconclusive comparisons and 44 unavailable comparisons remain frozen. M3 has 2,450 initial galaxy-scenario records and 9,800 planned model slots: 12 physical scenarios and 2 separate prior-width cases per galaxy. Actual model calculations 8568, including 4984 optimized problems and 3584 fixed predictions/evaluations. Model statuses: {'CONVERGED': 8537, 'NOT_APPLICABLE': 1144, 'INVALID_PROPOSAL': 88, 'UNSUPPORTED_DOMAIN': 16, 'NO_VALID_START': 15}. Null and invalid proposals are planned records, not successful fits or failed astrophysical theories. Full repeat covered all 175 galaxies.

## Operational classifications

| Category | Full inventory | Decisive M2 baseline subset |
|---|---:|---:|
| STABLE | 79 / 175 | 79 / 107 |
| SENSITIVE | 18 / 175 | 18 / 107 |
| INCONCLUSIVE | 29 / 175 | 5 / 107 |
| UNASSESSABLE | 49 / 175 | 5 / 107 |

Baseline unavailable cases are UNASSESSABLE by definition; baseline inconclusive cases remain INCONCLUSIVE. They are not silently reassigned a baseline winner. For decisive baselines, valid>=6 and valid/(12-null)>=0.6 required; then inconclusive/valid>=0.5 yields INCONCLUSIVE; otherwise persistence>=0.8 and flip/valid<=0.1 yields STABLE; remaining assessable cases SENSITIVE. Valid includes decisive and inconclusive scenarios. Every continuous metric, coverage and raw count is in fragility_classifications.csv / atlas_metrics.json.

## Persistence and changes with explicit denominators

Among 107 decisive baseline galaxies: 906 retained, 52 changed to a different decisive model, and 70 became inconclusive out of 1028 valid comparable physical scenarios. These are scenario-weighted counts, not independent galaxy trials. Other outcomes remain explicit: {'retained': 906, 'to_inconclusive': 70, 'not_applicable': 170, 'unavailable': 72, 'flipped': 52, 'invalid_proposal': 14}. Per-galaxy persistence median 1.0000, flip-frequency median 0.0000, each with 107/107 defined denominators. A high valid-only persistence fraction does not erase low coverage or unavailable outcomes.

All physical scenario outcomes: {'NO_VALID_COMPARISON': 508, 'NOT_APPLICABLE': 286, 'NOT_A_LIKELIHOOD_COMPARISON': 350, 'PREFERENCE': 1053, 'INCONCLUSIVE': 231, 'INVALID_PROPOSAL': 22}; the 350 MAP experiments are explicitly NOT_A_LIKELIHOOD_COMPARISON and excluded from these preference metrics. Actual rejected physical proposals are counted in both scenario and model-slot units. Unsupported-domain and failed-search states are not the same as an inconclusive valid comparison. Underlying all-175 inventory is never dropped.

## Definition, parameter and information sensitivity

Frozen classification alternatives: {'lenient': {'classification_counts': {'UNASSESSABLE': 45, 'INCONCLUSIVE': 29, 'STABLE': 88, 'SENSITIVE': 13}, 'changed_all_galaxies': 10, 'changed_baseline_decisive': 10}, 'strict': {'classification_counts': {'UNASSESSABLE': 55, 'INCONCLUSIVE': 29, 'STABLE': 68, 'SENSITIVE': 23}, 'changed_all_galaxies': 13, 'changed_baseline_decisive': 13}}. They use the same arrays and do not replace primary labels. Differences demonstrate the dependence of operational categories on normative thresholds; no categorical claim of calibrated scientific confidence is made.

Parameter ranges/medians use appropriate log/physical units; covariance/rank/near-minimum diagnostics and every new bound contact remain visible. New warning-bearing evaluations 4377/8568 actual calculations (9800 planned slots); bound-bearing evaluations 1111/8568. These overlapping sets must not be added or compared to the smaller M2 experiment without matching denominators. Low parameter variation at a bound does not imply a precise physical measurement.

The geometry ridge is verified for all 696 converged M2 MAP cases; this underdetermination and unknown radial covariance limit physical interpretation. Primary fixed-scenario and prior-width effects are separate. Joint/disk cases coincide without a bulge in 0/175 galaxies (details in overlapping_scenarios.json); equal weights describe the frozen named stress matrix, not an empirical perturbation distribution. The design tests limited stellar/geometric offsets, two prior strengths and statistical/numerical choices, not all possible astrophysics.

## Figures and interpretation

25 PNG/SVG figures cover all 175 IDs in readable matrix pages, stellar/distance/inclination outcomes, parameter spans, warning/bound frequencies, quality composition, category/threshold dependence, priors/statistics and selected before/after real rotation curves. Before/after selection is frozen maximum-change display among valid comparisons, or explicitly labeled context fallback; it is not typical-case sampling. No synthetic astronomical evidence or fabricated data appear.

The scientific conclusion is the saved conditional stability/coverage record, not a victory for a particle or gravity theory. Fragile results, unavailable comparisons and small or null perturbation effects remain legitimate outputs. No independent astrophysical novelty, discovery, publication readiness or theory probability is established.
