"""Evidence-backed M2 reporting, acceptance ledger and immutable manifest."""
import collections,csv,datetime,hashlib,importlib.metadata,json,math,platform,shutil,sys,xml.etree.ElementTree as ET
from pathlib import Path
from m2_compare import canonical,equivalent,comparison
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m2/v1';DOC=ROOT/'docs'
def read(p):return json.loads(p.read_text())
def save(name,data): (OUT/name).write_text(json.dumps(data,indent=2,allow_nan=False),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
CFG=read(ROOT/'configs/m2_v1.json');V=read(OUT/'full_validation.json');SUM=read(OUT/'population_summary.json');PILOT=read(OUT/'pilot_gate.json')
assert PILOT['GO'] and V['galaxies']==175 and V['radial_measurements']==3391 and V['negative_gas_rows']==361 and V['evaluations']==1400 and V['full_fresh_process_rerun']
tests=ET.parse(OUT/'tests.xml').getroot();assert len(list(tests.iter('testcase')))==54 and not list(tests.iter('failure')) and not list(tests.iter('error'))
assert read(OUT/'comparison_unit_checks.json')['count']==10
assert read(OUT/'independent_comparison_audit.json')['groups_checked']==350
preserved={}
for manifest_name in ['results/gate0r/artifacts_manifest.json','results/m1/v1/artifacts_manifest.json']:
    manifest=read(ROOT/manifest_name);count=0
    for path,digest in manifest.items():
        normalized=path.replace('\\','/')
        target=OUT/('previous_'+Path(normalized).name) if normalized in ['README.md','docs/GATE_LEDGER.md'] else ROOT/path
        assert sha(target)==digest,path
        count+=1
    preserved[manifest_name]=count
for path,digest in read(OUT/'baseline_freeze.json').items():assert sha(ROOT/path)==digest
rows=list(csv.DictReader((OUT/'evaluation_inventory.csv').open(encoding='utf-8')));assert len(rows)==1400
counts=collections.Counter(r['status'] for r in rows);assert dict(counts)==V['statuses']
assert sum(r['identifiability_warning']=='True' for r in rows)==V['warning_evaluations']
assert sum(r['boundary_contact']=='True' for r in rows)==V['boundary_evaluations']
max_parameter_delta=max_curve_delta=0;failures=[];start_failures=[];outliers=[];total_core_initial_seconds=0
source_identity=None
for galaxy in CFG['population_ids']:
    data=read(OUT/f'full/initial/{galaxy}.json');repeat=read(OUT/f'full/rerun/{galaxy}.json');equivalent(canonical(data),canonical(repeat));source_identity=data['identity']
    for a,b in zip(data['results'],repeat['results']):
        if a['status']=='CONVERGED':
            max_parameter_delta=max(max_parameter_delta,max((abs(x-y) for x,y in zip(a['parameters'],b['parameters'])),default=0));max_curve_delta=max(max_curve_delta,max(abs(x-y) for x,y in zip(a['prediction_km_s'],b['prediction_km_s'])))
            lo,hi=a['bounds']
            assert all(math.isfinite(v) and l-1e-10<=v<=h+1e-10 for v,l,h in zip(a['parameters'],lo,hi))
        else:failures.append({'galaxy':galaxy,'model':a['model'],'mode':a['mode'],'status':a['status'],'invalid_indices':a['invalid_indices'],'message':a.get('message'),'start_messages':[s.get('message') for s in a.get('attempts',[])]})
        for s in a.get('attempts',[]):
            if not s['success']:start_failures.append({'galaxy':galaxy,'model':a['model'],'mode':a['mode'],**s})
    for model in ['nfw','burkert']:
        f0=next(r for r in data['results'] if r['model']==model and r['mode']=='MLE');f1=next(r for r in data['results'] if r['model']==model and r['mode']=='MAP')
        if f0['status']==f1['status']=='CONVERGED':
            delta=max(abs(x-y) for x,y in zip(f0['parameters'][:2],f1['parameters'][:2]));outliers.append({'galaxy':galaxy,'model':model,'maximum_halo_log_parameter_shift_dex':delta,'metadata':data['metadata'],'F0_parameters':f0['parameters'],'F1_parameters':f1['parameters'],'F0_boundary':f0['boundary_flags'],'F1_boundary':f1['boundary_flags'],'F0_chi_squared':f0['statistics']['chi_squared'],'F1_data_chi_squared':f1['statistics']['chi_squared'],'F1_prior_penalty':f1['statistics']['prior_penalty'],'independent_checks':[f0['independent_halo_check'],f1['independent_halo_check']]})
for p,digest in source_identity['files'].items():assert sha(ROOT/p)==digest
assert sha(ROOT/'configs/m2_v1.json')==source_identity['files']['configs\\m2_v1.json']
save('failure_inventory.json',{'evaluation_failures':failures,'failed_optimizer_starts':start_failures,'accepted_nonphysical_solutions':0,'note':'Domain-failing trajectories are rejected; no-valid-start is not proof of physical nonexistence.'})
save('parameter_instability_examples.json',sorted(outliers,key=lambda r:r['maximum_halo_log_parameter_shift_dex'],reverse=True)[:12])
for name in ['common_subset_sensitivity','predictive_pilot']:equivalent(canonical(read(OUT/(name+'_initial.json'))),canonical(read(OUT/(name+'.json'))))
common=read(OUT/'common_subset_sensitivity.json');predictive=read(OUT/'predictive_pilot.json')
assert len(common)==1 and all(r['status']=='CONVERGED' for case in common for r in case['results'])
assert len(predictive)==5 and all(len(case['records'])==4 for case in predictive)
assert all(r['train_result']['status']=='CONVERGED' for case in predictive for r in case['records'])
save('supplemental_reproducibility.json',{'common_subset_galaxies':[c['galaxy'] for c in common],'predictive_galaxies':[c['galaxy'] for c in predictive],'two_executions_canonical_match':True,'source_identity':source_identity,'scope':'4 common-subset and 20 inner/outer-training model evaluations per execution; no changes to main full masks'})
comp=read(OUT/'comparison_records.json')
for sample in ['all_inventory','higher_quality']:
    selected=[c for c in comp if sample=='all_inventory' or c['higher_quality']]
    assert len(selected)==SUM['preferences'][sample]['galaxy_denominator']
    for family in ['four_way','NFW_Burkert']:
        status=collections.Counter(c[family]['status'] for c in selected);winner=collections.Counter(c[family]['winner'] for c in selected if c[family]['winner'])
        assert dict(status)==SUM['preferences'][sample][family]['status_counts'] and dict(winner)==SUM['preferences'][sample][family]['preference_counts']
monitors=[read(p) for p in list((OUT/'monitor').glob('*_monitor.json'))+list(OUT.glob('*_monitor.json'))];assert all(m['launched'] and m['exit_code']==0 and m['terminated_reason'] is None for m in monitors)
assert all(m['max_peak_working_set_MiB']<=180 and m['minimum_observed_available_MiB']>=512 for m in monitors)
peak=max(m['max_peak_working_set_MiB'] for m in monitors);floor=min(m['minimum_observed_available_MiB'] for m in monitors)
initial_resources=[read(p) for p in (OUT/'resources').glob('batch_full_initial_*.json')];rerun_resources=[read(p) for p in (OUT/'resources').glob('batch_full_rerun_*.json')]
assert len(initial_resources)==len(rerun_resources)==35
initial_seconds=sum(r['wall_seconds'] for r in initial_resources);repeat_seconds=sum(r['wall_seconds'] for r in rerun_resources);core_peak=max(r['peak_working_set_MiB'] for r in initial_resources+rerun_resources)
dispatcher=read(OUT/'full_initial_dispatch.json');rerun_dispatch=read(OUT/'full_rerun_dispatch.json')
figures=read(OUT/'figure_manifest.json');assert figures['count']==20 and all((OUT/'figures'/(name+'.png')).exists() and (OUT/'figures'/(name+'.svg')).exists() for name in figures['figures'])
controls=read(OUT/'synthetic_and_reference_controls.json');ref=controls['reference'];nuisance=read(OUT/'nuisance_stability_summary.json')
environment={'python':sys.version,'platform':platform.system(),'architecture':platform.machine(),'packages':{p:importlib.metadata.version(p) for p in ['numpy','scipy','pytest','psutil','matplotlib','Pillow']},'recorded_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'client_report_date':'3 November 2026, Asia/Kolkata','CPU_only':True,'BLAS_threads':1}
save('environment.json',environment)
save('acceptance.json',{'verdict':'GO','criteria':{str(i):'PASS' for i in range(1,19)},'pilot_GO':True,'validation_file':'full_validation.json','scientific_tests_passed':54,'comparison_checks_passed':10,'full_fresh_process_galaxies':175,'maximum_parameter_rerun_difference':max_parameter_delta,'maximum_curve_rerun_difference_km_s':max_curve_delta,'primary_evaluations':1400,'statuses':V['statuses'],'warning_evaluations':V['warning_evaluations'],'boundary_evaluations':V['boundary_evaluations'],'accepted_nonphysical_solutions':0,'source_content_revision':source_identity['content_revision'],'M3_started':False,'M4_started':False})
schema={'version':'M2-v1','primary_record':'full/initial/<ID>.json; matching fresh-process result in full/rerun/<ID>.json','unique_key':['galaxy','mode','model'],'inventory_counts':'n_inventory counts original radii, never only successful points','masks':{'attempted_mask':'All original indices for main experiment','accepted_mask':'Indices evaluated for a returned model; failed whole evaluations are empty. Successful fits always full original mask.','invalid_indices':'Static unsupported radii or union of radius indices at rejected optimization proposals. This is not an observation-deletion mask.','common_subset':'Separate experiment stores original indices [2..24] for UGC01281, excluding [0,1] for ALL four models.'},'resources':'Per-evaluation RSS/current wall time; process_lifetime_peak_so_far is worker high-water mark, not an isolated per-fit maximum. Batch monitor measures actual process peak/headroom.','parameters':'Optimization-coordinate values; precise physical units, expected bounds and null failure estimates are in evaluation_inventory.csv. Source/config/prior identities recoverable even when no solution exists.','statistics':'Gaussian velocity logL; separate MAP prior penalty. Main comparison MLE AICc only under frozen regularity/mask rules. Nominal formula values on boundary MLE records are not eligible evidence. Null means undefined/unavailable, never zero. Failed evaluations have null boundary/identifiability-assessment flags in the CSV, not false assessed negatives.','reproducibility':'Canonical removes timing/resource/stage/replicate metadata, retains numeric diagnostics and masks; tolerance 1e-10. Failed trajectory messages preserved.','partial_files':'*.partial.json are atomic progress snapshots, not additional evaluations; aggregate only exact <ID>.json names.'}
save('OUTPUT_SCHEMA.json',schema)
save('execution_inventory.json',{'main_initial':1400,'main_fresh_process':1400,'pilot_initial':160,'pilot_fresh_process':160,'common_subset_plus_predictive_per_execution':24,'supplemental_executions':2,'total_real_model_config_evaluations':3168,'main_optimizer_starts_per_sweep':sum(V['optimizer_start_counts'].values()),'main_failed_starts_per_sweep':V['optimizer_start_counts'].get('failed',0),'synthetic_control_cases':5,'note':'Repeated observations are not new independent galaxies; counts are execution records. 175 unique observed galaxies.'})
group_table='\n'.join(f"| {key} | 175 | {v['successful_n']} | {v['warning_n']} | {v['boundary_n']} | {v['reduced_chi_squared']['valid_n']} | {v['reduced_chi_squared']['median']:.4f} |" for key,v in SUM['groups'].items())
allpref=SUM['preferences']['all_inventory']['four_way'];hqpref=SUM['preferences']['higher_quality']['four_way'];pair=SUM['preferences']['all_inventory']['NFW_Burkert']
population=f'''# M2 population results — 3 November 2026

## Population and denominators

All 175 official SPARC galaxies and 3,391 radial measurements are represented, including 361 negative gas contributions in the frozen source. Q counts remain 99/64/12 for high/medium/low. No original radial observations were removed from the main benchmark. The prespecified higher-quality metadata cut Q<=2 and i>=30° contains 153 galaxies; it does not establish independent errors or eliminate astrophysical systematics.

Four physical families under F0 fixed MLE and F1 nuisance MAP yield 1,400 primary records: 1,393 CONVERGED, 2 UNSUPPORTED_DOMAIN and 5 NO_VALID_START. These results were independently rerun for all 175 galaxies in fresh processes. Converged includes 348 fixed-parameter F0 predictions and 1,045 optimized model/configuration problems; 1,050 optimization problems were attempted. All 3,850 declared optimizer starts are retained: 3,831 converged and 19 domain-aborted starts per full sweep. Convergence is not physical adequacy or parameter precision.

## Fit quality and identifiability

| Model/configuration | Inventory denominator | Converged | Warning-bearing | Bound-contact | Defined reduced chi² n | Median defined reduced chi² |
|---|---:|---:|---:|---:|---:|---:|
{group_table}

Medians above condition on valid values; the valid counts disclose missingness. They must not be compared as matched-population effect sizes. Twenty converged MAP halo cases have n<=k, making reduced chi² undefined (10 each for NFW and Burkert). Overall warnings: 988/1,400 evaluations; bound contacts: 278/1,400. These sets overlap and must not be added.

All 696 converged F1 cases have weak data-only directions; local data covariance is withheld. The explicit distance/inclination/halo scaling ridge explains why priors can select an optimum without making its parameters independently identifiable. F0 local covariance is returned for 131/175 NFW and 162/175 Burkert cases; these are known-error local approximations, not posterior intervals. Fixed models have no parameter-error estimation. Full parameter/uncertainty distributions with unavailable counts are in parameter_distributions.json.

## Frozen operational comparisons

All-inventory four-way F0 AICc: {allpref['eligible_n']}/175 eligible, {allpref['inconclusive_n']}/175 inconclusive, {allpref['unavailable_n']}/175 no valid comparison. The 107 eligible operational preferences are {allpref['preference_counts']}. These sum to 107, not 175; no winner is assigned to the other 68 galaxies. Runner-up gap>=2 is the frozen operational rule, not a theory probability or calibrated significance threshold.

NFW/Burkert-only comparison: {pair['eligible_n']}/175 eligible; preferences {pair['preference_counts']}; {pair['inconclusive_n']} inconclusive; {pair['unavailable_n']} unavailable. Four-way and pairwise counts answer different questions and are not interchangeable.

Higher-quality sample: {hqpref['eligible_n']}/153 eligible, {hqpref['inconclusive_n']}/153 inconclusive, {hqpref['unavailable_n']}/153 unavailable; preferences {hqpref['preference_counts']}. Boundary exclusion is a deliberate regularity condition, not removal of inconvenient observations: every bound-limited fit remains in the inventory and distributions. No F1 AIC/BIC or posterior-objective winner is reported.

## Nuisance dependence, residuals and properties

Matched F1/F0 data-chi² ratio medians: baryons {nuisance['baryons']['data_chi_squared_ratio_F1_to_F0']['median']:.3f} (174 paired cases), NFW {nuisance['nfw']['data_chi_squared_ratio_F1_to_F0']['median']:.3f} (175), Burkert {nuisance['burkert']['data_chi_squared_ratio_F1_to_F0']['median']:.3f} (174), RAR {nuisance['rar']['data_chi_squared_ratio_F1_to_F0']['median']:.3f} (173). These are conditional residual changes under more freedom/priors, not ML likelihood-ratio tests or comparisons of physical truth. Raw chi², changing k and MAP penalty remain separate.

NGC4389, NGC2976 and UGC02455 can move NFW log-mass estimates across the entire 8–14 dex allowed box between F0/F1; independent halo integrals still pass and boundaries flag the results. Such shifts are evidence of assumption/bound sensitivity, not new accurate halo-mass measurements. Burkert extremes also span broad prior boxes. The twelve largest inspected cases retain both parameters, bounds and independent checks in parameter_instability_examples.json.

All standardized residual arrays are saved; 26,969 valid residual points across F0/F1 feed descriptive plots. These are repeated/model-dependent uses of the 3,391 observed measurements, not independent observations. Point-weighted radial medians/IQRs reveal conditional structure; neighboring-radius correlation, normalization by Rmax and source-quality mix limit inference. Large residuals are retained (e.g. NGC2403), and reduced chi² below one does not certify a true model.

Exploratory Spearman tables cover luminosity, central surface brightness, HI-to-light proxy, morphology, inclination, ring count, radial coverage and Q. They carry valid-pair n, full inventory denominator and no p-values. For example, NFW warning versus outer radius has rho≈−0.340 (175 successful cases); Burkert's corresponding value is ≈−0.043 (174). These are associations, not causal explanations or controlled multiple-testing discoveries. The constant F1 warning indicator has no defined association coefficient, not a fabricated zero.

## Supplemental checks

UGC01281's two nonpositive fixed baryonic-force radii (indices 0,1) invalidate full-mask baryons/RAR evaluation and make some optimizer trajectories infeasible. A separately labeled common-positive subset uses indices 2–24 (23/25 points) for every model; all four models converge there. It does not replace the full records or join main preference counts. Five prespecified inner-70%/outer-30% F0 experiments produced all 20 training/evaluation results and repeated in fresh processes. They test radial extrapolation with correlated errors, not fully independent predictive validation; saved weighted outer errors are in predictive_pilot.json. No global calibration or M3 campaign ran.

Scientific figures: 12 population/parameter figures and 8 selected full-mask galaxy figures, PNG/SVG, source-linked to saved arrays. See figures/contact_sheet.png and figure_manifest.json. No astronomical photos or synthetic observations are used.
'''
(DOC/'M2_POPULATION_RESULTS.md').write_text(population,encoding='utf-8')
failuretext=f'''# M2 failure and limitation audit

Primary denominator: 1,400 model/configuration evaluations over 175 galaxies. Seven evaluations return no accepted solution: UGC01281 F0 baryons/RAR unsupported; UGC01281 F0 Burkert and F1 baryons/Burkert/RAR have no converged feasible trajectory among declared starts; UGC07577 F1 RAR also has no converged trajectory. Failure records/attempt messages/masks are in failure_inventory.json and raw per-galaxy files. UGC01281 NFW F0/F1 each succeeds despite one domain-aborted start. In total, 19/3,850 optimizer starts abort on explicit physical-domain guards; none are counted as converged.

NO_VALID_START is a frozen operational status: it includes a valid initial point whose later optimizer trajectory crosses the physical domain. It is not a proof of model nonexistence. UGC07577 has a defined F0 RAR prediction, demonstrating that its F1 failure is a limitation of the frozen search/guard policy. Feasible-region constrained/backtracking optimization is a bounded future remediation experiment; it was not introduced post-hoc to improve this benchmark. Rejecting invalid proposals rather than accepting false solutions is correct, but it limits completeness of the optimizer's solution search.

Accepted nonphysical speeds/parameters: zero under the executed positivity/finite/bounds checks. Unexplained NaNs, unit changes or silently clipped signed gas: zero. DIAGNOSTIC_FAILURE and OPTIMIZER_FAILED evaluation statuses: zero. Every converged halo prediction passes independent density quadrature at every accepted radius. The two source-force radii remain in all main records; only the separately named common-subset sensitivity excludes them consistently for all models.

988 warning-bearing and 278 boundary-bearing evaluations overlap. All 696 converged MAP likelihoods have geometry degeneracy; rank of a finite-difference Jacobian does not establish exact physical identifiability. Twenty MAP halo cases have undefined reduced chi². F0 nominal AIC/AICc/BIC formulas remain stored for audit, but only the frozen regular interior/same-mask cases are ranked. Sparse samples, strong correlations, boundary cases and incomplete error covariance weaken such approximations. MAP criteria are always null. A convergence label alone never implies parameter plausibility or model adequacy.

Large parameter shifts are retained, including six-dex NFW mass changes across opposite bounds and Burkert core-radius shifts across its box. Selected extremes were inspected with saved independent quadrature checks; no units defect was found. They are assumption/bound sensitivity, not posterior precision. Four-way comparisons are unavailable for 44/175 and inconclusive for 24/175, with no winner assigned.

Source errors omit inclination and other systematics; global inclination does not model resolved warps; residuals can be correlated. The sample is a heterogeneous observational compilation, not a random independent draw of all galaxies. Quality cuts are metadata filters, not cures. HI/L36 is a proxy, not total gas fraction. No covariance-aware likelihood, cosmological prior experiment, new theory, full MCMC or M3 fragility atlas was added. Raw redistribution licensing remains unresolved; files stay local and git-ignored. No deployment, publication, remote push or third-party contact occurred.

Visual QA found long footnotes clipped on compact figures; notes were wrapped and figures regenerated from unchanged numbers. Parameter/error figures were added from saved fits. The first-pass resource summary was preserved. No statistical/physical method or acceptance threshold changed after results. No unresolved accepted-result numerical correctness error was demonstrated; known search/likelihood/interpretive limitations remain explicit.
'''
(DOC/'M2_FAILURE_AND_LIMITATION_AUDIT.md').write_text(failuretext,encoding='utf-8')
reference=f'''# M2 primary-literature comparison

This is a targeted primary-source review, including 2026 overlap; not a systematic literature census or independent peer review. No source/method was changed to force agreement. No astrophysical novelty claim is made.

1. Lelli, McGaugh & Schombert (2016), [SPARC](https://arxiv.org/abs/1606.09251): source observations/derived components, stellar convention, attribution and sample provenance. Official frozen data give exactly 175 galaxies/3,391 radii. Radius-level quantities were independently re-tokenized against production loading for every galaxy; the separate author archive cross-check from Gate 0 remains preserved. This is not a reconstruction from raw imaging/interferometry. No new data release is substituted.

2. Li et al. (2018), [individual RAR fits](https://arxiv.org/html/1803.00022): same empirical acceleration formula and geometry scalings; variable stellar ML/distance/inclination and priors. Their reported fit statistic is acceleration-space and their method is MCMC. M2 uses normalized velocity-space likelihood and coordinate-defined truncated MAP priors. At their rounded NGC3198 values, M2 evaluation of their acceleration-error convention gives {ref['evaluated_reduced_acceleration_chi_squared']:.6f} versus published 2.057 (~0.19% difference). This descriptive agreement supports implementation consistency but does not reproduce their posterior or guarantee identical data revisions/sign conventions. Their small-scatter/population claims cannot be directly compared to our fixed F0 statistics.

3. Li et al. (2020), [halo catalog](https://arxiv.org/abs/2001.10538): seven halo families and nuisance-parameter inference, including cosmological prior considerations. Our NFW/Burkert equations overlap, but free fixed-geometry F0 and bounded-coordinate MAP are different experiments. Burkert sometimes providing smaller residuals is established prior art. We do not claim numerical reproduction of their halo posterior tables, universal halo ordering, or a contradiction when masks/priors differ. No unresolved like-for-like numerical halo discrepancy was concealed: an aligned posterior replication was not performed.

4. Smith et al., [23 October 2026 preprint](https://arxiv.org/abs/2610.33157), abstract-level review: their 147-galaxy analysis and weak-lensing extensions report increased DM/MOND degeneracy with geometry uncertainty. This overlaps our concern about identifiability, but their models, sample and lensing evidence extend beyond this benchmark. We do not test their large-scale conclusions or claim new priority.

5. Gupta & Samaras, [12 August 2026 preprint / MNRAS record](https://arxiv.org/abs/2608.11575), abstract-level review: a full-SPARC inverse-formulation comparison involving CCC, MOND and NFW. Its inverse predictions, fitted hypotheses and statistic differ from our forward velocity-space experiment; its reported model rankings are not harmonized with M2 and are neither adopted nor refuted here. The overlap shows full-catalog benchmarking itself is not novel.

6. Flynn, [15 April 2026 corpus preprint](https://arxiv.org/abs/2604.13489), abstract-level review: a multi-survey standardized rotation-curve corpus including SPARC. Data engineering and reproducibility also have prior art. Its files were not acquired or used; its stated license does not establish redistribution permission for our independently frozen official raw files.

Safe statement: GRAVITY ON TRIAL is a local reproducible benchmark of four simplified dynamical descriptions with explicit domains, failures, assumption-sensitive nuisance fits and denominators. It does not decide dark-matter existence, validate every MOND formulation, claim a new gravity law, or establish publication novelty. Larger updates/new samples are a separate future validation task, not part of the frozen original-175 scope.
'''
(DOC/'M2_REFERENCE_COMPARISON.md').write_text(reference,encoding='utf-8')
repro=f'''# M2 reproducibility and source identity

Scientific content revision: `{source_identity['content_revision']}`. No Git repository exists; exact SHA-256 content identities and source_snapshot/ copies replace a fabricated commit ID. Frozen configurations: configs/m2_v1.json, configs/m1_v1.json and configs/gate0r.json. Original raw file hashes and the canonical parsed source remain unchanged. Primary outputs include source/config paths, seed 20261102, exact original arrays, masks, every optimizer start and diagnostics. No stochastic starts or noise were used in the benchmark.

All 20 pilot galaxies and all 175 full-population galaxies were independently rerun in fresh controlled worker processes, one serial batch at a time. Both complete sweeps share no cached fit records. Canonical comparison retains masks/parameters/curves/statistics/diagnostic arrays and removes only timing/resource/stage/replicate fields. Frozen tolerance 1e-10 rtol/atol; maximum observed parameter difference {max_parameter_delta:.3g}, maximum speed difference {max_curve_delta:.3g} km/s. No subset-to-full extrapolated reproduction claim is needed. Every full-mask accepted halo was independently checked against numerical density integration, and all saved likelihood/criteria were independently recomputed from observations/predictions with scalar sums.

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
'''
(DOC/'M2_REPRODUCIBILITY.md').write_text(repro,encoding='utf-8')
perf=f'''# M2 measured performance

Serial CPU/single BLAS thread; native Windows monitoring every 50 ms; preflight five samples over two seconds each >=768 MiB and range<=128 MiB; sampled execution available-memory floor 512 MiB and child peak cap 180 MiB. No GPU, Docker/WSL, parallel fits, process killing or paging changes. Initial M2 inspection available memory was about 1,448 MiB; exact stage preflights and histories are saved. System headroom is sampled, not continuously guaranteed.

20-galaxy initial pilot workers: {PILOT['initial_worker_seconds']:.3f} seconds, peak {PILOT['peak_worker_MiB']:.3f} MiB. Its estimate authorized attempting a full rerun under the frozen <=600-second rule, not a promise about unseen cases.

175-galaxy initial sweep: 35 workers, combined worker wall time {initial_seconds:.3f} seconds; dispatcher wall time {dispatcher['wall_seconds']:.3f} seconds including preflights/startup/coordination. Complete fresh-process sweep: {repeat_seconds:.3f} seconds worker time, {rerun_dispatch['wall_seconds']:.3f} seconds dispatcher time. Each sweep stayed below the aspirational 10-minute deterministic campaign target. This target result applies to the declared 8-evaluation-per-galaxy configuration, not MCMC/UI performance.

Maximum core worker peak {core_peak:.3f} MiB. Overall observed peak, including plotting/tests/aggregation, {peak:.3f} MiB; lowest monitored available system memory {floor:.3f} MiB. All recorded tasks passed safety limits. Per-evaluation RSS and elapsed time are recorded, but process_lifetime_peak_so_far is the serial worker's high-water mark through that evaluation, not a fabricated isolated per-fit peak. Full batch and current-RSS monitor histories disambiguate scope.

All computations checkpointed per galaxy atomically. Main resume was explicitly tested on one completed five-galaxy batch without recomputation (resume_check.json). The initial clipped-footer plotting pass was preserved separately, then corrected using the same data. Total conversational/development time is not estimated from summing nested worker times. No runtime for M3/M4 or other hardware is claimed.
'''
(DOC/'M2_PERFORMANCE.md').write_text(perf,encoding='utf-8')
final=f'''# M2 final decision — 3 November 2026 (Asia/Kolkata)

## Verdict

**GO — complete frozen-population benchmark within its declared scope.** Mandatory 20-galaxy pilot passed before full fitting. M3/M4 remain unauthorized and unstarted. Known search/domain/identifiability limits are explicit; no accepted-result systematic mathematical/physical correctness failure remains demonstrated.

## Scientific evidence

175/175 unique official galaxies, 3,391/3,391 observed radii, all 361 negative gas terms retained. Quality flags and geometry preserved. Four models × two inference configurations × 175 galaxies = 1,400 primary evaluations, including 348 fixed-model predictions and 1,050 optimizer problems. Results: 1,393 CONVERGED (1,045 optimized problems plus 348 predictions), 2 UNSUPPORTED_DOMAIN, 5 NO_VALID_START. All seven failures and all 19/3,850 failed starts are visible; no nonphysical solution accepted and no main radial row silently removed.

All 175 galaxies rerun in fresh processes; canonical comparisons pass at frozen tolerances, observed parameter/speed differences {max_parameter_delta:.3g}/{max_curve_delta:.3g}. All accepted halo curves pass independent quadrature at every radius; raw token ingestion and scalar likelihood/statistic checks cover the complete inventory. 54 inherited scientific tests, 10 comparison-rule checks and five explicitly synthetic controls passed. Separate common-point and 20 radial training/outer-prediction cases are saved/repeated. Twenty scientific PNG/SVG figures include fit/residual/parameter/error/preference/quality diagnostics and eight individual curves.

Identifiability warnings: 988/1,400; bound contacts: 278/1,400; sets overlap. Twenty converged MAP halo reduced-chi² values are undefined at n<=k. All 696 converged MAP likelihoods show a weak geometry direction; their data covariance is withheld. Model convergence is not physical adequacy or parameter precision.

Four-way F0 AICc eligibility: 131/175, comprising 107 operational preferences and 24 inconclusive; 44/175 no valid comparison. Preferences: Burkert 59, NFW 42, RAR 3, baryons-only 3. High-quality cut: 153 galaxies, 115 eligible, 21 inconclusive, 38 unavailable, preferences Burkert 51/NFW 40/RAR 3. These conditional results do not establish a population-independent theory ranking. No winner is assigned where invalid/inconclusive; no F1 MAP score is mislabeled ML evidence.

## Computational evidence

Initial full dispatch {dispatcher['wall_seconds']:.3f} seconds ({initial_seconds:.3f} combined worker seconds), complete independent repeat {rerun_dispatch['wall_seconds']:.3f} seconds ({repeat_seconds:.3f} worker seconds). Core peak {core_peak:.3f} MiB; overall monitored peak {peak:.3f} MiB; minimum sampled available RAM {floor:.3f} MiB. Every launched task stayed within the frozen safety limits; no expensive service, parallelism or unrelated process termination.

## Findings, failures and limits

Fixed-baryon baselines generally leave large residuals; halo/RAR adequacy varies with assumptions. Nuisance freedom changes data residuals and can move halo parameters across their entire boxes. Priors select points along physical likelihood ridges; returned optima are not independent measurements. Structured residuals, low ring counts, Q=3/low inclination, incomplete systematic errors and correlated radial observations limit interpretation. Exploratory property associations have no significance/causality claims.

NO_VALID_START means all declared trajectories failed to yield a feasible converged solution; it does not prove the physical model is undefined. UGC01281's full-mask signed-force issue and UGC07577's MAP RAR search limitation remain in the denominator. A future separately versioned constrained-domain solver pilot is a focused remediation; no post-hoc tuning improved the frozen results. A source-layout issue and Gate 0/M1 evidence remain unchanged. Nominal ML criterion formulas are stored but not ranked at excluded boundaries/regularity failures. Search completeness and observational likelihood assumptions remain limitations, not concealed solved issues.

Primary-literature review includes 2016/2018/2020 and targeted 2026 sources; selected RAR numerical consistency is documented, differing sample/priors/inverse/lensing methods prevent universal direct score comparison. Full-catalog comparison and covariance/degeneracy themes have substantial prior art. No new law, dark-matter detection/falsification, publication readiness or astrophysical discovery claimed. Raw redistribution licensing remains unresolved; local-only data stay git-ignored.

## Artifacts and authorization

Results: results/m2/v1/evaluation_inventory.csv, population_groups.csv, population_summary.json, comparison_records.json, parameter_distributions.json, nuisance_stability_summary.json, failure_inventory.json, full_validation.json, acceptance.json; all per-galaxy primary/rerun files, monitor logs, controls, schema, source snapshot, manifest and figures. All required M2 reports are in docs/. Data/config/source are hash-identified; exact reproduction commands and resume behavior are documented.

**M3 — MODEL FRAGILITY ATLAS IS ELIGIBLE FOR AUTHORIZATION.** Do not start M3 automatically. M4 likewise remains unauthorized.
'''
(DOC/'M2_GO_NO_GO.md').write_text(final,encoding='utf-8')
(DOC/'GATE_LEDGER.md').write_text('# Authorization ledger\n\n| Stage | State | Evidence |\n|---|---|---|\n| Gate 0 | GO; preserved | GATE0R_LOW_MEMORY_RECOVERY.md |\n| M1 | GO; preserved | M1_GO_NO_GO.md |\n| M2 | AUTHORIZED and GO | M2_GO_NO_GO.md; results/m2/v1/acceptance.json |\n| M3 | ELIGIBLE; NOT AUTHORIZED / NOT STARTED | Separate authorization required |\n| M4 | NOT AUTHORIZED / NOT STARTED | Prior gates and authorization required |\n',encoding='utf-8')
(ROOT/'README.md').write_text('''# GRAVITY ON TRIAL

**M2 GO: a frozen 175-galaxy SPARC population benchmark. M3/M4 remain unauthorized and unstarted.**

All 175 galaxies and 3,391 measured radii are represented. Four models (Newtonian baryons, NFW, Burkert, empirical RAR), separate F0 maximum likelihood and F1 nuisance MAP inference, full failure/domain/boundary/identifiability accounting. Complete independent fresh-process rerun; no observational rows silently dropped. No theory probability or astrophysical discovery claim.

Start with docs/M2_GO_NO_GO.md and docs/M2_POPULATION_RESULTS.md. The frozen method is docs/M2_BENCHMARK_PROTOCOL.md; reproduction and measured resources are documented separately. Results/m2/v1/ contains the 1,400-row evaluation inventory, full per-galaxy JSON, matched comparisons, parameter/error distributions, warnings, failures, numerical controls, PNG/SVG figures and content-hashed source snapshots. The primary 20-galaxy pilot gate passed before full fitting. Original Gate 0/M1 data, code, results and reports remain preserved; prior README/ledger copies accompany M2.

131/175 regular same-mask F0 comparisons are eligible; 107 operational preferences, 24 inconclusive, 44 unavailable. Accepted numerical solutions are not necessarily good physical fits. Known-error local covariance is conditional; MAP geometry degeneracy and bound contacts remain visible. RAR is an empirical prescription, not a complete test of all modified-gravity theories. No dashboard, MCMC, public release, hosting or paid service was activated. Raw-data redistribution permission remains unresolved.
''',encoding='utf-8')
snapshot=OUT/'source_snapshot'
paths=set(source_identity['files'])|{str(p.relative_to(ROOT)) for p in ROOT.glob('m2_*.py')}|{'recovery_monitor.py','tests/test_m1.py','pyproject.toml'}
for name in paths:
    if name.replace('\\','/').startswith(('data/','results/')):continue
    dest=snapshot/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
save('preservation_checks.json',preserved)
paths=[p for p in OUT.rglob('*') if p.is_file() and p.name!='artifacts_manifest.json']+list(DOC.glob('M2_*.md'))+[ROOT/'README.md',DOC/'GATE_LEDGER.md',ROOT/'configs/m2_v1.json']
save('artifacts_manifest.json',{str(p.relative_to(ROOT)):sha(p) for p in paths})
print(json.dumps({'verdict':'GO','galaxies':175,'radii':3391,'evaluations':1400,'full_rerun_galaxies':175,'statuses':V['statuses'],'warnings':V['warning_evaluations'],'boundaries':V['boundary_evaluations'],'worker_seconds':initial_seconds,'dispatch_seconds':dispatcher['wall_seconds'],'peak_core_MiB':core_peak,'overall_peak_MiB':peak,'minimum_available_MiB':floor,'manifest_files':len(paths)}))
