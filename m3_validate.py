"""Full-inventory validation using scalar likelihood, prior and force checks."""
import collections,hashlib,json,math,sys
from pathlib import Path
from m2_compare import canonical,equivalent
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m3/v1';CFG=json.loads((ROOT/'configs/m3_v1.json').read_text());stage=sys.argv[1]
ids=CFG['pilot_ids'] if stage=='pilot' else CFG['population_ids'];SC={s['id']:s for s in CFG['scenarios']};statuses=collections.Counter();proposal=collections.Counter();comparison=collections.Counter();starts=collections.Counter();raw={g:[] for g in CFG['population_ids']}
for line in (ROOT/'data/raw/MassModels_Lelli2016c.mrt').read_text().splitlines():
    t=line.split()
    if t and t[0] in raw:raw[t[0]].append([float(x) for x in t[1:]])
maxp=maxv=0;reproduced=[];revisions=set();evaluated=0;warnings=boundaries=0;likelihoods=0;manual_forces=0
for g in ids:
    data=json.loads((OUT/f'{stage}/initial/{g}.json').read_text());revisions.add(data['identity']['content_revision']);assert data['complete'] and len(data['scenarios'])==14 and len(raw[g])==data['n_inventory']
    for index,row in enumerate(raw[g]):
        for j,key in enumerate(['radius_catalog_kpc','observed_km_s','error_km_s','gas_signed_km_s','disk_unit_ML_km_s','bulge_unit_ML_km_s'],1):assert row[j]==data[key][index]
    for s in data['scenarios']:
        assert len(s['results'])==4;proposal[s['proposal_status']]+=1;comparison[s['comparison']['status']]+=1
        if s['kind']=='physical':
            spec=s['spec'];assert spec['upsilon_disk']>0 and spec['upsilon_bulge']>0
            design=SC[s['scenario_id']];meta=data['metadata'];expected_d=1+design['distance_sigma']*meta['e_D']/meta['D'];expected_i=meta['Inc']+design['inclination_sigma']*meta['e_Inc']
            assert spec['upsilon_disk']==.5*10**design['disk_dex'] and spec['upsilon_bulge']==.7*10**design['bulge_dex']
            assert spec['distance_ratio']==expected_d and spec['inclination_deg']==expected_i
            changed=(design['disk_dex']!=0 and any(v!=0 for v in data['disk_unit_ML_km_s'])) or (design['bulge_dex']!=0 and any(v!=0 for v in data['bulge_unit_ML_km_s'])) or (design['distance_sigma']!=0 and meta['e_D']!=0) or (design['inclination_sigma']!=0 and meta['e_Inc']!=0)
            expected_proposal='INVALID_PROPOSAL' if expected_d<=0 or not 0<expected_i<=90 else 'APPLICABLE' if changed else 'NOT_APPLICABLE'
            assert s['proposal_status']==expected_proposal
            if expected_proposal!='APPLICABLE':assert all(r['status']==expected_proposal for r in s['results'])
            if s['proposal_status']=='APPLICABLE':assert spec['distance_ratio']>0 and 0<spec['inclination_deg']<=90
        for r in s['results']:
            statuses[r['status']]+=1
            if r['status'] in ['NOT_APPLICABLE','INVALID_PROPOSAL']:assert not r['accepted_mask'];continue
            evaluated+=1
            for a in r.get('attempts',[]):starts['converged' if a['success'] else 'failed']+=1
            if r['status']=='DIAGNOSTIC_FAILURE':raise AssertionError(('Unresolved diagnostic error',g,s['scenario_id'],r['message']))
            if r['status']!='CONVERGED':continue
            n=data['n_inventory'];k=len(r['parameters']);assert r['accepted_mask']==list(range(n)) and r['attempted_mask']==r['accepted_mask'];stats=r['statistics']
            pred=r['prediction_km_s'];assert len(pred)==n and all(math.isfinite(v) and v>=0 for v in pred)
            z=[(p-o)/e for p,o,e in zip(pred,data['observed_km_s'],data['error_km_s'])];chi=math.fsum(v*v for v in z);logl=-.5*(chi+math.fsum(math.log(2*math.pi*e*e) for e in data['error_km_s']))
            assert math.isclose(chi,stats['chi_squared'],rel_tol=1e-10,abs_tol=1e-8) and math.isclose(logl,stats['log_likelihood'],rel_tol=1e-10,abs_tol=1e-8)
            assert stats['n']==n and stats['k']==k and (stats['reduced_chi_squared'] is None)==(n<=k)
            lo,hi=r['bounds'];expected_bounds=[min(p-l,h-p)/(h-l)<1e-5 for p,l,h in zip(r['parameters'],lo,hi)];assert expected_bounds==r['boundary_flags'];assert all(l-1e-10<=p<=h+1e-10 for p,l,h in zip(r['parameters'],lo,hi))
            warnings+=bool(r['data_identifiability']['warnings']);boundaries+=any(r['boundary_flags']);likelihoods+=1
            if r['mode']=='MLE':
                assert math.isclose(stats['AIC'],2*k-2*logl,rel_tol=1e-10,abs_tol=1e-8)
                assert math.isclose(stats['BIC'],k*math.log(n)-2*logl,rel_tol=1e-10,abs_tol=1e-8)
                if n>k+1:assert math.isclose(stats['AICc'],2*k-2*logl+2*k*(k+1)/(n-k-1),rel_tol=1e-10,abs_tol=1e-8)
                else:assert stats['AICc'] is None
                if r['model'] in ['baryons','rar']:
                    f=math.sin(math.radians(spec['inclination_deg']))/math.sin(math.radians(data['metadata']['Inc']))
                    for i in range(n):
                        vgas=data['gas_signed_km_s'][i];v2=spec['distance_ratio']*math.fsum([spec['upsilon_disk']*data['disk_unit_ML_km_s'][i]**2,spec['upsilon_bulge']*data['bulge_unit_ML_km_s'][i]**2,math.copysign(vgas*vgas,vgas)])
                        if r['model']=='baryons':expected=math.sqrt(v2)*f
                        else:
                            radius=data['radius_catalog_kpc'][i]*spec['distance_ratio']*3.085677581491367e19;gb=v2*1e6/radius;expected=math.sqrt(gb/(-math.expm1(-math.sqrt(gb/1.2e-10)))*radius)/1000*f
                        assert math.isclose(pred[i],expected,rel_tol=1e-9,abs_tol=1e-9);manual_forces+=1
            else:
                assert all(stats[key] is None for key in ['AIC','AICc','BIC'])
                p=dict(zip(r['parameter_names'],r['parameters']));penalty=0
                for name,value in p.items():
                    if name.startswith('log10_upsilon'):center=math.log10(.5 if 'disk' in name else .7);sigma=s['spec']['ML_prior_sigma_dex']
                    elif name=='distance_ratio':center=1.;sigma=data['metadata']['e_D']/data['metadata']['D']
                    elif name=='inclination_deg':center=data['metadata']['Inc'];sigma=data['metadata']['e_Inc']
                    else:continue
                    penalty+=((value-center)/sigma)**2
                assert math.isclose(penalty,stats['prior_penalty'],rel_tol=1e-10,abs_tol=1e-8)
                assert math.isclose(stats['optimization_objective'],chi+penalty,rel_tol=1e-10,abs_tol=1e-8)
            if r['model'] in ['nfw','burkert']:assert r['independent_halo_check']['all_radii_quadrature_relative_error']<1e-9 and r['independent_halo_check']['n']==n
    path=OUT/f'{stage}/rerun/{g}.json'
    if path.exists():
        repeat=json.loads(path.read_text());equivalent(canonical(data),canonical(repeat));reproduced.append(g)
        for a,b in zip(data['scenarios'],repeat['scenarios']):
            for x,y in zip(a['results'],b['results']):
                if x['status']=='CONVERGED':maxp=max(maxp,max((abs(p-q) for p,q in zip(x['parameters'],y['parameters'])),default=0));maxv=max(maxv,max(abs(p-q) for p,q in zip(x['prediction_km_s'],y['prediction_km_s'])))
assert len(revisions)==1
for path,digest in data['identity']['files'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
result={'stage':stage,'galaxies':len(ids),'planned_scenario_records':len(ids)*14,'planned_model_slots':len(ids)*56,'scenario_proposal_counts':dict(proposal),'model_slot_status_counts':dict(statuses),'actual_evaluated_model_slots':evaluated,'comparison_status_counts':dict(comparison),'optimizer_start_counts':dict(starts),'warning_evaluations':warnings,'boundary_evaluations':boundaries,'scalar_likelihood_checks':likelihoods,'scalar_baryons_RAR_point_checks':manual_forces,'fresh_process_rerun_galaxies':len(reproduced),'rerun_ids':reproduced,'max_parameter_rerun_difference':maxp,'max_prediction_rerun_difference_km_s':maxv,'source_identity':next(iter(revisions))}
(OUT/f'{stage}_validation.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rerun_ids'}))
