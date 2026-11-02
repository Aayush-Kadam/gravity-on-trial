"""Frozen serial M3 execution: diagnostics, physical scenarios, MAP priors and controls."""
import collections,hashlib,json,math,sys,time,traceback
from pathlib import Path
import psutil
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m3/v1';sys.path.insert(0,str(ROOT/'src'))
PROC=psutil.Process();BEGUN=time.perf_counter();BASE=PROC.memory_info().rss/2**20
import numpy as np
from scipy.optimize import least_squares
from m1_worker import load
from m2_worker import independent_halo,scaled_sensitivity,ridge
from gravity_on_trial.m1_physics import DomainError
from gravity_on_trial.m1_inference import diagnostics
from m3_science import scenario_spec,computation_view,fit_fixed,fit_prior_width,independent_control_record
from m3_metrics import compare_score
CFG=json.loads((ROOT/'configs/m3_v1.json').read_text());M1=json.loads((ROOT/'configs/m1_v1.json').read_text());GATE=json.loads((ROOT/'configs/gate0r.json').read_text())
SCENARIOS={s['id']:s for s in CFG['scenarios']}
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2,allow_nan=False));tmp.replace(path)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity():
    files=[ROOT/f for f in ['m3_worker.py','m3_science.py','m3_metrics.py','m2_worker.py','m2_compare.py','m1_worker.py','configs/m3_v1.json','configs/m2_v1.json','configs/m1_v1.json','configs/gate0r.json','results/m2/v1/artifacts_manifest.json','results/m2/v1/comparison_records.json','data/raw/SPARC_Lelli2016c.mrt','data/raw/MassModels_Lelli2016c.mrt','data/raw/Rotmod_LTG.zip']]+sorted((ROOT/'src/gravity_on_trial').glob('*.py'))
    hashes={str(p.relative_to(ROOT)):sha(p) for p in files};return {'files':hashes,'content_revision':hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest(),'run_id':CFG['run_id'],'seed':CFG['seed']}

def identifiability_audit():
    labels=collections.Counter();warnings=boundaries=0;gal_warnings=collections.Counter();gal_bounds=collections.Counter();records=[]
    for galaxy in CFG['population_ids']:
        data=json.loads((ROOT/f'results/m2/v1/full/initial/{galaxy}.json').read_text());curve=load(galaxy)
        for r in data['results']:
            if r['status']!='CONVERGED':continue
            warns=r['data_identifiability']['warnings'];labels.update(warns);warnings+=bool(warns);boundaries+=any(r['boundary_flags']);gal_warnings[galaxy]+=bool(warns);gal_bounds[galaxy]+=any(r['boundary_flags'])
            near=[a for a in r['attempts'] if a['success'] and a['objective']-min((b['objective'] for b in r['attempts'] if b['success']),default=0)<=1]
            ranges=[max(a['x'][j] for a in near)-min(a['x'][j] for a in near) for j in range(len(r['parameters']))] if near else []
            geometry=ridge(curve,r) if r['mode']=='MAP' else None
            records.append({'galaxy':galaxy,'model':r['model'],'mode':r['mode'],'n':len(curve.r),'k':len(r['parameters']),'warnings':warns,'boundary_parameters':[n for n,b in zip(r['parameter_names'],r['boundary_flags']) if b],'data_rank':r['data_identifiability']['rank'],'data_condition':r['data_identifiability']['condition'],'normalized_condition':r['scaled_sensitivity']['normalized_condition'],'geometry_ridge':geometry,'near_minimum_objective_delta':1.,'near_minimum_parameter_ranges':dict(zip(r['parameter_names'],ranges)),'near_minimum_material_halo_variation':any(v>.1 for n,v in zip(r['parameter_names'],ranges) if n in GATE.get(r['model']+'_parameter_order',[])),'failed_start_count':sum(not a['success'] for a in r['attempts']),'radial_coverage_kpc':[float(min(curve.r)),float(max(curve.r))],'Q':curve.metadata['Q'],'Inc':curve.metadata['Inc']})
    assert warnings==988 and boundaries==278
    save(OUT/'identifiability_audit.json',{'warning_evaluations':warnings,'boundary_evaluations':boundaries,'evaluation_inventory_denominator':1400,'galaxies_with_any_warning':sum(n>0 for n in gal_warnings.values()),'galaxies_with_any_boundary':sum(n>0 for n in gal_bounds.values()),'galaxy_denominator':175,'warning_labels_overlapping':dict(labels),'warning_counts_by_galaxy':dict(gal_warnings),'boundary_counts_by_galaxy':dict(gal_bounds),'records':records,'identity':identity()})
    return {'warnings':warnings,'boundaries':boundaries}

def one_scenario(curve,scenario):
    start=time.perf_counter();spec=scenario_spec(curve,scenario)
    record={'scenario_id':scenario['id'],'family':scenario['family'],'kind':scenario['kind'],'spec':spec,'proposal_status':spec.get('proposal_status','APPLICABLE'),'results':[],'original_mask':list(range(len(curve.r)))}
    if record['proposal_status']!='APPLICABLE':
        record['results']=[{'model':m,'mode':'MLE','status':record['proposal_status'],'n_inventory':len(curve.r),'attempted_mask':list(range(len(curve.r))),'accepted_mask':[],'reason':spec['reason']} for m in CFG['models']]
        record['comparison']={'status':record['proposal_status'],'winner':None,'reasons':[spec['reason']]}
    else:
        for model in CFG['models']:
            t=time.perf_counter()
            try:
                result=fit_fixed(curve,model,spec,M1,GATE) if scenario['kind']=='physical' else fit_prior_width(curve,model,scenario['ML_prior_sigma_dex'],M1,GATE)
                if result['status']=='CONVERGED':
                    view,_=computation_view(curve,spec) if scenario['kind']=='physical' else (curve,1)
                    result['scaled_sensitivity']=scaled_sensitivity(view,result)
                    result['independent_halo_check']=independent_halo(curve,independent_control_record(result,spec))
            except (DomainError,ValueError,np.linalg.LinAlgError) as error:
                result={'status':'DIAGNOSTIC_FAILURE','model':model,'mode':'MLE' if scenario['kind']=='physical' else 'MAP','message':str(error),'traceback':traceback.format_exc(),'attempted_mask':list(range(len(curve.r))),'accepted_mask':[]}
            result['resource']={'wall_seconds_including_controls':time.perf_counter()-t,'RSS_after_MiB':PROC.memory_info().rss/2**20,'process_lifetime_peak_so_far_MiB':PROC.memory_info().peak_wset/2**20}
            record['results'].append(result)
        if scenario['kind']=='physical':
            record['comparison']=compare_score(record['results']);record['statistical_alternatives']={s:compare_score(record['results'],s) for s in CFG['statistical_alternatives']}
        else:record['comparison']={'status':'NOT_A_LIKELIHOOD_COMPARISON','winner':None,'reasons':['MAP prior-width experiment; AIC/BIC forbidden']}
    record['failure_reasons']=[{'model':r['model'],'status':r['status'],'invalid_indices':r.get('invalid_indices',[]),'failed_starts':sum(not a['success'] for a in r.get('attempts',[]))} for r in record['results'] if r['status']!='CONVERGED']
    record['wall_seconds']=time.perf_counter()-start;return record

def validate_data(data):
    assert len(data['scenarios'])==14 and {s['scenario_id'] for s in data['scenarios']}==set(SCENARIOS)
    for scenario in data['scenarios']:
        assert len(scenario['results'])==4
        for r in scenario['results']:
            if r['status']=='DIAGNOSTIC_FAILURE':raise RuntimeError('Unresolved diagnostic failure '+r['message'])
            if r['status']=='CONVERGED':
                assert r['accepted_mask']==list(range(data['n_inventory']))
                assert all(math.isfinite(p) and p>=0 for p in r['prediction_km_s'])
                s=r['statistics'];assert s['k']==len(r['parameters'])
                assert (s['reduced_chi_squared'] is None)==(s['n']<=s['k'])
                if r['mode']=='MAP':assert all(s[k] is None for k in ['AIC','AICc','BIC'])
                z=[(p-o)/e for p,o,e in zip(r['prediction_km_s'],data['observed_km_s'],data['error_km_s'])]
                assert math.isclose(math.fsum(v*v for v in z),s['chi_squared'],rel_tol=1e-10,abs_tol=1e-8)

def batch(stage,replicate,ids):
    if stage=='full':assert json.loads((OUT/'pilot_gate.json').read_text())['GO']
    ident=identity();complete=[]
    baseline_comp={c['galaxy']:c for c in json.loads((ROOT/'results/m2/v1/comparison_records.json').read_text())}
    for galaxy in ids:
        path=OUT/stage/replicate/(galaxy+'.json')
        if path.exists():
            old=json.loads(path.read_text());assert old['identity']==ident,'Resume identity mismatch';validate_data(old);complete.append(galaxy);continue
        curve=load(galaxy);baseline=json.loads((ROOT/f'results/m2/v1/full/initial/{galaxy}.json').read_text())
        data={'galaxy':galaxy,'stage':stage,'replicate':replicate,'identity':ident,'metadata':curve.metadata,'n_inventory':len(curve.r),'radius_catalog_kpc':curve.r.tolist(),'observed_km_s':curve.obs.tolist(),'error_km_s':curve.err.tolist(),'gas_signed_km_s':curve.gas.tolist(),'disk_unit_ML_km_s':curve.disk.tolist(),'bulge_unit_ML_km_s':curve.bulge.tolist(),'baseline':baseline_comp[galaxy]['four_way'],'baseline_results':baseline['results'],'scenarios':[]}
        for scenario in CFG['scenarios']:
            data['scenarios'].append(one_scenario(curve,scenario));save(path.with_suffix('.partial.json'),data)
        validate_data(data);data['complete']=True;save(path,data);complete.append(galaxy);print(galaxy,'completed 14 scenarios',flush=True)
    return {'completed':complete,'identity':ident}

def optimizer_checks():
    records=[];baseline_s={'kind':'physical','upsilon_disk':.5,'upsilon_bulge':.7,'distance_ratio':1.,'inclination_deg':None,'proposal_status':'APPLICABLE'}
    for g in CFG['optimizer_crosscheck_ids']:
        curve=load(g)
        for name in CFG['optimizer_crosscheck_scenarios']:
            spec={**baseline_s,'inclination_deg':curve.metadata['Inc']} if name=='baseline' else scenario_spec(curve,SCENARIOS[name])
            if spec['proposal_status']!='APPLICABLE':records.append({'galaxy':g,'scenario':name,'status':spec['proposal_status']});continue
            view,factor=computation_view(curve,spec)
            for model in ['nfw','burkert']:
                first=fit_fixed(curve,model,spec,M1,GATE);attempts=[]
                for start in [GATE[model+'_starts'][0],GATE[model+'_starts'][2]]:
                    try:
                        def residual(x):
                            from gravity_on_trial.m1_physics import predict
                            return (predict(view,model,x)-view.obs)/view.err
                        fit=least_squares(residual,start,bounds=GATE[model+'_bounds'],method='dogbox',x_scale='jac',ftol=1e-11,xtol=1e-11,gtol=1e-11,max_nfev=2000)
                        attempts.append({'success':bool(fit.success),'parameters':fit.x.tolist(),'chi_squared':float(fit.fun@fit.fun),'status':int(fit.status),'message':fit.message})
                    except (DomainError,ValueError) as error:attempts.append({'success':False,'message':str(error)})
                successful=[a for a in attempts if a['success']];best=min(successful,key=lambda a:a['chi_squared']) if successful else None
                delta=None if best is None or first['status']!='CONVERGED' else best['chi_squared']-first['statistics']['chi_squared']
                records.append({'galaxy':g,'model':model,'scenario':name,'trf_status':first['status'],'trf_chi_squared':first.get('statistics',{}).get('chi_squared'),'dogbox_attempts':attempts,'dogbox_best':best,'chi_squared_difference_dogbox_minus_trf':delta,'objective_agreement_within_target':None if delta is None else abs(delta)<=1e-6*max(1,first['statistics']['chi_squared']),'interpretation':'Separate numerical-method stress check; disagreements are sensitivity evidence, not changed frozen results'})
    save(OUT/'optimizer_crosschecks.json',{'records':records,'identity':identity()});return {'checks':len(records)}

if __name__=='__main__':
    if sys.argv[1]=='audit':summary=identifiability_audit()
    elif sys.argv[1]=='batch':summary=batch(sys.argv[2],sys.argv[3],sys.argv[4:])
    elif sys.argv[1]=='optimizer':summary=optimizer_checks()
    else:raise ValueError('Unknown task')
    save(OUT/'resources'/('_'.join(sys.argv[1:])+'.json'),{'wall_seconds':time.perf_counter()-BEGUN,'baseline_RSS_MiB':BASE,'peak_working_set_MiB':PROC.memory_info().peak_wset/2**20,'CPU_seconds':sum(PROC.cpu_times()[:2]),'summary':summary})
