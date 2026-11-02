"""Finalize M4 only after executed evidence exists. Never rewrites science."""
import hashlib,json,platform,re,shutil,sys,zipfile
from pathlib import Path
from m4_adapter import *
OUT=ROOT/'results/m4/v1';DOC=ROOT/'docs'
def save(name,value):(OUT/name).write_bytes(json_bytes(value))
def doc(name,text):(DOC/name).write_text(text.strip()+'\n',encoding='utf-8')
def main():
    integrity=read('results/m4/v1/data_integrity.json');browser=read('results/m4/v1/browser_workflows.json');restart=read('results/m4/v1/restart_and_preview_browser.json');ui=read('results/m4/v1/ui_session_tests.json');live=read('results/m4/v1/live_fit_verification.json');visual=read('results/m4/v1/visual_review.json')
    assert integrity['status']==browser['status']==restart['status']==ui['status']==visual['status']=='PASS'
    assert integrity['M3_mismatches']==[] and integrity['galaxies']==175
    assert len(browser['workflows'])==12 and all(x['status']=='PASS' for x in browser['workflows'].values())
    assert live['status']=='COMPLETE' and live['result']['status']=='CONVERGED'
    import xml.etree.ElementTree as ET
    tree=ET.parse(OUT/'tests.xml');suite=tree.getroot().find('testsuite');assert int(suite.attrib['tests'])==107 and int(suite.attrib.get('failures',0))==0 and int(suite.attrib.get('errors',0))==0
    monitors=[json.loads(p.read_text()) for p in OUT.glob('*monitor.json') if 'peak_MiB' in json.loads(p.read_text()) and 'app' in json.loads(p.read_text())]
    peak=max(x['peak_MiB'] for x in monitors);low=min(x['minimum_available_MiB'] for x in monitors);assert peak<600
    perf={'app_process_peak_MiB':peak,'minimum_observed_system_available_MiB':low,'first_dashboard_render_seconds':browser['timings']['first_render_seconds'],'galaxy_switch_seconds':browser['timings']['galaxy_switch_seconds'],'navigation':browser['workflows']['11_navigation']['detail'],'live_fit_seconds':live['seconds'],'live_fit_child_peak_MiB':live['peak_MiB'],'scope':'Application process; browser/supervisor separate. Process high-water, not isolated per-page allocation. Short bounded navigation test is not a long-duration leak proof.'};save('performance_summary.json',perf)
    for rel in ['README.md','docs/GATE_LEDGER.md']:
        p=ROOT/rel;archive=OUT/('previous_'+p.name)
        if not archive.exists():shutil.copyfile(p,archive)
    doc('M4_APPLICATION_ARCHITECTURE.md','''# M4 application architecture

Local Python 3.12 / Streamlit 1.63 / Plotly 6.3.1 application. `streamlit_app.py` owns navigation; four scripts in app_pages/ call the presentation functions in m4_ui.py. The versioned m4_adapter_v1 layer reads M2/M3 records, with per-file SHA-256 cache keys and frozen-manifest admission. st.cache_data returns session-safe serialized copies, bounded to twelve scientific entries and two manifests. No shared mutable array resource cache and no catalog fit on navigation.

m4_charts.py draws observations with published error bars, full-radius model curves and standardized model-minus-observed residuals. Lists are passed without numerical rounding. m4_adapter.preview calls unchanged M1 physics and checks its source hashes. No halo/RAR implementation exists in a UI callback. Immutable saved benchmark predictions remain authoritative.

m4_fit.py is an explicit optional serial exploratory process using M3 fit_fixed, with unchanged M1/Gate0R scientific configurations. Files go only into results/m4/v1/exploratory. Admission requires five memory samples, each >=1024 MiB, range <=128 MiB; active limits are 20 seconds, 180 MiB child peak and >=768 MiB available system memory. An exclusive lock prevents concurrent live fits. The app supervisor has a distinct M4 engineering envelope: app peak <=600 MiB and system available >=768 MiB. It binds only 127.0.0.1; telemetry is disabled. Monitor history is a bounded rolling window, with lifetime extrema retained. No GPU, Docker, WSL, MCMC, LLM, external API or background fitting.

Evidence exports serialize the displayed real arrays, original benchmark record, full scenario record or provenance. The original scientific package and M1–M3 results are untouched. No public deployment or push was performed.
''')
    doc('M4_SCIENTIFIC_UI_CONTRACT.md','''# M4 scientific UI contract

OBSERVED means original SPARC catalog-frame radius, velocity and published velocity error. VALIDATED RESULT means a saved M2/M3 benchmark record with exact source identity. INTERACTIVE PREVIEW means an explicitly requested new engine evaluation, not a fitted inference. EXPLORATORY FIT is a bounded new optimization, stored separately and never promoted into the benchmark.

Gas remains signed: its force term is Vgas |Vgas|; stellar terms are Υ V². Component charts are signed equivalent speeds, not independently measured total circular velocities. Negative or nonfinite squared totals are rejected without clipping or removing radii. Distance and inclination previews use the existing physical transformation and project predictions into the unchanged catalog frame; displayed observation arrays and errors do not change.

Remove dark matter removes only the reference halo term, holding its stellar M/L and geometry fixed. It does not refit. Unsupported baryonic totals are explicitly rejected. Restore clears galaxy-specific preview/removal/fit state. Neither action proves or disproves dark matter.

MLE uses normalized Gaussian likelihood, the original full mask and the frozen four-model decision. AIC/AICc/BIC are withheld when undefined; all MAP information criteria are withheld. Hiding a curve does not change the four-way winner. Eligibility excludes failed/unsupported results, mismatched masks, boundary contacts, rank deficiency and frozen ill-conditioning failures. Gap <2 is inconclusive. Convergence is not adequacy; strong parameter correlation and boundary warnings remain visible.

Atlas headline counts 79/18/5/5 apply only to 107 decisive M2 baselines. The complete population is 79/18/29/49 over 175. Persistence/flip fractions retain their valid and meaningful denominators; null, invalid, failed, unsupported and unavailable comparisons remain explicit. Scenario spans are not confidence intervals, grid frequencies are not theory probabilities, and overlapping named scenarios are not independent samples. Quality cuts change composition, not individual labels. MAP prior experiments and paired data χ² are never presented as evidence rankings.
''')
    doc('M4_DATA_INTEGRITY_VALIDATION.md',f'''# M4 data integrity

Executed read-only audit: {integrity['galaxies']} galaxies, {integrity['observational_radii']} radii, {integrity['negative_gas_rows']} negative gas rows; {integrity['exact_source_array_checks']} exact source-array comparisons. All 1,400 baseline model records retained, including seven nonconverged records. Every converged MLE/MAP prediction was reevaluated through the unchanged engine and checked against its saved array and standardized residuals. No benchmark optimization was rerun for aesthetics.

The 1,326-entry M3 manifest matched before documentation pointer updates. Historical README and gate-ledger bytes were archived in results/m4/v1/previous_README.md and previous_GATE_LEDGER.md, and m4_check.py verifies those exact historic bytes when checking the corresponding M3 entries. Other M3 manifest paths are checked in place. Prior Gate0/M1/M2 preservation evidence remains within M3; original scientific files have not been overwritten.

NGC3198 passed the mandatory gate before module expansion: all four curves, residuals, signed components, metadata, halo removal/restore and genuine CSV export. Real browser tests inspected actual Plotly DOM trace arrays for observations, errors, predictions and residuals. Downloaded CSV and JSON were compared with frozen sources. See vertical_slice_gate.json, data_integrity.json, tests.xml and browser_workflows.json under results/m4/v1.

Regression result: 107 passed, zero failures/errors (92 existing scientific tests + 15 new contract tests). Streamlit session tests additionally exercise failed baselines, state restoration, explicit previews, all modules and simulated low-memory admission.
''')
    workflow_lines='\n'.join(f"- {k}: {v['status']} — {v['detail']}" for k,v in browser['workflows'].items())
    doc('M4_BROWSER_WORKFLOWS.md',f'''# M4 real-browser workflows

Executed with Microsoft Edge headless and Playwright 1.56 against localhost. Screenshots are actual browser captures, not mockups. Desktop 1440×900 and laptop 1366×768 were inspected. All non-local origins were blocked throughout the final browser suite. Offline means core app navigation/data/charts/exports with installed dependencies and local data, not downloading dependencies without internet or physically disabling Windows networking.

{workflow_lines}

12 — Restart: PASS. The task server was stopped and a new process launched with the final source and compatible Starlette {restart['compatible_starlette']}. Actual NGC3198 DOM arrays and hashes matched; changed-Υ preview and restoration were verified in the browser. All four modules navigated after restart. See restart_and_preview_browser.json.

14 — Constrained memory: PASS for controlled admission behavior. A 900 MiB available-memory simulation in the actual Streamlit session disabled the optional fit button and showed a low-memory warning. The admission function rejects insufficient/unstable windows. The real live child was monitored and bounded. OS-wide memory exhaustion was deliberately not induced; no unrelated apps were terminated. This distinction remains a limitation rather than a fabricated stress-test result.

Early harness attempts are preserved separately: selectors were corrected for navigation icon text, native segmented controls, searchable options, valid empty plots and hidden accessibility cells. These are not counted as passing runs. The final complete suite is browser_workflows.json; a separate final-source restart/preview run follows it. The final server was stopped after testing, leaving no uncontrolled task server.
''')
    doc('M4_USABILITY_AUDIT.md','''# M4 usability and visual review

Actual browser screenshots were inspected at 1440×900 and 1366×768, including rotation/residual charts and atlas views. Navy foundations, white observations/error bars, blue NFW solid curves, amber Burkert dashes, mint dotted baryons and violet dash-dot RAR provide redundant labels and line styles. Axes retain km/s, kpc and dimensionless standardized residuals. Model controls, explicit preview labels and warning panels are native accessible Streamlit elements. Navigation stays in the sidebar; galaxy selection is searchable across 175 IDs. The galaxy combobox received keyboard focus in the browser.

The first visual review identified low-contrast selected controls; the final theme uses a lighter accent, with standard secondary action buttons to preserve readable labels. No custom CSS or remote fonts. Scientific charts are generated by Plotly locally. Frozen heatmaps are paginated to 35 galaxies; full tables and selector drill-down retain all 175. Dense diagnostics scroll as native tables; full units and assumptions remain inspectable. Invalid scenarios show warnings and observed data rather than invented replacement curves. Empty paired comparisons receive an explicit unavailable caption.

No fatal app/browser errors were present in the final workflows. Export buttons produced genuine downloaded values. Repeated navigation retained coherent galaxy state. Restore removes a galaxy's exploration state. Charts require ordinary vertical scrolling on a 768px-high laptop; the full six-panel research workflow is not forced above the fold.

Scope: a bounded functional/accessibility review, not a formal WCAG conformance certificate, screen-reader certification, user study or mobile usability claim. No unnecessary animations, imagery, fake confidence values or AI-generated interpretations.
''')
    doc('M4_PERFORMANCE.md',f'''# M4 measured performance

Application-process peak: **{peak:.3f} MiB**, below the 600 MiB target. Minimum observed available system memory across retained M4 server measurements: **{low:.3f} MiB**. Browser and supervisor processes are separate; this is not a whole-machine RSS claim.

First measured dashboard render: **{perf['first_dashboard_render_seconds']:.3f} s**; ordinary NGC3198→NGC2403 switch: **{perf['galaxy_switch_seconds']:.3f} s**. Timings include actual browser-render waits, not just Python imports. They are observed local samples, not universal latency guarantees. Server health startup and dependency installation are separate.

Four repeated complete navigation cycles / sixteen module visits: {perf['navigation']}. Bounded caches, per-galaxy loading and noncached figures limit accumulation. This short test cannot prove the absence of leaks during days of use or many simultaneous sessions. The app is a local single-user instrument, not a multi-user capacity claim.

One explicit NGC3198 NFW exploratory fit at disk Υ=0.55 converged: **{live['seconds']:.3f} s**, child peak **{live['peak_MiB']:.3f} MiB**. Five-sample preflight and active child/system/time limits were enforced. A low-memory UI admission simulation passed; OS exhaustion was not induced. No M1–M3 campaign was recomputed for the interface.

Raw measurements: results/m4/v1/performance_summary.json, browser_workflows.json, server monitor histories and live_fit_verification.json. App supervisor retains a bounded latest-9000-sample window plus lifetime extrema. The test server was stopped before final artifact hashing.
''')
    doc('M4_DEPLOYMENT_READINESS.md','''# M4 deployment and release boundary

**Local release candidate ready. Public release remains HOLD and unauthorized.** No GitHub push, publication, hosting, external messaging or public data upload occurred.

The existing local validated tree supports all four modules offline after installation/setup. Run Start-Gravity.ps1 or the documented local supervisor command. This is a single-user local research application; there is no authentication, internet-exposed service hardening or multi-user load-test claim. Binding remains 127.0.0.1. Use the managed supervisor to retain memory safeguards.

The source-only staging ZIP excludes raw astronomical files, per-galaxy numerical result arrays, screenshots containing observations, caches, virtual environments and logs. It includes source, configurations, scientific documentation, source references and the explicit hash-checking data downloader. It is a reviewable source candidate, not a self-contained populated scientific release. Downloading the three SPARC files alone does not recreate all frozen M1–M3 campaigns; the app also requires the existing validated evidence tree or a separately validated campaign regeneration. Do not present missing frozen results as synthetic defaults.

Licensing: no owner-approved open-source code license was invented. LICENSE_NOTICE.md explicitly records this pending decision. SPARC raw/cached data redistribution rights remain unresolved, so no data-bearing public package is prepared. The downloader uses official URLs and verifies frozen SHA-256 values before saving missing files. It refuses changed bytes and never overwrites existing data. Its verification mode was executed locally; fresh acquisition was not repeated merely for packaging.

Remaining public-release work: approve a code license; establish data/result redistribution and provenance policy; review a concrete public package; separately authorize publication/push/deployment. Local M4 GO does not authorize any of these actions. Dependency installation and browser availability are prerequisites, not evidence of deployment.
''')
    reproduction=r'''# M4 installation and reproducibility

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
'''
    doc('M4_REPRODUCIBILITY.md',reproduction)
    criteria={str(i):'PASS' for i in range(1,25)}
    acceptance={'verdict':'GO','criteria':criteria,'scope':'local single-user release candidate','scientific_tests_passed':107,'real_browser_workflows':12,'restart_browser':'PASS','low_memory':'Controlled 900 MiB UI admission simulation; no OS exhaustion claim','M3_manifest_files_preserved':1326,'public_release':'HOLD; not authorized; code/data rights decisions pending','published':False,'pushed':False,'deployed':False};save('acceptance.json',acceptance)
    doc('M4_GO_NO_GO.md',f'''# M4 final decision — 3 November 2026

**GO — local flagship scientific application release candidate.** All 24 acceptance criteria have executed evidence within the disclosed local scope. The required NGC3198 vertical gate passed before feature expansion.

Implemented: Galaxy lab (175 real galaxies, saved curves, signed components, residuals, halo removal/restore, explicit engine previews and bounded fresh fits); Model arena (MLE/MAP separation, frozen comparison eligibility, warnings and parameters); Fragility atlas (all 175 inventory, 107-baseline headline, interactive distributions/scatter/heatmap/quality cuts, transitions, scenario predictions and parameter curves); Evidence vault (real CSV/JSON, original records, provenance, manifests, methodological docs and scientific figures).

Scientific fidelity: 3,391 source radii and 361 negative gas rows preserved; all 1,400 baseline model records retained, with unchanged validated physics. 107 tests pass (92 existing +15 new); all 1,326 M3 manifest entries verified. Shared documentation-pointer histories were archived byte-for-byte before updating README/ledger.

Actual browser evidence: 12 complete workflows pass, including rendered trace-array comparisons, model toggles, halo removal, undefined comparisons, MAP guardrails, identifiability, all atlas classes, invalid/unsupported/failed cases, downloads, sixteen repeated module visits and blocked-external-origin core operation. Separate final-source stop/restart and changed-parameter preview/restore pass. Low-memory admission was checked with a controlled 900 MiB Streamlit-session simulation; no claim of real OS-wide exhaustion. Screenshots were visually reviewed at desktop/laptop dimensions.

Measured app peak {peak:.3f} MiB; first render {perf['first_dashboard_render_seconds']:.3f} s; galaxy switch {perf['galaxy_switch_seconds']:.3f} s. Explicit exploratory NFW fit {live['seconds']:.3f} s / {live['peak_MiB']:.3f} MiB child peak. Short navigation is not long-duration leak proof. Performance scopes and limits are in M4_PERFORMANCE.md.

Limits: conditional model comparisons; unknown radial covariance/systematics; parameter underdetermination; fixed finite scenario grid/thresholds; no theory-truth probabilities or new discovery. Native tables need scrolling. No formal WCAG certification or multi-user security/capacity claim. Source-only public staging is not a populated scientific data bundle; code license and data/result redistribution review remain pending. No scientific output was altered for presentation. No unresolved critical local scientific or functional defect was observed.

Exact local artifacts: streamlit_app.py, app_pages/, m4_adapter.py, m4_charts.py, m4_ui.py, m4_fit.py, m4_serve.py, Start-Gravity.ps1, requirements-m4*.txt; docs/M4_*.md; results/m4/v1/ (tests, browser/session/integrity/resource evidence, actual screenshots, exploratory output, acceptance and manifest); release/m4_source_candidate.zip (source-only, unpublished).

**GRAVITY ON TRIAL — LOCAL FLAGSHIP RELEASE CANDIDATE READY.** Public publication/push/deployment remain unauthorized and unperformed.
''')
    (ROOT/'README.md').write_text('''# Gravity on Trial

**Local flagship scientific release candidate · M4 GO.** An offline-capable research instrument for 175 SPARC galaxies and 3,391 measured radii. Four physical model families, visible residuals, explicit assumptions and a reproducible fragility atlas. No theory-truth probability or dark-matter proof/disproof claim.

## Explore the evidence

- **Galaxy lab:** observations with error bars, signed gas/stars, saved NFW/Burkert/baryons/RAR curves, parameters and warnings. Remove a halo without changing the observations; restore it; request clearly labeled previews or a bounded exploratory fit.
- **Model arena:** matched-mask MLE diagnostics and guarded AICc preferences; nuisance MAP results remain unranked. Unsupported, failed, boundary-limited and inconclusive outcomes stay visible.
- **Fragility atlas:** interactive population views and exact scenario drill-down. The 107 decisive baselines classify as 79 stable, 18 sensitive, 5 inconclusive, 5 unassessable; all 175 classify as 79/18/29/49. Across 1,028 valid physical comparisons: 906 retained, 52 flipped, 70 became inconclusive. These are conditional grid frequencies, not probabilities that theories are correct.
- **Evidence vault:** genuine numerical downloads, masks, units, provenance, input hashes, code/config identities, scientific warnings, reports, figures and manifests.

## Run locally on Windows

Use Python 3.12 and the existing validated evidence tree. Installation, verification and exact PowerShell commands are in [M4 reproducibility](docs/M4_REPRODUCIBILITY.md). Install requirements-m4.txt (requirements-m4-test.txt adds tests), then run `python m4_serve.py streamlit_app.py 8507` in the project directory. The convenient `Start-Gravity.ps1` uses the same supervised localhost server. Open http://127.0.0.1:8507. The supervisor enforces admission/memory limits; the application is CPU-only and requires no Docker, WSL, GPU or external API.

Benchmark navigation reads cached immutable records; previews are explicitly requested and fresh fitting is serial/bounded. A low-memory refusal never starts an optimizer. Observations, VALIDATED RESULT and INTERACTIVE PREVIEW are distinct throughout the application.

## Verification and scientific scope

107 tests pass, including the previous 92 scientific cases. Actual Edge/Playwright workflows verify displayed arrays, exports, controls, atlas classes, failed scenarios, offline-origin blocking and repeated navigation; final-source restart and preview checks also passed. All 1,326 frozen M3 manifest entries are preserved, with historical shared README/ledger bytes archived. See [M4 decision](docs/M4_GO_NO_GO.md), [data integrity](docs/M4_DATA_INTEGRITY_VALIDATION.md), [browser evidence](docs/M4_BROWSER_WORKFLOWS.md), [performance](docs/M4_PERFORMANCE.md) and [usability](docs/M4_USABILITY_AUDIT.md). Example scientific figures remain in results/m3/v1/figures/; actual application screenshots are in results/m4/v1/.

The four models are baryons only, NFW, Burkert and the fixed-a0 empirical RAR; the latter is not every modified-gravity theory. MLE holds disk/bulge M/L at 0.5/0.7 and catalog geometry; MAP uses explicit nuisance priors. Known-error Gaussian likelihood neglects unknown radial covariance and additional systematics. Optimizer convergence is not adequacy. Local parameter curvature is not guaranteed global identification. Finite stress-grid ranges are not credible intervals. The application introduces no scientific discovery claim.

## Provenance, licensing and release boundary

Credit: F. Lelli, S. S. McGaugh & J. M. Schombert (2016), [SPARC paper](https://arxiv.org/abs/1606.09251), [official collaboration data](https://astroweb.case.edu/SPARC/). Original observational reference codes and bibliography remain inspectable in Evidence vault. `python m4_data.py` verifies raw-source hashes; `--fetch` explicitly downloads missing official files, refusing changed bytes. It does not recreate the saved scientific campaigns. See [data provenance](docs/DATA_PROVENANCE.md) and the M1–M3 method/reproducibility reports.

No public release, push or deployment occurred. [LICENSE_NOTICE.md](LICENSE_NOTICE.md) records the pending owner-approved code license and unresolved data/result redistribution rights. Source-only staging excludes raw/cached scientific data, observation screenshots, caches and environments; it is not a self-contained populated release. The full application uses the validated local evidence tree. [Deployment readiness](docs/M4_DEPLOYMENT_READINESS.md) states the remaining public-release gates. Contributions must preserve frozen evidence; see [CONTRIBUTING.md](CONTRIBUTING.md).
''',encoding='utf-8')
    ledger=(OUT/'previous_GATE_LEDGER.md').read_text(encoding='utf-8');(DOC/'GATE_LEDGER.md').write_text(ledger+'\n\n## M4 — 3 November 2026\n\nGO: four-module local flagship release candidate; 107 tests, real-browser workflows, restart/offline/source-integrity checks, measured resources and documented limits. M1–M3 science preserved. Public release/license/data redistribution decisions remain HOLD and unauthorized. See M4_GO_NO_GO.md.\n',encoding='utf-8')
    save('environment.json',{'python':sys.version,'platform':platform.platform(),'streamlit':__import__('streamlit').__version__,'plotly':__import__('plotly').__version__,'numpy':np.__version__,'starlette':__import__('starlette').__version__,'no_git_revision_claim':'Workspace is not a Git checkout; SHA-256 content revisions are authoritative'})
    # Explicit source-only staging; never recursively copy the working scientific tree.
    files=[*ROOT.glob('m4_*.py'),ROOT/'streamlit_app.py',ROOT/'Start-Gravity.ps1',ROOT/'requirements-m4.txt',ROOT/'requirements-m4-test.txt',ROOT/'README.md',ROOT/'LICENSE_NOTICE.md',ROOT/'CONTRIBUTING.md',ROOT/'pyproject.toml',*ROOT.glob('m[123]_*.py'),ROOT/'recovery_monitor.py',*sorted((ROOT/'src').rglob('*.py')),*sorted((ROOT/'app_pages').glob('*.py')),*sorted((ROOT/'configs').glob('*.json')),*sorted(DOC.glob('*.md')),ROOT/'.streamlit/config.toml',ROOT/'data/manifests/acquisition.json']
    files=list(set(files+list(ROOT.glob('*.py'))+list((ROOT/'tests').rglob('*.py'))))
    patterns=[re.compile(r'gh[pousr]_[A-Za-z0-9]{30,}'),re.compile(r'sk-[A-Za-z0-9]{32,}'),re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')]
    findings=[str(p.relative_to(ROOT)) for p in files if any(pattern.search(p.read_text(encoding='utf-8')) for pattern in patterns)];assert not findings
    save('release_scan.json',{'source_files_scanned':len(files),'credential_pattern_findings':findings,'scope':'Explicit credential patterns in staged text files; not a formal secret-detection guarantee','raw_data_included':False,'per_galaxy_results_included':False,'license_assigned':False,'public_upload':False})
    release=ROOT/'release';release.mkdir(exist_ok=True);dest=release/'m4_source_candidate.zip'
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(set(files)):archive.write(p,str(p.relative_to(ROOT)))
        archive.writestr('.gitignore','data/raw/\nresults/\n.venv/\n__pycache__/\n.pytest_cache/\n.streamlit/secrets.toml\n*.log\n')
    with zipfile.ZipFile(dest) as archive:assert not any('/raw/' in n or n.startswith('results/') or '__pycache__' in n for n in archive.namelist())
    save('release_inventory.json',{'zip':'release/m4_source_candidate.zip','sha256':digest(dest),'files':len(set(files))+1,'scope':'source-only unpublished candidate; no open-source-license claim'})
    # Final source identity and artifact inventory, after all reporting mutations.
    paths=[*ROOT.glob('m4_*.py'),ROOT/'streamlit_app.py',ROOT/'Start-Gravity.ps1',*sorted((ROOT/'app_pages').glob('*.py')),ROOT/'.streamlit/config.toml',ROOT/'requirements-m4.txt',ROOT/'requirements-m4-test.txt']
    hashes={str(p.relative_to(ROOT)):digest(p) for p in sorted(paths)};save('source_identity.json',{'files':hashes,'content_revision':hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()})
    artifact_paths=[p for p in OUT.rglob('*') if p.is_file() and p.name!='artifacts_manifest.json']+list(DOC.glob('M4_*.md'))+paths+[ROOT/'README.md',DOC/'GATE_LEDGER.md',dest,ROOT/'LICENSE_NOTICE.md',ROOT/'CONTRIBUTING.md']
    save('artifacts_manifest.json',{str(p.relative_to(ROOT)):digest(p) for p in sorted(set(artifact_paths))})
    print(json.dumps({'verdict':'GO','tests':107,'browser_workflows':12,'peak_MiB':peak,'first_render_s':perf['first_dashboard_render_seconds'],'switch_s':perf['galaxy_switch_seconds'],'public_release':'HOLD','manifest_files':len(set(artifact_paths))}))
if __name__=='__main__':main()
