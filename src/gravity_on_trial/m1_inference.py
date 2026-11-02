"""Separate MLE/MAP objectives with known-error likelihood diagnostics."""
import hashlib,json,math,time
import numpy as np
from scipy.optimize import least_squares
from .m1_physics import DomainError,predict

def diagnostics(obs,pred,err,k,mode='MLE'):
    obs,pred,err=[np.asarray(a,float) for a in (obs,pred,err)]
    if obs.ndim!=1 or obs.shape!=pred.shape or obs.shape!=err.shape or len(obs)==0: raise ValueError('Aligned nonempty arrays required')
    if k<0 or int(k)!=k: raise ValueError('Nonnegative integer parameter count required')
    if any(np.any(~np.isfinite(a)) for a in [obs,pred,err]) or np.any(err<=0): raise ValueError('Invalid observations/predictions/errors')
    if mode not in ['MLE','MAP']: raise ValueError('Unknown objective mode')
    z=(pred-obs)/err; n=len(obs); chi=float(z@z)
    logl=-.5*(chi+float(np.sum(np.log(2*np.pi)+2*np.log(err)))); mle=mode=='MLE'
    aic=2*k-2*logl if mle else None
    return {'n':n,'k':k,'degrees_of_freedom':n-k,'chi_squared':chi,'log_likelihood':logl,'reduced_chi_squared':chi/(n-k) if n>k else None,'weighted_RMSE_km_s':float(np.sqrt(np.sum((pred-obs)**2/err**2)/np.sum(1/err**2))),'max_absolute_residual_km_s':float(np.max(np.abs(pred-obs))),'max_absolute_standardized_residual':float(np.max(np.abs(z))),'standardized_residual_mean':float(np.mean(z)),'standardized_residual_std':float(np.std(z)),'AIC':aic,'AICc':aic+2*k*(k+1)/(n-k-1) if mle and n>k+1 else None,'BIC':k*np.log(n)-2*logl if mle else None,'information_criterion_policy':'MLE only; AICc requires n>k+1; not theory probabilities','standardized_residuals':z.tolist()}

def boundary_flags(x,bounds):
    lo,hi=np.asarray(bounds,float)
    return (np.minimum(np.asarray(x)-lo,hi-np.asarray(x))/(hi-lo)<1e-5).tolist()

def identifiability(jac,boundary):
    jac=np.asarray(jac,float); n,k=jac.shape
    if k==0: return {'rank':0,'condition':None,'covariance':[],'correlation':[],'standard_errors':[],'warnings':[]}
    _,s,vt=np.linalg.svd(jac,full_matrices=False)
    rank=int(np.sum(s>max(jac.shape)*np.finfo(float).eps*s[0])) if len(s) and s[0]>0 else 0
    condition=float(s[0]/s[-1]) if rank==k else None
    warnings=[]
    if rank<k: warnings.append('rank deficient: parameters not individually identified')
    if condition is not None and condition>1e8: warnings.append('ill-conditioned local sensitivity')
    if any(boundary): warnings.append('boundary solution: unconstrained Gaussian errors unreliable')
    if n<=k: warnings.append('insufficient residual degrees of freedom')
    cov=corr=se=None
    if rank==k and condition<=1e8 and not any(boundary) and n>k:
        cov=(vt.T/s**2)@vt; se=np.sqrt(np.diag(cov)); corr=cov/np.outer(se,se)
        if np.any(np.abs(corr-np.eye(k))>.95): warnings.append('strong local parameter correlation >0.95')
    return {'rank':rank,'condition':condition,'covariance':None if cov is None else cov.tolist(),'correlation':None if corr is None else corr.tolist(),'standard_errors':None if se is None else se.tolist(),'warnings':warnings,'interpretation':'Local linear known-error approximation in optimization coordinates; not posterior credible intervals; no chi-square rescaling'}

def parameter_spec(curve,model,mode,config,gate):
    names=[];lo=[];hi=[]; starts=[[]]; centers=[];sigmas=[]
    if model in ['nfw','burkert']:
        names+=gate[model+'_parameter_order']; lo+=gate[model+'_bounds'][0];hi+=gate[model+'_bounds'][1];starts=[list(s) for s in gate[model+'_starts']]
    if mode=='MAP':
        nuisance=[]
        if np.any(curve.disk!=0): nuisance.append(('log10_upsilon_disk',math.log10(.5),.1,math.log10(.05),math.log10(2)))
        if np.any(curve.bulge!=0): nuisance.append(('log10_upsilon_bulge',math.log10(.7),.1,math.log10(.05),math.log10(2)))
        sigma=curve.metadata['e_D']/curve.metadata['D']
        if sigma>0: nuisance.append(('distance_ratio',1.,sigma,max(.1,1-3*sigma),1+3*sigma))
        i,ei=curve.metadata['Inc'],curve.metadata['e_Inc']
        if ei>0: nuisance.append(('inclination_deg',i,ei,max(1,i-3*ei),min(90,i+3*ei)))
        for name,center,sigma,l,h in nuisance:
            if l>=h: raise ValueError('Degenerate nuisance bounds')
            names.append(name);centers.append(center);sigmas.append(sigma);lo.append(l);hi.append(h)
        # Nuisance starts at prior center; additional deterministic perturbations.
        if len(starts)==1: starts=[starts[0][:] for _ in range(3)]
        for index,start in enumerate(starts):
            for center,sigma,l,h in zip(centers,sigmas,lo[-len(centers):],hi[-len(centers):]):
                start.append(float(np.clip(center+([0,.5,-.5,0][index%4])*sigma,l+1e-8,h-1e-8)))
    return names,[lo,hi],starts,centers,sigmas

def fit_curve(curve,model,mode,config,gate,max_nfev=2000):
    started=time.perf_counter();curve.validate()
    names,bounds,starts,centers,sigmas=parameter_spec(curve,model,mode,config,gate)
    k=len(names); nh=2 if model in ['nfw','burkert'] else 0
    domain=[]
    def prediction(x):
        params=dict(zip(names,x));return predict(curve,model,x[:nh],ud=10**params.get('log10_upsilon_disk',math.log10(.5)),ub=10**params.get('log10_upsilon_bulge',math.log10(.7)),d=params.get('distance_ratio',1),inc=params.get('inclination_deg',curve.metadata['Inc']))
    def data_residual(x): return (prediction(x)-curve.obs)/curve.err
    def prior_residual(x): return (np.asarray(x[nh:])-centers)/sigmas if mode=='MAP' and len(centers) else np.array([])
    def objective(x):
        try: return np.r_[data_residual(x),prior_residual(x)]
        except DomainError as e:
            domain.append({'parameters':list(map(float,x)),'message':str(e),'indices':e.indices});raise
    attempts=[];solutions=[]
    if not k:
        try: pred=prediction([])
        except DomainError as e: return {'model':model,'mode':mode,'status':'UNSUPPORTED_DOMAIN','message':str(e),'invalid_indices':e.indices,'n_inventory':len(curve.r),'excluded_points':0}
        x=np.array([]);jac=np.zeros((len(curve.r),0));bound=[];success=True
    else:
        for start in starts:
            try:
                f=least_squares(objective,start,bounds=bounds,ftol=1e-11,xtol=1e-11,gtol=1e-11,x_scale='jac',max_nfev=max_nfev)
                attempts.append({'start':start,'x':f.x.tolist(),'success':bool(f.success),'status':int(f.status),'message':f.message,'data_chi_squared':float(data_residual(f.x)@data_residual(f.x)),'prior_penalty':float(prior_residual(f.x)@prior_residual(f.x)),'objective':float(f.fun@f.fun),'nfev':f.nfev,'optimality':float(f.optimality)})
                solutions.append(f)
            except (DomainError,ValueError,FloatingPointError) as e:
                attempts.append({'start':start,'success':False,'status':'INVALID_DOMAIN_OR_INPUT','message':str(e)})
        successful=[f for f in solutions if f.success]
        pool=successful or solutions
        if not pool: return {'model':model,'mode':mode,'status':'FAILED','attempts':attempts,'domain_failures':domain,'n_inventory':len(curve.r),'excluded_points':0}
        f=min(pool,key=lambda f:float(f.fun@f.fun));x=f.x;success=bool(f.success);pred=prediction(x);bound=boundary_flags(x,bounds)
        # Differentiate data residuals separately: MAP prior curvature is not data information.
        jac=np.empty((len(curve.r),k));lo,hi=np.asarray(bounds)
        for j in range(k):
            h=1e-5*max(1,abs(x[j]));left=x.copy();right=x.copy();left[j]=max(lo[j],x[j]-h);right[j]=min(hi[j],x[j]+h)
            jac[:,j]=(data_residual(right)-data_residual(left))/(right[j]-left[j])
    stats=diagnostics(curve.obs,pred,curve.err,k,mode)
    ident=identifiability(jac,bound)
    post_ident=identifiability(f.jac,bound) if mode=='MAP' and k else None
    prior=prior_residual(x); prior_penalty=float(prior@prior)
    stats.update({'prior_penalty':prior_penalty,'optimization_objective':stats['chi_squared']+prior_penalty,'objective_label':'data chi-square' if mode=='MLE' else 'data chi-square + Gaussian prior penalties in stated coordinates'})
    z=np.asarray(stats['standardized_residuals']);mid=len(z)//2
    stats['inner_mean_standardized_residual']=float(np.mean(z[:mid])) if mid else None
    stats['outer_mean_standardized_residual']=float(np.mean(z[mid:]))
    stats['neighbor_residual_correlation']=float(np.corrcoef(z[:-1],z[1:])[0,1]) if len(z)>2 and np.std(z[:-1])>0 and np.std(z[1:])>0 else None
    mask=list(range(len(curve.r)))
    return {'model':model,'mode':mode,'status':'CONVERGED' if success else 'OPTIMIZER_FAILED','galaxy':curve.galaxy,'parameter_names':names,'parameters':x.tolist(),'bounds':bounds,'parameter_units':'log halo units encoded in names; ML log10 solar units at 3.6 microns; distance ratio; inclination degrees','boundary_flags':bound,'prediction_km_s':pred.tolist(),'mask':mask,'mask_sha256':hashlib.sha256(json.dumps(mask).encode()).hexdigest(),'excluded_points':0,'statistics':stats,'data_identifiability':ident,'posterior_local_curvature':post_ident,'domain_failures':domain,'attempts':attempts,'wall_seconds':time.perf_counter()-started}
