# M3 reproducibility

Scientific content revision `88d20d31b743733b779db7bba82fa34a8f13871b80280a0c54a43ccd226917b1`; source_snapshot/, environment.json and SHA-256 artifact manifest identify the exact code/configuration/data. No Git repository exists and no commit ID is invented. Deterministic seed 20261103 is recorded; scenarios/starts are fixed, not random draws. Source/raw/benchmark hashes remain unchanged.

20 pilot galaxies and all 175 full-campaign galaxies were rerun in separate controlled worker processes. All parameters, curves, accepted masks and numerical diagnostics pass frozen 1e-10 rtol/atol comparisons. Observed full-rerun parameter/speed maxima 0/0 km/s. Canonical comparison omits only timing/resource/stage/replicate metadata, never science values. All per-galaxy classifications are independently audited from scalar score gaps, original masks and explicit denominator arithmetic, not merely called twice through the same metric function.

92 test cases: original 54 plus 38 M3 cases, including fiducial MAP adapter regression, independent synthetic geometry recovery, signed gas, invalid/null proposals, normalized reference-frame likelihood and classification edges. Every accepted halo curve was independently density-integrated at all radii; 71100 scalar force-point checks and 8537 scalar likelihood/prior/statistic checks passed. These controls validate numerical implementation, not astrophysical truth. Second-method optimization has only the declared bounded coverage, not all 175 cases.

Actual interrupted-batch resumes preserved complete records and checked source identity before reuse; 55 initial-sweep and 50 repeat-sweep IDs were reused after two preflight refusals. No completed numerical fit was overwritten or counted as a fresh rerun merely because a cache was read. Initial and rerun namespaces were independently computed. Progress *.partial.json files are snapshots, never extra experiments. Resource values explicitly distinguish serial-worker lifetime peak from isolated fit estimates.

Commands from this project directory (existing complete matching results are reused):

```powershell
python m3_monitor.py tests
python m3_monitor.py audit
python m3_identifiability_report.py
python m3_run.py pilot initial
python m3_run.py pilot rerun
python m3_validate.py pilot
python m3_monitor.py optimizer
python m3_pilot_gate.py
python m3_run.py full initial
python m3_run.py full rerun
python m3_validate.py full
python m3_monitor.py aggregate
python m3_independent_audit.py
python m3_monitor.py plots
python m3_finalize.py
```

For a new independent calculation without deleting evidence, use a new namespace such as `python m3_run.py full independent_check` and compare canonical files with the saved initial results using m2_compare.equivalent/canonical. A methodology change requires a separately identified version; do not edit frozen configs/m3_v1.json. m3_prepare.py is the initial freeze, not a command to overwrite finished provenance. No clean-environment installation, external human replication or different-hardware reproducibility is claimed.
