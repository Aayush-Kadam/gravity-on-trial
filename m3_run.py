"""Bounded serial M3 dispatch; complete pilot gate required before full execution."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m3/v1';CFG=json.loads((ROOT/'configs/m3_v1.json').read_text())
stage,replicate=sys.argv[1:];assert stage in ['pilot','full']
if stage=='full':assert json.loads((OUT/'pilot_gate.json').read_text())['GO']
ids=CFG['pilot_ids'] if stage=='pilot' else CFG['population_ids'];begun=time.perf_counter();complete=[];cached=[];verified_identity=None
dispatch_path=OUT/f'{stage}_{replicate}_dispatch.json';previous=json.loads(dispatch_path.read_text()) if dispatch_path.exists() else {};prior_seconds=previous.get('wall_seconds',0) if not previous.get('complete') else 0
for offset in range(0,len(ids),CFG['batch_size']):
    batch=ids[offset:offset+CFG['batch_size']]
    paths=[OUT/stage/replicate/(g+'.json') for g in batch]
    if all(p.exists() for p in paths):
        existing=[json.loads(p.read_text()) for p in paths]
        if verified_identity is None:
            verified_identity=existing[0]['identity']
            assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in verified_identity['files'].items()),'Resume source identity changed'
        assert all(d['complete'] and len(d['scenarios'])==14 and d['identity']==verified_identity for d in existing),'Invalid cached batch'
        complete+=batch;cached+=batch
        dispatch_path.write_text(json.dumps({'complete':len(complete)==len(ids),'completed_ids':complete,'cached_ids_without_recomputation':cached,'wall_seconds':prior_seconds+time.perf_counter()-begun,'timing_scope':'Active dispatcher segments, excluding manual interruption time'},indent=2))
        continue
    result=subprocess.run([sys.executable,str(ROOT/'m3_monitor.py'),'batch',stage,replicate,*batch])
    record={'complete':False,'completed_ids':complete,'last_batch':batch,'wall_seconds':prior_seconds+time.perf_counter()-begun,'return_code':result.returncode,'cached_ids_without_recomputation':cached,'timing_scope':'Active dispatcher segments, excluding manual interruption time'}
    if result.returncode:
        (OUT/f'{stage}_{replicate}_dispatch.json').write_text(json.dumps(record,indent=2));sys.exit(result.returncode)
    complete+=batch;record.update(complete=len(complete)==len(ids),completed_ids=complete)
    (OUT/f'{stage}_{replicate}_dispatch.json').write_text(json.dumps(record,indent=2))
print(stage,replicate,'completed',len(complete))
