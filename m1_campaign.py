"""Serial M1 eight-galaxy comparison; preserve completed checkpoints, stop on failure."""
import json,math,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m1/v1'
config=json.loads((ROOT/'configs/m1_v1.json').read_text());completed=[]
for galaxy in config['galaxies']:
    for replicate in ['initial','rerun']:
        path=OUT/f'{galaxy}_{replicate}.json'
        if not path.exists() or not json.loads(path.read_text()).get('complete'):
            result=subprocess.run([sys.executable,str(ROOT/'m1_monitor.py'),'real',galaxy,replicate])
            if result.returncode: sys.exit(result.returncode)
    a=json.loads((OUT/f'{galaxy}_initial.json').read_text());b=json.loads((OUT/f'{galaxy}_rerun.json').read_text())
    if a['identity']!=b['identity']: raise ValueError('Implementation/config/data identity differs between reruns')
    checks=[]
    for x,y in zip(a['results'],b['results'],strict=True):
        assert x['status']==y['status']
        if x['status']=='CONVERGED':
            maxdiff={}
            for field in ['parameters','prediction_km_s']:
                assert len(x[field])==len(y[field])
                maxdiff[field]=max((abs(i-j) for i,j in zip(x[field],y[field])),default=0)
                assert all(math.isclose(i,j,rel_tol=1e-10,abs_tol=1e-10) for i,j in zip(x[field],y[field])),field
            assert math.isclose(x['statistics']['chi_squared'],y['statistics']['chi_squared'],rel_tol=1e-10,abs_tol=1e-10)
            checks.append({'model':x['model'],'mode':x['mode'],'status':x['status'],'maximum_absolute_rerun_differences':maxdiff})
        else: checks.append({'model':x['model'],'mode':x['mode'],'status':x['status']})
    completed.append({'galaxy':galaxy,'comparisons':checks})
    (OUT/'campaign_reproducibility.json').write_text(json.dumps({'galaxies':completed,'complete':len(completed)==len(config['galaxies'])},indent=2))
print('M1 bounded galaxy campaign completed')
