"""Bounded serial dispatch with content-checked resume and stage gating."""
import json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m2/v1';CFG=json.loads((ROOT/'configs/m2_v1.json').read_text())
stage,replicate=sys.argv[1:];ids=CFG['pilot_ids'] if stage=='pilot' else CFG['population_ids']
if stage=='full':assert json.loads((OUT/'pilot_gate.json').read_text())['GO'],'Pilot gate not passed'
if stage not in ['pilot','full']:raise ValueError('Invalid stage')
started=time.perf_counter();completed=[]
for index in range(0,len(ids),CFG['batch_size']):
    batch=ids[index:index+CFG['batch_size']]
    command=[sys.executable,str(ROOT/'m2_monitor.py'),'batch',stage,replicate,*batch]
    result=subprocess.run(command)
    if result.returncode:
        (OUT/f'{stage}_{replicate}_dispatch.json').write_text(json.dumps({'complete':False,'completed_ids':completed,'stopped_batch':batch,'wall_seconds':time.perf_counter()-started},indent=2))
        sys.exit(result.returncode)
    completed+=batch
    (OUT/f'{stage}_{replicate}_dispatch.json').write_text(json.dumps({'complete':len(completed)==len(ids),'completed_ids':completed,'wall_seconds':time.perf_counter()-started},indent=2))
print(stage,replicate,'completed',len(completed),flush=True)
