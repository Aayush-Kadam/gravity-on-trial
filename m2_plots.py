"""Standalone population figures from saved real numerical evidence only."""
import collections,gc,json,math,textwrap,time
from pathlib import Path
import psutil
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m2/v1';FIG=OUT/'figures';FIG.mkdir(exist_ok=True)
START=time.perf_counter();P=psutil.Process()
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
DATA=json.loads((OUT/'figure_data.json').read_text());SUMMARY=json.loads((OUT/'population_summary.json').read_text());ROWS=DATA['evaluation_rows'];MODELS=['baryons','nfw','burkert','rar'];MODES=['MLE','MAP']
COLORS={'baryons':'#668438','nfw':'#2365A4','burkert':'#C98117','rar':'#A43C70'};STYLES={'baryons':':','nfw':'-','burkert':'--','rar':'-.'}
rendered=[]
def save(fig,name,note):
    fig.get_layout_engine().set(rect=(0,.115,1,.885))
    width=int(fig.get_figwidth()*15)
    footer=textwrap.fill('Source: SPARC, Lelli, McGaugh & Schombert (2016); frozen M2-v1 numerical outputs.',width)+'\n'+textwrap.fill(note,width)
    fig.text(.035,.025,footer,fontsize=8,va='bottom')
    fig.savefig(FIG/(name+'.png'),dpi=120);fig.savefig(FIG/(name+'.svg'));fig.clear();plt.close(fig);gc.collect();rendered.append(name)
def selected(mode,model):return [r for r in ROWS if r['mode']==mode and r['model']==model]
def ecdf(ax,values,label,model):
    values=np.sort(values);ax.step(values,np.arange(1,len(values)+1)/len(values),where='post',label=label,color=COLORS[model],linestyle=STYLES[model])

fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
statuses=['CONVERGED','UNSUPPORTED_DOMAIN','NO_VALID_START','OPTIMIZER_FAILED','DIAGNOSTIC_FAILURE'];statuscolors=['#2365A4','#C98117','#A43C70','#555555','#111111']
for ax,mode in zip(axes,MODES):
    left=np.zeros(4)
    for status,color in zip(statuses,statuscolors):
        counts=np.array([sum(r['status']==status for r in selected(mode,m)) for m in MODELS]);ax.barh(MODELS,counts,left=left,color=color,label=status.replace('_',' ').title());left+=counts
    ax.set(xlabel='Galaxy evaluations (175 per model)',title='F0 / MLE' if mode=='MLE' else 'F1 / MAP',xlim=(0,180))
axes[1].legend(fontsize=7,loc='lower right');fig.suptitle('Complete evaluation accounting: 1,400 initial records')
save(fig,'01_evaluation_status','No failed/domain cases removed from denominators. No-valid-start means no feasible converged trajectory under the frozen starts, not no physical solution.')

for field,name,title in [('chi_squared','02_chi_squared_distribution','Data chi-squared distributions'),('reduced_chi_squared','03_reduced_chi_squared_distribution','Reduced chi-squared where defined')]:
    fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained',sharey=True,sharex=True)
    for ax,mode in zip(axes,MODES):
        for model in MODELS:
            values=[r[field] for r in selected(mode,model) if r['status']=='CONVERGED' and r[field] is not None]
            ecdf(ax,values,f'{model.upper()} n={len(values)}/175',model)
        ax.set(xscale='log',xlabel=field.replace('_',' ')+' (dimensionless)',title='F0 / MLE' if mode=='MLE' else 'F1 / MAP: data statistic only');ax.legend(fontsize=8);ax.grid(alpha=.2)
    axes[0].set_ylabel('Fraction of defined successful evaluations');fig.suptitle(title)
    save(fig,name,'Conditional distributions: legends give valid n out of 175 per model. F1 priors excluded from data chi-square; differing k affects reduced chi-square. No theory probabilities.')

by={(r['galaxy'],r['mode'],r['model']):r for r in ROWS}
fig,ax=plt.subplots(figsize=(7,6),layout='constrained');x=[];y=[];flag=[]
for g in DATA['features']:
    a=by[g,'MLE','nfw'];b=by[g,'MLE','burkert']
    if a['status']=='CONVERGED' and b['status']=='CONVERGED' and a['reduced_chi_squared'] is not None and b['reduced_chi_squared'] is not None:
        x.append(a['reduced_chi_squared']);y.append(b['reduced_chi_squared']);flag.append(a['boundary_contact'] or b['boundary_contact'])
x=np.array(x);y=np.array(y);flag=np.array(flag)
ax.scatter(x[~flag],y[~flag],s=20,color=COLORS['nfw'],label=f'No boundary n={sum(~flag)}');ax.scatter(x[flag],y[flag],s=28,facecolors='none',edgecolors='#888888',marker='s',label=f'Boundary caution n={sum(flag)}')
lo=min(min(x),min(y))*.8;hi=max(max(x),max(y))*1.2;ax.plot([lo,hi],[lo,hi],':',color='black');ax.set(xscale='log',yscale='log',xlabel='NFW reduced chi-square (dimensionless)',ylabel='Burkert reduced chi-square (dimensionless)',title=f'F0 matched full-mask halo fits, n={len(x)} / 175');ax.legend(fontsize=8);ax.grid(alpha=.2)
save(fig,'04_nfw_burkert','Below equality: Burkert has lower reduced chi-square. Boundary cases shown, not used as regular AICc evidence. Fit quality is not cosmological truth.')

fig,ax=plt.subplots(figsize=(7,6),layout='constrained');x=[];y=[]
for g in DATA['features']:
    rows=[by[g,'MLE',m] for m in ['nfw','burkert','rar']]
    if all(r['status']=='CONVERGED' for r in rows):x.append(rows[2]['chi_squared']);y.append(min(rows[0]['chi_squared'],rows[1]['chi_squared']))
lo=min(x+y)*.8;hi=max(x+y)*1.2;ax.scatter(x,y,s=20,color=COLORS['rar']);ax.plot([lo,hi],[lo,hi],':',color='black');ax.set(xscale='log',yscale='log',xlabel='Fixed empirical RAR data chi-square',ylabel='Lower data chi-square of NFW / Burkert',title=f'F0 empirical RAR versus fitted halos, n={len(x)} / 175');ax.grid(alpha=.2)
save(fig,'05_rar_diagnostics','RAR has k=0; each halo has k=2. This is descriptive residual quality, not complexity-adjusted evidence. Only common full-mask converged cases shown.')

fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained',sharex=True,sharey=True)
for ax,mode in zip(axes,MODES):
    for model in MODELS:
        values=[p[4] for p in DATA['residual_points'] if p[1]==mode and p[2]==model];ecdf(ax,values,f'{model.upper()} radial n={len(values)}',model)
    ax.set_xscale('symlog',linthresh=3);ax.axvline(0,color='black',lw=.5);ax.set(xlabel='(model − observation) / catalog sigma',title='F0 / MLE' if mode=='MLE' else 'F1 / MAP');ax.legend(fontsize=7);ax.grid(alpha=.2)
axes[0].set_ylabel('Cumulative fraction of valid residual points');fig.suptitle('Point-weighted standardized residual distributions')
save(fig,'06_residual_distributions','All valid residual values retained, including tails; symmetric-log x scale. Galaxies with more rings contribute more points. Neighboring errors may be correlated.')

fig,ax=plt.subplots(figsize=(10,5),layout='constrained');labels=[];values=[];unknown=[]
for mode in MODES:
    for model in MODELS:
        rows=selected(mode,model);labels.append(('F0 ' if mode=='MLE' else 'F1 ')+model.upper());values.append(sum(bool(r['boundary_contact']) for r in rows));unknown.append(sum(r['status']!='CONVERGED' for r in rows))
positions=np.arange(8);ax.bar(positions,values,color='#2365A4',label='Bound-contact solution');ax.bar(positions,unknown,bottom=values,color='#888888',hatch='//',label='No converged solution; boundary not assessed')
for i,(v,u) in enumerate(zip(values,unknown)):ax.text(i,v+u+1,str(v),ha='center',fontsize=8)
ax.set_xticks(positions,labels,rotation=30,ha='right');ax.set(ylabel='Evaluations out of 175 per model/configuration',ylim=(0,175),title='Boundary contacts retained as scientific cautions');ax.legend(fontsize=8)
save(fig,'07_parameter_boundaries','Numbers label bound-contact counts, not probabilities. Gray hatched counts are unassessed failures/domain cases. Bounds/priors were frozen before population fitting.')

fig,ax=plt.subplots(figsize=(10,5),layout='constrained');legacy=[];normalized=[]
for mode in MODES:
    for model in MODELS:
        rows=selected(mode,model);legacy.append(sum(bool(r['identifiability_warning']) for r in rows));normalized.append(sum(bool(r['normalized_weak_direction']) for r in rows))
ax.bar(positions-.18,legacy,.36,color='#2365A4',label='Any M1 identifiability warning');ax.bar(positions+.18,normalized,.36,color='#C98117',hatch='//',label='Column-normalized weak direction')
ax.set_xticks(positions,labels,rotation=30,ha='right');ax.set(ylabel='Warning-bearing evaluations / 175',ylim=(0,175),title='Identifiability: physical degeneracy and local diagnostics');ax.legend(fontsize=8)
save(fig,'08_identifiability','Categories overlap and must not be added. F1 data likelihood has an exact geometry ridge; prior curvature is not independent data information. Failures remain separate.')

fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained');categories=['baryons','nfw','burkert','rar','INCONCLUSIVE','NO_VALID_COMPARISON'];markers=['o','s','^','D','x','+'];categorycolors=[COLORS[m] for m in MODELS]+['#777777','#AAAAAA']
for ax,prop,xlabel,log in zip(axes.flat,['L36','SBdisk','gas_to_light_proxy','Inc'],['3.6-micron luminosity (10^9 solar luminosities)','Disk central surface brightness (solar luminosities / pc²)','Catalog HI mass / 3.6-micron luminosity (solar units)','Catalog inclination (degrees)'],[True,True,True,False]):
    for index,category in enumerate(categories):
        ids=[c['galaxy'] for c in DATA['comparisons'] if (c['four_way']['winner'] or c['four_way']['status'])==category]
        ax.scatter([DATA['features'][g][prop] for g in ids],[index]*len(ids),s=17,marker=markers[index],color=categorycolors[index])
    ax.set_yticks(range(6),['Baryons','NFW','Burkert','RAR','Inconclusive','No valid comparison']);ax.set_xlabel(xlabel);ax.grid(alpha=.15)
    if log:ax.set_xscale('log')
fig.suptitle('F0 operational AICc preference versus galaxy characteristics: all 175')
save(fig,'09_preference_properties','Exploratory only. Fixed same-mask eligibility and runner-up gap>=2; no winner for inconclusive/invalid comparisons. HI-to-light is a proxy, not a measured total gas fraction.')

fig,axes=plt.subplots(2,2,figsize=(11,7),layout='constrained',sharex=True)
for ax,model in zip(axes.flat,MODELS):
    points=np.array([[p[3],p[4]] for p in DATA['residual_points'] if p[1]=='MLE' and p[2]==model]);centers=[];med=[];q1=[];q3=[];counts=[]
    for low in np.arange(0,1,.1):
        z=points[(points[:,0]>low)&(points[:,0]<=low+.10000001),1];centers.append(low+.05);counts.append(len(z));med.append(np.median(z));q1.append(np.quantile(z,.25));q3.append(np.quantile(z,.75))
    ax.fill_between(centers,q1,q3,color=COLORS[model],alpha=.18,label='Point distribution IQR');ax.plot(centers,med,color=COLORS[model],linestyle=STYLES[model],marker='o',markersize=3,label='Median');ax.axhline(0,color='black',lw=.5)
    ax.set(title=f'{model.upper()} F0, radial n={len(points)}',xlabel='R / outermost measured R (dimensionless)',ylabel='Standardized residual');ax.legend(fontsize=7);ax.grid(alpha=.2)
fig.suptitle('Residual structure over relative radius')
save(fig,'10_radial_residual_structure','Point-weighted medians and interquartile spread, not confidence bands. Each panel has its own y scale. Radius normalization and correlated measurements limit interpretation.')

for galaxy,data in DATA['selected_curves'].items():
    fig,axes=plt.subplots(3,2,figsize=(12,9),layout='constrained',sharex=True,gridspec_kw={'height_ratios':[3,1,1]});r=data['radius_kpc']
    for col,mode in enumerate(MODES):
        ax,res,zoom=axes[:,col];ax.errorbar(r,data['observed_km_s'],yerr=data['error_km_s'],fmt='k.',markersize=3,label='SPARC observed ± catalog error');ax.plot(r,data['gas_signed_km_s'],':',color='gray',label='Signed gas component convention')
        ax.plot(r,np.sqrt(.5)*np.array(data['disk_unit_ML_km_s']),'--',color='#9977AA',alpha=.6,label='Fiducial disk contribution');ax.plot(r,np.sqrt(.7)*np.array(data['bulge_unit_ML_km_s']),'--',color='#997755',alpha=.6,label='Fiducial bulge contribution')
        invalid=[]
        for result in data['results']:
            if result['mode']!=mode:continue
            m=result['model']
            if result['status']!='CONVERGED':invalid.append(m+': '+result['status']);continue
            ax.plot(r,result['prediction_km_s'],color=COLORS[m],linestyle=STYLES[m],label=m.upper())
            z=result['statistics']['standardized_residuals'];res.plot(r,z,color=COLORS[m],linestyle=STYLES[m])
            if m!='baryons':zoom.plot(r,z,color=COLORS[m],linestyle=STYLES[m])
        if invalid:ax.text(.02,.02,'\n'.join(invalid),transform=ax.transAxes,fontsize=7,va='bottom')
        ax.set(title='F0 / fixed MLE' if mode=='MLE' else 'F1 / nuisance MAP',ylabel='Velocity / component (km/s)');ax.legend(fontsize=6)
        res.set_ylabel('All residuals / sigma');zoom.set(ylabel='Halo + RAR residuals / sigma',xlabel='Catalog radius (kpc)')
        for a in [ax,res,zoom]:a.grid(alpha=.2)
        for a in [res,zoom]:a.axhline(0,color='black',lw=.5)
    fig.suptitle(f"{galaxy}: n={data['n_inventory']}, Q={data['metadata']['Q']}, catalog D={data['metadata']['D']} Mpc, i={data['metadata']['Inc']}°")
    save(fig,'galaxy_'+galaxy,'Full original point mask; unsupported curves are not clipped. F1 in catalog frame; dashed components are fiducial references. RAR is empirical, and errors omit inclination systematics.')

# Parameter/error figures use saved F0 fits; missing covariance remains missing.
parameter_rows=[]
for galaxy in DATA['features']:
    full=json.loads((OUT/f'full/initial/{galaxy}.json').read_text())
    for r in full['results']:
        if r['mode']=='MLE' and r['model'] in ['nfw','burkert'] and r['status']=='CONVERGED':
            se=r['data_identifiability']['standard_errors']
            for index,name in enumerate(r['parameter_names']):parameter_rows.append({'galaxy':galaxy,'model':r['model'],'name':name,'value':r['parameters'][index],'local_standard_error':None if se is None else se[index],'boundary':any(r['boundary_flags'])})
(OUT/'halo_parameter_plot_data.json').write_text(json.dumps(parameter_rows,indent=2))
fig,axes=plt.subplots(2,2,figsize=(11,7),layout='constrained')
names=[('nfw','log10_M200_Msun','log10 M200 (solar masses)'),('nfw','log10_c200','log10 concentration (dimensionless)'),('burkert','log10_rho0_Msun_kpc3','log10 central density (solar masses / kpc³)'),('burkert','log10_r0_kpc','log10 core radius (kpc)')]
for ax,(m,name,label) in zip(axes.flat,names):
    values=[r['value'] for r in parameter_rows if r['name']==name];ax.hist(values,bins=20,color=COLORS[m],edgecolor='white');ax.set(title=f'{m.upper()} F0 converged n={len(values)} / 175',xlabel=label,ylabel='Galaxies')
fig.suptitle('Halo parameter estimates under frozen F0 assumptions')
save(fig,'11_halo_parameter_estimates','Includes bound-contact estimates; no claim that every fitted parameter is precisely identified or cosmologically plausible. Parameter bounds remain frozen.')
fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
for ax,m in zip(axes,['nfw','burkert']):
    for index,name in enumerate([name for model,name,_ in names if model==m]):
        values=[r['local_standard_error'] for r in parameter_rows if r['name']==name and r['local_standard_error'] is not None]
        ecdf(ax,values,name.replace('log10_','')+f' n={len(values)}/175',m)
        # Distinguish the two same-model error curves by line style.
        ax.lines[-1].set_linestyle('-' if index==0 else '--')
    ax.set(xscale='log',xlabel='Local standard error in log10 parameter (dex)',ylabel='Fraction of returned local standard errors',title=m.upper()+' F0');ax.legend(fontsize=7);ax.grid(alpha=.2)
fig.suptitle('Conditional local error diagnostics, not posterior intervals')
save(fig,'12_local_parameter_uncertainty','Known-error linear covariance, withheld at bounds/poor rank or conditioning. F1 data covariance is withheld for all converged halo fits because of geometry degeneracy.')

# Contact sheet is a separate visual-QA artifact, not a replacement for full figures.
from PIL import Image,ImageDraw
sheet=Image.new('RGB',(1200,330*((len(rendered)+2)//3)),'white');draw=ImageDraw.Draw(sheet)
for i,name in enumerate(rendered):
    with Image.open(FIG/(name+'.png')) as im:
        im.thumbnail((395,300));sheet.paste(im,(400*(i%3),330*(i//3)+22))
    draw.text((400*(i%3)+3,330*(i//3)+3),name,fill='black')
sheet.save(FIG/'contact_sheet.png')
(OUT/'figure_manifest.json').write_text(json.dumps({'figures':rendered,'count':len(rendered),'source':'figure_data.json; population_summary.json','wall_seconds':time.perf_counter()-START,'peak_working_set_MiB':P.memory_info().peak_wset/2**20},indent=2));print(len(rendered),'scientific figures saved')
