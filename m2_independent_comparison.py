"""Independent AICc-gap/boundary audit; does not call comparison implementation."""
import collections,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m2/v1'
config=json.loads((ROOT/'configs/m2_v1.json').read_text());expected={c['galaxy']:c for c in json.loads((OUT/'comparison_records.json').read_text())};checks=[]
for galaxy in config['population_ids']:
    data=json.loads((OUT/f'full/initial/{galaxy}.json').read_text());f0=[r for r in data['results'] if r['mode']=='MLE']
    for family,roster in [('four_way',['baryons','nfw','burkert','rar']),('NFW_Burkert',['nfw','burkert'])]:
        selected=[r for r in f0 if r['model'] in roster];eligible=True;scores=[]
        for r in selected:
            if r['status']!='CONVERGED':eligible=False;continue
            n=len(data['observed_km_s']);k=len(r['parameters']);lo,hi=r['bounds']
            independently_on_boundary=any((p-l)/(h-l)<1e-5 or (h-p)/(h-l)<1e-5 for p,l,h in zip(r['parameters'],lo,hi))
            assert independently_on_boundary==any(r['boundary_flags'])
            if n<=k+1 or independently_on_boundary or r['data_identifiability']['rank']!=k or (k and (r['data_identifiability']['condition'] is None or r['data_identifiability']['condition']>1e8)):eligible=False;continue
            assert r['mask']==list(range(n))
            chi=math.fsum(((o-p)/e)**2 for o,p,e in zip(data['observed_km_s'],r['prediction_km_s'],data['error_km_s']))
            # Constant Gaussian normalization is identical across this same mask.
            scores.append((chi+2*k+2*k*(k+1)/(n-k-1),r['model']))
        target=expected[galaxy][family]
        if not eligible:assert target['status']=='NO_VALID_COMPARISON' and target['winner'] is None
        else:
            scores.sort();gap=scores[1][0]-scores[0][0];winner=scores[0][1] if gap>=2 else None
            assert winner==target['winner'] and target['status']==('PREFERENCE' if gap>=2 else 'INCONCLUSIVE')
            assert math.isclose(gap,target['gap'],rel_tol=1e-10,abs_tol=1e-10)
        checks.append({'galaxy':galaxy,'family':family,'pass':True})
(OUT/'independent_comparison_audit.json').write_text(json.dumps({'groups_checked':len(checks),'all_match':True,'method':'Independent scalar chi-square + parameter/sample correction; common normalization cancels only within identical data masks; independent bound-distance checks.','checks':checks},indent=2));print(len(checks),'independent comparison groups verified')
