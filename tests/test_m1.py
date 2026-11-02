"""Independent scientific controls. Synthetic cases are implementation tests only."""
import json,math
from pathlib import Path
import numpy as np
import pytest
from scipy.integrate import quad
from scipy.stats import norm
from gravity_on_trial.halos import nfw,burkert
from gravity_on_trial.m1_physics import Curve,DomainError,signed_baryons,speed,rar_acceleration,rar_speed,inclination_factor,distance_transform,KPC_M,predict
from gravity_on_trial.m1_inference import diagnostics,fit_curve,boundary_flags,identifiability
ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/'configs/m1_v1.json').read_text());GATE=json.loads((ROOT/'configs/gate0r.json').read_text())

def synthetic(model='nfw'):
    r=np.geomspace(.05,80,80);gas=10*np.sqrt(r/(1+r));disk=80*np.sqrt(r)*np.exp(-r/10)
    c=Curve('SYNTHETIC',r,np.zeros(80),np.full(80,1.),gas,disk,np.zeros(80),{'D':10.,'e_D':1.,'Inc':60.,'e_Inc':3.})
    # Independent density integration generates injected halo, not production halo prediction.
    b=.5*disk**2+gas**2
    if model=='nfw':
        m,c200=1e11,10.;R=(4.30091e-6*m/(100*.073**2))**(1/3);rs=R/c200
        h=np.array([4.30091e-6*m*quad(lambda t:t/(1+t)**2,0,float(v/rs))[0]/(math.log1p(c200)-c200/(1+c200))/v for v in r])
    elif model=='burkert':
        rho,r0=1e7,3.;h=np.array([4.30091e-6*4*math.pi*rho*r0**3*quad(lambda t:t*t/((1+t)*(1+t*t)),0,float(v/r0))[0]/v for v in r])
    else: h=np.zeros_like(r)
    c.obs=np.sqrt(b+h);return c

@pytest.mark.parametrize('profile,params',[('nfw',[11,1]),('nfw',[8,-.2]),('nfw',[13,1.9]),('burkert',[7,.5]),('burkert',[10,-1]),('burkert',[5,2])])
def test_density_quadrature(profile,params):
    r=np.geomspace(1e-7,1000,24); a,b=10.**np.array(params)
    if profile=='nfw':
        critical=3*.073**2/(8*math.pi*4.30091e-6);R=(3*a/(4*math.pi*200*critical))**(1/3);rs=R/b;normf=math.log1p(b)-b/(1+b)
        mass=[a*quad(lambda t:t/(1+t)**2,0,float(v/rs),epsabs=1e-25,epsrel=1e-12)[0]/normf for v in r]
    else: mass=[4*math.pi*a*b**3*quad(lambda t:t*t/((1+t)*(1+t*t)),0,float(v/b),epsabs=1e-25,epsrel=1e-12)[0] for v in r]
    got={'nfw':nfw,'burkert':burkert}[profile](r,params)
    np.testing.assert_allclose(got,4.30091e-6*np.array(mass)/r,rtol=1e-9,atol=0)

def test_halo_limits_and_units():
    m,c=1e11,10.;R=(4.30091e-6*m/(100*(73/1000)**2))**(1/3);rs=R/c;r=rs*1e-6
    assert nfw(np.array([R]),[11,1])[0]==pytest.approx(4.30091e-6*m/R,rel=1e-9)
    expected=4.30091e-6*m/(math.log1p(c)-c/(1+c))*r/(2*rs**2)
    assert nfw(np.array([r]),[11,1])[0]==pytest.approx(expected,rel=2e-6)
    rho,r0=1e7,3.;r=r0*1e-6
    assert burkert(np.array([r]),[7,math.log10(r0)])[0]==pytest.approx(4.30091e-6*4*math.pi*rho*r*r/3,rel=2e-6)
    # NFW outer enclosed mass is logarithmic, not a finite total mass.
    radii=rs*np.array([1e5,1e6]);mass=nfw(radii,[11,1])*radii/4.30091e-6
    assert (mass[1]-mass[0])/(m/(math.log1p(c)-c/(1+c)))==pytest.approx(math.log(10),rel=1e-5)

@pytest.mark.parametrize('value',[0,-1,float('nan'),float('inf')])
def test_invalid_halo_radius(value):
    for fn in [nfw,burkert]:
        with pytest.raises(ValueError): fn(np.array([value]),[10,1])

def test_signed_baryons_and_limits():
    assert signed_baryons([-3],[4],[5],.5,.7)[0]==pytest.approx(16.5)
    assert signed_baryons([-3],[4],[5],0,0)[0]==-9
    assert signed_baryons([2],[4],[0],.5,.7)[0]==12
    with pytest.raises(DomainError): speed([-1])
    assert speed([0])[0]==0
    with pytest.raises(DomainError): signed_baryons([1],[2],[3],-.1,.7)

def test_rar_limits_and_SI():
    assert rar_acceleration(np.array([1.2e-6]))[0]==pytest.approx(1.2e-6,rel=1e-12)
    g=1.2e-24
    assert rar_acceleration(np.array([g]))[0]==pytest.approx(math.sqrt(g*1.2e-10),rel=1e-6)
    r=2.;v2=10000.;g=v2*1000**2/(r*3.085677581491367e19)
    expected=math.sqrt(g/(1-math.exp(-math.sqrt(g/1.2e-10)))*r*3.085677581491367e19)/1000
    assert rar_speed(np.array([r]),np.array([v2]))[0]==pytest.approx(expected,rel=1e-12)
    assert KPC_M==pytest.approx(3.085677581491367e19)

@pytest.mark.parametrize('g',[0,-1,float('nan'),float('inf')])
def test_rar_domain(g):
    with pytest.raises(DomainError): rar_acceleration([g])

def test_distance_geometry_independent():
    c=synthetic();ratio=1.2
    rr,bb=distance_transform(c.r,signed_baryons(c.gas,c.disk,c.bulge),ratio)
    np.testing.assert_allclose(rr,c.r*ratio);np.testing.assert_allclose(bb,ratio*(.5*c.disk**2+c.gas**2))
    expected=np.sqrt(bb+nfw(rr,[11,1]));np.testing.assert_allclose(predict(c,'nfw',[11,1],d=ratio),expected)
    for value in [0,-1,float('nan')]:
        with pytest.raises(DomainError): distance_transform(c.r,c.disk,value)

@pytest.mark.parametrize('old,new',[(60,50),(10,15),(89,90),(90,89),(1,2)])
def test_inclination_equivalent_frames(old,new):
    f=math.sin(math.radians(new))/math.sin(math.radians(old));v=np.array([30.,70]);sigma=np.array([2.,4]);physical=np.array([32.,68])
    catalog=(physical*f-v)/sigma;corrected=(physical-v/f)/(sigma/f)
    np.testing.assert_allclose(catalog,corrected,rtol=1e-12,atol=1e-12)
    assert inclination_factor(old,new)==pytest.approx(f,rel=1e-12)

@pytest.mark.parametrize('i',[0,-1,91,float('nan')])
def test_invalid_inclination(i):
    with pytest.raises(DomainError): inclination_factor(60,i)

def test_likelihood_normalization_and_weighted_RMS():
    obs=np.array([1.,2.,4.]);pred=np.array([2.,2.,2.]);err=np.array([1.,2.,3.]);s=diagnostics(obs,pred,err,1)
    assert s['log_likelihood']==pytest.approx(sum(norm.logpdf(obs,loc=pred,scale=err)))
    assert s['weighted_RMSE_km_s']==pytest.approx(math.sqrt((1+4/9)/(1+1/4+1/9)))
    assert s['AIC']==pytest.approx(2-2*s['log_likelihood']);assert s['BIC']==pytest.approx(math.log(3)-2*s['log_likelihood'])

@pytest.mark.parametrize('n,k',[(1,0),(1,1),(2,1),(2,2),(3,2),(4,2)])
def test_statistical_applicability(n,k):
    d=diagnostics(np.ones(n),np.ones(n),np.ones(n),k)
    assert (d['AICc'] is None)==(n<=k+1)
    assert (d['reduced_chi_squared'] is None)==(n<=k)
    m=diagnostics(np.ones(n),np.ones(n),np.ones(n),k,'MAP')
    assert all(m[key] is None for key in ['AIC','AICc','BIC'])

@pytest.mark.parametrize('error',[0,-1,float('nan')])
def test_bad_uncertainty_no_exclusions(error):
    with pytest.raises(ValueError): diagnostics([1],[1],[error],0)
    c=synthetic();c.err[0]=error
    with pytest.raises(DomainError): c.validate()

@pytest.mark.parametrize('model,truth',[('nfw',[11,1]),('burkert',[7,math.log10(3)])])
def test_synthetic_halo_recovery_and_determinism(model,truth):
    c=synthetic(model); a=fit_curve(c,model,'MLE',CONFIG,GATE);b=fit_curve(c,model,'MLE',CONFIG,GATE)
    assert a['status']=='CONVERGED';np.testing.assert_allclose(a['parameters'],truth,atol=1e-5,rtol=0)
    assert a['parameters']==b['parameters'];assert all(s['success'] for s in a['attempts'])
    assert len(a['attempts'])==4

def test_synthetic_baryons_negative_control_and_misspecification():
    c=synthetic('baryons');r=fit_curve(c,'baryons','MLE',CONFIG,GATE)
    assert r['statistics']['chi_squared']<1e-20 and r['statistics']['k']==0
    halo=fit_curve(c,'nfw','MLE',CONFIG,GATE)
    assert r['statistics']['AIC']<halo['statistics']['AIC']
    c=synthetic('nfw');wrong=fit_curve(c,'baryons','MLE',CONFIG,GATE)
    assert wrong['statistics']['reduced_chi_squared']>100

def test_MAP_likelihood_separation_and_inactive_bulge():
    c=synthetic('nfw');c.obs=c.obs*1.08
    f=fit_curve(c,'nfw','MAP',CONFIG,GATE)
    s=f['statistics']; assert s['AICc'] is None and s['BIC'] is None
    assert s['optimization_objective']==pytest.approx(s['chi_squared']+s['prior_penalty'])
    assert s['prior_penalty']>0
    assert 'log10_upsilon_bulge' not in f['parameter_names']
    assert s['k']==5

def test_boundary_identifiability_and_masks():
    assert boundary_flags([0,.5],[[0,0],[1,1]])==[True,False]
    d=identifiability(np.ones((5,2)),[False,False]);assert d['rank']==1 and d['covariance'] is None
    c=synthetic('baryons'); a=fit_curve(c,'baryons','MLE',CONFIG,GATE);b=fit_curve(c,'rar','MLE',CONFIG,GATE)
    assert a['mask']==b['mask'] and a['mask_sha256']==b['mask_sha256']
    c.r[1]=c.r[0]
    with pytest.raises(DomainError): c.validate()

def test_optimizer_failure_not_success():
    c=synthetic();c.obs=c.obs*1.037
    f=fit_curve(c,'nfw','MLE',CONFIG,GATE,max_nfev=1)
    assert f['status']=='OPTIMIZER_FAILED' and not any(a['success'] for a in f['attempts'])

def test_domain_failure_is_explicit():
    c=synthetic();c.gas[:]=-100;c.disk[:]=0
    a=fit_curve(c,'baryons','MLE',CONFIG,GATE);b=fit_curve(c,'rar','MLE',CONFIG,GATE)
    assert a['status']==b['status']=='UNSUPPORTED_DOMAIN'
    assert a['excluded_points']==0 and len(a['invalid_indices'])==80

def test_inclination_density_normalization_jacobian():
    f=inclination_factor(60,50);obs=np.array([30.,50.]);err=np.array([2.,3.]);pred=np.array([32.,48.])
    fixed=diagnostics(obs,pred*f,err,0)['log_likelihood']
    transformed=diagnostics(obs/f,pred,err/f,0)['log_likelihood']
    assert fixed==pytest.approx(transformed-len(obs)*math.log(f))

@pytest.mark.parametrize('key,value',[('D',-1),('D',float('nan')),('e_D',-1),('e_D',float('nan')),('e_Inc',-1),('e_Inc',float('nan'))])
def test_invalid_geometry_metadata(key,value):
    c=synthetic();c.metadata[key]=value
    with pytest.raises(DomainError):c.validate()

def test_missing_geometry_metadata():
    c=synthetic();del c.metadata['e_D']
    with pytest.raises(DomainError):c.validate()

def test_list_arrays_normalized_and_inactive_components():
    c=synthetic();c.disk=[0.]*80;c.bulge=[0.]*80;c.validate()
    f=fit_curve(c,'baryons','MAP',CONFIG,GATE)
    assert 'log10_upsilon_disk' not in f['parameter_names']
    assert 'log10_upsilon_bulge' not in f['parameter_names']

def test_zero_geometry_uncertainty_fixed_parameters():
    c=synthetic();c.metadata['e_D']=0;c.metadata['e_Inc']=0
    f=fit_curve(c,'nfw','MAP',CONFIG,GATE)
    assert f['statistics']['k']==3
    assert 'distance_ratio' not in f['parameter_names'] and 'inclination_deg' not in f['parameter_names']
