"""Save explicit synthetic negative-control numerical outcomes, never SPARC evidence."""
import importlib.util,json,sys,time
from pathlib import Path
import psutil
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m1/v1';sys.path.insert(0,str(ROOT/'src'))
start=time.perf_counter();process=psutil.Process()
spec=importlib.util.spec_from_file_location('controls',ROOT/'tests/test_m1.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
from gravity_on_trial.m1_inference import fit_curve
cases=[]
for injected,fitted in [('baryons','baryons'),('baryons','nfw'),('nfw','nfw'),('burkert','burkert'),('nfw','baryons')]:
    curve=module.synthetic(injected);result=fit_curve(curve,fitted,'MLE',module.CONFIG,module.GATE)
    cases.append({'label':'SYNTHETIC IMPLEMENTATION CONTROL','injected_model':injected,'fitted_model':fitted,'observed_noiseless_synthetic_km_s':curve.obs.tolist(),'radius_kpc':curve.r.tolist(),'result':result})
(OUT/'synthetic_controls.json').write_text(json.dumps({'label':'SYNTHETIC; no empirical interpretation','seed':module.CONFIG['seed'],'generation':'Noise-free; no random draws; independent density quadrature for injected halos; fixed baryons','cases':cases,'peak_working_set_MiB':process.memory_info().peak_wset/2**20,'wall_seconds':time.perf_counter()-start},indent=2,allow_nan=False))
print('Saved synthetic control outputs')
