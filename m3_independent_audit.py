"""Independent scalar rankings and denominator/classification audit; no production metric calls."""
import collections,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m3/v1';CFG=json.loads((ROOT/'configs/m3_v1.json').read_text());ATLAS={m['galaxy']:m for m in json.loads((OUT/'atlas_metrics.json').read_text())}
checked=rankings=0;by_outcome=collections.Counter();diagnostics=[]
for galaxy in CFG['population_ids']:
    data=json.loads((OUT/f'full/initial/{galaxy}.json').read_text());base=data['baseline'];expected=collections.Counter();valid=0;null=0
    for scenario in data['scenarios']:
        if scenario['kind']!='physical':
            assert scenario['comparison']['winner'] is None and scenario['comparison']['status']=='NOT_A_LIKELIHOOD_COMPARISON';continue
        prop=scenario['proposal_status']
        if prop=='NOT_APPLICABLE':expected['not_applicable']+=1;null+=1;continue
        if prop=='INVALID_PROPOSAL':expected['invalid_proposal']+=1;continue
        eligible=True;scores=[]
        for r in scenario['results']:
            if r['status']!='CONVERGED':eligible=False;continue
            k=len(r['parameters']);n=data['n_inventory'];lo,hi=r['bounds'];on_bound=any(min(v-l,h-v)/(h-l)<1e-5 for v,l,h in zip(r['parameters'],lo,hi))
            assert on_bound==any(r['boundary_flags'])
            if on_bound or n<=k+1 or r['data_identifiability']['rank']!=k or k and (r['data_identifiability']['condition'] is None or r['data_identifiability']['condition']>1e8):eligible=False;continue
            assert r['accepted_mask']==list(range(n))
            chi=math.fsum(((v-o)/e)**2 for v,o,e in zip(r['prediction_km_s'],data['observed_km_s'],data['error_km_s']))
            scores.append((chi+2*k+2*k*(k+1)/(n-k-1),r['model']))
        if not eligible:status='NO_VALID_COMPARISON';winner=None
        else:
            scores.sort();gap=scores[1][0]-scores[0][0];winner=scores[0][1] if gap>=2 else None;status='PREFERENCE' if gap>=2 else 'INCONCLUSIVE';assert math.isclose(gap,scenario['comparison']['gap'],rel_tol=1e-10,abs_tol=1e-10)
        assert status==scenario['comparison']['status'] and winner==scenario['comparison']['winner'];rankings+=1
        if status=='NO_VALID_COMPARISON':expected['unavailable']+=1
        else:
            valid+=1
            if base['status']!='PREFERENCE':expected['emergent_decisive' if winner is not None else 'baseline_nondecisive_valid_inconclusive']+=1
            elif winner is None:expected['to_inconclusive']+=1
            elif winner==base['winner']:expected['retained']+=1
            else:expected['flipped']+=1
    atlas=ATLAS[galaxy];assert sum(expected.values())==12
    for key,count in atlas['counts'].items():assert count==(12 if key=='planned' else expected[key]),(galaxy,key)
    assert atlas['meaningful_scenarios']==12-null and atlas['valid_comparable_scenarios']==valid
    for label,t in [('primary',CFG['classification']),*[(t['id'],t) for t in CFG['classification_alternatives']]]:
        if base['status']=='NO_VALID_COMPARISON':result='UNASSESSABLE'
        elif base['status']=='INCONCLUSIVE':result='INCONCLUSIVE'
        elif valid<t['minimum_valid'] or valid/(12-null)<t['minimum_coverage']:result='UNASSESSABLE'
        elif expected['to_inconclusive']/valid>=t['inconclusive_fraction']:result='INCONCLUSIVE'
        elif expected['retained']/valid>=t['stable_persistence'] and expected['flipped']/valid<=t['maximum_stable_flip_fraction']:result='STABLE'
        else:result='SENSITIVE'
        assert result==(atlas['classification'] if label=='primary' else atlas['alternative_classifications'][label])
    if base['status']=='PREFERENCE':
        assert valid==expected['retained']+expected['flipped']+expected['to_inconclusive']
        assert atlas['persistence_fraction']==(expected['retained']/valid if valid else None)
        assert atlas['flip_fraction']==(expected['flipped']/valid if valid else None)
        by_outcome.update(expected)
    else:assert atlas['persistence_fraction'] is None and atlas['flip_fraction'] is None
    for model in CFG['models']:
        actual=[next(r for r in s['results'] if r['model']==model) for s in data['scenarios'] if s['kind']=='physical'];success=[r for r in actual if r['status']=='CONVERGED'];summary=atlas['model_summaries'][model]
        assert summary['boundary_n']==sum(any(r['boundary_flags']) for r in success) and summary['boundary_unknown_n']==12-null-len(success)
        assert summary['warning_n']==sum(bool(r['data_identifiability']['warnings']) for r in success)
    diagnostics.append({'galaxy':galaxy,'baseline_status':base['status'],'classification':atlas['classification'],'all_denominators_and_rules_match':True});checked+=1
(OUT/'independent_metric_audit.json').write_text(json.dumps({'galaxies_checked':checked,'independent_ranking_groups':rankings,'all_pass':True,'decisive_baseline_outcomes':dict(by_outcome),'records':diagnostics,'note':'Scalar chi-square/complexity gaps recomputed; shared normalization cancels only on identical catalog masks. Threshold labels and failure denominators independently applied.'},indent=2));print(checked,'galaxies independently audited')
