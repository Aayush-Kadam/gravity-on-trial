"""Serial single-galaxy fit with independent halo quadrature controls."""
import json, math, sys, time
from pathlib import Path
import psutil
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
process=psutil.Process(); baseline=process.memory_info().rss/2**20; begun=time.perf_counter()
import numpy as np
from scipy.integrate import quad
from scipy.optimize import least_squares
from gravity_on_trial.halos import nfw,burkert
galaxy,model,replicate=sys.argv[1:]
config=json.loads((ROOT/'configs/gate0r.json').read_text())
fn={'nfw':nfw,'burkert':burkert}[model]
# Stream only this galaxy's fields from frozen raw MRT; never load the full catalog.
rows=[]
for line in (ROOT/'data/raw/MassModels_Lelli2016c.mrt').open():
    if line[:11].strip()==galaxy:
        rows.append([float(line[a-1:b]) for a,b in [(20,25),(27,32),(34,38),(40,45),(47,52),(54,59)]])
if not rows: raise ValueError('Unknown galaxy')
r,obs,err,gas,disk,bulge=np.array(rows).T
bar=.5*disk**2+.7*bulge**2+gas*np.abs(gas)
if np.any(bar<0): raise ValueError('Negative baryonic squared speed requires explicit domain handling')

def independent(radii,p):
    a,b=10.**np.asarray(p)
    if model=='nfw':
        # Re-derive density from critical density, then integrate dimensionless density.
        critical=3*(73/1000)**2/(8*math.pi*4.30091e-6)
        R=(a/(200*critical*4*math.pi/3))**(1/3); scale=R/b
        norm=math.log(1+b)-b/(1+b)
        rho=a/(4*math.pi*scale**3*norm)
        density=lambda t: t/(1+t)**2
    else:
        rho=a; scale=b; density=lambda t:t*t/((1+t)*(1+t*t))
    return np.array([4.30091e-6*(4*math.pi*rho*scale**3*quad(density,0,float(radius/scale),epsabs=1e-25,epsrel=1e-12)[0])/radius for radius in radii])

controls=[]
for p in config[model+'_starts']:
    radii=np.geomspace(1e-7,1e3,30)
    direct=fn(radii,p); reference=independent(radii,p)
    delta=float(np.max(np.abs(direct/reference-1)))
    assert delta<config['identity_relative_tolerance'],delta
    assert np.all(direct>0)
    controls.append({'parameters':p,'max_relative_quadrature_error':delta})
if model=='nfw':
    m,c=1e11,10; R=(4.30091e-6*m/(100*.073**2))**(1/3); rs=R/c; tiny=rs*1e-6
    asymptotic=4.30091e-6*m/(math.log1p(c)-c/(1+c))*tiny/(2*rs**2)
    got=fn(np.array([tiny]),[11,1])[0]
    assert math.isclose(fn(np.array([R]),[11,1])[0],4.30091e-6*m/R,rel_tol=1e-9)
else:
    rho,r0=1e7,2.; tiny=r0*1e-6
    asymptotic=4.30091e-6*4*math.pi*rho*tiny**2/3
    got=fn(np.array([tiny]),[7,math.log10(r0)])[0]
assert abs(got/asymptotic-1)<config['asymptotic_relative_tolerance']
for invalid in [0,-1,float('nan')]:
    try: fn(np.array([invalid]),config[model+'_starts'][0])
    except ValueError: pass
    else: raise AssertionError('Invalid radius accepted')

def residual(p):
    total=bar+fn(r,p)
    if np.any(total<0) or np.any(~np.isfinite(total)): raise ValueError('Invalid total squared speed')
    return (np.sqrt(total)-obs)/err
attempts=[]; solutions=[]
for start in config[model+'_starts']:
    t=time.perf_counter()
    fit=least_squares(residual,start,bounds=config[model+'_bounds'],ftol=1e-11,xtol=1e-11,gtol=1e-11,max_nfev=2000,x_scale='jac')
    chi=float(np.sum(fit.fun**2)); solutions.append(fit)
    attempts.append({'start':start,'parameters_log10':fit.x.tolist(),'chi_squared':chi,'success':bool(fit.success),'status':int(fit.status),'message':fit.message,'nfev':fit.nfev,'optimality':float(fit.optimality),'active_mask':fit.active_mask.tolist(),'wall_seconds':time.perf_counter()-t})
best=min(solutions,key=lambda f:np.sum(f.fun**2)); prediction=np.sqrt(bar+fn(r,best.x))
independent_prediction=np.sqrt(bar+independent(r,best.x))
discrepancy=float(np.max(np.abs(prediction/independent_prediction-1)))
assert discrepancy<1e-9
lo,hi=np.array(config[model+'_bounds']); bound=bool(np.any(np.minimum(best.x-lo,hi-best.x)/(hi-lo)<1e-5))
chi=float(np.sum(best.fun**2)); n=len(r)
out={'galaxy':galaxy,'model':model,'replicate':replicate,'parameter_order':config[model+'_parameter_order'],'parameters_log10':best.x.tolist(),'parameters_physical':(10.**best.x).tolist(),'n':n,'k':2,'chi_squared':chi,'reduced_chi_squared':chi/(n-2),'residual_mean':float(np.mean(best.fun)),'residual_RMS':float(np.sqrt(np.mean(best.fun**2))),'boundary_limited':bound,'success':bool(best.success),'jacobian_condition_number':float(np.linalg.cond(best.jac)),'all_starts':attempts,'controls':controls,'small_radius_relative_error':float(abs(got/asymptotic-1)),'fitted_quadrature_max_relative_error':discrepancy,'r_kpc':r.tolist(),'observed_km_s':obs.tolist(),'error_km_s':err.tolist(),'gas_signed_km_s':gas.tolist(),'disk_unit_ML_km_s':disk.tolist(),'bulge_unit_ML_km_s':bulge.tolist(),'bar_squared_km2_s2':bar.tolist(),'prediction_km_s':prediction.tolist(),'standardized_residuals':best.fun.tolist(),'excluded_points':0,'resource':{'baseline_RSS_MiB':baseline,'peak_working_set_MiB':process.memory_info().peak_wset/2**20,'wall_seconds':time.perf_counter()-begun}}
path=ROOT/'results/gate0r'/f'{galaxy}_{model}_{replicate}.json'
path.write_text(json.dumps(out,indent=2,allow_nan=False))
print(json.dumps({k:out[k] for k in ['galaxy','model','success','chi_squared','boundary_limited','resource']}))
if not best.success: sys.exit(3)
