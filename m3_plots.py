"""Static scientific atlas from saved arrays; no fits, synthetic observations or UI."""
import collections,gc,json,math,textwrap,time
from pathlib import Path
import psutil
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m3/v1';FIG=OUT/'figures';FIG.mkdir(exist_ok=True)
P=psutil.Process();START=time.perf_counter()
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
CFG=json.loads((ROOT/'configs/m3_v1.json').read_text());DATA=json.loads((OUT/'plot_data.json').read_text());METRICS=DATA['metrics'];ROWS=DATA['scenario_rows'];MODELS=CFG['models'];COLORS={'baryons':'#668438','nfw':'#2365A4','burkert':'#C98117','rar':'#A43C70'};STYLE={'baryons':':','nfw':'-','burkert':'--','rar':'-.'};CLASSES=['STABLE','SENSITIVE','INCONCLUSIVE','UNASSESSABLE'];CC={'STABLE':'#2365A4','SENSITIVE':'#C98117','INCONCLUSIVE':'#D8BC77','UNASSESSABLE':'#BBBBBB'}
rendered=[]
def save(fig,name,note):
    fig.get_layout_engine().set(rect=(0,.115,1,.885));width=int(fig.get_figwidth()*15)
    text=textwrap.fill('Source: SPARC, Lelli, McGaugh & Schombert (2016); frozen M3-v1 saved numerical results.',width)+'\n'+textwrap.fill(note,width)
    fig.text(.035,.02,text,fontsize=8,va='bottom');fig.savefig(FIG/(name+'.png'),dpi=130);fig.savefig(FIG/(name+'.svg'));fig.clear();plt.close(fig);gc.collect();rendered.append(name)

# Five readable pages preserve all 175 IDs rather than tiny decorative labels.
for page in range(5):
    chosen=METRICS[page*35:(page+1)*35];values=np.array([[m['model_preference_fractions'][model] if m['model_preference_fractions'][model] is not None else np.nan for model in MODELS] for m in chosen]);fig,ax=plt.subplots(figsize=(8.5,13),layout='constrained')
    cmap=plt.get_cmap('Blues').copy();cmap.set_bad('#DDDDDD');im=ax.imshow(np.ma.masked_invalid(values),aspect='auto',vmin=0,vmax=1,cmap=cmap)
    labels=[m['galaxy']+' ['+{'PREFERENCE':'P','INCONCLUSIVE':'I','NO_VALID_COMPARISON':'U'}[m['baseline_status']]+f"; n={m['valid_comparable_scenarios']}]" for m in chosen]
    ax.set_yticks(range(len(chosen)),labels,fontsize=8);ax.set_xticks(range(4),['Baryons','NFW','Burkert','Empirical RAR']);ax.set(xlabel='Preferred model in valid physical scenarios',ylabel='Galaxy [M2 baseline P/I/U; valid scenario count]',title=f'Operational preference matrix — page {page+1}/5, 35/175 galaxies')
    for i in range(len(chosen)):
        for j in range(4):ax.text(j,i,'NA' if np.isnan(values[i,j]) else f'{values[i,j]:.2f}',ha='center',va='center',fontsize=7,color='white' if values[i,j]>.6 else 'black')
    fig.colorbar(im,ax=ax,fraction=.04,pad=.03,label='Fraction of valid scenarios preferring model')
    save(fig,f'01_preference_matrix_page{page+1}','12 named physical scenarios; nulls excluded, invalid/unavailable counted separately. Valid denominator includes inconclusive, so rows may sum below one. Gray NA is unavailable, not zero. Fractions are not theory probabilities.')

OUTCOME=['retained','flipped','to_inconclusive','unavailable','invalid_proposal','not_applicable'];OC=['#2365A4','#C98117','#D8BC77','#999999','#A43C70','#EEEEEE'];OL=['Retained','Different decisive preference','To inconclusive','Unavailable comparison','Invalid physical proposal','Not applicable']
for name,prefixes,title in [('02_stellar_mass_sensitivity',['ML_'],'Stellar mass-to-light stress cases (+/-0.1 dex)'),('03_distance_sensitivity',['distance_','joint_geometry_'],'Catalog distance stress cases (+/-1 sigma)'),('04_inclination_sensitivity',['inclination_','joint_geometry_'],'Catalog inclination stress cases (+/-1 sigma)')]:
    ids=[s['id'] for s in CFG['scenarios'] if s['kind']=='physical' and any(s['id'].startswith(p) for p in prefixes)];fig,ax=plt.subplots(figsize=(12,6),layout='constrained');left=np.zeros(len(ids))
    for outcome,color,label in zip(OUTCOME,OC,OL):
        counts=np.array([sum(r['scenario_id']==sid and r['baseline_status']=='PREFERENCE' and r['transition']==outcome for r in ROWS) for sid in ids]);ax.barh(ids,counts,left=left,color=color,label=label,hatch='//' if outcome=='not_applicable' else None,edgecolor='white',linewidth=.3);left+=counts
    assert np.all(left==107)
    ax.set(xlabel='Galaxy outcomes out of 107 decisive M2 baselines per scenario',xlim=(0,107),title=title);ax.legend(fontsize=7,loc='lower center',bbox_to_anchor=(.5,1.02),ncol=3)
    save(fig,name,'Same source observations/errors and unchanged halo bounds. Joint-geometry rows also appear in the other geometry figure and must not be added. Null/invalid/unavailable outcomes do not support persistence.')

fig,axes=plt.subplots(2,2,figsize=(11,7),layout='constrained');fields=[('nfw','log10_M200_Msun','NFW log10 M200 (dex in solar masses)'),('nfw','log10_c200','NFW log10 concentration (dex)'),('burkert','log10_rho0_Msun_kpc3','Burkert log10 density (dex in Msun/kpc³)'),('burkert','log10_r0_kpc','Burkert log10 core radius (dex in kpc)')]
for ax,(model,parameter,label) in zip(axes.flat,fields):
    values=[m['model_summaries'][model]['parameters'][parameter]['range'] for m in METRICS if m['model_summaries'][model]['parameters'][parameter]['range'] is not None];ax.hist(values,bins=25,color=COLORS[model],edgecolor='white');ax.set(xlabel='Scenario range: '+label,ylabel='Galaxies',title=f'Finite ranges n={len(values)}/175')
fig.suptitle('Physical-parameter stability across the fixed stress design')
save(fig,'05_parameter_stability','Ranges use converged physical scenarios, with valid counts/failures in the atlas table. They are not posterior intervals. A small range at a bound or along a weak likelihood does not prove a precise parameter.')

for name,field,title in [('06_identifiability_frequency','warning','Identifiability diagnostics across physical scenarios'),('07_boundary_sensitivity','boundary','Parameter-bound contacts across physical scenarios')]:
    fig,ax=plt.subplots(figsize=(10,5),layout='constrained');positive=[];negative=[];unknown=[]
    for model in MODELS:
        p=sum(m['model_summaries'][model][field+'_n'] for m in METRICS);u=sum(m['model_summaries'][model][field+'_unknown_n'] for m in METRICS);meaningful=sum(m['model_summaries'][model]['meaningful'] for m in METRICS);positive.append(p);unknown.append(u);negative.append(meaningful-p-u)
    ax.bar(MODELS,positive,color='#2365A4',label='Flag present');ax.bar(MODELS,negative,bottom=positive,color='#B7D0E5',label='Successful, no such flag');ax.bar(MODELS,unknown,bottom=np.array(positive)+negative,color='#999999',hatch='//',label='Invalid / failed / unassessed')
    ax.set(ylabel='Meaningful model-scenario slots (null perturbations excluded)',title=title);ax.legend(fontsize=8)
    save(fig,name,'All 175 galaxies retained. Unknown states are not assessed negatives; denominators/counts are explicit in atlas_metrics.json. Baryons/RAR have no fitted halo parameters. These are operational frequencies, not probabilities.')

fig,ax=plt.subplots(figsize=(11,6),layout='constrained');sample_names=CFG['sample_definitions'];left=np.zeros(5)
for category in CLASSES:
    counts=np.array([DATA['quality'][s]['fragility_classes'].get(category,0) for s in sample_names]);ax.barh(sample_names,counts,left=left,color=CC[category],label=category);left+=counts
ax.set(xlabel='Galaxies in catalog-defined population',title='Quality-cut composition changes: individual classifications unchanged');ax.legend(fontsize=8,ncol=2)
save(fig,'08_quality_composition','Cuts use original catalog Q/inclination, not perturbed membership. Population composition changes are never counted as individual preference flips. The complete 175-galaxy inventory remains available.')

fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained');all_counts=DATA['summary']['primary_classification_counts'];decisive_counts=DATA['summary']['decisive_baseline_classification_counts']
for ax,counts,n,title in [(axes[0],all_counts,175,'All original galaxies'),(axes[1],decisive_counts,107,'Decisive M2 baselines only')]:
    values=[counts.get(c,0) for c in CLASSES];bars=ax.bar(CLASSES,values,color=[CC[c] for c in CLASSES]);ax.bar_label(bars);ax.set(ylabel='Galaxies',title=title+f' (n={n})');ax.tick_params(axis='x',rotation=20)
fig.suptitle('Frozen operational fragility categories')
save(fig,'09_stable_sensitive_populations','Baseline unavailable cases are automatically UNASSESSABLE; baseline inconclusive cases remain INCONCLUSIVE. Category thresholds are design choices. Continuous persistence, flip and coverage metrics accompany every label.')

fig,ax=plt.subplots(figsize=(11,5),layout='constrained');experiments=['primary','lenient','strict'];left=np.zeros(3)
for category in CLASSES:
    values=[]
    for exp in experiments:values.append(sum((m['classification'] if exp=='primary' else m['alternative_classifications'][exp])==category for m in METRICS if m['baseline_status']=='PREFERENCE'))
    ax.barh(experiments,values,left=left,color=CC[category],label=category);left+=values
assert np.all(left==107);ax.set(xlabel='Galaxies out of 107 decisive baselines',title='Classification sensitivity to preregistered threshold choices');ax.legend(fontsize=8,ncol=2)
save(fig,'10_threshold_sensitivity','Same numerical results; only separately frozen classification thresholds differ. No alternative replaces the primary labels. Differences measure definition sensitivity, not sampling uncertainty.')

prior=json.loads((OUT/'prior_sensitivity.json').read_text());fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained',sharex=True,sharey=True)
for ax,width in zip(axes,[.05,.2]):
    for model in MODELS:
        values=sorted(r['data_chi_squared']/r['baseline_MAP_data_chi_squared'] for r in prior if r['model']==model and r['width_dex']==width and r['status']==r['baseline_MAP_status']=='CONVERGED' and r['baseline_MAP_data_chi_squared']>0)
        ax.step(values,np.arange(1,len(values)+1)/len(values),where='post',color=COLORS[model],linestyle=STYLE[model],label=model.upper()+f' n={len(values)}/175')
    ax.axvline(1,color='black',lw=.6);ax.set_xscale('symlog',linthresh=.01);ax.set(xlabel='Data chi-square ratio to fiducial 0.1-dex MAP',title=f'Stellar prior width {width} dex');ax.legend(fontsize=7);ax.grid(alpha=.2)
axes[0].set_ylabel('Fraction of successful paired cases');fig.suptitle('Prior strength changes: data residuals, not evidence rankings')
save(fig,'11_prior_strength','Same stellar centers, geometry priors, physical bounds and initializations. MAP prior penalties are separate, and no AIC/BIC ranking is assigned. The data-likelihood ridge does not disappear when priors narrow.')

fig,ax=plt.subplots(figsize=(11,5),layout='constrained');categories=MODELS+['INCONCLUSIVE','NO_VALID_COMPARISON'];colors=[COLORS[m] for m in MODELS]+['#D8BC77','#BBBBBB'];left=np.zeros(3)
stats=DATA['statistical'];baseline_AICc={m['galaxy']:{'status':m['baseline_status'],'winner':m['baseline_winner']} for m in METRICS}
for cat,color in zip(categories,colors):
    values=[]
    for stat in ['AICc','AIC','BIC']:
        results=list(baseline_AICc.values()) if stat=='AICc' else [r['alternative'] for r in stats[stat]['baseline_records']]
        values.append(sum((r.get('winner') or r['status'])==cat for r in results))
    ax.barh(['AICc','AIC','BIC'],values,left=left,color=color,label=cat);left+=values
assert np.all(left==175);ax.set(xlabel='Galaxies out of 175',title='Statistical criterion sensitivity on identical eligible masks');ax.legend(fontsize=7,ncol=3)
save(fig,'12_statistical_criteria','MLE only, same common eligibility and operational gap>=2. Criteria are complexity approximations, not theory probabilities. MAP prior experiments are excluded.')

# Frozen before/after selection: original five + domain case, then first case per category.
chosen=['NGC3198','NGC2403','NGC3741','DDO154','NGC2841','UGC01281']
for category in CLASSES:
    cases=sorted(m['galaxy'] for m in METRICS if m['classification']==category)
    if cases and cases[0] not in chosen:chosen.append(cases[0])
curve_selection=[]
for galaxy in chosen:
    data=json.loads((OUT/f'full/initial/{galaxy}.json').read_text());base={r['model']:r for r in data['baseline_results'] if r['mode']=='MLE'};candidates=[]
    for s in data['scenarios']:
        if s['kind']!='physical' or s['comparison']['status'] not in ['PREFERENCE','INCONCLUSIVE']:continue
        changes=[abs(p-q) for r in s['results'] if r['status']=='CONVERGED' and base[r['model']]['status']=='CONVERGED' for p,q in zip(r['prediction_km_s'],base[r['model']]['prediction_km_s'])]
        if changes:candidates.append((max(changes),s['scenario_id'],s))
    selected=max(candidates,key=lambda x:(x[0],x[1]))[2] if candidates else next(s for s in data['scenarios'] if s['kind']=='physical' and s['proposal_status']=='APPLICABLE')
    curve_selection.append({'galaxy':galaxy,'scenario_id':selected['scenario_id'],'selection':'Largest max absolute prediction change among valid physical comparisons' if candidates else 'No valid comparison; first applicable scenario shown for context only'})
    fig,axes=plt.subplots(3,2,figsize=(12,9),layout='constrained',sharex=True,gridspec_kw={'height_ratios':[3,1,1]});radii=data['radius_catalog_kpc']
    for col,records,title in [(0,list(base.values()),'Frozen M2 F0 baseline'),(1,selected['results'],selected['scenario_id'])]:
        ax,res,zoom=axes[:,col];ax.errorbar(radii,data['observed_km_s'],yerr=data['error_km_s'],fmt='k.',markersize=3,label='SPARC observed ± catalog error');ax.plot(radii,data['gas_signed_km_s'],':',color='gray',label='Published signed gas convention');invalid=[]
        for rr in records:
            model=rr['model']
            if rr['status']!='CONVERGED':invalid.append(model+': '+rr['status']);continue
            ax.plot(radii,rr['prediction_km_s'],color=COLORS[model],linestyle=STYLE[model],label=model.upper());z=rr['statistics']['standardized_residuals'];res.plot(radii,z,color=COLORS[model],linestyle=STYLE[model])
            if model!='baryons':zoom.plot(radii,z,color=COLORS[model],linestyle=STYLE[model])
        if invalid:ax.text(.02,.02,'\n'.join(invalid),transform=ax.transAxes,fontsize=6)
        ax.set(title=title,ylabel='Catalog-frame speed / gas convention (km/s)');ax.legend(fontsize=6);res.set_ylabel('All residuals / sigma');zoom.set(ylabel='Halo/RAR residuals / sigma',xlabel='Catalog radius (kpc)')
        for a in [ax,res,zoom]:a.grid(alpha=.2)
        for a in [res,zoom]:a.axhline(0,color='black',lw=.5)
    fig.suptitle(f"{galaxy}, n={data['n_inventory']}, Q={data['metadata']['Q']} — before/after selected stress case")
    save(fig,'galaxy_'+galaxy,'Identical original observations/errors, no hidden point deletion. After-case selection is a frozen maximum-change rule, not a typical-case claim. Curves are published-component model predictions; unsupported curves remain explicitly labeled.')
save_path=OUT/'figure_selection.json';save_path.write_text(json.dumps(curve_selection,indent=2))
from PIL import Image,ImageDraw
sheet=Image.new('RGB',(1200,340*((len(rendered)+2)//3)),'white');draw=ImageDraw.Draw(sheet)
for i,name in enumerate(rendered):
    with Image.open(FIG/(name+'.png')) as im:im.thumbnail((395,310));sheet.paste(im,(400*(i%3),340*(i//3)+22))
    draw.text((400*(i%3)+3,340*(i//3)+3),name,fill='black')
sheet.save(FIG/'contact_sheet.png');(OUT/'figure_manifest.json').write_text(json.dumps({'figures':rendered,'count':len(rendered),'source':'plot_data.json; atlas_metrics.json; scenario raw arrays','wall_seconds':time.perf_counter()-START,'peak_working_set_MiB':P.memory_info().peak_wset/2**20},indent=2));print(len(rendered),'figures generated')
