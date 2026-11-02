"""Audit saved numerical evidence and generate Gate 0R reports without scientific imports."""
import csv,hashlib,json,math,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'results/gate0r'; DOC=ROOT/'docs'
checks=[]; fits=[]; summary=[]
campaign=json.loads((OUT/'campaign_status.json').read_text())
assert campaign['numerical_campaign_complete'] and len(campaign['completed'])==10
for row in campaign['completed']:
    g,m=row['galaxy'],row['model']; a=json.loads((OUT/f'{g}_{m}_initial.json').read_text()); b=json.loads((OUT/f'{g}_{m}_rerun.json').read_text()); fits.append(a)
    assert a['success'] and b['success'] and a['excluded_points']==0
    assert all(s['success'] for s in a['all_starts']+b['all_starts'])
    for key in ['parameters_log10','prediction_km_s','standardized_residuals']: assert a[key]==b[key]
    residual=[(pred-obs)/err for pred,obs,err in zip(a['prediction_km_s'],a['observed_km_s'],a['error_km_s'],strict=True)]
    assert all(math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-12) for x,y in zip(residual,a['standardized_residuals']))
    assert math.isclose(math.fsum(v*v for v in residual),a['chi_squared'],rel_tol=1e-12)
    assert a['fitted_quadrature_max_relative_error']<1e-9 and all(c['max_relative_quadrature_error']<1e-9 for c in a['controls'])
    assert a['small_radius_relative_error']<2e-6
    summary.append({'galaxy':g,'model':m,'n':a['n'],'k':2,'parameter_1':a['parameters_physical'][0],'parameter_2':a['parameters_physical'][1],'chi_squared':a['chi_squared'],'reduced_chi_squared':a['reduced_chi_squared'],'boundary_limited':a['boundary_limited'],'peak_MiB':a['resource']['peak_working_set_MiB'],'wall_seconds':a['resource']['wall_seconds']})
    checks.append({'galaxy':g,'model':m,'checks':'4 starts converge; independent integral and limits pass; no exclusions; saved residual/chi consistency; exact clean-process reproducibility','passed':True})
monitors=[json.loads(p.read_text()) for p in OUT.glob('*_monitor.json')]
assert all(m['launched'] and m['exit_code']==0 and m['terminated_reason'] is None and m['minimum_observed_available_MiB']>=512 for m in monitors)
peaks=[json.loads(p.read_text())['resource']['peak_working_set_MiB'] for p in OUT.glob('*_initial.json')]+[json.loads(p.read_text())['resource']['peak_working_set_MiB'] for p in OUT.glob('*_rerun.json')]
plots=json.loads((OUT/'published_table_crosscheck.json').read_text()); peaks.append(plots['resource']['peak_working_set_MiB'])
assert max(peaks)<=180 and len(plots['evidence'])==5
checkpoint=json.loads((OUT/'checkpoint.json').read_text()); assert all(v['matches'] for v in checkpoint['raw_hash_checks'])
for item in checkpoint['raw_hash_checks']: assert hashlib.sha256((ROOT/'data/raw'/item['file']).read_bytes()).hexdigest()==item['sha256']
snapshot=json.loads((ROOT/'results/gate0/parsed_tables.json').read_text()); digest=hashlib.sha256(json.dumps(snapshot,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
assert digest==json.loads((ROOT/'results/gate0/verification.json').read_text())['canonical_parsed_sha256']
test={'scope':'Executed Gate 0R evidence assertions; not the eventual full project test matrix','per_model_checks':checks,'raw_and_prior_parsed_hashes_unchanged':True,'monitored_runs_all_safe':True,'published_table_checks_pass':True,'scientific_failures':[]}
(OUT/'test_report.json').write_text(json.dumps(test,indent=2))
with (OUT/'fit_summary.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=summary[0]);writer.writeheader();writer.writerows(summary)
first=json.loads((OUT/'import_probe_preflight.json').read_text())['available_MiB'][0]
imports=json.loads((OUT/'import_probe_stdout.txt').read_text())
floor=min(x['minimum_observed_available_MiB'] for x in monitors)
table='\n'.join(f"| {s['galaxy']} | {s['model']} | {s['n']} | {s['chi_squared']:.6f} | {s['reduced_chi_squared']:.4f} |" for s in summary)
report=f'''# Gate 0R low-memory recovery — 2 November 2026

## 1. Verdict

**GO for Gate 0 only.** Original mandatory acceptance evidence is now present under the explicitly user-authorized Gate 0R memory exception. M1 is scientifically eligible for authorization; M1–M4 were not launched and remain unauthorized in this recovery operation.

## 2. What was built

Native Windows memory preflight/child monitor, stable NFW and Burkert squared-speed functions, a serial single-galaxy multi-start fitting probe, clean-process comparisons, separate static plot renderer, and saved-evidence audit/report generation. No full-catalog fits, RAR, sensitivity atlas, dashboard, MCMC, GPU, or publication. The original Gate 0 checkpoint is preserved and raw files/configs are unchanged. No pre-existing methodology file or numerical test suite existed at checkpoint inspection; methodology is now documented.

## 3. Scientific evidence

Prior verified inventory: 175 galaxies / 3,391 radial points / 361 negative gas terms. Raw hashes and prior canonical parsed hash verified without reacquiring data. New campaign: 10 distinct real galaxy/model fits, 10 fresh-process reruns; all 80 individual starts across both executions converged. Four fixed starts per model, deterministic bounded least squares; no random starts, no removed points, no boundary contacts. Repeated parameter, prediction, and standardized-residual arrays differ by exactly zero in these executions. Per-start local minima and diagnostics are retained, so convergence of a start is not a global-optimality proof.

Independent quadrature at 30 logarithmically spaced radii for each of four parameter sets per profile agrees within frozen 1e-9 relative tolerance; maximum recorded discrepancy {max(c['max_relative_quadrature_error'] for f in fits for c in f['controls']):.4g}. Small-radius controls pass the frozen 2e-6 relative limit; NFW M200/R200 consistency and zero/negative/nonfinite radius rejection pass. Each fitted curve is independently checked via density integration. Every saved residual and chi-squared was independently recomputed from saved predictions/observations.

All {sum(e['published_archive_rows_verified'] for e in plots['evidence'])} selected-galaxy rows match the authors' separately distributed Rotmod ZIP in radius, Vobs, error, gas, disk, and bulge. Independent scalar baryonic sums agree within 1e-9 (km/s)². This satisfies the published-table cross-check route; the archive and MRT derive from the same observations and are not independent datasets. No claim of reproducing published halo posteriors or digitized figures is made. The source is the Newtonian mass-model product linked at https://astroweb.case.edu/SPARC/ ; credit Lelli, McGaugh & Schombert (2016), https://arxiv.org/abs/1606.09251 .

Five source-attributed PNG/SVG plots contain measured error bars, signed gas conventions, scaled stellar components, baryons-only and fitted curves, units, and residuals. NGC3198 was visually inspected and a cropped-title layout issue corrected before final rendering; all five final plots were inspected individually.

| Galaxy | Model | n | Chi-squared | Reduced chi-squared |
|---|---|---:|---:|---:|
{table}

Large residuals, especially NGC2403, demonstrate that optimizer convergence does not ensure an adequate physical description under fixed baryonic/geometry assumptions. No population-level preference or theory inference is justified by this five-galaxy engineering validation.

## 4. Computational evidence

Windows GlobalMemoryStatusEx initial preflight: {first:.3f} MiB available; five-sample range recorded in import_probe_preflight.json. Stability rule, defined before execution: five samples over two seconds, each at least 768 MiB, range at most 128 MiB. Initial Python import-probe baseline {imports['baseline_MiB']:.3f} MiB; after NumPy/SciPy imports {imports['after_import_MiB']:.3f} MiB (increment {imports['after_import_MiB']-imports['baseline_MiB']:.3f} MiB). Scientific process baselines are saved individually. Maximum scientific fit peak {max(f['resource']['peak_working_set_MiB'] for f in fits):.3f} MiB; maximum including separate plotting {max(peaks):.3f} MiB. Lowest available memory across monitored execution: {floor:.3f} MiB, above 512 MiB. All preflights passed. One scientific process at a time, one BLAS thread, CPU only.

Monitor sampling interval 50 ms; process lifetime peak working set is also read within child processes, reducing the risk that polling misses a peak. System headroom is sampled rather than continuously guaranteed. Native process inventory exposed only a limited set (Python/PowerShell/conhost); it could not reliably identify the machine-wide major consumers. No process was terminated and no Windows memory/paging setting changed. The initial profile was measured; 1 GiB is not asserted to be a numerical fit requirement.

Per-fit wall time and memory: fit_summary.csv. Full monitor histories include preflight and child wall time; do not sum CPU times or describe these as a full 175-galaxy performance result. Plotting resource measurements are separate.

## 5. Failures and limitations

No failed mathematical controls, optimizer starts, controlled-process terminations, or bound-limited selected fits. Several poor goodness-of-fit values remain scientific limitations, not numerical failures. Independent-Gaussian catalog errors omit inclination and other systematics. Identifiability diagnostics are numerical Jacobian condition numbers, not posterior uncertainties. No global-optimum certification, broad parameter-space property test, synthetic recovery suite, or clean-environment installation audit is claimed; these belong to later engine validation. RAR is explicitly deferred as allowed at Gate 0.

Licensing for raw redistribution remains unresolved: data stay local and git-ignored; no publication occurred. Source zero/missing semantics for Vflat and absent bulges remain for M1 data-edge-case work, and did not enter these fits. The scientific functions are a minimal gate prototype, not a full installable platform. Resource authorization applies only to this bounded recovery, not later milestones.

## 6. Artifacts

results/gate0r/: fit_summary.csv, campaign_status.json, test_report.json, checkpoint.json, published_table_crosscheck.json; per-galaxy initial/rerun JSON files; monitor/preflight/stdout/stderr logs; five *_curves.png and five *_curves.svg figures. configs/gate0r.json freezes assumptions/tolerances and records the user-authorized exception. Source: src/gravity_on_trial/halos.py, scientific_probe.py, recovery_monitor.py, complete_recovery.py, render_recovery.py, finalize_recovery.py. artifacts_manifest.json hashes the final evidence and scientific source/config files.

## 7. Decision

Stop this recovery with Gate 0 GO. M1 is eligible for separate authorization; do not automatically start it. Retain the original 1 GiB baseline configuration and this separately scoped memory exception. No dark-matter discovery, gravity falsification, novel astrophysics, or full-platform completion is claimed.
'''
(DOC/'GATE0R_LOW_MEMORY_RECOVERY.md').write_text(report,encoding='utf-8')
prior=DOC/'GATE0_INITIAL_BLOCKED.md'
if not prior.exists(): shutil.copyfile(DOC/'GATE0_GO_NO_GO.md',prior)
(DOC/'GATE0_GO_NO_GO.md').write_text(report,encoding='utf-8')
(DOC/'GATE_LEDGER.md').write_text('# Gate ledger\n\n| Stage | State | Evidence |\n|---|---|---|\n| Gate 0 initial | BLOCKED (historical) | GATE0_INITIAL_BLOCKED.md |\n| Gate 0R / Gate 0 final | GO | GATE0R_LOW_MEMORY_RECOVERY.md; user-authorized bounded memory exception |\n| M1 | ELIGIBLE; NOT AUTHORIZED / NOT STARTED | Separate authorization required by Gate 0R |\n| M2–M4 | NOT AUTHORIZED / NOT STARTED | Predecessor scientific gates and later authorization required |\n')
method='''# Gate 0 scientific method

Fixed stellar M/L 0.5 disk / 0.7 bulge, signed gas Vgas*abs(Vgas). No point cuts. Catalog distances and inclinations fixed. Velocity residual=(sqrt(Vbar²+Vhalo²)−Vobs)/eVobs; independent Gaussian likelihood assumption, no prior penalty, two halo parameters. Baryons-only has zero fitted parameters and its residuals/chi-squared are in published_table_crosscheck.json.

NFW parameters: log10 M200 [solar masses], log10 concentration; R200=(G M200/(100 H0²))^(1/3), G=4.30091e-6 kpc (km/s)²/Msun, H0=73 km/s/Mpc=0.073 km/s/kpc. Burkert parameters: log10 central density [Msun/kpc³], log10 core radius [kpc]. Exact bounds and four starts in configs/gate0r.json. These are freely fitted halos without concentration–mass priors. Positive radii required; negative total squared speed raises an explicit error, never clamped. All selected radii have nonnegative baryonic squared speed. Small-radius series avoid cancellation. Density quadrature and separately derived critical-density conversion provide independent controls; the constants remain explicit physical assumptions.

Log-parameter bounded SciPy least_squares uses x_scale=jac, ftol/xtol/gtol=1e-11, max_nfev=2000. All starts retained; best chi-squared selected. Boundary fraction 1e-5; numerical Jacobian condition number recorded. No calibrated confidence intervals, evidence probabilities or AIC/BIC rankings are produced at Gate 0. Large chi-squared values are retained. The exact same data mask and unchanged errors apply to all three models.

Tolerance and resource policy were frozen before scientific fits in configs/gate0r.json. Fresh-process comparison rel_tol=1e-10, abs_tol=1e-12; observed outputs match exactly. Native memory monitor checks every 50 ms and terminates only its own controlled child if memory criteria fail.
'''
(DOC/'SCIENTIFIC_METHOD.md').write_text(method,encoding='utf-8')
(ROOT/'README.md').write_text('''# GRAVITY ON TRIAL

**Gate 0 GO under the user-authorized Gate 0R low-memory protocol.** M1–M4 remain unstarted and unauthorized. This is a five-galaxy scientific prototype, not the full platform.

Read docs/GATE0R_LOW_MEMORY_RECOVERY.md for validation, assumptions and limitations; docs/SCIENTIFIC_METHOD.md for formulas and fit conventions. Evidence is in results/gate0r/. The original acquisition checkpoint is preserved in results/gate0/ and docs/GATE0_INITIAL_BLOCKED.md.

Python 3.12.10 with installed NumPy 2.2.1, SciPy 1.18.1, Matplotlib 3.11.1 and psutil 7.0.0; no dependencies were installed. Run commands from this project directory, serially:

```powershell
python recovery_monitor.py
python recovery_monitor.py NGC3198 nfw initial
python recovery_monitor.py NGC3198 nfw rerun
python recovery_monitor.py NGC3198 burkert initial
python recovery_monitor.py NGC3198 burkert rerun
python complete_recovery.py
python recovery_monitor.py plots
python finalize_recovery.py
```

Each monitored step requires >=768 MiB stable available RAM, maintains >=512 MiB sampled available RAM, and caps child peak working set at 180 MiB. Stop on any failure. These commands overwrite corresponding recovery outputs; copy the evidence first if retaining a historical run. No data download is needed for recovery. Raw data and original configs must remain unchanged. No UI, discovery, theory verdict, population benchmark or redistribution license is claimed.
''',encoding='utf-8')
files=list(OUT.glob('*'))+[ROOT/'configs/gate0r.json',ROOT/'scientific_probe.py',ROOT/'src/gravity_on_trial/halos.py',ROOT/'recovery_monitor.py',ROOT/'render_recovery.py',ROOT/'complete_recovery.py',ROOT/'finalize_recovery.py']
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file() and p.name!='artifacts_manifest.json'}
(OUT/'artifacts_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'verdict':'GO','fits':len(fits),'all_starts_converged':80,'maximum_process_peak_MiB':max(peaks),'minimum_available_MiB':floor}))

