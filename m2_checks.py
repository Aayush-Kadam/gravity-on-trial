"""Comparison/status unit checks, separate from the preserved 54 M1 tests."""
import copy,json
from pathlib import Path
from m2_compare import comparison,canonical,equivalent
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m2/v1'
data=json.loads((OUT/'pilot/initial/NGC3198.json').read_text());base=copy.deepcopy([r for r in data['results'] if r['mode']=='MLE'])
checks=[]
def reset():return copy.deepcopy(base)
r=reset()
for i,a in enumerate(r):a['statistics']['AICc']=10*i
assert comparison(r)['status']=='PREFERENCE';checks.append('Gap >=2 assigns only an eligible operational preference')
r[1]['statistics']['AICc']=1
assert comparison(r)['status']=='INCONCLUSIVE' and comparison(r)['winner'] is None;checks.append('Small gap has no winner')
r=reset();r[0]['status']='UNSUPPORTED_DOMAIN'
assert comparison(r)['winner'] is None;checks.append('Unsupported full-mask model invalidates four-way comparison')
r=reset();r[1]['boundary_flags']=[True,False]
assert comparison(r)['status']=='NO_VALID_COMPARISON';checks.append('Boundary solutions excluded from regular criteria ranking')
r=reset();r[2]['mask']=r[2]['mask'][:-1]
assert comparison(r)['winner'] is None;checks.append('Different radial masks cannot be ranked')
r=reset();r[1]['statistics']['AICc']=None
assert comparison(r)['winner'] is None;checks.append('Undefined AICc prevents a four-way winner')
assert comparison([a for a in data['results'] if a['mode']=='MAP'])['status']=='NO_VALID_COMPARISON';checks.append('MAP never enters MLE comparison')
equivalent(canonical(data),canonical({**data,'replicate':'another','resource':{'wall_seconds':100}}));checks.append('Canonical reproducibility ignores resource measurements only')
try:equivalent([1.],[1.1])
except AssertionError:checks.append('Canonical reproducibility detects scientific numerical differences')
else:raise AssertionError('Numerical mutation undetected')
r=reset();r[1]['data_identifiability']['rank']=1
assert comparison(r)['winner'] is None;checks.append('Data rank deficiency invalidates regular ranking')
(OUT/'comparison_unit_checks.json').write_text(json.dumps({'checks_passed':checks,'count':len(checks)},indent=2));print(len(checks),'comparison checks passed')
