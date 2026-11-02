"""Frozen M2 scientific execution. Reports/plots are separate consumers."""
import hashlib,json,math,sys,time,traceback
from pathlib import Path
import psutil
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m2/v1'
sys.path.insert(0,str(ROOT/'src'))
PROC=psutil.Process();START=time.perf_counter();BASE=PROC.memory_info().rss/2**20
import numpy as np
from scipy.optimize import brentq
from scipy.integrate import quad
from gravity_on_trial.m1_physics import Curve,DomainError,predict
from gravity_on_trial.m1_inference import fit_curve
from m1_worker import load
CFG=json.loads((ROOT/'configs/m2_v1.json').read_text());M1=json.loads((ROOT/CFG['base_config_file']).read_text());GATE=json.loads((ROOT/CFG['halo_config_file']).read_text())

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2,allow_nan=False));tmp.replace(path)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity():
    paths=[ROOT/'m2_worker.py',ROOT/'m1_worker.py',ROOT/'configs/m2_v1.json',ROOT/CFG['base_config_file'],ROOT/CFG['halo_config_file'],*sorted((ROOT/'src/gravity_on_trial').glob('*.py')),ROOT/'data/raw/MassModels_Lelli2016c.mrt',ROOT/'data/raw/SPARC_Lelli2016c.mrt',ROOT/'data/raw/Rotmod_LTG.zip',ROOT/'results/gate0/parsed_tables.json']
    files={str(p.relative_to(ROOT)):sha(p) for p in paths}
    return {'files':files,'content_revision':hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest(),'seed':CFG['seed'],'run_id':CFG['run_id'],'python':sys.version.split()[0]}

def pred_params(curve,model,names,x):
    d=dict(zip(names,x));nh=2 if model in ['nfw','burkert'] else 0
    return predict(curve,model,x[:nh],ud=10**d.get('log10_upsilon_disk',math.log10(.5)),ub=10**d.get('log10_upsilon_bulge',math.log10(.7)),d=d.get('distance_ratio',1),inc=d.get('inclination_deg',curve.metadata['Inc']))

def scaled_sensitivity(curve,result,hfactor=1e-5):
    names=result['parameter_names'];x=np.array(result['parameters']);n=len(curve.r);k=len(x)
    if not k:return {'column_norms':[],'normalized_singular_values':[],'normalized_condition':None,'weak_direction':False}
    lo,hi=np.array(result['bounds']);jac=np.zeros((n,k))
    for j in range(k):
        h=hfactor*max(1,abs(x[j]));left=x.copy();right=x.copy();left[j]=max(lo[j],x[j]-h);right[j]=min(hi[j],x[j]+h)
        jac[:,j]=(pred_params(curve,result['model'],names,right)-pred_params(curve,result['model'],names,left))/(right[j]-left[j])/curve.err
    norms=np.linalg.norm(jac,axis=0);scaled=np.divide(jac,norms,out=np.zeros_like(jac),where=norms>0);s=np.linalg.svd(scaled,compute_uv=False)
    condition=float(s[0]/s[-1]) if len(s)==k and s[-1]>0 else None
    return {'column_norms':norms.tolist(),'normalized_singular_values':s.tolist(),'normalized_condition':condition,'weak_direction':condition is None or condition>1e6,'note':'Column-normalized local sensitivities; finite differences are not proof of exact mathematical rank'}

def ridge(curve,result):
    names=result['parameter_names'];x=np.array(result['parameters']);params=dict(zip(names,x));model=result['model']
    if 'distance_ratio' not in names or 'inclination_deg' not in names:return {'applicable':False}
    lam=1.00001;d=params['distance_ratio'];inc=params['inclination_deg']
    new=x.copy();new[names.index('distance_ratio')]=d*lam
    new[names.index('inclination_deg')]=math.degrees(math.asin(math.sin(math.radians(inc))/math.sqrt(lam)))
    if model=='burkert':new[0]=x[0]-math.log10(lam);new[1]=x[1]+math.log10(lam)
    elif model=='nfw':
        mass,c=10**x[0],10**x[1];f=lambda z:math.log1p(z)-z/(1+z)
        cnew=brentq(lambda z:z**3/f(z)-c**3/f(c)/lam,.001,10000,xtol=1e-12)
        new[0]=math.log10(mass*(lam*cnew/c)**3);new[1]=math.log10(cnew)
    a=pred_params(curve,model,names,x);b=pred_params(curve,model,names,new)
    relative=float(np.max(np.abs(a-b)/np.maximum(np.abs(a),1)))
    assert relative<1e-9,(curve.galaxy,model,relative)
    lo,hi=np.array(result['bounds'])
    return {'applicable':True,'distance_scale_perturbation':lam,'max_relative_velocity_difference':relative,'perturbed_parameters':new.tolist(),'perturbation_within_prior_box':bool(np.all((new>=lo)&(new<=hi))),'interpretation':'Exact physical scaling direction in likelihood, not a random resampling or posterior interval; priors/bounds may restrict this direction'}

def audit():
    records=[]
    for galaxy in M1['galaxies']:
        curve=load(galaxy);data=json.loads((ROOT/f'results/m1/v1/{galaxy}_initial.json').read_text())
        for r in data['results']:
            checks=[{'step':h,**scaled_sensitivity(curve,r,h)} for h in [1e-4,1e-5,1e-6]]
            records.append({'galaxy':galaxy,'model':r['model'],'mode':r['mode'],'n':r['statistics']['n'],'k':r['statistics']['k'],'r_min':float(curve.r.min()),'r_max':float(curve.r.max()),'warnings':r['data_identifiability']['warnings'],'boundary_parameters':[n for n,b in zip(r['parameter_names'],r['boundary_flags']) if b],'boundary_values':dict(zip(r['parameter_names'],r['parameters'])) if any(r['boundary_flags']) else None,'legacy_condition':r['data_identifiability']['condition'],'normalized_step_checks':checks,'exact_geometry_ridge':ridge(curve,r) if r['mode']=='MAP' else None,'all_starts_converged':all(a['success'] for a in r['attempts']),'start_objective_range':max((a['objective'] for a in r['attempts']),default=0)-min((a['objective'] for a in r['attempts']),default=0)})
    save(OUT/'identifiability_audit.json',{'records':records,'warning_count':sum(bool(r['warnings']) for r in records),'boundary_count':sum(bool(r['boundary_parameters']) for r in records),'identity':identity()})
    return {'records':len(records),'warnings':sum(bool(r['warnings']) for r in records)}

def independent_halo(curve,result):
    if result['model'] not in ['nfw','burkert'] or result['status']!='CONVERGED':return None
    names=result['parameter_names'];d=dict(zip(names,result['parameters']));a,b=10.**np.array(result['parameters'][:2]);distance=d.get('distance_ratio',1);r=curve.r*distance
    if result['model']=='nfw':
        critical=3*.073**2/(8*math.pi*4.30091e-6);R=(3*a/(4*math.pi*200*critical))**(1/3);scale=R/b;normal=math.log1p(b)-b/(1+b)
        masses=[a*quad(lambda t:t/(1+t)**2,0,float(radius/scale),epsabs=1e-20,epsrel=1e-12)[0]/normal for radius in r]
    else:masses=[4*math.pi*a*b**3*quad(lambda t:t*t/((1+t)*(1+t*t)),0,float(radius/b),epsabs=1e-20,epsrel=1e-12)[0] for radius in r]
    ud=10**d.get('log10_upsilon_disk',math.log10(.5));ub=10**d.get('log10_upsilon_bulge',math.log10(.7))
    bar=np.array([distance*math.fsum([ud*disk*disk,ub*bulge*bulge,math.copysign(gas*gas,gas)]) for disk,bulge,gas in zip(curve.disk,curve.bulge,curve.gas)])
    independent=np.sqrt(bar+4.30091e-6*np.array(masses)/r)*math.sin(math.radians(d.get('inclination_deg',curve.metadata['Inc'])))/math.sin(math.radians(curve.metadata['Inc']))
    error=float(np.max(np.abs(independent-np.array(result['prediction_km_s']))/np.maximum(independent,1)))
    assert error<1e-9,(curve.galaxy,result['model'],error)
    return {'all_radii_quadrature_relative_error':error,'n':len(r)}

def evaluate(curve,model,mode):
    start=time.perf_counter();before=PROC.memory_info().rss/2**20
    try:result=fit_curve(curve,model,mode,M1,GATE)
    except (DomainError,ValueError,np.linalg.LinAlgError) as error:
        result={'status':'DIAGNOSTIC_FAILURE','model':model,'mode':mode,'message':str(error),'traceback':traceback.format_exc()}
    status=result['status']
    if status=='FAILED':result['status']='NO_VALID_START'
    result['attempted_mask']=list(range(len(curve.r)));result['accepted_mask']=result.get('mask',[])
    result['invalid_indices']=result.get('invalid_indices',sorted({i for entry in result.get('domain_failures',[]) for i in entry.get('indices',[])}))
    result['n_inventory']=len(curve.r);result['n_accepted']=len(result['accepted_mask']);result['whole_evaluation_rejected']=not bool(result['accepted_mask'])
    result['priors']=None if mode=='MLE' else {k:M1[k] for k in ['ML_prior','distance_prior','inclination_prior','ML_bounds_solar','prior_justification']}
    result['resource']={'wall_seconds':time.perf_counter()-start,'RSS_before_MiB':before,'RSS_after_MiB':PROC.memory_info().rss/2**20,'process_lifetime_peak_so_far_MiB':PROC.memory_info().peak_wset/2**20,'peak_scope':'Lifetime high-water mark of this serial worker through this evaluation, not an isolated per-fit peak'}
    if result['status']=='CONVERGED':
        result['scaled_sensitivity']=scaled_sensitivity(curve,result)
        result['independent_halo_check']=independent_halo(curve,result)
        for value in result['prediction_km_s']:assert math.isfinite(value) and value>=0
    return result

def validate_file(data):
    assert len(data['results'])==8 and len({(r['mode'],r['model']) for r in data['results']})==8
    for r in data['results']:
        assert r['status'] in CFG['failure_statuses']
        if r['status']=='DIAGNOSTIC_FAILURE':raise RuntimeError('Unresolved diagnostic error: '+str(r.get('message')))
        if r['status']=='CONVERGED':
            s=r['statistics'];assert len(r['prediction_km_s'])==data['n_inventory']
            assert r['accepted_mask']==list(range(data['n_inventory']))
            assert (s['reduced_chi_squared'] is None)==(s['n']<=s['k'])
            assert (s['AICc'] is None)==(r['mode']=='MAP' or s['n']<=s['k']+1)
            if r['mode']=='MAP':assert s['AIC'] is None and s['BIC'] is None
            assert s['k']==len(r['parameter_names'])
            z=[(p-o)/e for p,o,e in zip(r['prediction_km_s'],data['observed_km_s'],data['error_km_s'])]
            assert math.isclose(math.fsum(v*v for v in z),s['chi_squared'],rel_tol=1e-12,abs_tol=1e-10)

def batch(stage,replicate,ids):
    if stage=='full' and not json.loads((OUT/'pilot_gate.json').read_text())['GO']:raise RuntimeError('Pilot GO required')
    ident=identity();completed=[]
    for g in ids:
        path=OUT/stage/replicate/(g+'.json')
        if path.exists():
            previous=json.loads(path.read_text());assert previous['identity']==ident,'Resume identity mismatch';validate_file(previous);completed.append(g);continue
        curve=load(g);data={'galaxy':g,'stage':stage,'replicate':replicate,'metadata':curve.metadata,'n_inventory':len(curve.r),'radius_kpc':curve.r.tolist(),'observed_km_s':curve.obs.tolist(),'error_km_s':curve.err.tolist(),'gas_signed_km_s':curve.gas.tolist(),'disk_unit_ML_km_s':curve.disk.tolist(),'bulge_unit_ML_km_s':curve.bulge.tolist(),'identity':ident,'results':[],'source_url':'https://astroweb.case.edu/SPARC/MassModels_Lelli2016c.mrt','quality_flags':{'Q3':curve.metadata['Q']==3,'low_inclination':curve.metadata['Inc']<30}}
        for mode in CFG['modes']:
            for model in CFG['models']:
                data['results'].append(evaluate(curve,model,mode));save(path.with_suffix('.partial.json'),data)
        validate_file(data);data['complete']=True;save(path,data);completed.append(g)
        print(g,[(r['model'],r['mode'],r['status']) for r in data['results'] if r['status']!='CONVERGED'],flush=True)
    return {'completed':completed,'identity':ident}

def extras():
    output=[]
    inventory=json.loads((OUT/'inventory.json').read_text())['galaxies']
    for c in inventory:
        if not c['nonpositive_bar_rows']:continue
        curve=load(c['ID']);bar=.5*curve.disk**2+.7*curve.bulge**2+curve.gas*np.abs(curve.gas);indices=np.flatnonzero(bar>0)
        sub=Curve(curve.galaxy,*(a[indices] for a in [curve.r,curve.obs,curve.err,curve.gas,curve.disk,curve.bulge]),curve.metadata)
        records=[evaluate(sub,m,'MLE') for m in CFG['models']]
        output.append({'galaxy':curve.galaxy,'label':'SEPARATE COMMON POSITIVE-BARYONIC-FORCE SUBSET; never substitutes for full inventory','original_mask':indices.tolist(),'excluded_original_indices':np.flatnonzero(bar<=0).tolist(),'results':records})
    save(OUT/'common_subset_sensitivity.json',output)
    predictive=[]
    for g in CFG['predictive_ids']:
        curve=load(g);bar=.5*curve.disk**2+.7*curve.bulge**2+curve.gas*np.abs(curve.gas)
        if len(curve.r)<10 or np.any(bar<=0):predictive.append({'galaxy':g,'status':'INELIGIBLE'});continue
        split=int(.7*len(curve.r));train=Curve(g,*(a[:split] for a in [curve.r,curve.obs,curve.err,curve.gas,curve.disk,curve.bulge]),curve.metadata);records=[]
        for model in CFG['models']:
            result=evaluate(train,model,'MLE')
            if result['status']=='CONVERGED':
                prediction=pred_params(curve,model,result['parameter_names'],result['parameters']);z=(prediction[split:]-curve.obs[split:])/curve.err[split:]
                records.append({'model':model,'train_result':result,'outer_prediction_km_s':prediction[split:].tolist(),'outer_standardized_residuals':z.tolist(),'outer_chi_squared':float(z@z),'outer_weighted_RMSE_km_s':float(np.sqrt(np.sum((prediction[split:]-curve.obs[split:])**2/curve.err[split:]**2)/np.sum(1/curve.err[split:]**2)))})
            else:records.append({'model':model,'train_result':result})
        predictive.append({'galaxy':g,'status':'ATTEMPTED','train_mask':list(range(split)),'test_mask':list(range(split,len(curve.r))),'records':records,'interpretation':'Radial extrapolation with potentially correlated neighboring errors; no independent random-test claim'})
    save(OUT/'predictive_pilot.json',predictive);return {'common_subset_cases':len(output),'predictive_cases':len(predictive)}

if __name__=='__main__':
    command=sys.argv[1]
    if command=='audit':result=audit()
    elif command=='batch':result=batch(sys.argv[2],sys.argv[3],sys.argv[4:])
    elif command=='extras':result=extras()
    else:raise ValueError('Unknown task')
    save(OUT/'resources'/('_'.join(sys.argv[1:])+'.json'),{'wall_seconds':time.perf_counter()-START,'baseline_RSS_MiB':BASE,'peak_working_set_MiB':PROC.memory_info().peak_wset/2**20,'CPU_seconds':sum(PROC.cpu_times()[:2]),'result':result})
