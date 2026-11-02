"""M3 inference adapters. Existing M1/M2 scientific source is unchanged."""
import copy,math,time
import numpy as np
from scipy.optimize import least_squares
from gravity_on_trial.m1_physics import Curve,DomainError,predict
from gravity_on_trial.m1_inference import fit_curve,parameter_spec,diagnostics,identifiability,boundary_flags

def scenario_spec(curve,scenario):
    if scenario['kind']=='prior':return {'kind':'prior','ML_prior_sigma_dex':scenario['ML_prior_sigma_dex']}
    ud=.5*10**scenario['disk_dex'];ub=.7*10**scenario['bulge_dex'];d=1+scenario['distance_sigma']*curve.metadata['e_D']/curve.metadata['D'];inc=curve.metadata['Inc']+scenario['inclination_sigma']*curve.metadata['e_Inc']
    spec={'kind':'physical','upsilon_disk':ud,'upsilon_bulge':ub,'distance_ratio':d,'inclination_deg':inc,'catalog_inclination_deg':curve.metadata['Inc'],'physical_distance_Mpc':curve.metadata['D']*d}
    if d<=0 or not 0<inc<=90:return {**spec,'proposal_status':'INVALID_PROPOSAL','reason':'Nonpositive distance or inclination outside (0,90]; not clipped'}
    changed=(scenario['disk_dex']!=0 and np.any(curve.disk!=0)) or (scenario['bulge_dex']!=0 and np.any(curve.bulge!=0)) or (scenario['distance_sigma']!=0 and curve.metadata['e_D']!=0) or (scenario['inclination_sigma']!=0 and curve.metadata['e_Inc']!=0)
    return {**spec,'proposal_status':'APPLICABLE' if changed else 'NOT_APPLICABLE','reason':None if changed else 'Changed component absent or geometry uncertainty zero'}

def computation_view(curve,spec):
    d=spec['distance_ratio'];f=math.sin(math.radians(spec['inclination_deg']))/math.sin(math.radians(curve.metadata['Inc']))
    meta={**curve.metadata,'D':curve.metadata['D']*d,'e_D':curve.metadata['e_D']*d,'Inc':spec['inclination_deg']}
    view=Curve(curve.galaxy,curve.r*d,curve.obs/f,curve.err/f,curve.gas*math.sqrt(d),curve.disk*math.sqrt(d*spec['upsilon_disk']/.5),curve.bulge*math.sqrt(d*spec['upsilon_bulge']/.7),meta)
    return view.validate(),f

def finalize(result,curve):
    if result['status']=='FAILED':result['status']='NO_VALID_START'
    result['n_inventory']=len(curve.r);result['attempted_mask']=list(range(len(curve.r)));result['accepted_mask']=result.get('mask',[]);result['excluded_original_points']=[]
    return result

def fit_fixed(curve,model,spec,m1,gate):
    start=time.perf_counter();view,f=computation_view(curve,spec)
    result=fit_curve(view,model,'MLE',m1,gate)
    if 'prediction_km_s' in result:
        physical=np.array(result['prediction_km_s']);projected=physical*f;old=result['statistics'];stats=diagnostics(curve.obs,projected,curve.err,len(result['parameters']),'MLE')
        transformed_logl=old['log_likelihood']-len(curve.r)*math.log(f)
        if not math.isclose(stats['log_likelihood'],transformed_logl,rel_tol=1e-10,abs_tol=1e-8):raise AssertionError('Inclination likelihood Jacobian mismatch')
        for name in ['inner_mean_standardized_residual','outer_mean_standardized_residual','neighbor_residual_correlation']:
            if name in old:stats[name]=old[name]
        stats.update(prior_penalty=0.,optimization_objective=stats['chi_squared'],objective_label='catalog-frame maximum-likelihood data chi-square')
        nh=2 if model in ['nfw','burkert'] else 0
        direct=predict(curve,model,result['parameters'][:nh],ud=spec['upsilon_disk'],ub=spec['upsilon_bulge'],d=spec['distance_ratio'],inc=spec['inclination_deg'])
        relative=float(np.max(np.abs(direct-projected)/np.maximum(np.abs(direct),1)))
        if relative>1e-9:raise AssertionError('Equivalent physical/view predictions differ')
        result['prediction_physical_km_s']=physical.tolist();result['prediction_km_s']=projected.tolist();result['statistics']=stats
        result['geometry_check']={'equivalent_prediction_relative_error':relative,'catalog_logL_minus_transformed_logL':stats['log_likelihood']-transformed_logl,'projection_factor':f}
    result['fixed_assumptions']=spec;result['wall_seconds']=time.perf_counter()-start
    return finalize(result,curve)

def prediction_from_parameters(curve,model,names,x):
    p=dict(zip(names,x));nh=2 if model in ['nfw','burkert'] else 0
    return predict(curve,model,x[:nh],ud=10**p.get('log10_upsilon_disk',math.log10(.5)),ub=10**p.get('log10_upsilon_bulge',math.log10(.7)),d=p.get('distance_ratio',1),inc=p.get('inclination_deg',curve.metadata['Inc']))

def prior_residual_vector(x,nh,centers,sigmas):return (np.asarray(x[nh:])-centers)/sigmas if len(centers) else np.array([])

def fit_prior_width(curve,model,width,m1,gate):
    """Same M2 bounded MAP problem except explicitly changed ML penalty widths."""
    started=time.perf_counter();curve.validate();names,bounds,starts,centers,sigmas=parameter_spec(curve,model,'MAP',m1,gate)
    nh=2 if model in ['nfw','burkert'] else 0;k=len(names);sigmas=np.array(sigmas,float)
    if not np.isfinite(width) or width<=0:raise ValueError('Prior width must be positive dex')
    for i,name in enumerate(names[nh:]):
        if name.startswith('log10_upsilon'):sigmas[i]=width
    def pred(x):return prediction_from_parameters(curve,model,names,x)
    def datares(x):return (pred(x)-curve.obs)/curve.err
    def priors(x):return prior_residual_vector(x,nh,centers,sigmas)
    failures=[]
    def objective(x):
        try:return np.r_[datares(x),priors(x)]
        except DomainError as e:failures.append({'parameters':list(map(float,x)),'indices':e.indices,'message':str(e)});raise
    attempts=[];solutions=[]
    for start in starts:
        try:
            f=least_squares(objective,start,bounds=bounds,ftol=1e-11,xtol=1e-11,gtol=1e-11,max_nfev=2000,x_scale='jac')
            attempts.append({'start':start,'x':f.x.tolist(),'success':bool(f.success),'status':int(f.status),'message':f.message,'data_chi_squared':float(datares(f.x)@datares(f.x)),'prior_penalty':float(priors(f.x)@priors(f.x)),'objective':float(f.fun@f.fun),'nfev':f.nfev,'optimality':float(f.optimality)});solutions.append(f)
        except (DomainError,ValueError,FloatingPointError) as e:attempts.append({'start':start,'success':False,'status':'INVALID_DOMAIN_OR_INPUT','message':str(e)})
    pool=[f for f in solutions if f.success] or solutions
    if not pool:return finalize({'status':'NO_VALID_START','model':model,'mode':'MAP','parameter_names':names,'bounds':bounds,'attempts':attempts,'domain_failures':failures,'prior_sigma_dex':width,'wall_seconds':time.perf_counter()-started},curve)
    f=min(pool,key=lambda f:float(f.fun@f.fun));x=f.x;prediction=pred(x);boundary=boundary_flags(x,bounds)
    jac=np.empty((len(curve.r),k));lo,hi=np.asarray(bounds)
    for j in range(k):
        h=1e-5*max(1,abs(x[j]));left=x.copy();right=x.copy();left[j]=max(lo[j],x[j]-h);right[j]=min(hi[j],x[j]+h);jac[:,j]=(datares(right)-datares(left))/(right[j]-left[j])
    stats=diagnostics(curve.obs,prediction,curve.err,k,'MAP');pr=priors(x);penalty=float(pr@pr);stats.update(prior_penalty=penalty,optimization_objective=stats['chi_squared']+penalty,objective_label='data chi-square plus declared Gaussian prior penalties; no information criteria')
    return finalize({'status':'CONVERGED' if f.success else 'OPTIMIZER_FAILED','model':model,'mode':'MAP','galaxy':curve.galaxy,'parameter_names':names,'parameters':x.tolist(),'bounds':bounds,'prior_sigma_dex':width,'prior_centers':centers,'all_nuisance_prior_sigmas':sigmas.tolist(),'prior_coordinate_density':'Gaussian in log10 ML, distance ratio and degrees; unchanged M2 boxes/geometry priors','prediction_km_s':prediction.tolist(),'statistics':stats,'data_identifiability':identifiability(jac,boundary),'posterior_local_curvature':identifiability(f.jac,boundary),'boundary_flags':boundary,'mask':list(range(len(curve.r))),'attempts':attempts,'domain_failures':failures,'wall_seconds':time.perf_counter()-started},curve)

def independent_control_record(result,spec):
    """Append fixed assumptions for independent quadrature only, never as fitted k."""
    control=copy.deepcopy(result)
    if result['mode']=='MLE' and result['status']=='CONVERGED':
        control['parameter_names']+=['log10_upsilon_disk','log10_upsilon_bulge','distance_ratio','inclination_deg']
        control['parameters'] += [math.log10(spec['upsilon_disk']),math.log10(spec['upsilon_bulge']),spec['distance_ratio'],spec['inclination_deg']]
    return control
