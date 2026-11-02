"""Freeze M2 methodology and pilot selection before any M2 fit."""
import collections,hashlib,json,math,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m2/v1';OUT.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['results/gate0r/artifacts_manifest.json','results/m1/v1/artifacts_manifest.json']:
    assert all(sha(ROOT/p)==h for p,h in json.loads((ROOT/name).read_text()).items()),name
source=json.loads((ROOT/'results/gate0/parsed_tables.json').read_text());cat=source['catalog'];mass=source['mass_models'];groups={c['ID']:[] for c in cat}
for row in mass:groups[row['ID']].append(row)
assert len(cat)==175 and len(mass)==3391
features=[]
for c in cat:
    rows=groups[c['ID']];features.append({**c,'n':len(rows),'radius_min_kpc':min(r['R'] for r in rows),'radius_max_kpc':max(r['R'] for r in rows),'negative_gas_rows':sum(r['Vgas']<0 for r in rows),'nonpositive_bar_rows':[i for i,r in enumerate(rows) if .5*r['Vdisk']**2+.7*r['Vbul']**2+r['Vgas']*abs(r['Vgas'])<=0],'bulge_max_squared':max(r['Vbul']**2 for r in rows),'gas_to_light_proxy':c['MHI']/c['L36']})
pilot=[];rationale={}
def add(c,reason):
    g=c['ID']
    if g not in pilot:pilot.append(g)
    rationale.setdefault(g,[]).append(reason)
by={c['ID']:c for c in features}
for g in ['NGC3198','NGC2403','NGC3741','DDO154','NGC2841','UGC00731','NGC4157','F567-2']:add(by[g],'Retained M1 implementation-validation case')
for field in ['SBdisk','gas_to_light_proxy','n','radius_max_kpc','Inc','bulge_max_squared']:
    add(min(features,key=lambda c:(c[field],c['ID'])),'Minimum catalog '+field)
    add(max(features,key=lambda c:(c[field],c['ID'])),'Maximum catalog '+field)
for q in [1,2,3]:
    add(min([c for c in features if c['Q']==q],key=lambda c:c['ID']),f'Lexicographic first Q={q}')
add(max(features,key=lambda c:(c['negative_gas_rows'],c['ID'])),'Most negative gas rows')
for c in sorted(features,key=lambda c:c['ID']):
    if c['nonpositive_bar_rows']:add(c,'Fixed-baryon nonpositive domain edge case')
# Keep 20 while ensuring late domain cases cannot be dropped by truncation.
mandatory=[g for g in pilot if by[g]['nonpositive_bar_rows']]
pilot=pilot[:20]
for g in mandatory:
    if g not in pilot:pilot[-1 if pilot[-1] not in mandatory else -2]=g
for c in sorted(features,key=lambda c:c['ID']):
    if len(pilot)==20:break
    if c['ID'] not in pilot:pilot.append(c['ID']);rationale[c['ID']]=['Deterministic lexicographic fill to 20']
assert len(pilot)==20 and len(set(pilot))==20
config={'version':'m2-v1','run_id':'sparc175_m2_v1','authorization':'M2 only; full campaign requires saved pilot GO','population_ids':sorted(groups),'pilot_ids':pilot,'pilot_selection':[{'ID':g,'reasons':rationale[g],'metadata':by[g]} for g in pilot],'models':['baryons','nfw','burkert','rar'],'modes':['MLE','MAP'],'base_config_file':'configs/m1_v1.json','halo_config_file':'configs/gate0r.json','seed':20261102,'high_quality_rule':'Q<=2 and catalog inclination>=30 degrees','all_inventory_denominator':175,'radial_inventory_denominator':3391,'comparison_statistic':'F0 AICc, same complete mask; delta runner-up >=2 gives operational preference; otherwise INCONCLUSIVE','four_way_eligibility':'All 4 CONVERGED, identical masks and n; all AICc defined; no boundary; each data rank=k and finite condition<=1e8 when k>0. Correlation warnings retained as cautions; not automatically rank deficiency.','pairwise_eligibility':'Same rules applied only to NFW and Burkert, reported separately from 4-way','MAP_comparison':'No AIC/BIC or posterior-evidence winners. Describe matched-data residual changes at MAP only.','weak_identifiability_rule':'Any legacy identifiability warning; report separate rank/condition/boundary/small-n/high-correlation labels. Normalize Jacobian columns for audit; condition>1e6 adds dimensionless weak-direction warning.','diagnostic_coordinate_audit':'Data Jacobian at h factors 1e-4,1e-5,1e-6 in mixed optimization coordinates; normalize columns to unit norm; compare conditions and exact geometry ridge. Finite differences do not certify exact rank.','invalid_domain_policy':'F0 invalid radii remain visible and invalidate full-mask comparison, never remove them per model silently. Separate F0 common positive-bar subset sensitivity for affected galaxies, original indices saved. Failed MAP start != proof of no physical solution.','failure_statuses':['CONVERGED','UNSUPPORTED_DOMAIN','NO_VALID_START','OPTIMIZER_FAILED','DIAGNOSTIC_FAILURE','INVALID_DATA'],'accepted_points':'All catalog radii for main benchmark; immutable index masks.','batch_size':5,'preflight_minimum_MiB':768,'execution_floor_MiB':512,'child_peak_cap_MiB':180,'target_core_MiB':350,'execution':'Serial CPU, single BLAS thread; atomic per-galaxy records; guarded resume by content identity.','identity_rtol':1e-9,'reproducibility_rtol':1e-10,'reproducibility_atol':1e-10,'rerun_plan':'Pilot 20 fresh-process reruns; after pilot estimate, full 175 rerun if estimated total per sweep <=600 seconds and safety passes; else deterministic 35 evenly spaced sorted-catalog IDs frozen below.','fallback_rerun_ids':[sorted(groups)[round(i*174/34)] for i in range(35)],'predictive_ids':pilot[:5],'predictive_rule':'F0 only; n>=10 and all fixed bar>0; train inner floor(0.7n) radii and evaluate remaining outer radii. All four on same train/test masks. Extrapolation and neighboring-radius correlation caveat.','selection_exploration':'Population property associations descriptive Spearman coefficients only, no p-values/discovery claims or multiple-testing significance.','protocol_change_policy':'Freeze this JSON before fits; any changed method requires a separately named experiment/version, not overwriting this run.'}
path=ROOT/'configs/m2_v1.json'
if path.exists():assert json.loads(path.read_text())==config,'Refusing changed frozen config'
else:path.write_text(json.dumps(config,indent=2))
(OUT/'inventory.json').write_text(json.dumps({'galaxies':features,'counts':{'galaxies':len(cat),'radii':len(mass),'negative_gas':sum(r['Vgas']<0 for r in mass),'quality':dict(collections.Counter(str(c['Q']) for c in cat))}},indent=2))
files=[p for p in (ROOT/'src').rglob('*.py')]+list((ROOT/'configs').glob('*.json'))+[ROOT/'docs/M1_GO_NO_GO.md',ROOT/'docs/M1_SCIENTIFIC_METHOD.md']
(OUT/'baseline_freeze.json').write_text(json.dumps({str(p.relative_to(ROOT)):sha(p) for p in files},indent=2))
for name in ['README.md','docs/GATE_LEDGER.md']:
    dest=OUT/('previous_'+Path(name).name)
    if not dest.exists():shutil.copyfile(ROOT/name,dest)
protocol='''# M2 frozen benchmark protocol

Run sparc175_m2_v1, configuration configs/m2_v1.json; exact SHA-256 checked before execution. This is M2 only. All existing Gate 0/M1 artifacts remain unchanged. M1 physics, halo bounds, four declared starts, three nuisance-only starts, tolerances, stellar priors, catalog error likelihood, log-coordinate MAP density and geometry conventions are inherited without changes; their full definitions and units are in M1_SCIENTIFIC_METHOD.md and baseline_freeze.json. No prior objective is used for ML information criteria.

Main inventory: all 175 IDs, 3391 radii, signed gas unchanged. Main F0/F1 use every original point; models that cannot evaluate a full mask retain explicit failure/domain records. No per-model hidden clipping. Fixed negative/nonpositive bar cases get a separately labeled common-positive-bar F0 experiment with all models refit to the identical subset and original indices recorded. This never substitutes for the full inventory record. All successes and failures retain n_inventory and attempted/accepted/excluded masks, source identity, units, bounds, priors, optimizer starts, diagnostics, time and memory.

Primary comparison: F0 AICc, all four converged on exactly the same mask, n>k+1, no boundary, data Jacobian rank=k and condition<=1e8. A high-correlation warning alone is not rank deficiency; retain it visibly. If eligible, runner-up gap >=2 gives an operational preference; gap<2 is INCONCLUSIVE. If ineligible, NO_VALID_COMPARISON and no winner. NFW/Burkert pairwise comparisons are separately counted. No posterior-theory probabilities. F1 MAP has no AIC/AICc/BIC, no posterior-evidence ranking; report nuisance shifts/data residual changes separately.

Report full inventory, Q<=2 & i>=30 prespecified higher-quality sample, and eligible/successful subsets with explicit denominators. Population median/distribution summaries disclose their valid count and missing count; no successful-only statement implies whole-sample performance. Warning classes distinguish high correlation, numerical rank/conditioning, boundary, n<=k, and unsupported domains. Exploratory property associations use Spearman coefficient with valid pair count, no p-values or causal claims.

Pilot: 20 deterministic metadata-selected IDs below, chosen before M2 fits; complete all 8 model/config evaluations and fresh-process reruns. GO requires immutable data, valid status/mask/statistics handling, independent controls, consistent warnings, no unresolved correctness bug and measured safe resources. Poor fits are not failures of software acceptance. Full campaign may begin only with saved pilot GO. Batches of five serial galaxies, one controlled child; monitored preflight and 512 MiB floor/180 MiB cap remain unchanged. Checkpoint every galaxy atomically, content identity guards reuse. Sampling safety is measured, not a continuous guarantee.

Fresh-process plan: all 20 pilot cases rerun, then full 175 rerun if measured estimate for a sweep <=600 seconds; otherwise use the 35 frozen evenly spaced IDs. Identity requires canonical parameters, masks and diagnostic arrays equal within 1e-10 rtol/atol; timing/memory fields excluded. Independent halo quadrature, signed gas, synthetic negative controls and statistical edge tests are mandatory. No full-rerun claim based on subset.

Predictive pilot: first five frozen pilot IDs with n>=10 and positive bar throughout, F0 inner 70% training and outer 30% test, same masks for every model. This is radial extrapolation with correlated neighboring measurements, not independent random test data. No global parameter calibration. This bounded pilot is not M3.

Scientific visualizations are standalone PNG/SVG alongside these Markdown reports, from saved numerical arrays, with source, sample, units/configuration and caveats. Data and code are local; no publication, external contact, new hypothesis or paid service.

## Pilot identities and selection

'''
protocol+='\n'.join('- '+g+': '+ '; '.join(rationale[g]) for g in pilot)
(ROOT/'docs/M2_BENCHMARK_PROTOCOL.md').write_text(protocol,encoding='utf-8')
print(json.dumps({'pilot':pilot,'high_quality_count':sum(c['Q']<=2 and c['Inc']>=30 for c in features),'domain_cases':[c['ID'] for c in features if c['nonpositive_bar_rows']]}))
