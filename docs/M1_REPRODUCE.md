# Reproduce M1

Use this project directory and Python 3.12.10; exact installed dependencies in pyproject.toml. No clean-environment installation was performed. Results use source content revision recorded per galaxy and frozen source_snapshot/ copies under results/m1/v1/. No data network fetch required. Verify artifacts_manifest.json before using evidence. Old Gate 0 ingestion commands rewrite their outputs: do not run them to reproduce M1.

Each m1_monitor command runs one child with native safety preflight. Stop on any failure; do not lower thresholds to obtain a pass. For a completely fresh comparison, preserve this versioned evidence first and use a separate output version or restore the snapshot in a separate workspace. Commands below overwrite their corresponding M1 evidence. m1_campaign skips complete existing results and checks identities; delete nothing to force a run.

```powershell
python m1_monitor.py tests
python m1_monitor.py controls
python m1_monitor.py real NGC3198 initial
python m1_monitor.py real NGC3198 rerun
python m1_campaign.py
python m1_monitor.py references
python m1_monitor.py plots
python m1_monitor.py preview
python m1_finalize.py
```

To rerun all eight galaxies, execute the two real commands for each frozen configs/m1_v1.json ID, then m1_campaign.py verifies fresh-process pairs. Source snapshots plus manifests provide identity without inventing a Git commit. Python/SciPy/NumPy/BLAS differences may alter optimizer stopping; recorded tolerances, masks, all starts and outputs allow audit.
