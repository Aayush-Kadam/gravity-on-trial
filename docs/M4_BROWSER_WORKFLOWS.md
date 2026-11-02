# M4 real-browser workflows

Executed with Microsoft Edge headless and Playwright 1.56 against localhost. Screenshots are actual browser captures, not mockups. Desktop 1440×900 and laptop 1366×768 were inspected. All non-local origins were blocked throughout the final browser suite. Offline means core app navigation/data/charts/exports with installed dependencies and local data, not downloading dependencies without internet or physically disabling Windows networking.

- 01_startup: PASS — {'galaxy': 'NGC3198', 'observations': 43, 'models': ['baryons', 'nfw', 'burkert', 'rar'], 'actual_DOM_arrays_verified': True}
- 02_galaxy_selection: PASS — {'galaxy': 'NGC2403', 'observations': 73, 'models': ['baryons', 'nfw', 'burkert', 'rar'], 'actual_DOM_arrays_verified': True}
- 03_model_toggle: PASS — All four model toggles verified against actual Plotly traces
- 04_remove_and_restore: PASS — {'galaxy': 'NGC3198', 'observations': 43, 'models': ['preview'], 'actual_DOM_arrays_verified': True}
- 05_residuals: PASS — {'galaxy': 'NGC3198', 'observations': 43, 'models': ['baryons', 'nfw', 'burkert', 'rar'], 'actual_DOM_arrays_verified': True}
- 06_statistical_validity: PASS — Unavailable CamB; MAP unranked; actual MAP arrays verified
- 07_identifiability: PASS — Explicit MAP identifiability warning visible
- 08_atlas_classes_and_drilldown: PASS — {'STABLE': 'DDO154', 'SENSITIVE': 'F583-4', 'INCONCLUSIVE': 'D512-2', 'UNASSESSABLE': 'F574-2'}
- 09_failed_unsupported_invalid: PASS — {'INVALID_PROPOSAL': ['IC4202', 'inclination_plus1sigma'], 'UNSUPPORTED_DOMAIN': ['UGC01281', 'ML_disk_minus01dex'], 'NO_VALID_START': ['UGC01281', 'ML_disk_minus01dex']}
- 10_evidence_downloads: PASS — CSV and JSON downloaded in browser and matched source
- 11_navigation: PASS — {'cycles': 4, 'module_visits': 16, 'RSS_after_cycles_MiB': [159.39453125, 161.0625, 161.58203125, 161.640625], 'growth_last_minus_first_MiB': 2.24609375}
- 13_offline_core: PASS — Core workflows passed with all non-local origins blocked; installation/setup already complete

12 — Restart: PASS. The task server was stopped and a new process launched with the final source and compatible Starlette 0.49.3. Actual NGC3198 DOM arrays and hashes matched; changed-Υ preview and restoration were verified in the browser. All four modules navigated after restart. See restart_and_preview_browser.json.

14 — Constrained memory: PASS for controlled admission behavior. A 900 MiB available-memory simulation in the actual Streamlit session disabled the optional fit button and showed a low-memory warning. The admission function rejects insufficient/unstable windows. The real live child was monitored and bounded. OS-wide memory exhaustion was deliberately not induced; no unrelated apps were terminated. This distinction remains a limitation rather than a fabricated stress-test result.

Early harness attempts are preserved separately: selectors were corrected for navigation icon text, native segmented controls, searchable options, valid empty plots and hidden accessibility cells. These are not counted as passing runs. The final complete suite is browser_workflows.json; a separate final-source restart/preview run follows it. The final server was stopped after testing, leaving no uncontrolled task server.
