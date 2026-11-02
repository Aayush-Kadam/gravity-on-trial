"""Prespecified matched-mask F0 comparison rules; no MAP evidence ranking."""
def comparison(results,models=('baryons','nfw','burkert','rar')):
    selected=[r for r in results if r['mode']=='MLE' and r['model'] in models]
    reasons=[]
    if len(selected)!=len(models):reasons.append('missing_model_record')
    for r in selected:
        if r['status']!='CONVERGED':reasons.append(r['model']+':'+r['status']);continue
        s=r['statistics'];ident=r['data_identifiability']
        if s['AICc'] is None:reasons.append(r['model']+':undefined_AICc')
        if any(r['boundary_flags']):reasons.append(r['model']+':boundary')
        if ident['rank']!=s['k']:reasons.append(r['model']+':rank_deficient')
        if s['k'] and (ident['condition'] is None or ident['condition']>1e8):reasons.append(r['model']+':ill_conditioned')
    masks=[r.get('mask') for r in selected]
    if any(mask!=masks[0] for mask in masks[1:]):reasons.append('mismatched_data_masks')
    if reasons:return {'status':'NO_VALID_COMPARISON','winner':None,'reasons':reasons,'models':list(models)}
    ordered=sorted(selected,key=lambda r:(r['statistics']['AICc'],r['model']));gap=ordered[1]['statistics']['AICc']-ordered[0]['statistics']['AICc']
    return {'status':'PREFERENCE' if gap>=2 else 'INCONCLUSIVE','winner':ordered[0]['model'] if gap>=2 else None,'gap':gap,'ordered_scores':[(r['model'],r['statistics']['AICc']) for r in ordered],'models':list(models),'reasons':[]}

def canonical(result):
    """Discard only nondeterministic measurements; preserve diagnostics/masks."""
    if isinstance(result,dict):return {k:canonical(v) for k,v in result.items() if k not in ['resource','wall_seconds','replicate','stage','complete']}
    if isinstance(result,list):return [canonical(v) for v in result]
    return result

def equivalent(a,b,path='root'):
    import math
    if isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool):
        if not math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10):raise AssertionError((path,a,b))
    elif isinstance(a,dict):
        if a.keys()!=b.keys():raise AssertionError((path,'keys'))
        for key in a:equivalent(a[key],b[key],path+'.'+key)
    elif isinstance(a,list):
        if len(a)!=len(b):raise AssertionError((path,'length'))
        for i,(x,y) in enumerate(zip(a,b)):equivalent(x,y,path+f'[{i}]')
    elif a!=b:raise AssertionError((path,a,b))
