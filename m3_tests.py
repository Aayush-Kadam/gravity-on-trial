"""M3-specific controls, run alongside the unchanged 54 M1 tests."""
import copy,importlib.util,json,math
from pathlib import Path
import numpy as np
import pytest
from scipy.integrate import quad
from scipy.stats import norm
from m1_worker import load
from m3_science import scenario_spec,computation_view,fit_fixed,fit_prior_width
from m3_metrics import galaxy_metrics,category,compare_score
ROOT=Path(__file__).resolve().parent;CFG=json.loads((ROOT/'configs/m3_v1.json').read_text());M1=json.loads((ROOT/'configs/m1_v1.json').read_text());GATE=json.loads((ROOT/'configs/gate0r.json').read_text());SC={s['id']:s for s in CFG['scenarios']}
spec=importlib.util.spec_from_file_location('synthetic_source',ROOT/'tests/test_m1.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

@pytest.mark.parametrize('model',['baryons','nfw','burkert','rar'])
@pytest.mark.parametrize('scenario',['ML_joint_plus01dex','distance_plus1sigma','inclination_minus1sigma'])
def test_derived_view_matches_explicit_catalog_prediction(model,scenario):
    from gravity_on_trial.m1_physics import predict
    curve=old.synthetic();before=[a.copy() for a in [curve.r,curve.obs,curve.err,curve.gas,curve.disk,curve.bulge]];s=scenario_spec(curve,SC[scenario]);view,f=computation_view(curve,s);p=[11,1] if model=='nfw' else [7,math.log10(3)]
    expected=predict(curve,model,p if model in ['nfw','burkert'] else [],ud=s['upsilon_disk'],ub=s['upsilon_bulge'],d=s['distance_ratio'],inc=s['inclination_deg'])
    computed=predict(view,model,p if model in ['nfw','burkert'] else [])*f
    np.testing.assert_allclose(computed,expected,rtol=1e-12,atol=1e-12)
    for a,b in zip(before,[curve.r,curve.obs,curve.err,curve.gas,curve.disk,curve.bulge]):np.testing.assert_array_equal(a,b)

@pytest.mark.parametrize('model,truth',[('nfw',[11,1]),('burkert',[7,math.log10(3)])])
def test_independent_injected_geometry_recovery(model,truth):
    curve=old.synthetic(model);d=1.2;i=53.;ud=.5*10**.1;factor=math.sin(math.radians(i))/math.sin(math.radians(curve.metadata['Inc']));r=curve.r*d
    if model=='nfw':
        mass,c=1e11,10.;R=(4.30091e-6*mass/(100*.073**2))**(1/3);scale=R/c;normf=math.log1p(c)-c/(1+c)
        enclosed=[mass*quad(lambda t:t/(1+t)**2,0,float(radius/scale),epsabs=1e-25,epsrel=1e-12)[0]/normf for radius in r]
    else:enclosed=[4*math.pi*1e7*3**3*quad(lambda t:t*t/((1+t)*(1+t*t)),0,float(radius/3),epsabs=1e-25,epsrel=1e-12)[0] for radius in r]
    curve.obs=np.sqrt(d*(ud*curve.disk**2+curve.gas*np.abs(curve.gas))+4.30091e-6*np.array(enclosed)/r)*factor
    s={'upsilon_disk':ud,'upsilon_bulge':.7,'distance_ratio':d,'inclination_deg':i}
    result=fit_fixed(curve,model,s,M1,GATE);assert result['status']=='CONVERGED';np.testing.assert_allclose(result['parameters'],truth,atol=1e-5,rtol=0)

def test_catalog_normalized_likelihood_and_signed_gas():
    c=old.synthetic();c.gas[0]=-3.;s={'upsilon_disk':.5,'upsilon_bulge':.7,'distance_ratio':1.2,'inclination_deg':50.}
    result=fit_fixed(c,'rar',s,M1,GATE);expected=sum(norm.logpdf(c.obs,loc=result['prediction_km_s'],scale=c.err))
    assert result['statistics']['log_likelihood']==pytest.approx(expected,rel=1e-12)
    view,_=computation_view(c,s);assert view.gas[0]<0
    assert result['geometry_check']['equivalent_prediction_relative_error']<1e-9

def test_invalid_geometry_proposals_are_not_clipped():
    c=old.synthetic();c.metadata['e_D']=2*c.metadata['D']
    assert scenario_spec(c,SC['distance_minus1sigma'])['proposal_status']=='INVALID_PROPOSAL'
    c.metadata['Inc']=90
    assert scenario_spec(c,SC['inclination_plus1sigma'])['proposal_status']=='INVALID_PROPOSAL'

def test_null_component_perturbations_are_not_persistence_trials():
    c=old.synthetic();assert np.all(c.bulge==0)
    assert scenario_spec(c,SC['ML_bulge_plus01dex'])['proposal_status']=='NOT_APPLICABLE'
    c.metadata['e_D']=c.metadata['e_Inc']=0
    assert scenario_spec(c,SC['joint_geometry_minus1sigma'])['proposal_status']=='NOT_APPLICABLE'

@pytest.mark.parametrize('galaxy',['NGC3198','DDO154','NGC2841'])
@pytest.mark.parametrize('model',['baryons','nfw','burkert','rar'])
def test_fiducial_prior_adapter_reproduces_M2(galaxy,model):
    c=load(galaxy);r=fit_prior_width(c,model,.1,M1,GATE);base=json.loads((ROOT/f'results/m2/v1/full/initial/{galaxy}.json').read_text());oldr=next(a for a in base['results'] if a['model']==model and a['mode']=='MAP')
    assert r['status']==oldr['status']=='CONVERGED'
    np.testing.assert_allclose(r['parameters'],oldr['parameters'],rtol=1e-10,atol=1e-10)
    np.testing.assert_allclose(r['prediction_km_s'],oldr['prediction_km_s'],rtol=1e-10,atol=1e-10)
    assert r['statistics']['prior_penalty']==pytest.approx(oldr['statistics']['prior_penalty'],rel=1e-10,abs=1e-10)

def test_prior_changes_only_declared_widths_and_no_MLE_criteria():
    c=old.synthetic();a=fit_prior_width(c,'nfw',.05,M1,GATE);b=fit_prior_width(c,'nfw',.2,M1,GATE);again=fit_prior_width(c,'nfw',.2,M1,GATE)
    assert a['bounds']==b['bounds'] and [s['start'] for s in a['attempts']]==[s['start'] for s in b['attempts']]
    assert b['parameters']==again['parameters']
    assert all(b['statistics'][k] is None for k in ['AIC','AICc','BIC'])
    assert b['all_nuisance_prior_sigmas'][0]==.2 and a['all_nuisance_prior_sigmas'][0]==.05
    assert b['all_nuisance_prior_sigmas'][1:]==a['all_nuisance_prior_sigmas'][1:]
    with pytest.raises(ValueError):fit_prior_width(c,'nfw',0,M1,GATE)

BASE={'status':'PREFERENCE','winner':'nfw'}
def scenarios(outcomes):
    result=[]
    for i,outcome in enumerate(outcomes):
        status='APPLICABLE';comp={'status':'PREFERENCE','winner':'nfw'}
        if outcome=='flip':comp['winner']='burkert'
        if outcome=='inconclusive':comp={'status':'INCONCLUSIVE','winner':None}
        if outcome=='unavailable':comp={'status':'NO_VALID_COMPARISON','winner':None}
        if outcome=='invalid':status='INVALID_PROPOSAL'
        if outcome=='null':status='NOT_APPLICABLE'
        result.append({'scenario_id':str(i),'family':'TEST','proposal_status':status,'comparison':comp})
    return result

@pytest.mark.parametrize('outcomes,expected',[( ['retain']*8+['flip']+['inconclusive']+['unavailable']*2,'STABLE'),(['retain']*7+['flip']*2+['inconclusive']+['unavailable']*2,'SENSITIVE'),(['retain']*5+['inconclusive']*5+['unavailable']*2,'INCONCLUSIVE'),(['retain']*5+['invalid']*7,'UNASSESSABLE')])
def test_operational_classifications(outcomes,expected):
    r=galaxy_metrics(BASE,scenarios(outcomes),CFG['classification']);assert r['classification']==expected
    assert r['counts']['retained']+r['counts']['flipped']+r['counts']['to_inconclusive']==r['valid_comparable_scenarios']

def test_nulls_and_invalids_have_explicit_different_denominators():
    r=galaxy_metrics(BASE,scenarios(['retain']*6+['null']*2+['invalid']*4),CFG['classification'])
    assert r['counts']['planned']==12 and r['meaningful_scenarios']==10 and r['valid_comparable_scenarios']==6
    assert r['coverage']==.6 and r['persistence_fraction']==1 and r['retained_over_all_meaningful']==.6

@pytest.mark.parametrize('status,classification',[('INCONCLUSIVE','INCONCLUSIVE'),('NO_VALID_COMPARISON','UNASSESSABLE')])
def test_nondecisive_baselines_do_not_get_invented_flips(status,classification):
    r=galaxy_metrics({'status':status,'winner':None},scenarios(['flip']*12),CFG['classification'])
    assert r['classification']==classification and r['persistence_fraction'] is None and r['flip_fraction'] is None
    assert r['counts']['emergent_decisive']==12

def test_statistical_choices_share_eligibility_and_MAP_is_excluded():
    data=json.loads((ROOT/'results/m2/v1/full/initial/NGC3198.json').read_text())
    for stat in ['AIC','AICc','BIC']:assert compare_score(data['results'],stat)['status']!='NO_VALID_COMPARISON'
    assert compare_score([r for r in data['results'] if r['mode']=='MAP'],'BIC')['status']=='NO_VALID_COMPARISON'
