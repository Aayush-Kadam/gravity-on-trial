"""Execute synthetic and source-reference checks without modifying M1 artifacts."""
import importlib.util,json,math,sys,time
from pathlib import Path
import psutil
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m2/v1';sys.path.insert(0,str(ROOT/'src'))
from gravity_on_trial.m1_inference import fit_curve
from gravity_on_trial.m1_physics import predict
from m2_worker import identity,load
spec=importlib.util.spec_from_file_location('m1_test_controls',ROOT/'tests/test_m1.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
cases=[]
for injected,fitted in [('baryons','baryons'),('baryons','nfw'),('nfw','nfw'),('burkert','burkert'),('nfw','baryons')]:
    curve=module.synthetic(injected);result=fit_curve(curve,fitted,'MLE',module.CONFIG,module.GATE)
    cases.append({'label':'SYNTHETIC IMPLEMENTATION CONTROL; not observed SPARC data','injected_model':injected,'fitted_model':fitted,'result':result})
for c in cases:
    if c['injected_model']==c['fitted_model']=='nfw':assert max(abs(x-y) for x,y in zip(c['result']['parameters'],[11,1]))<1e-5
    if c['injected_model']==c['fitted_model']=='burkert':assert max(abs(x-y) for x,y in zip(c['result']['parameters'],[7,math.log10(3)]))<1e-5
null=cases[0]['result']['statistics'];extra=cases[1]['result']['statistics'];wrong=cases[-1]['result']['statistics']
assert null['chi_squared']<1e-20 and null['AIC']<extra['AIC'] and wrong['reduced_chi_squared']>100
curve=load('NGC3198');prediction=predict(curve,'rar',ud=.77,d=10.4/curve.metadata['D'],inc=71.1)
factor=math.sin(math.radians(71.1))/math.sin(math.radians(curve.metadata['Inc']))
z=[((obs/factor)**2-(pred/factor)**2)/(2*(obs/factor)*(err/factor)) for obs,pred,err in zip(curve.obs,prediction,curve.err)]
reference={'source':'https://arxiv.org/html/1803.00022','galaxy':'NGC3198','published_rounded_values':{'ML_disk':.77,'D_Mpc':10.4,'i_deg':71.1,'reported_reduced_acceleration_chi_squared':2.057},'evaluated_reduced_acceleration_chi_squared':math.fsum(v*v for v in z)/(len(z)-3),'note':'Descriptive rounded-parameter check, not posterior replication; M2 optimizes a velocity-space likelihood.'}
(OUT/'synthetic_and_reference_controls.json').write_text(json.dumps({'identity':identity(),'synthetic_cases':cases,'reference':reference,'peak_working_set_MiB':psutil.Process().memory_info().peak_wset/2**20},indent=2,allow_nan=False));print('Synthetic and source-reference controls passed')
