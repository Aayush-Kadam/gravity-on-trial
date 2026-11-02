"""M3 reports and decision generated from verified experiment tables, not narrative guesses."""
import collections,csv,datetime,hashlib,importlib.metadata,json,math,platform,shutil,sys,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m3/v1';DOC=ROOT/'docs'
def read(p):return json.loads(p.read_text())
def save(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fmt(value):return 'NA' if value is None else f'{value:.4f}'
CFG=read(ROOT/'configs/m3_v1.json');V=read(OUT/'full_validation.json');SUM=read(OUT/'atlas_summary.json');METRICS=read(OUT/'atlas_metrics.json');QUALITY=read(OUT/'quality_composition.json');PILOT=read(OUT/'pilot_gate.json');AUDIT=read(OUT/'identifiability_audit.json')
assert PILOT['GO'] and V['galaxies']==175 and V['planned_scenario_records']==2450 and V['planned_model_slots']==9800 and V['fresh_process_rerun_galaxies']==175
assert len(METRICS)==175 and sum(SUM['primary_classification_counts'].values())==175 and SUM['baseline_decisive_n']==107
assert V['model_slot_status_counts'].get('DIAGNOSTIC_FAILURE',0)==0
assert read(OUT/'independent_metric_audit.json')['all_pass'] and read(OUT/'independent_metric_audit.json')['galaxies_checked']==175
tests=ET.parse(OUT/'tests.xml').getroot();assert len(list(tests.iter('testcase')))==92 and not list(tests.iter('failure')) and not list(tests.iter('error'))
preserved={}
for name in ['results/gate0r/artifacts_manifest.json','results/m1/v1/artifacts_manifest.json','results/m2/v1/artifacts_manifest.json']:
    manifest=read(ROOT/name)
    for path,digest in manifest.items():
        normalized=path.replace('\\','/')
        if normalized in ['README.md','docs/GATE_LEDGER.md']:
            parent=ROOT/'results/m2/v1' if '/m1/' in name else OUT
            target=parent/('previous_'+Path(normalized).name)
        else:target=ROOT/path
        assert sha(target)==digest,(name,path)
    preserved[name]=len(manifest)
assert sha(ROOT/'configs/m3_v1.json')==read(OUT/'baseline_verification.json')['config_sha256']
model_rows=list(csv.DictReader((OUT/'model_evaluations.csv').open(encoding='utf-8')));scenario_rows=list(csv.DictReader((OUT/'scenario_inventory.csv').open(encoding='utf-8')))
assert len(model_rows)==9800 and len(scenario_rows)==2450
assert dict(collections.Counter(r['status'] for r in model_rows))==V['model_slot_status_counts']
assert sum(r['identifiability_warning']=='True' for r in model_rows)==V['warning_evaluations'] and sum(r['boundary_contact']=='True' for r in model_rows)==V['boundary_evaluations']
failure_records=[];source=None;actual_optimized=actual_fixed=0;near_counts=0;duplicate_records=[]
for galaxy in CFG['population_ids']:
    data=read(OUT/f'full/initial/{galaxy}.json');source=data['identity'];seen={};dupes=[]
    for s in data['scenarios']:
        if s['kind']=='physical' and s['proposal_status']=='APPLICABLE':
            key=tuple(s['spec'][name] for name in ['upsilon_disk','upsilon_bulge','distance_ratio','inclination_deg'])
            if key in seen:dupes.append({'scenario_id':s['scenario_id'],'same_fixed_assumptions_as':seen[key]})
            else:seen[key]=s['scenario_id']
        for r in s['results']:
            if r['status'] not in ['NOT_APPLICABLE','INVALID_PROPOSAL']:
                if r.get('attempts'):actual_optimized+=1
                else:actual_fixed+=1
            if r['status']!='CONVERGED':failure_records.append({'galaxy':galaxy,'scenario':s['scenario_id'],'kind':s['kind'],'model':r['model'],'mode':r['mode'],'status':r['status'],'reason':r.get('reason',r.get('message')),'failed_start_messages':[a.get('message') for a in r.get('attempts',[]) if not a['success']],'invalid_indices':r.get('invalid_indices',[])})
    if dupes:duplicate_records.append({'galaxy':galaxy,'duplicates':dupes})
for path,digest in source['files'].items():assert sha(ROOT/path)==digest,path
save('failure_inventory.json',{'records':failure_records,'status_counts':V['model_slot_status_counts'],'accepted_nonphysical_solutions':0,'note':'Null/invalid planned slots are not failed calculations. Domain-aborted optimizer trajectories do not establish physical model nonexistence.'})
save('overlapping_scenarios.json',{'galaxies_with_overlapping_fixed_assumptions':len(duplicate_records),'records':duplicate_records,'interpretation':'Joint stellar and disk-only perturbations coincide without a bulge; other zero-uncertainty directions may overlap. The named frozen grid retains these equal-weight design slots. They are not independent random draws or a posterior.'})
monitor_files=list((OUT/'monitor').glob('*_monitor.json'));monitors=[read(p) for p in monitor_files];launched=[m for m in monitors if m['launched']]
assert all(m['exit_code']==0 and m['terminated_reason'] is None and m['max_peak_working_set_MiB']<=180 and m['minimum_observed_available_MiB']>=512 for m in launched)
refusals=[read(p) for p in OUT.glob('preflight_refusal_*.json')];assert all(not r['launched'] for r in refusals)
peak=max(m['max_peak_working_set_MiB'] for m in launched);floor=min(m['minimum_observed_available_MiB'] for m in launched)
initial_resources=[read(p) for p in (OUT/'resources').glob('batch_full_initial_*.json')];repeat_resources=[read(p) for p in (OUT/'resources').glob('batch_full_rerun_*.json')];assert len(initial_resources)==len(repeat_resources)==35
initial_seconds=sum(r['wall_seconds'] for r in initial_resources);repeat_seconds=sum(r['wall_seconds'] for r in repeat_resources);core_peak=max(r['peak_working_set_MiB'] for r in initial_resources+repeat_resources)
dispatch=read(OUT/'full_initial_dispatch.json');redispatch=read(OUT/'full_rerun_dispatch.json');assert dispatch['complete'] and redispatch['complete']
figures=read(OUT/'figure_manifest.json');assert figures['count']>=22 and all((OUT/'figures'/(name+'.png')).exists() and (OUT/'figures'/(name+'.svg')).exists() for name in figures['figures'])
optimizer=read(OUT/'optimizer_crosschecks.json')['records'];assert len(optimizer)==36 and sum(r.get('objective_agreement_within_target') is True for r in optimizer)==33
method_records=[]
for r in optimizer:
    if r.get('dogbox_best') is None or r['trf_status']!='CONVERGED':continue
    if r['scenario']=='baseline':data=read(ROOT/f'results/m2/v1/full/initial/{r["galaxy"]}.json');trf=next(a for a in data['results'] if a['mode']=='MLE' and a['model']==r['model'])
    else:data=read(OUT/f'full/initial/{r["galaxy"]}.json');trf=next(a for s in data['scenarios'] if s['scenario_id']==r['scenario'] for a in s['results'] if a['model']==r['model'])
    method_records.append({'galaxy':r['galaxy'],'model':r['model'],'scenario':r['scenario'],'objective_difference':r['chi_squared_difference_dogbox_minus_trf'],'log_parameter_differences':[a-b for a,b in zip(r['dogbox_best']['parameters'],trf['parameters'])]})
save('optimizer_method_parameter_changes.json',method_records)
near_counts=sum(r.get('material_halo_range') is True for r in read(OUT/'optimizer_start_sensitivity.json'))
save('preservation_checks.json',preserved);save('environment.json',{'python':sys.version,'platform':platform.system(),'architecture':platform.machine(),'packages':{p:importlib.metadata.version(p) for p in ['numpy','scipy','pytest','psutil','matplotlib','Pillow']},'UTC_recorded':datetime.datetime.now(datetime.timezone.utc).isoformat(),'client_report_date':'3 November 2026, Asia/Kolkata','CPU_only':True,'BLAS_threads':1})
decisive=[m for m in METRICS if m['baseline_status']=='PREFERENCE'];valid_total=sum(m['valid_comparable_scenarios'] for m in decisive);retained=sum(m['counts']['retained'] for m in decisive);flipped=sum(m['counts']['flipped'] for m in decisive);to_inc=sum(m['counts']['to_inconclusive'] for m in decisive)
assert retained+flipped+to_inc==valid_total
save('acceptance.json',{'verdict':'GO','M3_criteria':{str(i):'PASS' for i in range(1,19)},'pilot_GO':True,'galaxies':175,'planned_scenario_records':2450,'planned_model_slots':9800,'actually_evaluated_model_slots':V['actual_evaluated_model_slots'],'model_status_counts':V['model_slot_status_counts'],'primary_fragility_classes':SUM['primary_classification_counts'],'baseline_decisive_fragility_classes':SUM['decisive_baseline_classification_counts'],'decisive_baseline_valid_comparisons':valid_total,'retained':retained,'flipped':flipped,'to_inconclusive':to_inc,'warning_evaluations':V['warning_evaluations'],'boundary_evaluations':V['boundary_evaluations'],'test_cases_passed':92,'dogbox_comparable':33,'dogbox_total':36,'full_fresh_process_galaxies':175,'source_content_revision':source['content_revision'],'M4_started':False})
save('OUTPUT_SCHEMA.json',{'version':'m3-v1','inventory':'175 original galaxies; 14 named scenarios/galaxy, including explicit null and invalid states','physical_scenarios':'12 per galaxy. MLE halo k=2; fixed baryons/RAR k=0. Fixed external perturbations are not counted as fitted parameters. Source observations/errors/masks unchanged.','prior_scenarios':'2 per galaxy, MAP only. Parameter ordering, sigmas, centers/bounds and data/prior objectives distinct; no AIC/BIC ranking.','masks':'original_mask is intended catalog mask. accepted_mask is all original indices for valid returned models, empty on null/invalid/whole-rejected cases. No main radius-level exclusion.','parameters':'Log10 M200/Msun and c200, or log10 rho0/(Msun/kpc^3) and r0/kpc; stellar ML log10 solar units at 3.6 micron; distance ratio dimensionless, inclination degrees. Fixed assumptions in scenario.spec.','resources':'process_lifetime_peak_so_far is worker high-water mark through evaluation, not an isolated fit peak; monitor contains measured RSS/headroom','metrics':'Retained/flipped/inconclusive divided by valid comparable perturbations for decisive baseline. Unknowns/invalids also retained in planned and meaningful denominators. Nulls are not supporting trials.','labels':'Prespecified operational STABLE/SENSITIVE/INCONCLUSIVE/UNASSESSABLE; primary and lenient/strict alternatives separate; no posterior interpretation','partial_files':'*.partial.json are progress snapshots, not extra evaluations','source_identity':source})
baseline_counts={'PREFERENCE':107,'INCONCLUSIVE':24,'NO_VALID_COMPARISON':44};model_status=V['model_slot_status_counts'];primary_classes=SUM['primary_classification_counts'];decisive_classes=SUM['decisive_baseline_classification_counts']
star_rows=[r for r in scenario_rows if r['family']=='F1_ML'];geo_rows=[r for r in scenario_rows if r['family']=='F2_geometry'];priors=read(OUT/'prior_sensitivity.json');stats=read(OUT/'statistical_sensitivity.json')
classification_table='\n'.join(f"| {c} | {primary_classes.get(c,0)} / 175 | {decisive_classes.get(c,0)} / 107 |" for c in ['STABLE','SENSITIVE','INCONCLUSIVE','UNASSESSABLE'])
quality_table='\n'.join(f"| {name} | {q['galaxy_denominator']} | {q['baseline_comparison_counts']} | {q['fragility_classes']} |" for name,q in QUALITY.items())
def transition_table(rows):
    return '\n'.join(f"| {sid} | "+' | '.join(str(sum(r['scenario_id']==sid and r['baseline_status']=='PREFERENCE' and r['transition']==outcome for r in rows)) for outcome in ['retained','flipped','to_inconclusive','unavailable','invalid_proposal','not_applicable'])+' |' for sid in dict.fromkeys(r['scenario_id'] for r in rows))
heading='| Scenario | Retained | Different preference | Inconclusive | Unavailable | Invalid proposal | Not applicable |\n|---|---:|---:|---:|---:|---:|---:|\n'
star=f'''# M3 stellar-mass sensitivity

Six frozen fixed stellar perturbations per galaxy: disk-only, bulge-only, joint +/-0.1 dex around 0.5/0.7 solar M/L. Same 175 galaxies, observed radii/errors, halo bounds/starts, H0 and fixed RAR acceleration scale. No unrelated nuisance parameter was refit; only the halo's two free parameters remain fitted. Signed gas always preserved.

Named stellar scenario outcomes among 107 decisive M2 baselines (each row denominator 107):

{heading}{transition_table(star_rows)}

Null bulge-only shifts are explicitly NOT_APPLICABLE, not artificial support for persistence. Joint and disk-only shifts coincide when the bulge is absent; primary fractions retain the frozen named-grid weights, not independent-sample weights. Such overlap and every invalid/unavailable state are saved. This grid does not exhaust stellar-population uncertainties.

Per-model before/after parameter values, prediction changes in km/s, catalog-frame data likelihood, AICc/BIC applicability, conditioning and bounds are in model_evaluations.csv and full per-galaxy JSON. Ranges use log10 physical units encoded in parameter names. They are scenario spans, not confidence/credible intervals. M3 physical cases do not alter model complexity to make an assumption perturbation look like an extra fitted parameter. Static figures 02 and 05 and selected galaxy before/after curves derive from these actual arrays.
'''
(DOC/'M3_STELLAR_MASS_SENSITIVITY.md').write_text(star,encoding='utf-8')
geo=f'''# M3 distance/inclination sensitivity

Six fixed geometry cases per galaxy: D +/-eD, i +/-eI, two joint same-sign corners. Catalog uncertainties provide scales; these are deterministic stress cases, not posterior draws or an empirical covariance model. Covariance between errors is unknown; the selected corners neither estimate it nor exhaust all joint combinations. D<=0 or i outside (0,90] is INVALID_PROPOSAL, never clipped/replaced. Error-bar values remain unchanged in the saved catalog-frame likelihood.

Geometry scenario outcomes among the 107 decisive baselines (each row denominator 107):

{heading}{transition_table(geo_rows)}

For ratio d=Dnew/Dcat, physical radii and signed baryonic squared speeds scale by d; halos are evaluated at rescaled radius. Physical model speed projects to catalog frame by sin(inew)/sin(icat). The alternate computation view divides both observations and errors by that factor. The full log-likelihood transformation includes the density Jacobian, not merely residual equivalence. All applicable accepted predictions were checked against explicit geometry evaluation; all catalog-frame likelihoods independently recomputed. {V['scalar_baryons_RAR_point_checks']} scalar baryons/RAR force-point checks and all-radius halo quadrature checks passed, in addition to the 92 tests including independent injected-geometry recovery.

All original 3,391 measurements remain present. Rejected proposals reduce valid coverage and remain in the meaningful-scenario denominator; they cannot support a baseline preference. Parameter changes and bound/identifiability transitions are saved. Distance-inclination likelihood ridges do not become physical measurements because an optimizer or prior picks a single point. No inclination correction was applied twice.
'''
(DOC/'M3_DISTANCE_INCLINATION_SENSITIVITY.md').write_text(geo,encoding='utf-8')
qualitytext=f'''# M3 observational-quality composition sensitivity

All five samples use original catalog metadata. Changing a population definition never changes an individual galaxy's source radii, fit, or fragility classification. Perturbed inclinations do not change membership in these catalog-defined cuts. No radial uncertainty filter was introduced. Lower-quality systems remain in the complete inventory.

| Sample | Galaxy denominator | M2 baseline classifications | M3 operational classes |
|---|---:|---|---|
{quality_table}

quality_composition.json additionally supplies per-sample valid physical comparison counts, preferred-model counts, planned model-slot denominators, warning/bound counts, unavailable assessments, residual distributions and luminosity/surface-brightness/HI-to-light/inclination/ring-count/coverage distributions. Successful-only summaries disclose their valid n and missing n. Warning and boundary sets overlap; null/invalid slots must not be called assessed negatives.

Differences between these population tables are composition effects, not individual preference flips. Q/inclination cuts do not establish independence, remove every systematic, or calibrate theory probabilities. Residuals remain conditional on the declared independent Gaussian catalog-error approximation. The HI-to-light quantity is a proxy, not a directly measured total gas fraction.
'''
(DOC/'M3_QUALITY_CUT_SENSITIVITY.md').write_text(qualitytext,encoding='utf-8')
prior_counts=collections.Counter((r['width_dex'],r['status']) for r in priors)
statistical=f'''# M3 prior, optimizer and statistical sensitivity

## Prior strength, separate MAP experiments

Two MAP stellar prior widths, 0.05 and 0.2 dex, bracket the 0.1-dex fiducial. Centers 0.5/0.7, geometry priors, positive domains, all physical boxes and the same deterministic M2 starts are unchanged. Widths are prior-strength stress cases, not measured populations. No concentration-mass or other cosmological halo prior is added; such a relation would change the physical hypothesis. Counts by width/status: {dict(prior_counts)}.

Per-parameter changes, data chi², prior penalty and boundary/conditioning outputs are retained in prior_sensitivity.json. No MAP AIC/AICc/BIC or cross-prior posterior-evidence ranking is calculated. Different prior widths can select different ridge locations without new information. The new adapter at 0.1 dex reproduced frozen M2 MAP parameters/predictions for 12 real galaxy/model cases before M3 fitting. No legacy source was edited.

## Optimizer checks

Each physical halo scenario uses four deterministic M2 initializations; nuisance MAP starts also remain unchanged. All attempts, domain aborts, objective ranges and ranges among solutions within delta objective<=1 are retained. {near_counts} galaxy/scenario/halo records show >0.1 dex spread among such near-objective solutions; this flags practical ambiguity, not proof of posterior multimodality. Identical repeats do not prove physical identifiability.

Independent dogbox trust-region checks covered six frozen galaxies × three scenarios × two halos =36 problems, with two starts, unchanged bounds and 1e-6 relative objective agreement target. 33 comparable cases agree; three UGC01281 Burkert cases yield no feasible pair under the frozen domain/search policies. Their failures are visible, not proof of physical model nonexistence. Parameter differences despite objective agreement are in optimizer_method_parameter_changes.json. No bound was narrowed or failed solution counted successful.

## Likelihood-comparison choices

AIC/AICc/BIC alternatives use identical data/likelihoods and the common M2 regular-eligibility gate. The operational decisive gap stays 2. At the M2 baseline, changing from AICc changes decision/winner status in {stats['AIC']['baseline_changed_count']}/175 cases for AIC and {stats['BIC']['baseline_changed_count']}/175 for BIC. Across applicable physical scenarios, decision/winner changes are {stats['AIC']['physical_changed_decision_count']} / {stats['AIC']['physical_applicable_scenarios']} for AIC and {stats['BIC']['physical_changed_decision_count']} / {stats['BIC']['physical_applicable_scenarios']} for BIC; their valid comparison denominators are separately stored. No criterion choice is pooled into primary physical persistence fractions.

Predicted performance, ML criterion penalties, MAP objectives, parameter plausibility and curve adequacy are different quantities. None becomes a probability that a gravity theory is true. No MCMC, bootstrap probability calibration, new global acceleration fitting or full stochastic uncertainty campaign was run. This bounded deterministic design and its stored parameter/likelihood ranges are the declared uncertainty experiment.
'''
(DOC/'M3_STATISTICAL_SENSITIVITY.md').write_text(statistical,encoding='utf-8')
atlas=f'''# M3 Model Fragility Atlas results — 3 November 2026

## Inventory and execution

All 175 original galaxies and 3,391 measurements remain represented. M2's 107 operational preferences, 24 inconclusive comparisons and 44 unavailable comparisons remain frozen. M3 has 2,450 initial galaxy-scenario records and 9,800 planned model slots: 12 physical scenarios and 2 separate prior-width cases per galaxy. Actual model calculations {V['actual_evaluated_model_slots']}, including {actual_optimized} optimized problems and {actual_fixed} fixed predictions/evaluations. Model statuses: {model_status}. Null and invalid proposals are planned records, not successful fits or failed astrophysical theories. Full repeat covered all 175 galaxies.

## Operational classifications

| Category | Full inventory | Decisive M2 baseline subset |
|---|---:|---:|
{classification_table}

Baseline unavailable cases are UNASSESSABLE by definition; baseline inconclusive cases remain INCONCLUSIVE. They are not silently reassigned a baseline winner. For decisive baselines, valid>=6 and valid/(12-null)>=0.6 required; then inconclusive/valid>=0.5 yields INCONCLUSIVE; otherwise persistence>=0.8 and flip/valid<=0.1 yields STABLE; remaining assessable cases SENSITIVE. Valid includes decisive and inconclusive scenarios. Every continuous metric, coverage and raw count is in fragility_classifications.csv / atlas_metrics.json.

## Persistence and changes with explicit denominators

Among 107 decisive baseline galaxies: {retained} retained, {flipped} changed to a different decisive model, and {to_inc} became inconclusive out of {valid_total} valid comparable physical scenarios. These are scenario-weighted counts, not independent galaxy trials. Other outcomes remain explicit: {SUM['decisive_baseline_transition_counts']}. Per-galaxy persistence median {fmt(SUM['decisive_galaxy_persistence_distribution']['median'])}, flip-frequency median {fmt(SUM['decisive_galaxy_flip_distribution']['median'])}, each with {SUM['decisive_galaxy_persistence_distribution']['valid_n']}/107 defined denominators. A high valid-only persistence fraction does not erase low coverage or unavailable outcomes.

All physical scenario outcomes: {V['comparison_status_counts']}; the 350 MAP experiments are explicitly NOT_A_LIKELIHOOD_COMPARISON and excluded from these preference metrics. Actual rejected physical proposals are counted in both scenario and model-slot units. Unsupported-domain and failed-search states are not the same as an inconclusive valid comparison. Underlying all-175 inventory is never dropped.

## Definition, parameter and information sensitivity

Frozen classification alternatives: {SUM['threshold_sensitivity']}. They use the same arrays and do not replace primary labels. Differences demonstrate the dependence of operational categories on normative thresholds; no categorical claim of calibrated scientific confidence is made.

Parameter ranges/medians use appropriate log/physical units; covariance/rank/near-minimum diagnostics and every new bound contact remain visible. New warning-bearing evaluations {V['warning_evaluations']}/{V['actual_evaluated_model_slots']} actual calculations ({V['planned_model_slots']} planned slots); bound-bearing evaluations {V['boundary_evaluations']}/{V['actual_evaluated_model_slots']}. These overlapping sets must not be added or compared to the smaller M2 experiment without matching denominators. Low parameter variation at a bound does not imply a precise physical measurement.

The geometry ridge is verified for all 696 converged M2 MAP cases; this underdetermination and unknown radial covariance limit physical interpretation. Primary fixed-scenario and prior-width effects are separate. Joint/disk cases coincide without a bulge in {len(duplicate_records)}/175 galaxies (details in overlapping_scenarios.json); equal weights describe the frozen named stress matrix, not an empirical perturbation distribution. The design tests limited stellar/geometric offsets, two prior strengths and statistical/numerical choices, not all possible astrophysics.

## Figures and interpretation

{figures['count']} PNG/SVG figures cover all 175 IDs in readable matrix pages, stellar/distance/inclination outcomes, parameter spans, warning/bound frequencies, quality composition, category/threshold dependence, priors/statistics and selected before/after real rotation curves. Before/after selection is frozen maximum-change display among valid comparisons, or explicitly labeled context fallback; it is not typical-case sampling. No synthetic astronomical evidence or fabricated data appear.

The scientific conclusion is the saved conditional stability/coverage record, not a victory for a particle or gravity theory. Fragile results, unavailable comparisons and small or null perturbation effects remain legitimate outputs. No independent astrophysical novelty, discovery, publication readiness or theory probability is established.
'''
(DOC/'M3_FRAGILITY_ATLAS_RESULTS.md').write_text(atlas,encoding='utf-8')
prior_art='''# M3 prior art and novelty assessment

This targeted primary-source review supports a software/benchmark contribution, not a claim of a new physical effect or an exhaustive literature search.

- [Lelli, McGaugh & Schombert (2016)](https://arxiv.org/abs/1606.09251) supplied SPARC observations and derived mass components. GRAVITY ON TRIAL uses those products, not independently reduced telescope data. Rotation-curve mass discrepancies and a heterogeneous 175-galaxy test bed are prior work.
- [Li et al. (2018)](https://arxiv.org/html/1803.00022) explicitly studied stellar ML, distance and inclination nuisance freedom in individual RAR fits, including 0.1-dex stellar scatter. Our stellar/geometric sensitivity questions and ridge interpretation are not new. Our fixed-scenario velocity likelihood and separate coordinate-defined MAP widths differ from their acceleration-space/MCMC reporting; no identical posterior replication is claimed.
- [Li et al. (2020)](https://arxiv.org/abs/2001.10538) already compared halo profiles across SPARC with nuisance parameters and cosmological-prior considerations. Cored/cuspy comparisons, halo correlations and prior impacts are established subjects. This Atlas neither tests all dark-matter physics nor implements every MOND formulation.
- [Sosna (9 August 2026)](https://arxiv.org/html/2608.08945), abstract and relevant method/limitations review: an explicit SPARC identifiability audit benchmarks proposed RAR corrections against nuisance, mass and quality baselines, with pipeline sensitivity and predictive checks. This is substantial overlap with the need for adversarial degeneracy/quality controls. Its structural-regression hypotheses, selected samples and reported statistics are different; those empirical claims were not reproduced here.
- [Da Silva (5 October 2026)](https://arxiv.org/html/2610.05871), abstract/method-level review: full-SPARC model comparisons distinguish free NFW and concentration-mass constrained hypotheses while including nuisance freedom. This reinforces that a cosmological prior changes the question. Its individual fits use a simple interpolation function instead of our exponential empirical RAR, and its BIC proxy uses the data statistic at MAP. We do not equate those counts with ordinary MLE evidence or with our four-model, strictly separated MLE/MAP experiments, nor adopt its physical conclusions.
- [Smith et al. (23 October 2026)](https://arxiv.org/abs/2610.33157), abstract-level review retained from M2: geometry uncertainty and DM/MOND degeneracy, with a different 147-galaxy sample and additional lensing. It is not a like-for-like Atlas validation.
- [Gupta & Samaras (2026)](https://arxiv.org/abs/2608.11575), abstract-level M2 review: full-sample comparisons in an inverse formulation overlap benchmarking practice but use different predictions/objectives. No direct numerical ranking equivalence is asserted.

The publisher page for *Consequences of radially correlated rotation curves for galaxy mass models* and its identified author-repository route could not be read through the available web tool (publisher redirect failure; repository 403). We therefore do not claim a full-text review or rely on its specific quantitative findings. Unknown radial covariance remains an explicitly unmodeled observational limitation, not a newly established result here.

What is reproduced: established mass models/RAR, published derived SPARC inputs, nuisance-coordinate transformations and conventional likelihood/complexity calculations. What the Atlas adds as software: a bounded named scenario matrix, complete valid/invalid/null/unknown accounting, per-galaxy operational persistence and parameter/boundary diagnostics, classification-threshold audits, traceable arrays and exact fresh-process replay. These are useful engineering/instrumentation properties, not proven new statistical estimators.

No empirical finding has been established as genuinely distinct from prior results through independent external replication. The STABLE/SENSITIVE labels depend on their declared finite design and thresholds; scenario fractions are not posterior theory probabilities. Raw rotation curves alone cannot decide cosmology, new particles or all alternative gravitational theories. A new hypothesis, stronger covariance model or publication claim requires separate preregistered validation and rights/provenance review. No publication or external outreach occurred.
'''
(DOC/'M3_PRIOR_ART_AND_NOVELTY.md').write_text(prior_art,encoding='utf-8')
repro=f'''# M3 reproducibility

Scientific content revision `{source['content_revision']}`; source_snapshot/, environment.json and SHA-256 artifact manifest identify the exact code/configuration/data. No Git repository exists and no commit ID is invented. Deterministic seed 20261103 is recorded; scenarios/starts are fixed, not random draws. Source/raw/benchmark hashes remain unchanged.

20 pilot galaxies and all 175 full-campaign galaxies were rerun in separate controlled worker processes. All parameters, curves, accepted masks and numerical diagnostics pass frozen 1e-10 rtol/atol comparisons. Observed full-rerun parameter/speed maxima {V['max_parameter_rerun_difference']:.3g}/{V['max_prediction_rerun_difference_km_s']:.3g} km/s. Canonical comparison omits only timing/resource/stage/replicate metadata, never science values. All per-galaxy classifications are independently audited from scalar score gaps, original masks and explicit denominator arithmetic, not merely called twice through the same metric function.

92 test cases: original 54 plus 38 M3 cases, including fiducial MAP adapter regression, independent synthetic geometry recovery, signed gas, invalid/null proposals, normalized reference-frame likelihood and classification edges. Every accepted halo curve was independently density-integrated at all radii; {V['scalar_baryons_RAR_point_checks']} scalar force-point checks and {V['scalar_likelihood_checks']} scalar likelihood/prior/statistic checks passed. These controls validate numerical implementation, not astrophysical truth. Second-method optimization has only the declared bounded coverage, not all 175 cases.

Actual interrupted-batch resumes preserved complete records and checked source identity before reuse; {len(dispatch.get('cached_ids_without_recomputation',[]))} initial-sweep and {len(redispatch.get('cached_ids_without_recomputation',[]))} repeat-sweep IDs were reused after two preflight refusals. No completed numerical fit was overwritten or counted as a fresh rerun merely because a cache was read. Initial and rerun namespaces were independently computed. Progress *.partial.json files are snapshots, never extra experiments. Resource values explicitly distinguish serial-worker lifetime peak from isolated fit estimates.

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
'''
(DOC/'M3_REPRODUCIBILITY.md').write_text(repro,encoding='utf-8')
performance=f'''# M3 performance and safety

Single serial scientific child, single BLAS thread, CPU only. Unchanged native Windows preflight: five samples over two seconds, >=768 MiB available and range<=128 MiB; active sampling every 50 ms, >=512 MiB system floor and <=180 MiB child lifetime peak. No browser/dashboard, GPU framework, Docker/WSL, MCMC, unrelated process termination or paging changes.

Pilot workers {PILOT['worker_seconds']:.3f} seconds, {PILOT['peak_worker_MiB']:.3f} MiB peak. Projected full worker time {PILOT['projected_full_sweep_seconds']:.3f} seconds was below the frozen 900-second budget before full authorization. Actual initial full worker time {initial_seconds:.3f} seconds; independent sweep {repeat_seconds:.3f} seconds. Initial active dispatcher segments {dispatch['wall_seconds']:.3f} seconds; repeat {redispatch['wall_seconds']:.3f} seconds. Dispatcher timings include preflights/startup and interrupted active segments, but exclude manual investigation pauses. Total conversational/development duration is not inferred from these numbers.

Core peak {core_peak:.3f} MiB; overall monitored peak {peak:.3f} MiB; lowest observed execution headroom {floor:.3f} MiB. All launched recorded tasks respected safety limits. Two preflights refused launch because available RAM varied 135 and 249 MiB over their windows despite >1.5 GiB headroom. Logs retained; one later bounded window per interruption passed unchanged criteria. No unsafe child launched and no threshold was loosened. Stable preflight does not guarantee unsampled system minima; full monitoring histories are retained.

Atomic per-galaxy/scenario checkpoints and content-checked dispatcher reuse preserved progress. Runtime, current RSS and worker high-water marks are recorded at appropriate scopes; process_lifetime_peak_so_far is not falsely described as an isolated per-fit peak. Figures were rendered separately from fitting and measured independently. No M4/UI performance or unbounded campaign feasibility claim is made.
'''
(DOC/'M3_PERFORMANCE.md').write_text(performance,encoding='utf-8')
final=f'''# M3 final decision — 3 November 2026 (Asia/Kolkata)

## Verdict

**GO — the frozen bounded Model Fragility Atlas is validated within its declared scope. M4 remains unauthorized and unstarted.** All 18 M3 criteria have executed evidence in acceptance.json. A stable majority or universal physical model success is not an acceptance condition.

## Scientific evidence

175/175 original galaxies, 3,391/3,391 observations; Gate 0/M1/M2 source/data/results preserved. M2 baseline remains 107 preferred, 24 inconclusive, 44 unavailable, with 988 warning and 278 bound-contact evaluations. M3 planned/executed all 2,450 galaxy-scenario records and 9,800 model slots (12 physical plus 2 prior scenarios per galaxy). Actual calculations {V['actual_evaluated_model_slots']}, {actual_optimized} optimizer problems and {actual_fixed} fixed-model evaluations; statuses {model_status}. Null and rejected inputs remain visible, not counted as successful calculations.

Primary classes over 175: {primary_classes}; within the 107 decisive baselines: {decisive_classes}. Among those baselines, {retained}/{valid_total} valid physical comparisons retained the original winner, {flipped}/{valid_total} preferred a different model, and {to_inc}/{valid_total} became inconclusive. Invalid/unavailable/null outcomes are reported separately, including coverage and unconditional meaningful-scenario rates. These named-grid fractions are not posterior or calibrated probabilities.

New warnings {V['warning_evaluations']}/{V['actual_evaluated_model_slots']} actual calculations; bound contacts {V['boundary_evaluations']}/{V['actual_evaluated_model_slots']}, overlapping sets. All classifications have continuous metrics, raw counts, model/parameter diagnostics and preregistered alternative-threshold labels. Quality cuts change composition only. MAP prior-width effects and AIC/BIC criterion changes are separate from primary physical frequencies.

92 passing scientific tests; independent scalar rankings/classification/denominator audit for all 175; all-radius halo quadrature and independent baryonic/RAR force/likelihood checks. Complete fresh-process repeat for all 175/14 scenarios; observed parameter/prediction maxima {V['max_parameter_rerun_difference']:.3g}/{V['max_prediction_rerun_difference_km_s']:.3g}. Bounded dogbox check: 33 comparable objectives agree, three domain/search-limited cases noncomparable and retained. {figures['count']} scientific PNG/SVG figures and complete machine-readable inventories saved.

## Computational evidence

Initial workers {initial_seconds:.3f} seconds; full independent workers {repeat_seconds:.3f} seconds. Active dispatcher segments {dispatch['wall_seconds']:.3f}/{redispatch['wall_seconds']:.3f} seconds; manual pauses excluded. Core peak {core_peak:.3f} MiB, overall peak {peak:.3f} MiB, minimum monitored headroom {floor:.3f} MiB. Two launch refusals were honored; unchanged fresh preflights passed and checkpoints resumed. No floor/cap violation, parallel inference, GPU or unrelated process termination.

## Interpretation, failures and limitations

The result is a conditional robustness record: model preference, parameter stability and comparison availability depend on assumptions, priors, numerical domains, information and criterion choice. Genuine geometry underdetermination remains; priors select ridge locations without adding measurements. Strong correlation, bounds and limited observations remain visible. Ranges are stress-design spans, not credible/confidence intervals; joint/marginal named cases can overlap. Operational thresholds are normative and their sensitivity is reported. Unknown radial covariance/systematics are not modeled. Scenario weights are neither independent samples nor an exhaustive uncertainty distribution.

Domain-aborted searches do not prove a physical model cannot fit. No clipping or quiet radius removal was introduced to obtain a preferred narrative. Separate prior and statistical experiments are never ranked with incommensurable objectives. No unresolved fundamental numerical correctness failure was demonstrated. Targeted primary literature, including 2026 identifiability/model-comparison work, shows substantial prior art; no distinct astrophysical discovery or publication-level originality is established. One covariance-paper full text remained inaccessible and is disclosed. Raw redistribution rights remain unresolved; no publication, deployment or external outreach occurred.

## Artifacts and authorization

results/m3/v1/: fragility_classifications.csv; atlas_metrics.json; atlas_summary.json; scenario_inventory.csv; model_evaluations.csv; quality_composition.json; prior_sensitivity.json; statistical_sensitivity.json; independent_metric_audit.json; full_validation.json; acceptance.json; failures, controls, all full initial/rerun files, figures, logs, environment, source snapshot and manifest. All twelve required M3 reports are in docs/; experimental configuration is configs/m3_v1.json.

**M4 — FLAGSHIP SCIENTIFIC PLATFORM IS ELIGIBLE FOR AUTHORIZATION.** Do not automatically begin it.
'''
(DOC/'M3_GO_NO_GO.md').write_text(final,encoding='utf-8')
(DOC/'GATE_LEDGER.md').write_text('# Authorization ledger\n\n| Stage | State | Evidence |\n|---|---|---|\n| Gate 0 | GO; preserved | GATE0R_LOW_MEMORY_RECOVERY.md |\n| M1 | GO; preserved | M1_GO_NO_GO.md |\n| M2 | GO; preserved | M2_GO_NO_GO.md |\n| M3 | AUTHORIZED and GO | M3_GO_NO_GO.md; results/m3/v1/acceptance.json |\n| M4 | ELIGIBLE; NOT AUTHORIZED / NOT STARTED | Separate authorization required |\n',encoding='utf-8')
(ROOT/'README.md').write_text(f'''# GRAVITY ON TRIAL

**M3 GO: a bounded, reproducible Model Fragility Atlas. M4 remains unauthorized and unstarted.**

175 real SPARC galaxies / 3,391 original radii. Four model families, fixed physical stress cases and separately labeled nuisance-prior experiments; full invalid/null/failure and identifiability/boundary accounting. Frozen 14-scenario matrix, complete fresh-process replay, 92 passing scientific tests and independent all-galaxy metric checks. No observations silently removed, no posterior theory-probability interpretation, no astrophysical discovery claim.

Primary operational classes: {primary_classes}. Categories depend on frozen thresholds and a finite, partly overlapping scenario design. All continuous metrics/coverage and alternative-threshold labels remain available. Earlier Gate 0/M1/M2 results are unchanged.

Read docs/M3_GO_NO_GO.md and docs/M3_FRAGILITY_ATLAS_RESULTS.md. Method: docs/M3_EXPERIMENT_PROTOCOL.md; exact commands: docs/M3_REPRODUCIBILITY.md. Results/m3/v1/ contains the classification table, full scenario/model inventories, source/config hashes, per-galaxy initial/rerun arrays, static scientific figures, diagnostics and performance logs. The raw SPARC redistribution license is unresolved; data remain local/git-ignored. No dashboard, publication, hosting, MCMC or paid service was activated.
''',encoding='utf-8')
save('execution_inventory.json',{'primary_scenario_records':2450,'primary_planned_model_slots':9800,'primary_actual_calculations':V['actual_evaluated_model_slots'],'full_fresh_process_scenario_records':2450,'pilot_scenario_records_per_sweep':280,'pilot_sweeps':2,'dogbox_problem_count':36,'TRF_control_recomputations':36,'note':'Counts are repeated execution records, not extra independent galaxies. Null/invalid slots do not involve a scientific fit. Synthetic tests separately labeled.'})
snapshot=OUT/'source_snapshot';paths=set(source['files'])|{str(p.relative_to(ROOT)) for p in ROOT.glob('m3_*.py')}|{'recovery_monitor.py','tests/test_m1.py','pyproject.toml'}
for name in paths:
    if name.replace('\\','/').startswith(('data/','results/')):continue
    target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='artifacts_manifest.json']+list(DOC.glob('M3_*.md'))+[ROOT/'configs/m3_v1.json',ROOT/'README.md',DOC/'GATE_LEDGER.md'];save('artifacts_manifest.json',{str(p.relative_to(ROOT)):sha(p) for p in files})
print(json.dumps({'verdict':'GO','galaxies':175,'scenario_records':2450,'planned_model_slots':9800,'actual_calculations':V['actual_evaluated_model_slots'],'classes':primary_classes,'retained':retained,'flipped':flipped,'to_inconclusive':to_inc,'valid_decisive_baseline_scenarios':valid_total,'worker_seconds':initial_seconds,'repeat_worker_seconds':repeat_seconds,'core_peak_MiB':core_peak,'overall_peak_MiB':peak,'min_available_MiB':floor,'manifest_files':len(files)}))
