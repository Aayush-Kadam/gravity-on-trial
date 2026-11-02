"""Independent saved-output audit and fresh-process comparison for M2."""
import collections,hashlib,json,math,sys
from pathlib import Path
from m2_compare import canonical,equivalent,comparison
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m2/v1';CFG=json.loads((ROOT/'configs/m2_v1.json').read_text())
stage=sys.argv[1] if len(sys.argv)>1 else 'full';ids=CFG['population_ids'] if stage=='full' else CFG['pilot_ids']
statuses=collections.Counter();starts=collections.Counter();quality=collections.Counter();nrad=negative=0;records=[];sourceidentity=set();weak=boundary=undefined=0
raw={g:[] for g in CFG['population_ids']}
for line in (ROOT/'data/raw/MassModels_Lelli2016c.mrt').read_text().splitlines():
    values=line.split()
    if values and values[0] in raw:raw[values[0]].append([float(v) for v in values[1:]])
for g in ids:
    a=json.loads((OUT/f'{stage}/initial/{g}.json').read_text());sourceidentity.add(a['identity']['content_revision'])
    assert a['complete'] and len(a['results'])==8 and len(raw[g])==a['n_inventory']
    nrad+=a['n_inventory'];negative+=sum(v<0 for v in a['gas_signed_km_s']);quality[str(a['metadata']['Q'])]+=1
    # Independent token parse versus production fixed-width loader at every real radius.
    for i,row in enumerate(raw[g]):
        for j,key in enumerate(['radius_kpc','observed_km_s','error_km_s','gas_signed_km_s','disk_unit_ML_km_s','bulge_unit_ML_km_s'],1):assert row[j]==a[key][i]
    assert {(r['model'],r['mode']) for r in a['results']}=={(m,mode) for m in CFG['models'] for mode in CFG['modes']}
    for r in a['results']:
        statuses[r['status']]+=1
        for start in r.get('attempts',[]):starts['converged' if start['success'] else 'failed']+=1
        if r['status']=='DIAGNOSTIC_FAILURE':raise AssertionError(('unresolved diagnostic error',g,r['message']))
        if r['status']=='CONVERGED':
            s=r['statistics'];pred=r['prediction_km_s'];err=a['error_km_s'];obs=a['observed_km_s'];z=[(p-o)/e for p,o,e in zip(pred,obs,err)]
            chi=math.fsum(v*v for v in z);logl=-.5*(chi+math.fsum(math.log(2*math.pi*e*e) for e in err))
            assert math.isclose(chi,s['chi_squared'],rel_tol=1e-12,abs_tol=1e-9)
            assert math.isclose(logl,s['log_likelihood'],rel_tol=1e-12,abs_tol=1e-8)
            assert r['accepted_mask']==list(range(a['n_inventory'])) and r['attempted_mask']==r['accepted_mask']
            assert s['n']==len(z) and s['k']==len(r['parameter_names'])
            if r['mode']=='MLE':
                assert math.isclose(s['AIC'],2*s['k']-2*logl,rel_tol=1e-12,abs_tol=1e-8)
                assert math.isclose(s['BIC'],s['k']*math.log(s['n'])-2*logl,rel_tol=1e-12,abs_tol=1e-8)
                if s['n']>s['k']+1:assert math.isclose(s['AICc'],2*s['k']-2*logl+2*s['k']*(s['k']+1)/(s['n']-s['k']-1),rel_tol=1e-12,abs_tol=1e-8)
                else:assert s['AICc'] is None
            else:
                assert all(s[k] is None for k in ['AIC','AICc','BIC'])
                assert math.isclose(s['optimization_objective'],chi+s['prior_penalty'],rel_tol=1e-12,abs_tol=1e-8)
            assert (s['reduced_chi_squared'] is None)==(s['n']<=s['k'])
            weak+=bool(r['data_identifiability']['warnings']);boundary+=any(r['boundary_flags']);undefined+=s['reduced_chi_squared'] is None
            if r['model'] in ['nfw','burkert']:assert r['independent_halo_check']['all_radii_quadrature_relative_error']<1e-9
        else:assert not r['accepted_mask'] or r['status']=='OPTIMIZER_FAILED'
    records.append({'galaxy':g,'four_way':comparison(a['results']),'NFW_Burkert':comparison(a['results'],('nfw','burkert'))})
assert len(sourceidentity)==1
for p,digest in a['identity']['files'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==digest
rerunids=ids if all((OUT/f'{stage}/rerun/{g}.json').exists() for g in ids) else [g for g in CFG['fallback_rerun_ids'] if (OUT/f'{stage}/rerun/{g}.json').exists()]
rerun=[]
for g in rerunids:
    a=json.loads((OUT/f'{stage}/initial/{g}.json').read_text());b=json.loads((OUT/f'{stage}/rerun/{g}.json').read_text());equivalent(canonical(a),canonical(b));rerun.append(g)
result={'stage':stage,'galaxies':len(ids),'radial_measurements':nrad,'negative_gas_rows':negative,'quality_counts':dict(quality),'evaluations':sum(statuses.values()),'statuses':dict(statuses),'optimizer_start_counts':dict(starts),'warning_evaluations':weak,'boundary_evaluations':boundary,'undefined_reduced_chi_squared':undefined,'fresh_process_rerun_count':len(rerun),'fresh_process_rerun_ids':rerun,'full_fresh_process_rerun':len(rerun)==len(ids),'all_radii_raw_token_checks_passed':True,'independent_likelihood_statistics_checks_passed':True,'source_identity':next(iter(sourceidentity)),'comparisons':records}
(OUT/f'{stage}_validation.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['comparisons','fresh_process_rerun_ids']}))
