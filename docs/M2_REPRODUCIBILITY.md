# M2 reproducibility and source identity

Scientific content revision: `a94be7f57dd53d91d99dcbaf337c97b521104a554dfe187b84e7589ebc85730a`. No Git repository exists; exact SHA-256 content identities and source_snapshot/ copies replace a fabricated commit ID. Frozen configurations: configs/m2_v1.json, configs/m1_v1.json and configs/gate0r.json. Original raw file hashes and the canonical parsed source remain unchanged. Primary outputs include source/config paths, seed 20261102, exact original arrays, masks, every optimizer start and diagnostics. No stochastic starts or noise were used in the benchmark.

All 20 pilot galaxies and all 175 full-population galaxies were independently rerun in fresh controlled worker processes, one serial batch at a time. Both complete sweeps share no cached fit records. Canonical comparison retains masks/parameters/curves/statistics/diagnostic arrays and removes only timing/resource/stage/replicate fields. Frozen tolerance 1e-10 rtol/atol; maximum observed parameter difference 0, maximum speed difference 0 km/s. No subset-to-full extrapolated reproduction claim is needed. Every full-mask accepted halo was independently checked against numerical density integration, and all saved likelihood/criteria were independently recomputed from observations/predictions with scalar sums.

Existing M1 54-test suite passed under M2 monitoring, including independent halo/units/RAR/geometry, synthetic known solutions, signed gas, masks, prior separation, invalid-domain and boundary/statistical controls. Ten additional comparison/reproduction-rule unit checks passed. Five saved synthetic controls are prominently labeled and do not enter empirical counts. The 23/25-point common-subset case and all 20 radial training/outer-prediction cases also matched in separate fresh-process repetitions. Code/environment/seed and output schema are saved locally. Tests are necessary but not proof of astrophysical truth.

Resume behavior: m2_worker checks complete per-galaxy records against the exact source identity; it refuses mismatches and validates existing records before reuse. A controlled interruption leaves *.partial.json progress snapshots and preserves completed galaxy files. We tested actual no-recompute resume on a completed batch separately; no crash-injection claim is made. Partial snapshots are never additional observations/evaluations. The source snapshot and manifests preserve exact evidence; copying raw data to public repositories is not authorized.

Reproduction from this project directory with the recorded environment:

```powershell
python m2_monitor.py tests
python m2_monitor.py audit
python m2_run.py pilot initial
python m2_run.py pilot rerun
python m2_monitor.py checks
python m2_pilot_gate.py
python m2_run.py full initial
python m2_run.py full rerun
python m2_validate.py full
python m2_monitor.py extras
python m2_monitor.py controls
python m2_monitor.py aggregate
python m2_monitor.py plots
python m2_finalize.py
```

These commands reuse complete matching outputs; to execute new independent fits without deleting evidence, use a new replicate namespace, e.g. `python m2_run.py full independent_check`. Compare its per-galaxy files with the original using m2_compare.canonical/equivalent, as in m2_validate.py. Use a separate workspace/version for methodology changes; do not edit the frozen configuration in place. Initial m2_prepare.py is a one-time preregistration step, not a command to overwrite a finished baseline. No clean-environment installation was executed.
