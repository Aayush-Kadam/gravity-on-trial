# Gate 0R low-memory recovery — 2 November 2026

## 1. Verdict

**GO for Gate 0 only.** Original mandatory acceptance evidence is now present under the explicitly user-authorized Gate 0R memory exception. M1 is scientifically eligible for authorization; M1–M4 were not launched and remain unauthorized in this recovery operation.

## 2. What was built

Native Windows memory preflight/child monitor, stable NFW and Burkert squared-speed functions, a serial single-galaxy multi-start fitting probe, clean-process comparisons, separate static plot renderer, and saved-evidence audit/report generation. No full-catalog fits, RAR, sensitivity atlas, dashboard, MCMC, GPU, or publication. The original Gate 0 checkpoint is preserved and raw files/configs are unchanged. No pre-existing methodology file or numerical test suite existed at checkpoint inspection; methodology is now documented.

## 3. Scientific evidence

Prior verified inventory: 175 galaxies / 3,391 radial points / 361 negative gas terms. Raw hashes and prior canonical parsed hash verified without reacquiring data. New campaign: 10 distinct real galaxy/model fits, 10 fresh-process reruns; all 80 individual starts across both executions converged. Four fixed starts per model, deterministic bounded least squares; no random starts, no removed points, no boundary contacts. Repeated parameter, prediction, and standardized-residual arrays differ by exactly zero in these executions. Per-start local minima and diagnostics are retained, so convergence of a start is not a global-optimality proof.

Independent quadrature at 30 logarithmically spaced radii for each of four parameter sets per profile agrees within frozen 1e-9 relative tolerance; maximum recorded discrepancy 1.328e-12. Small-radius controls pass the frozen 2e-6 relative limit; NFW M200/R200 consistency and zero/negative/nonfinite radius rejection pass. Each fitted curve is independently checked via density integration. Every saved residual and chi-squared was independently recomputed from saved predictions/observations.

All 199 selected-galaxy rows match the authors' separately distributed Rotmod ZIP in radius, Vobs, error, gas, disk, and bulge. Independent scalar baryonic sums agree within 1e-9 (km/s)². This satisfies the published-table cross-check route; the archive and MRT derive from the same observations and are not independent datasets. No claim of reproducing published halo posteriors or digitized figures is made. The source is the Newtonian mass-model product linked at https://astroweb.case.edu/SPARC/ ; credit Lelli, McGaugh & Schombert (2016), https://arxiv.org/abs/1606.09251 .

Five source-attributed PNG/SVG plots contain measured error bars, signed gas conventions, scaled stellar components, baryons-only and fitted curves, units, and residuals. NGC3198 was visually inspected and a cropped-title layout issue corrected before final rendering; all five final plots were inspected individually.

| Galaxy | Model | n | Chi-squared | Reduced chi-squared |
|---|---|---:|---:|---:|
| NGC3198 | nfw | 43 | 57.086082 | 1.3923 |
| NGC3198 | burkert | 43 | 69.990570 | 1.7071 |
| NGC2403 | nfw | 73 | 710.890868 | 10.0125 |
| NGC2403 | burkert | 73 | 1742.354075 | 24.5402 |
| NGC3741 | nfw | 21 | 6.537494 | 0.3441 |
| NGC3741 | burkert | 21 | 23.072580 | 1.2143 |
| DDO154 | nfw | 12 | 117.712081 | 11.7712 |
| DDO154 | burkert | 12 | 12.436461 | 1.2436 |
| NGC2841 | nfw | 50 | 160.330377 | 3.3402 |
| NGC2841 | burkert | 50 | 335.695583 | 6.9937 |

Large residuals, especially NGC2403, demonstrate that optimizer convergence does not ensure an adequate physical description under fixed baryonic/geometry assumptions. No population-level preference or theory inference is justified by this five-galaxy engineering validation.

## 4. Computational evidence

Windows GlobalMemoryStatusEx initial preflight: 1007.676 MiB available; five-sample range recorded in import_probe_preflight.json. Stability rule, defined before execution: five samples over two seconds, each at least 768 MiB, range at most 128 MiB. Initial Python import-probe baseline 17.039 MiB; after NumPy/SciPy imports 68.633 MiB (increment 51.594 MiB). Scientific process baselines are saved individually. Maximum scientific fit peak 70.594 MiB; maximum including separate plotting 94.969 MiB. Lowest available memory across monitored execution: 941.176 MiB, above 512 MiB. All preflights passed. One scientific process at a time, one BLAS thread, CPU only.

Monitor sampling interval 50 ms; process lifetime peak working set is also read within child processes, reducing the risk that polling misses a peak. System headroom is sampled rather than continuously guaranteed. Native process inventory exposed only a limited set (Python/PowerShell/conhost); it could not reliably identify the machine-wide major consumers. No process was terminated and no Windows memory/paging setting changed. The initial profile was measured; 1 GiB is not asserted to be a numerical fit requirement.

Per-fit wall time and memory: fit_summary.csv. Full monitor histories include preflight and child wall time; do not sum CPU times or describe these as a full 175-galaxy performance result. Plotting resource measurements are separate.

## 5. Failures and limitations

No failed mathematical controls, optimizer starts, controlled-process terminations, or bound-limited selected fits. Several poor goodness-of-fit values remain scientific limitations, not numerical failures. Independent-Gaussian catalog errors omit inclination and other systematics. Identifiability diagnostics are numerical Jacobian condition numbers, not posterior uncertainties. No global-optimum certification, broad parameter-space property test, synthetic recovery suite, or clean-environment installation audit is claimed; these belong to later engine validation. RAR is explicitly deferred as allowed at Gate 0.

Licensing for raw redistribution remains unresolved: data stay local and git-ignored; no publication occurred. Source zero/missing semantics for Vflat and absent bulges remain for M1 data-edge-case work, and did not enter these fits. The scientific functions are a minimal gate prototype, not a full installable platform. Resource authorization applies only to this bounded recovery, not later milestones.

## 6. Artifacts

results/gate0r/: fit_summary.csv, campaign_status.json, test_report.json, checkpoint.json, published_table_crosscheck.json; per-galaxy initial/rerun JSON files; monitor/preflight/stdout/stderr logs; five *_curves.png and five *_curves.svg figures. configs/gate0r.json freezes assumptions/tolerances and records the user-authorized exception. Source: src/gravity_on_trial/halos.py, scientific_probe.py, recovery_monitor.py, complete_recovery.py, render_recovery.py, finalize_recovery.py. artifacts_manifest.json hashes the final evidence and scientific source/config files.

## 7. Decision

Stop this recovery with Gate 0 GO. M1 is eligible for separate authorization; do not automatically start it. Retain the original 1 GiB baseline configuration and this separately scoped memory exception. No dark-matter discovery, gravity falsification, novel astrophysics, or full-platform completion is claimed.
