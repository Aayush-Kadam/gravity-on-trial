# M4 installation and reproducibility

From the project directory in PowerShell, use Python 3.12:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-m4-test.txt
$env:PYTHONPATH = (Resolve-Path src).Path
.\.venv\Scripts\python.exe m4_data.py
.\.venv\Scripts\python.exe m4_check.py
.\.venv\Scripts\python.exe -m pytest tests m3_tests.py m4_tests.py -q
.\.venv\Scripts\python.exe m4_ui_tests.py
.\Start-Gravity.ps1
```

Open http://127.0.0.1:8507. The Start script prefers the local .venv; the existing task installation also supports the task-local dependency folder without changing unrelated global packages. `python m4_serve.py streamlit_app.py 8507` is the equivalent supervisor command in an activated environment. Ctrl+C stops the supervisor and its child. Run one local server at a time. A refused memory preflight launches no server; close only apps you choose and retry later without weakening the limits.

The current local project already contains validated evidence. `python m4_data.py --fetch` retrieves only missing official raw sources after hash validation; it does not regenerate model fits. Existing frozen M1–M3 numerical records and manifests are required. Do not run historical finalizers to initialize a new UI session. Scientific-campaign commands and their bounded-run requirements remain in M1/M2/M3 reproducibility documents.

With the server running, `python m4_browser_tests.py` executes actual Edge browser workflows (requires Microsoft Edge at the documented Windows installation path and Playwright). `python m4_restart_test.py` intentionally stops/restarts only the task's server, performs final-source preview checks and stops it afterward. Browser tests write M4 evidence only. They are separate from the 107-test numerical suite. Local health/browser access must be permitted by the environment.
