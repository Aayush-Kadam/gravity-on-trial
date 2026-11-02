"""Test safe completed-batch reuse and identity-mismatch refusal without altering fits."""
import hashlib,json,time
from pathlib import Path
import m2_worker as worker
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m2/v1';CFG=json.loads((ROOT/'configs/m2_v1.json').read_text());ids=CFG['population_ids'][:5]
paths=[OUT/f'full/initial/{g}.json' for g in ids]
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
original=worker.identity
worker.identity=lambda:{**original(),'content_revision':'intentional_identity_mismatch_test'}
refused=False
try:worker.batch('full','initial',ids)
except AssertionError as error:
    assert 'identity' in str(error).lower();refused=True
finally:worker.identity=original
assert refused
def no_recompute(*args,**kwargs):raise AssertionError('Resume unexpectedly recomputed an existing fit')
worker.evaluate=no_recompute
start=time.perf_counter();result=worker.batch('full','initial',ids)
after={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};assert before==after and result['completed']==ids
(OUT/'resume_check.json').write_text(json.dumps({'galaxies':ids,'all_per_galaxy_bytes_unchanged':True,'no_evaluation_function_called':True,'mismatched_identity_refused':refused,'resume_seconds_excluding_import':time.perf_counter()-start},indent=2));print('Completed-batch resume and mismatch refusal passed')
