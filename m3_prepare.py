"""Freeze M3 scenarios, eligibility and classification before new fits."""
import collections,csv,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m3/v1';OUT.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(ROOT/'results/m2/v1/artifacts_manifest.json');assert all(sha(ROOT/p)==h for p,h in manifest.items())
for r in read(ROOT/'data/manifests/acquisition.json'):assert sha(ROOT/'data/raw'/r['url'].rsplit('/',1)[1])==r['sha256']
features={c['ID']:c for c in read(ROOT/'results/m2/v1/inventory.json')['galaxies']};comparisons={c['galaxy']:c for c in read(ROOT/'results/m2/v1/comparison_records.json')}
counts=collections.Counter(c['four_way']['status'] for c in comparisons.values());assert counts=={'PREFERENCE':107,'INCONCLUSIVE':24,'NO_VALID_COMPARISON':44}
rows=list(csv.DictReader((ROOT/'results/m2/v1/evaluation_inventory.csv').open()));assert sum(r['identifiability_warning']=='True' for r in rows)==988 and sum(r['boundary_contact']=='True' for r in rows)==278
selected=[];reasons={}
def add(g,why):
    if g not in selected:selected.append(g)
    reasons.setdefault(g,[]).append(why)
for g in ['NGC3198','NGC2403','NGC3741','DDO154','NGC2841','UGC01281']:add(g,'Retained real validation / signed-force edge case')
for status in ['PREFERENCE','INCONCLUSIVE','NO_VALID_COMPARISON']:add(min(g for g,c in comparisons.items() if c['four_way']['status']==status),'Lexicographic first baseline '+status)
for q in [1,2,3]:add(min(g for g,c in features.items() if c['Q']==q),f'Lexicographic first Q={q}')
for field,extreme in [('gas_to_light_proxy',max),('gas_to_light_proxy',min),('negative_gas_rows',max),('bulge_max_squared',max),('n',min),('n',max)]:
    g=extreme(features,key=lambda g:(features[g][field],g));add(g,extreme.__name__+' catalog '+field)
add(max(features,key=lambda g:(features[g]['e_D']/features[g]['D'],g)),'Largest fractional distance uncertainty')
add(max(features,key=lambda g:(features[g]['e_Inc'],g)),'Largest inclination uncertainty')
boundary=collections.Counter(r['galaxy'] for r in rows if r['boundary_contact']=='True');add(max(boundary,key=lambda g:(boundary[g],g)),'Most M2 boundary contacts')
strong=sorted({r['galaxy'] for r in rows if r['mode']=='MLE' and r['model']=='nfw' and r['status']=='CONVERGED' and r['identifiability_warning']=='False'})
add(strong[0],'Fixed NFW fit without an identifiability warning')
if len(selected)>20:raise RuntimeError('Selection exceeds frozen 20-case budget; resolve before any M3 fit')
for g in sorted(features):
    if len(selected)==20:break
    if g not in selected:add(g,'Deterministic lexicographic fill')
assert len(selected)==20 and {comparisons[g]['four_way']['status'] for g in selected}==set(counts) and {features[g]['Q'] for g in selected}=={1,2,3}
scenarios=[]
for component in ['disk','bulge','joint']:
    for sign in [-1,1]:scenarios.append({'id':f'ML_{component}_{"minus" if sign<0 else "plus"}01dex','family':'F1_ML','kind':'physical','disk_dex':sign*.1 if component in ['disk','joint'] else 0,'bulge_dex':sign*.1 if component in ['bulge','joint'] else 0,'distance_sigma':0,'inclination_sigma':0})
for component in ['distance','inclination','joint_geometry']:
    for sign in [-1,1]:scenarios.append({'id':f'{component}_{"minus" if sign<0 else "plus"}1sigma','family':'F2_geometry','kind':'physical','disk_dex':0,'bulge_dex':0,'distance_sigma':sign if component in ['distance','joint_geometry'] else 0,'inclination_sigma':sign if component in ['inclination','joint_geometry'] else 0})
for width in [.05,.2]:scenarios.append({'id':f'MAP_ML_prior_{str(width).replace(".","p")}dex','family':'F4_prior','kind':'prior','ML_prior_sigma_dex':width})
cfg={'version':'m3-v1','run_id':'sparc175_fragility_m3_v1','authorization':'M3 only; M4 unauthorized','population_ids':sorted(features),'pilot_ids':selected,'pilot_selection':[{'ID':g,'reasons':reasons[g],'baseline_status':comparisons[g]['four_way']['status'],'metadata':features[g]} for g in selected],'models':['baryons','nfw','burkert','rar'],'scenarios':scenarios,'physical_scenario_count':12,'prior_scenario_count':2,'planned_galaxy_scenario_records_full':2450,'planned_model_slots_full':9800,'seed':20261103,'baseline':'Frozen M2-v1 F0 AICc comparison; M2 F1 used only for nuisance/prior diagnostics','comparison_policy':'Same M2 regular interior, rank and full original mask eligibility. AICc runner-up gap>=2 preferred; otherwise inconclusive. Never rank MAP objectives.','statistical_alternatives':['AIC','BIC'],'statistical_alternative_policy':'Same common eligibility as AICc; same gap>=2 operational threshold; separate from physical-scenario frequencies.','null_scenarios':'A changed stellar component identically zero, or geometry uncertainty exactly zero for all changed coordinates, is NOT_APPLICABLE. Keep slots/records; exclude nulls from meaningful-scenario denominator.','invalid_proposals':'Reject Dnew<=0 or i_new outside (0,90]; no clipping or replacement. Count separately.','geometry':'Independent catalog error shifts; +/-sigma are deterministic stress cases, not random draws. Joint diagonal shifts assert no empirical covariance. Catalog-frame velocities/errors remain unchanged in reported likelihood.','classification':{'minimum_valid':6,'minimum_coverage':.6,'stable_persistence':.8,'maximum_stable_flip_fraction':.1,'inconclusive_fraction':.5,'baseline_unavailable':'UNASSESSABLE','baseline_inconclusive':'INCONCLUSIVE','decisive_rules':'If valid<minimum or valid/(planned-null)<coverage: UNASSESSABLE. Else if inconclusive/valid>=0.5: INCONCLUSIVE. Else if retained/valid>=0.8 and flipped/valid<=0.1: STABLE. Else SENSITIVE.'},'classification_alternatives':[{'id':'lenient','minimum_valid':5,'minimum_coverage':.5,'stable_persistence':.7,'maximum_stable_flip_fraction':.2,'inconclusive_fraction':.5},{'id':'strict','minimum_valid':7,'minimum_coverage':.7,'stable_persistence':.9,'maximum_stable_flip_fraction':.05,'inconclusive_fraction':.5}],'metric_denominators':'Valid comparable means preferred or inconclusive, never unavailable/invalid. Retained + flipped + to-inconclusive = valid for decisive baseline. Also report every outcome / (12-null) and planned 12; rejected/unavailable scenarios never support persistence.','prior_policy':'ML normal priors in log10 coordinates, widths 0.05/0.2 dex around same 0.5/0.7 centers; same geometry priors and all bounds as M2. Same deterministic starting points as M2. No concentration-mass/cosmological prior added.','prior_justification':'Half/double the 0.1 dex literature-motivated fiducial scatter are prior-strength sensitivity cases, not independently measured distributions or exhaustive astrophysical uncertainty.','optimizer_crosscheck_ids':selected[:6],'optimizer_crosscheck_scenarios':['baseline','ML_joint_plus01dex','distance_plus1sigma'],'optimizer_crosscheck_method':'SciPy dogbox least_squares, two frozen starts [first and third M2 halo starts], same physical bounds','optimizer_objective_relative_tolerance':1e-6,'near_equivalent_objective_delta':1.,'material_parameter_range_dex':.1,'sample_definitions':['all175','Q_le2','Q_eq1','incl_ge30','Q_le2_and_incl_ge30'],'batch_size':5,'preflight_MiB':768,'system_floor_MiB':512,'child_cap_MiB':180,'full_sweep_projected_budget_seconds':900,'full_rerun_policy':'Attempt all 175 full scenarios in fresh processes if pilot estimate<=900 seconds per sweep and safety passes. Otherwise stop at pilot with measured partial scope; do not silently reduce scenarios.','reproducibility_rtol':1e-10,'reproducibility_atol':1e-10,'independent_identity_rtol':1e-9,'synthetic_parameter_recovery_atol_dex':1e-5,'likelihood_frame_log_normalization_atol':1e-8,'plot_selection':'Prespecified original five plus UGC01281; additionally first sorted STABLE/SENSITIVE/INCONCLUSIVE/UNASSESSABLE case. Before/after uses largest absolute prediction deviation among valid physical scenarios; rule frozen, not typical-case evidence.','no_probability_interpretation':True}
path=ROOT/'configs/m3_v1.json'
if path.exists():assert read(path)==cfg,'Refusing changed frozen M3 protocol'
else:path.write_text(json.dumps(cfg,indent=2))
(OUT/'baseline_verification.json').write_text(json.dumps({'M2_manifest_files_verified':len(manifest),'M2_baseline_counts':dict(counts),'M2_warning_evaluations':988,'M2_boundary_evaluations':278,'M2_source_identity':read(ROOT/'results/m2/v1/acceptance.json')['source_content_revision'],'config_sha256':sha(path)},indent=2))
for name in ['README.md','docs/GATE_LEDGER.md']:
    dest=OUT/('previous_'+Path(name).name)
    if not dest.exists():shutil.copyfile(ROOT/name,dest)
protocol='''# M3 frozen experiment protocol

Run sparc175_fragility_m3_v1. M3 only; M4 forbidden. Exact scenarios, pilot IDs, thresholds, units, masks, budgets and reproduction tolerances are frozen in configs/m3_v1.json before fitting. M2's 107 preferred / 24 inconclusive / 44 unavailable states, all 988 warnings and 278 boundary contacts are preserved, not reinterpreted as theory probabilities.

## Scenario matrix and scientific boundaries

Twelve physical cases per original galaxy: disk-only, bulge-only and joint stellar ML shifts +/-0.1 dex around 0.5/0.7; D +/-eD; inclination +/-eI; joint geometry +/-eD and +/-eI. All four models use the same original radii/observations and catalog-frame velocity likelihood. Only explicitly changed fixed quantities change; halo parameters are refit using unchanged bounds/four M2 starts. RAR a0 stays universal 1.2e-10 SI. Signed gas preserved. No radial cuts. Zero-sensitivity scenarios are NOT_APPLICABLE, not artificial persistence support. D<=0 or invalid inclination proposals are rejected, counted and never clipped.

The +/-sigma shifts are deterministic stress cases, not draws from a posterior or an empirical covariance. Joint diagonal cases assume no measured covariance and do not exhaust uncertainty. A computation view may rescale component arrays/radii and correct both observations/errors, but saved predictions/log-likelihood are returned to the immutable catalog frame and independently checked. No source file or observation is changed.

Two separate MAP cases vary the log10 stellar ML prior width to 0.05 and 0.2 dex, around unchanged fiducials. Geometry priors, positive bounds and deterministic M2 starting points remain identical. This tests prior strength relative to the 0.1 dex fiducial, not a new measured stellar population. No cosmological halo prior or concentration-mass hypothesis is introduced. MAP prior objectives have no AIC/BIC ranking and never enter primary physical persistence fractions.

Quality cuts all175, Q<=2, Q=1, i>=30 and Q<=2&i>=30 change population composition only. They never change individual observed masks or count as individual preference flips. No unplanned radial uncertainty filtering. AIC and BIC are evaluated separately on the same MLE/common eligible masks as AICc; no mixing of incomparable objectives.

## Primary operational metrics and categories

Baseline decisive galaxies: retained, different decisive preference, inconclusive, unavailable, failed/domain, invalid physical proposal and not-applicable outcomes all recorded. Valid comparable scenarios include decisive or inconclusive; unavailable outcomes never support the original preference. Retained+flipped+inconclusive=valid. Persistence=retained/valid and flip frequency=flipped/valid; report the numerator/denominator and also all outcomes over 12 planned slots and 12-minus-null meaningful slots. Neither fraction is a posterior probability or calibrated sampling probability.

Baseline unavailable -> UNASSESSABLE. Baseline inconclusive -> INCONCLUSIVE; no baseline winner or flip probability invented. Baseline decisive: valid>=6 and valid/(12-null)>=0.6 required, otherwise UNASSESSABLE. Then inconclusive/valid>=0.5 -> INCONCLUSIVE; otherwise persistence>=0.8 and flip fraction<=0.1 -> STABLE; else SENSITIVE. Continuous counts/fractions always accompany labels. Frozen lenient/strict alternative thresholds in the JSON quantify classification-definition sensitivity without changing the primary rule.

Parameter ranges/medians use optimization log coordinates and physical units; scenario ranges are not confidence intervals. Boundary and identifiability frequencies show successful and unknown/failure counts with explicit denominators. Data-only and prior-inclusive curvature remain distinct. Multistart objective ranges and parameter ranges among solutions within delta objective<=1 are saved; >0.1 dex is a descriptive material-variation flag, not a proof of multimodality. Bounded dogbox cross-check: six frozen galaxies, baseline/joint-ML-plus/distance-plus, two declared starts and unchanged bounds; objective agreement target relative 1e-6. Distinct minima are reported rather than hidden.

## Pilot, scaling, resources and reproducibility

20 deterministic galaxies below span all three M2 outcome categories, quality levels, correlation/boundary behavior, gas/stellar/bulge components, negative gas and geometry uncertainty. No M3 sensitivity outcome was used in selection. Pilot must pass physical transforms, normalized likelihood, prior separation, failure bookkeeping, independent predictions, classification tests and fresh-process rerun. Poor fits, fragile preferences and valid rejected proposals do not fail the gate.

14 scenario records and 56 planned model slots per galaxy: 2,450 full galaxy-scenario records / 9,800 model slots, including explicit null/invalid slots. No combinatorial expansion. Pilot runtime projects full sweeps; if >900 seconds, stop with partial results rather than silently shrink scope. Otherwise attempt full campaign and full independent rerun, serial batches of five, unchanged 768 MiB stable preflight / 512 MiB floor / 180 MiB child cap. Checkpoint per galaxy, guard exact content identity, one BLAS thread, no GPU/MCMC/browser/dashboard. Numerical rerun tolerances 1e-10 rtol/atol; identities/quadrature 1e-9; synthetic recovery 1e-5 dex. No tuning thresholds after full results.

## Frozen pilot selection

'''
protocol+='\n'.join('- '+g+': '+ '; '.join(reasons[g]) for g in selected)
(ROOT/'docs/M3_EXPERIMENT_PROTOCOL.md').write_text(protocol,encoding='utf-8')
print(json.dumps({'pilot_ids':selected,'scenarios':len(scenarios),'full_model_slots':9800,'M2_files_preserved':len(manifest)}))
