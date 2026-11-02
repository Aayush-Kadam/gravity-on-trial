# M4 data integrity

Executed read-only audit: 175 galaxies, 3391 radii, 361 negative gas rows; 1050 exact source-array comparisons. All 1,400 baseline model records retained, including seven nonconverged records. Every converged MLE/MAP prediction was reevaluated through the unchanged engine and checked against its saved array and standardized residuals. No benchmark optimization was rerun for aesthetics.

The 1,326-entry M3 manifest matched before documentation pointer updates. Historical README and gate-ledger bytes were archived in results/m4/v1/previous_README.md and previous_GATE_LEDGER.md, and m4_check.py verifies those exact historic bytes when checking the corresponding M3 entries. Other M3 manifest paths are checked in place. Prior Gate0/M1/M2 preservation evidence remains within M3; original scientific files have not been overwritten.

NGC3198 passed the mandatory gate before module expansion: all four curves, residuals, signed components, metadata, halo removal/restore and genuine CSV export. Real browser tests inspected actual Plotly DOM trace arrays for observations, errors, predictions and residuals. Downloaded CSV and JSON were compared with frozen sources. See vertical_slice_gate.json, data_integrity.json, tests.xml and browser_workflows.json under results/m4/v1.

Regression result: 107 passed, zero failures/errors (92 existing scientific tests + 15 new contract tests). Streamlit session tests additionally exercise failed baselines, state restoration, explicit previews, all modules and simulated low-memory admission.
