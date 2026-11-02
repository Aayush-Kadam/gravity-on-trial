# M1 decision

## A. Verdict

**GO — M1 only.** All 16 frozen M1 acceptance criteria have executed evidence (acceptance.json). This is scientific software validation with explicit model inadequacy/identifiability warnings, not assurance that a physical hypothesis fits every galaxy. M2/M3/M4 remain unstarted and unauthorized.

## B. Scientific evidence

Eight prespecified real galaxies: NGC3198, NGC2403, NGC3741, DDO154, NGC2841, UGC00731, NGC4157, F567-2; 233 observed radii, no exclusions. Four labeled models; F0 fixed maximum likelihood and F1 prior-constrained inference kept separate. 64 initial model/configuration evaluations, all converged; 128 including fresh-process reruns, 352 optimizer starts, 0 failed starts. 54 passing automated scientific tests, explicit noiseless synthetic positive/negative controls, independent halo integration, RAR/units/domain limits, geometry-frame likelihood checks, matching masks and statistical applicability tests. Exact fresh-process parameter/prediction arrays and chi² reproduce. Original ten Gate 0 halo fits and checkpoint files preserved. Eight labeled comparison figures generated and visually inspected.

9 initial MAP solutions have boundary contacts and 45 evaluations carry data-identifiability warnings. F567-2's n=k halo nuisance case correctly returns undefined reduced chi². Controlled 10-point profile pilot and per-parameter local information document uncertainty/degeneracy. Poor residuals are retained and investigated, not removed or hidden. Published NGC3198 RAR parameter evaluation gives acceleration-space reduced chi² 2.060854 versus 2.057, while its velocity statistic differs; methodological differences from 2018/2020 studies are explicit. No published halo posterior replication, significance, new law or astrophysical discovery claimed.

## C. Computational evidence

Fitting peak 72.363 MiB; overall monitored peak 146.734 MiB; minimum observed available RAM 1580.863 MiB. All launched scientific tasks stayed within 180 MiB cap / 512 MiB sampled headroom. Eight initial workers took 14.378 seconds combined. Read M1_PERFORMANCE.md and per-task logs for scopes. No GPU/Docker/parallel campaigns; all outputs checkpointed.

## D. Failure analysis and limits

No unresolved scientific correctness failure demonstrated. Resolved development failures: a synthetic failure test initially included its exact solution as a start; a worker bracket typo prevented one launch. Logs retained; both fixed before successful validation. One transient preflight stability refusal was honored and a later bounded retry passed. A separate cross-implementation audit initially expected the same selected candidate within 1e-8 km/s. DDO154 NFW differed by 8.69e-7 km/s; all four per-start parameter arrays were exactly unchanged. Audit v2 checks every trajectory exactly and reports the dot-product versus np.sum tie-break difference (chi² 2.84e-14), without relaxing the frozen fresh-process tolerances. Full explanation: M1_REGRESSION_AUDIT_V2.md.

Known limits: local multistart optimization does not prove a global optimum; Gaussian independent catalog errors omit systematics/correlation; formal covariance/profile curvature is conditional and may be unreliable under model inadequacy; MAP coordinate density and truncated priors affect results; boundary solutions are not precise measurements; sparse/low-quality data weaken model comparison; empirical RAR is not a full gravity theory. No new nuisance capability is deferred. Wide parameter-space validation, broader source comparisons and clean-environment installation were not part of this bounded numerical campaign. Raw redistribution licensing unresolved; local-only data remain git-ignored. Project has no Git repository, so exact content hashes/source snapshots substitute for a Git revision; no commit/push/publication occurred.

## E. Final authorization

**M2 IS ELIGIBLE FOR AUTHORIZATION.** Do not begin it automatically. This M1 operation stops here.

Artifacts: results/m1/v1/model_comparison.csv; model_comparisons.json; uncertainty_summary.json; tests.xml; synthetic_controls.json; reference_comparison.json; campaign_reproducibility.json; gate0_regression.json; acceptance.json; all per-galaxy initial/rerun JSON, profile grids, PNG/SVG figures, monitor logs, original checkpoint freeze and artifact manifest. Method/tolerance/selection: configs/m1_v1.json, docs/M1_SCIENTIFIC_METHOD.md. Exact reproduction commands: docs/M1_REPRODUCE.md.

Execution accounting: these counts describe the final authoritative campaign. The earlier input-hardening pilot is preserved separately: 128 additional real model/configuration evaluations and 352 optimizer starts. Total across both recorded campaigns: 256 evaluations and 704 starts, with no failed starts. Valid-input parameter, prediction and statistic outputs are exactly unchanged after schema hardening (input_hardening_regression.json). Earlier timings are not added to the stated final-campaign runtime.
