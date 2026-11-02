# R0R final decision — 3 November 2026 (Asia/Kolkata)

## Verdict: GO

The source-only setup blocker is resolved in release/r0r_v1/. All 18 acceptance criteria have executed evidence in results/r0r/v1/acceptance.json. No scientific scope was expanded or reduced, and no observational dataset was bundled.

Remediation: benchmark_setup.py, the included r0_processes.py helper, frozen-source contract, checkpoint/manifest generation, setup-aware streamlit_app.py, guarded Evidence Vault collections, process-tree browser measurements, twelve new failure tests, complete plotting dependency lock, Windows/setup/offline documentation, new publication inventory and data-free setup screenshot. Exact added/changed files versus R0 are recorded in changed_vs_R0.json.

Command: `python benchmark_setup.py bootstrap --from-official-sources`; `python benchmark_setup.py verify` validates completion. Use the isolated Windows Python 3.12 environment from README. First-run absence/corruption is explicit; no synthetic fallback or hidden developer input is used.

Dataset: 175 galaxies /3,391 radii /361 negative-gas rows; official source and normalized-catalog hashes match exactly. Regenerated M2: 1,400 evaluation slots. Regenerated M3: 2,450 scenarios /9,800 slots; 8,537 converged, 1,144 null slots, 88 invalid-proposal slots, 16 unsupported and 15 failed searches. Complete numerical outputs and 25 scientific figures were generated locally. All 350 galaxy records and 11,200 slots were externally compared after generation; all 9,930 converged parameter/prediction arrays matched exactly, maximum differences 0. Timing/run/identity/resource metadata are legitimately different and separately documented; no byte-hash equality is claimed for them.

119 tests passed. The actual interruption/resume, preflight refusal/recovery, idempotence (1,345 unchanged result-file hashes), source/checkpoint/schema/manifest corruption, no-data UI and offline controls passed. Real browser workflows covered all four modules, multiple galaxies, halo removal, unavailable/warning cases, all fragility classes, genuine exports, regenerated figures/receipt, stop/restart and blocked-external-origin post-bootstrap operation. Actual screenshots were reviewed; test servers stopped.

Measured computation-child peak 144.039 MiB; app process-tree peak 167.785 MiB. M2 evaluation sum 46.191s; M3 scenario sum 195.161s. Startup/preflight/I/O/interruption scopes are distinguished in the performance report; no unmeasured total is invented. System headroom never crossed the monitored 512 MiB floor.

Preservation: all 1,326 M3 and 87 M4 protected entries match; original R0 archive/manifest unchanged. Apache-2.0 remains limited to approved original code. Raw/derived data-bearing arrays/images are excluded; official downloader/local regeneration is used. Security scan found no credential/path patterns; locked dependency check found no OSV matches at the recorded time. No scientific-truth, peer-review, cosmological, exhaustive-theory, formal accessibility, multi-user or public-hosting claim is introduced.

Caveats: validated Windows/Python 3.12/locked dependency scope; first setup needs official-site/PyPI availability; finite deterministic scenario grid and known scientific limitations remain; manifests are unsigned corruption checks; browser offline tests block non-local origins rather than disabling the OS network. Failure-window samples and total full-parent-lifetime memory were not captured, and those limits are disclosed. Data redistribution rights remain unestablished, handled through exclusion rather than a legal claim. A new official byte version correctly stops setup until reviewed.

Exact review artifacts: docs/R0R_*.md; results/r0r/v1/numerical_equivalence.json, regression.xml, real_failure_controls.json, browser_clean_room.json, runtime_memory_storage.json, source/security/preservation evidence and publication_manifest.json; release/r0r_v1/; release/r0r_source_candidate_v1.zip. The complete generated clean-room tree stays private under work/r0r/final_source and is not included in the source ZIP.

**GRAVITY ON TRIAL — SOURCE-ONLY PUBLIC RELEASE CANDIDATE READY FOR USER APPROVAL.** No publication, remote repository creation, push, deployment or external distribution occurred. Stop pending separate owner approval of the exact final inventory.
