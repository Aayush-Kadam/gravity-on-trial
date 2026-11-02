"""Population tables from explicit inventory records; no successful-only denominator drift."""
import collections,csv,json,math,statistics
from pathlib import Path
from m2_compare import comparison
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m2/v1';CFG=json.loads((ROOT/'configs/m2_v1.json').read_text());GATE=json.loads((ROOT/'configs/gate0r.json').read_text())
FEATURES={c['ID']:c for c in json.loads((OUT/'inventory.json').read_text())['galaxies']}
def quantile(values,p):
    a=sorted(values)
    if not a:return None
    pos=(len(a)-1)*p;i=int(pos);return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(pos-i)
def distribution(values,total):
    a=[v for v in values if v is not None and math.isfinite(v)]
    return {'inventory_denominator':total,'valid_n':len(a),'undefined_or_unavailable_n':total-len(a),'median':quantile(a,.5),'p10':quantile(a,.1),'p90':quantile(a,.9),'min':min(a) if a else None,'max':max(a) if a else None}
def ranks(values):
    order=sorted(range(len(values)),key=lambda i:values[i]);result=[0.]*len(values);i=0
    while i<len(order):
        j=i+1
        while j<len(order) and values[order[j]]==values[order[i]]:j+=1
        for k in order[i:j]:result[k]=(i+j-1)/2
        i=j
    return result
def spearman(pairs):
    if len(pairs)<3:return None
    x=ranks([p[0] for p in pairs]);y=ranks([p[1] for p in pairs]);mx=statistics.mean(x);my=statistics.mean(y)
    denom=math.sqrt(sum((v-mx)**2 for v in x)*sum((v-my)**2 for v in y))
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/denom if denom else None

rows=[];comparisons=[];points=[];curves={};groups=collections.defaultdict(list);case_results=[]
for galaxy in CFG['population_ids']:
    data=json.loads((OUT/f'full/initial/{galaxy}.json').read_text());feature=FEATURES[galaxy];higher_quality=feature['Q']<=2 and feature['Inc']>=30
    comp={'galaxy':galaxy,'higher_quality':higher_quality,'four_way':comparison(data['results']),'NFW_Burkert':comparison(data['results'],('nfw','burkert'))};comparisons.append(comp)
    if galaxy in CFG['pilot_ids'][:5]+['UGC01281','F567-2','IC2574']:curves[galaxy]=data
    for r in data['results']:
        key=r['mode']+'_'+r['model'];groups[key].append((feature,r));s=r.get('statistics',{});ident=r.get('data_identifiability',{});names=r.get('parameter_names');bounds=r.get('bounds')
        if names is None:
            names=GATE.get(r['model']+'_parameter_order',[])[:];bounds=[b[:] for b in GATE.get(r['model']+'_bounds',[[],[]])]
            if r['mode']=='MAP':
                nuisance=[]
                if any(v!=0 for v in data['disk_unit_ML_km_s']):nuisance.append(('log10_upsilon_disk',math.log10(.05),math.log10(2)))
                if any(v!=0 for v in data['bulge_unit_ML_km_s']):nuisance.append(('log10_upsilon_bulge',math.log10(.05),math.log10(2)))
                sigma=feature['e_D']/feature['D']
                if sigma>0:nuisance.append(('distance_ratio',max(.1,1-3*sigma),1+3*sigma))
                if feature['e_Inc']>0:nuisance.append(('inclination_deg',max(1,feature['Inc']-3*feature['e_Inc']),min(90,feature['Inc']+3*feature['e_Inc'])))
                for name,lo,hi in nuisance:names.append(name);bounds[0].append(lo);bounds[1].append(hi)
        units={n:('dex(Msun)' if n=='log10_M200_Msun' else 'dex(Msun/kpc^3)' if n=='log10_rho0_Msun_kpc3' else 'dex(kpc)' if n=='log10_r0_kpc' else 'dex(dimensionless)' if n=='log10_c200' else 'dex(solar M/L at 3.6um)' if n.startswith('log10_upsilon') else 'degree' if n=='inclination_deg' else 'dimensionless') for n in names}
        row={'galaxy':galaxy,'quality':feature['Q'],'distance_Mpc':feature['D'],'distance_error_Mpc':feature['e_D'],'inclination_deg':feature['Inc'],'inclination_error_deg':feature['e_Inc'],'n_inventory':data['n_inventory'],'n_accepted':r['n_accepted'],'mode':r['mode'],'model':r['model'],'status':r['status'],'k_expected':len(names),'k_fitted':s.get('k'),'parameters_JSON':json.dumps(dict(zip(names,r.get('parameters',[])))) if 'parameters' in r else None,'parameter_units_JSON':json.dumps(units),'bounds_JSON':json.dumps(bounds),'chi_squared':s.get('chi_squared'),'dof':s.get('degrees_of_freedom'),'reduced_chi_squared':s.get('reduced_chi_squared'),'log_likelihood':s.get('log_likelihood'),'AIC':s.get('AIC'),'AICc':s.get('AICc'),'BIC':s.get('BIC'),'prior_penalty':s.get('prior_penalty'),'optimization_objective':s.get('optimization_objective'),'max_absolute_standardized_residual':s.get('max_absolute_standardized_residual'),'weighted_RMSE_km_s':s.get('weighted_RMSE_km_s'),'data_rank':ident.get('rank'),'data_condition':ident.get('condition'),'normalized_condition':r.get('scaled_sensitivity',{}).get('normalized_condition'),'identifiability_warning':bool(ident.get('warnings')) if r['status']=='CONVERGED' else None,'normalized_weak_direction':r.get('scaled_sensitivity',{}).get('weak_direction'),'warnings':'; '.join(ident.get('warnings',[])),'boundary_contact':any(r.get('boundary_flags',[])) if r['status']=='CONVERGED' else None,'domain_failed_start_count':sum(not s['success'] for s in r.get('attempts',[])),'accepted_mask_JSON':json.dumps(r['accepted_mask']),'attempted_mask_JSON':json.dumps(r['attempted_mask']),'invalid_indices_JSON':json.dumps(r['invalid_indices']),'data_file':f'full/initial/{galaxy}.json','content_revision':data['identity']['content_revision'],'config_ref':'configs/m2_v1.json + configs/m1_v1.json + configs/gate0r.json','wall_seconds':r['resource']['wall_seconds'],'RSS_after_MiB':r['resource']['RSS_after_MiB'],'process_lifetime_peak_so_far_MiB':r['resource']['process_lifetime_peak_so_far_MiB']}
        rows.append(row)
        if r['status']=='CONVERGED':
            for radius,z in zip(data['radius_kpc'],s['standardized_residuals']):points.append([galaxy,r['mode'],r['model'],radius/max(data['radius_kpc']),z])
    # Matched-data F0/F1 changes: residual comparison only, never penalized criteria.
    for m in CFG['models']:
        a=next(r for r in data['results'] if r['mode']=='MLE' and r['model']==m);b=next(r for r in data['results'] if r['mode']=='MAP' and r['model']==m)
        case_results.append({'galaxy':galaxy,'model':m,'F0_status':a['status'],'F1_status':b['status'],'F0_data_chi_squared':a.get('statistics',{}).get('chi_squared'),'F1_data_chi_squared_at_MAP':b.get('statistics',{}).get('chi_squared'),'F1_prior_penalty':b.get('statistics',{}).get('prior_penalty'),'F0_halo_parameters':a.get('parameters',[])[:2] if m in ['nfw','burkert'] else [],'F1_halo_parameters':b.get('parameters',[])[:2] if m in ['nfw','burkert'] else [],'note':'Changed nuisance assumptions; not an ML likelihood-ratio test or posterior evidence ranking'})
summary={};parameter_distributions={}
for key,entries in groups.items():
    success=[r for _,r in entries if r['status']=='CONVERGED']
    summary[key]={'inventory_denominator':175,'status_counts':dict(collections.Counter(r['status'] for _,r in entries)),'successful_n':len(success),'warning_n':sum(bool(r['data_identifiability']['warnings']) for r in success),'boundary_n':sum(any(r['boundary_flags']) for r in success),'normalized_weak_n':sum(r['scaled_sensitivity']['weak_direction'] for r in success),'local_covariance_available_n':sum(r['statistics']['k']>0 and r['data_identifiability']['covariance'] is not None for r in success),'local_covariance_not_applicable_n':sum(r['statistics']['k']==0 for r in success),'chi_squared':distribution([r.get('statistics',{}).get('chi_squared') for _,r in entries],175),'reduced_chi_squared':distribution([r.get('statistics',{}).get('reduced_chi_squared') for _,r in entries],175),'neighbor_residual_correlation':distribution([r.get('statistics',{}).get('neighbor_residual_correlation') for _,r in entries],175),'data_condition':distribution([r.get('data_identifiability',{}).get('condition') for _,r in entries],175)}
    names=sorted({name for r in success for name in r['parameter_names']})
    parameter_distributions[key]={}
    for name in names:
        present=[r for r in success if name in r['parameter_names']];values=[r['parameters'][r['parameter_names'].index(name)] for r in present]
        se=[r['data_identifiability']['standard_errors'][r['parameter_names'].index(name)] for r in present if r['data_identifiability']['standard_errors'] is not None]
        parameter_distributions[key][name]={'optimization_coordinate_values':distribution(values,175),'local_known_error_standard_errors':distribution(se,175),'parameter_present_in_successful_n':len(present),'not_present_or_failed_n':175-len(present),'interpretation':'Absent bulge/fixed-zero-error geometry means parameter deliberately not fitted; covariance may be withheld. Log-coordinate errors are not credible intervals.'}
preference={}
for sample in ['all_inventory','higher_quality']:
    chosen=[c for c in comparisons if sample=='all_inventory' or c['higher_quality']]
    preference[sample]={'galaxy_denominator':len(chosen)}
    for family in ['four_way','NFW_Burkert']:
        counts=collections.Counter(c[family]['status'] for c in chosen);winners=collections.Counter(c[family]['winner'] for c in chosen if c[family]['winner'])
        preference[sample][family]={'status_counts':dict(counts),'preference_counts':dict(winners),'eligible_n':sum(c[family]['status']!='NO_VALID_COMPARISON' for c in chosen),'inconclusive_n':counts['INCONCLUSIVE'],'unavailable_n':counts['NO_VALID_COMPARISON']}
explore=[]
properties=['L36','SBdisk','gas_to_light_proxy','T','Inc','n','radius_max_kpc','Q']
for key,entries in groups.items():
    for metric in ['reduced_chi_squared','neighbor_residual_correlation']:
        for prop in properties:
            pairs=[(c[prop],r['statistics'][metric]) for c,r in entries if r['status']=='CONVERGED' and r['statistics'][metric] is not None]
            explore.append({'group':key,'metric':metric,'property':prop,'valid_pair_n':len(pairs),'inventory_denominator':175,'Spearman_rho_descriptive':spearman(pairs),'p_value':None,'interpretation':'Exploratory association; multiple comparisons, no causal or significance claim'})
    for prop in properties:
        pairs=[(c[prop],int(bool(r.get('data_identifiability',{}).get('warnings')))) for c,r in entries if r['status']=='CONVERGED']
        explore.append({'group':key,'metric':'warning_indicator','property':prop,'valid_pair_n':len(pairs),'inventory_denominator':175,'Spearman_rho_descriptive':spearman(pairs),'p_value':None,'interpretation':'Warnings among successful cases; failure count remains separate; not causal'})
nuisance_summary={}
for model in CFG['models']:
    matched=[c for c in case_results if c['model']==model and c['F0_status']==c['F1_status']=='CONVERGED']
    ratios=[c['F1_data_chi_squared_at_MAP']/c['F0_data_chi_squared'] for c in matched if c['F0_data_chi_squared']>0]
    nuisance_summary[model]={'inventory_denominator':175,'matched_successful_n':len(matched),'data_chi_squared_ratio_F1_to_F0':distribution(ratios,175),'halo_log_parameter_absolute_shifts':[distribution([abs(c['F1_halo_parameters'][i]-c['F0_halo_parameters'][i]) for c in matched],175) for i in range(2)] if model in ['nfw','burkert'] else None,'interpretation':'Paired residual changes at MAP under changed assumptions, not ML evidence or a calibrated hypothesis test'}
for name,obj in [('population_summary.json',{'groups':summary,'preferences':preference,'galaxy_count':175,'radial_count':3391,'negative_gas_rows':361}),('parameter_distributions.json',parameter_distributions),('comparison_records.json',comparisons),('exploratory_associations.json',explore),('nuisance_changes.json',case_results),('nuisance_stability_summary.json',nuisance_summary),('figure_data.json',{'evaluation_rows':rows,'residual_points':points,'selected_curves':curves,'comparisons':comparisons,'features':FEATURES})]:
    (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False))
with (OUT/'evaluation_inventory.csv').open('w',newline='',encoding='utf-8') as f:
    writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
with (OUT/'population_groups.csv').open('w',newline='',encoding='utf-8') as f:
    records=[{'group':k,'inventory_denominator':v['inventory_denominator'],'success_n':v['successful_n'],'warning_n':v['warning_n'],'boundary_n':v['boundary_n'],'local_covariance_available_n':v['local_covariance_available_n'],'median_reduced_chi_squared':v['reduced_chi_squared']['median'],'valid_reduced_chi_squared_n':v['reduced_chi_squared']['valid_n']} for k,v in summary.items()]
    writer=csv.DictWriter(f,fieldnames=records[0]);writer.writeheader();writer.writerows(records)
print(json.dumps({'evaluations':len(rows),'residual_points':len(points),'preferences':preference}))
