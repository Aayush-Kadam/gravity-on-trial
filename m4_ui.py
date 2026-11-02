"""Presentation layer. Data, physics, and provenance are owned by adapters."""
import copy,json,math,time
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from m4_adapter import *
from m4_charts import rotation,components,polish,COLORS
from recovery_monitor import available

@st.cache_data(max_entries=2,show_spinner=False)
def manifest(relative,sha):return checked_read(relative,sha)
@st.cache_data(max_entries=12,show_spinner=False)
def frozen(relative,sha,manifest_sha,milestone,adapter_version=ADAPTER_VERSION):
    mpath=f'results/{milestone}/v1/artifacts_manifest.json';m=manifest(mpath,manifest_sha)
    expected=m.get(relative.replace('/','\\'),m.get(relative))
    if expected!=sha:raise ValueError('Frozen artifact integrity mismatch: '+relative)
    return checked_read(relative,sha)
def load(relative,milestone='m3'):
    return frozen(relative,fingerprint(relative),fingerprint(f'results/{milestone}/v1/artifacts_manifest.json'),milestone)
def get_base():return load(baseline_path(st.session_state['galaxy']),'m2')
def get_metric(g):return next(r for r in load('results/m3/v1/atlas_metrics.json') if r['galaxy']==g)
def sidebar():
    with st.sidebar:
        st.markdown('### GRAVITY ON TRIAL')
        st.caption('A local instrument for the evidence')
        ids=catalog()
        st.selectbox('Galaxy · 175 SPARC objects',ids,index=ids.index('NGC3198'),key='galaxy')
        st.caption('M2 benchmark · M3 fragility atlas\n\nNo inference runs during navigation.')
        free=available()
        st.caption(f'Available system memory: {free:,.0f} MiB')
        if free<1024:st.warning('Low memory: optional live fitting is unavailable. Saved results remain accessible.')
def heading(kicker,title,description):
    st.caption(kicker.upper());st.title(title);st.write(description)
def metadata(b):
    m=b['metadata'];cols=st.columns(4)
    for col,label,value in zip(cols,['Distance (Mpc)','Inclination (°)','Quality flag','Observed radii'],[f"{m['D']:g} ± {m['e_D']:g}",f"{m['Inc']:g} ± {m['e_Inc']:g}",str(m['Q']),str(len(b['radius_kpc']))]):col.metric(label,value,border=True)
    st.caption(f"OBSERVED · SPARC 2016 · {b['galaxy']} · Original references: {m['Ref']} · catalog-frame radii and velocities")
def comparison_panel(c):
    status=c['status']
    if status=='PREFERENCE':st.info(f"Operationally preferred: {LABELS[c['winner']]} · frozen full-mask AICc gap {c['gap']:.3f} (threshold 2).")
    elif status=='INCONCLUSIVE':st.warning('Inconclusive · eligible models have an AICc gap below 2. No operational winner.')
    else:st.warning('Unavailable · '+('; '.join(c.get('reasons',[])) or status)+'. No operational winner.')
    st.caption('Conditional on the listed models, assumptions and known-error likelihood. Convergence does not establish adequacy; a preference does not prove a theory. Radial covariance and additional systematics are unmodeled.')
def diagnostics(records):
    rows=score_rows(records);warnings=[f"{r['model']}: {r['warnings']}" for r in rows if r['warnings']];bounds=[f"{r['model']}: {r['boundary_parameters']}" for r in rows if r['boundary_parameters']]
    if warnings:st.warning('Identifiability warning · '+' | '.join(warnings))
    if bounds:st.warning('Parameter-boundary contact · '+' | '.join(bounds))
    for r in records:
        if r['status']!='CONVERGED':st.warning(f"{LABELS[r['model']]} · {r['status']} · {r.get('message','full-domain prediction unavailable')}")
    st.dataframe(pd.DataFrame(rows),hide_index=True,width='stretch')
    st.caption('χ² uses the stated published errors. Reduced χ² is undefined for n ≤ k; empty criteria are unavailable. MAP information criteria are deliberately withheld. Local rank/curvature does not supply global identification or credible intervals.')
    with st.expander('Parameters, units and assumptions'):
        st.dataframe(pd.DataFrame(parameter_rows(records)),hide_index=True,width='stretch')
        st.json({LABELS[r['model']]:assumptions(get_base(),r) for r in records},expanded=False)
        st.caption('Υ in solar units at 3.6 μm. MLE baseline fixes disk Υ=0.5, bulge Υ=0.7 and catalog geometry. MAP fits nuisance parameters under Gaussian penalties and finite bounds. RAR uses fixed a₀=1.2×10⁻¹⁰ m/s²; it is an empirical prescription, not every modified-gravity theory.')
def downloads(b,records,prefix):
    with st.container(horizontal=True):
        st.download_button('Download curve CSV',csv_bytes(table(b,records)),f"{b['galaxy']}_{prefix}.csv",'text/csv',key=prefix+'_csv')
        st.download_button('Download evidence JSON',json_bytes({'provenance':provenance(b),'records':records}),f"{b['galaxy']}_{prefix}.json",'application/json',key=prefix+'_json')
def reset_lab():
    g=st.session_state['galaxy']
    for key in list(st.session_state):
        if key.startswith('lab_'+g):del st.session_state[key]
def galaxy_lab():
    b=get_base();g=b['galaxy'];key='lab_'+g
    heading('01 / Galaxy lab',g,'Inspect real observations. Remove a halo, change an assumption, and follow the residuals.')
    metadata(b)
    selected=st.pills('Validated models',MODELS,default=MODELS,selection_mode='multi',format_func=lambda m:LABELS[m],key=key+'_models')
    with st.container(horizontal=True):
        halo_model=st.selectbox('Halo reference',['nfw','burkert'],format_func=lambda m:LABELS[m],key=key+'_halo')
        remove=st.toggle('Remove dark matter',key=key+'_remove',help='Remove only the halo term at the reference model’s existing stellar and geometry assumptions; no refit.')
        st.button('Restore original configuration',on_click=reset_lab)
    rs={m:result(b,m) for m in selected};shown=rs.copy()
    if remove:
        ref=result(b,halo_model)
        try:shown={'preview':remove_halo(b,ref)};st.warning('INTERACTIVE PREVIEW · halo removed, stellar M/L and geometry held fixed. No optimization. Observations and uncertainties are unchanged. This operation alone proves or disproves no theory.')
        except DomainError as e:shown={};st.error('Halo-removed prediction is unsupported: '+str(e))
    elif key+'_preview' in st.session_state:
        shown['preview']=st.session_state[key+'_preview'];st.warning('INTERACTIVE PREVIEW · parameters changed without fitting. Identifiability and evidence ranking are not assessed for this curve.')
    else:st.caption('VALIDATED RESULT · frozen M2-v1 maximum-likelihood predictions')
    st.plotly_chart(rotation(b,shown),theme=None,key=key+'_curve')
    downloads(b,shown,'lab')
    with st.expander('Published baryonic components'):
        st.plotly_chart(components(b),theme=None,key=key+'_components')
        st.caption('Signed equivalent gas speed encodes Vgas |Vgas| in the squared-speed sum; the stellar terms are ΥV². Negative gas is never clipped. These published components use the baseline geometry and M/L.')
    diagnostics(list(rs.values()))
    with st.expander('Explore parameters · explicit preview or bounded fit'):
        pm=st.selectbox('Preview model',MODELS,index=1,format_func=lambda m:LABELS[m],key=key+'_pm')
        ref=result(b,pm);names=ref.get('parameter_names',[])[:2] if pm in ['nfw','burkert'] else []
        if pm in ['nfw','burkert'] and not names:names=['log10_M200_Msun','log10_c200'] if pm=='nfw' else ['log10_rho0_Msun_kpc3','log10_r0_kpc']
        with st.form(key+'_form'):
            cols=st.columns(2)
            ud=cols[0].number_input('Disk mass-to-light ratio (solar, 3.6 μm)',min_value=0.0,max_value=5.0,value=.5,step=.05)
            ub=cols[1].number_input('Bulge mass-to-light ratio (solar, 3.6 μm)',min_value=0.0,max_value=5.0,value=.7,step=.05)
            d=cols[0].number_input('Distance / catalog distance',min_value=.05,max_value=5.,value=1.,step=.05)
            inc=cols[1].number_input('Inclination (degrees)',min_value=.1,max_value=90.,value=float(b['metadata']['Inc']),step=.5)
            hp=[]
            for j,n in enumerate(names):
                bounds=ref.get('bounds',read('configs/gate0r.json')[pm+'_bounds']);lo,hi=bounds[0][j],bounds[1][j]
                value=ref.get('parameters',[float((bounds[0][i]+bounds[1][i])/2) for i in range(2)])[j]
                hp.append(st.number_input(n+' · '+UNITS.get(n,''),min_value=float(lo),max_value=float(hi),value=float(value),key=key+pm+n))
            submitted=st.form_submit_button('Calculate preview')
        values={'ud':ud,'ub':ub,'d':d,'inc':inc}
        if submitted:
            try:st.session_state[key+'_preview']=preview(b,pm,values,hp);st.rerun()
            except DomainError as e:st.error(f'Unsupported preview · {e}; rejected radii {e.indices}. No clipping or mask changes.');st.session_state.pop(key+'_preview',None)
        st.caption('Preview parameters are not fitted inferences. A fresh fit uses the entered stellar/geometry assumptions and the validated M3 fixed-assumption MLE engine; halo starts and bounds follow the frozen protocol. No new model-selection winner is inferred.')
        if st.button('Run bounded exploratory fit',disabled=available()<1024):
            from m4_fit import bounded_fit
            with st.spinner('Exploratory fit · serial CPU · at most 20 seconds'):
                st.session_state[key+'_fit']=bounded_fit(g,pm,values)
        if key+'_fit' in st.session_state:
            fitted=st.session_state[key+'_fit'];st.write('EXPLORATORY FIT · '+fitted['status']);st.json(fitted,expanded=False)
            if 'result' in fitted:
                fr=fitted['result'];diagnostics([fr]);st.plotly_chart(rotation(b,{'preview':fr}),theme=None,key=key+'_fit_curve')
                st.download_button('Download exploratory fit',json_bytes(fitted),g+'_exploratory.json','application/json')
    source_panel(b)
def source_panel(b):
    with st.expander('Source provenance and reproducibility'):
        st.markdown('[SPARC collaboration and data](https://astroweb.cwru.edu/SPARC/) · [Lelli, McGaugh & Schombert (2016)](https://arxiv.org/abs/1606.09251)')
        st.write('Original observational reference codes: '+b['metadata']['Ref']+'; resolve with the SPARC catalog reference list in Evidence vault.')
        st.json(provenance(b),expanded=False)
def model_arena():
    b=get_base();heading('02 / Model arena',b['galaxy']+' · model arena','Compare matched observations, explicit objectives and the limits of interpretation.')
    metadata(b)
    mode=st.segmented_control('Inference configuration',['MLE','MAP'],default='MLE',key='arena_mode') or 'MLE'
    selected=st.pills('Models shown',MODELS,default=MODELS,selection_mode='multi',format_func=lambda m:LABELS[m],key='arena_models')
    rs,c=scientific_state(b,mode)
    comparison_panel(c)
    st.caption('The operational decision always uses the frozen four-model comparison. Hiding a curve does not create a new winner.')
    chosen=[r for r in rs if r['model'] in selected]
    st.plotly_chart(rotation(b,{r['model']:r for r in chosen}),theme=None,key='arena_curve');diagnostics(chosen);downloads(b,{r['model']:r for r in chosen},'arena_'+mode)
    with st.expander('How to read this comparison',expanded=True):
        st.write('The preferred label is a rule-based summary of a normalized likelihood and parameter penalty under common full-radius masks. It depends on fixed M/L and geometry for MLE. MAP instead balances data residuals with explicit nuisance priors, so its penalties are not evidence scores. Inspect residual structure and parameter warnings even when an optimizer converges.')
    source_panel(b)

def fragility_atlas():
    heading('03 / Model fragility atlas','How stable is the preference?','Fragility is sensitivity to tested assumptions, not the probability that a gravitational theory is false.')
    metrics=load('results/m3/v1/atlas_metrics.json');summary=load('results/m3/v1/atlas_summary.json')
    st.caption('107 originally decisive baselines · the full 175-galaxy inventory remains below')
    cols=st.columns(4)
    for col,k in zip(cols,['STABLE','SENSITIVE','INCONCLUSIVE','UNASSESSABLE']):col.metric(k.capitalize(),summary['decisive_baseline_classification_counts'][k],border=True)
    st.caption('Across all 175: 79 stable · 18 sensitive · 29 inconclusive · 49 unassessable. Original baseline: 107 preferences, 24 inconclusive, 44 unavailable.')
    view=st.segmented_control('Atlas view',['Population','Assumption sensitivity','Galaxy detail'],default='Population',key='atlas_view') or 'Population'
    if view=='Population':
        cls=st.multiselect('Class filter',['STABLE','SENSITIVE','INCONCLUSIVE','UNASSESSABLE'],default=['STABLE','SENSITIVE','INCONCLUSIVE','UNASSESSABLE'])
        sub=[m for m in metrics if m['classification'] in cls]
        rows=[{'galaxy':m['galaxy'],'classification':m['classification'],'baseline':m['baseline_status'],'preferred':m['baseline_winner'],'persistence':m['persistence_fraction'],'flip_fraction':m['flip_fraction'],'valid':m['valid_comparable_scenarios'],'meaningful':m['meaningful_scenarios'],'coverage':m['coverage']} for m in sub]
        st.dataframe(pd.DataFrame(rows),hide_index=True,width='stretch')
        chosen=st.selectbox('Drill into an aggregate galaxy',[r['galaxy'] for r in rows] or [st.session_state['galaxy']],key='atlas_drill')
        def open_detail():st.session_state['galaxy']=chosen;st.session_state['atlas_view']='Galaxy detail'
        st.button('Open galaxy detail',on_click=open_detail)
        f=go.Figure();class_colors={'STABLE':'#69b9ff','SENSITIVE':'#f2b45d','INCONCLUSIVE':'#d4a6ff','UNASSESSABLE':'#94a3b8'}
        for k in cls:
            group=[m for m in sub if m['classification']==k and m['persistence_fraction'] is not None]
            f.add_trace(go.Scatter(x=[m['coverage'] for m in group],y=[m['persistence_fraction'] for m in group],text=[m['galaxy'] for m in group],name=k,mode='markers',marker=dict(color=class_colors[k],size=8,symbol=['circle','diamond','square','x'][list(class_colors).index(k)]),hovertemplate='%{text}<br>coverage %{x}<br>persistence %{y}<extra></extra>'))
        f.update_xaxes(title='Valid / meaningful physical scenarios',range=[-.04,1.04]);f.update_yaxes(title='Retained / valid scenarios',range=[-.04,1.04]);st.plotly_chart(polish(f,'Persistence and coverage · defined decisive baselines'),theme=None)
        st.caption('Undefined fractions are omitted from this scatter, never replaced by zero. Points may overlap. Use the complete table and selector for drill-down.')
        h=go.Figure(go.Histogram(x=[m['flip_fraction'] for m in sub if m['flip_fraction'] is not None],xbins=dict(start=0,end=1.05,size=.1),marker_color='#f2b45d'));h.update_xaxes(title='Flips / valid physical scenarios');h.update_yaxes(title='Galaxies');st.plotly_chart(polish(h,'Flip-frequency distribution · defined values only',320),theme=None)
        pages=max(1,math.ceil(len(sub)/35));page=st.selectbox('Heatmap page',list(range(1,pages+1)));heat_sub=sub[(page-1)*35:page*35]
        heat=[[None for model in MODELS] for m in heat_sub]
        # Saved schema supplies explicit per-model preferred fractions.
        if sub:
            first=sub[0]['model_preference_fractions']
            if isinstance(first.get('nfw'),(float,int)) or first.get('nfw') is None:heat=[[m['model_preference_fractions'].get(model) for model in MODELS] for m in heat_sub]
            else:heat=[[m['model_preference_fractions'].get(model,{}).get('fraction') for model in MODELS] for m in heat_sub]
            st.plotly_chart(polish(go.Figure(go.Heatmap(z=heat,y=[m['galaxy'] for m in heat_sub],x=[LABELS[m] for m in MODELS],zmin=0,zmax=1,colorscale='Blues',hoverongaps=False,colorbar=dict(title='Preferred / valid'))),'Operational model preference · gaps are unavailable',max(420,len(heat_sub)*18)),theme=None)
        q=load('results/m3/v1/quality_composition.json');f=go.Figure()
        for k in class_colors:f.add_trace(go.Bar(name=k,y=list(q),x=[q[c]['fragility_classes'].get(k,0) for c in q],orientation='h',marker_color=class_colors[k]))
        f.update_layout(barmode='stack');f.update_xaxes(title='Galaxies in catalog-defined subset');st.plotly_chart(polish(f,'Quality cuts change population composition, not individual labels',360),theme=None)
    elif view=='Assumption sensitivity':
        g=st.session_state['galaxy'];atlas_detail(g,metrics,assumption_only=True)
    else:atlas_detail(st.session_state['galaxy'],metrics)
    st.download_button('Download complete classifications CSV',(ROOT/'results/m3/v1/fragility_classifications.csv').read_bytes(),'fragility_classifications.csv','text/csv')
    st.caption('Frozen scenario grid: 12 physical perturbations + 2 MAP-prior variants. Null, invalid and unavailable outcomes have separate denominators. Named scenarios can overlap; weights are design choices, not independent samples or posterior probabilities.')

def atlas_detail(g,metrics,assumption_only=False):
    m=next(x for x in metrics if x['galaxy']==g);b=load(baseline_path(g),'m2');s=load(scenario_path(g))
    st.subheader(g+' · '+m['classification']);comparison_panel(s['baseline'])
    st.write(f"Retained {m['counts']['retained']} · flipped {m['counts']['flipped']} · to inconclusive {m['counts']['to_inconclusive']} · valid {m['valid_comparable_scenarios']} / meaningful {m['meaningful_scenarios']}")
    st.json({'counts':m['counts'],'persistence':m['persistence_fraction'],'flip_fraction':m['flip_fraction'],'coverage':m['coverage'],'threshold_alternatives':m['alternative_classifications']},expanded=False)
    scenarios=s['scenarios'];outcome={r['scenario_id']:r['outcome'] for r in m['outcomes']}
    rows=[{'scenario':x['scenario_id'],'family':x['family'],'proposal':x['proposal_status'],'comparison':x['comparison']['status'],'preferred':x['comparison'].get('winner'),'transition':outcome.get(x['scenario_id'],'prior, not ranked'),'model_statuses':'; '.join(r['model']+': '+r['status'] for r in x['results'])} for x in scenarios]
    st.dataframe(pd.DataFrame(rows),hide_index=True,width='stretch')
    pick=st.selectbox('Perturbation scenario',[x['scenario_id'] for x in scenarios],key='scenario_'+g);sc=next(x for x in scenarios if x['scenario_id']==pick)
    left,right=st.columns(2)
    left.write('Baseline assumptions: Υdisk=0.5 · Υbulge=0.7 · catalog geometry');right.write('Saved scenario assumptions');right.json(sc['spec'],expanded=True)
    comparison_panel(sc['comparison'])
    if sc['proposal_status']!='APPLICABLE':st.warning(sc['proposal_status']+' · '+str(sc['spec'].get('reason','No valid physical proposal')))
    st.plotly_chart(rotation(b,{r['model']:r for r in sc['results']}),theme=None,key='scenario_curve_'+g)
    diagnostics(sc['results'])
    f=go.Figure()
    for model in ['nfw','burkert']:
        names=list(m['model_summaries'][model]['parameters'])
        for n in names:
            points=[(x['scenario_id'],dict(zip(r.get('parameter_names',[]),r.get('parameters',[]))).get(n)) for x in scenarios if x['kind']=='physical' and x['proposal_status']=='APPLICABLE' for r in x['results'] if r['model']==model and r['status']=='CONVERGED']
            f.add_trace(go.Scatter(x=[x for x,y in points],y=[y for x,y in points],name=model+' · '+n,mode='lines+markers',line=dict(dash='dash' if 'r0' in n or 'c200' in n else 'solid')))
    f.update_yaxes(title='Log10 parameter (physical units in legend)');st.plotly_chart(polish(f,'Saved physical-parameter sensitivity · stress spans, not intervals',430),theme=None)
    paired=go.Figure()
    for model in MODELS:
        base=result(b,model);target=next(r for r in sc['results'] if r['model']==model)
        if base.get('statistics') and target.get('statistics'):paired.add_trace(go.Scatter(x=['M2 baseline',pick],y=[base['statistics']['chi_squared'],target['statistics']['chi_squared']],name=LABELS[model],mode='lines+markers',line=dict(color=COLORS[model])))
    if len(paired.data):
        paired.update_yaxes(title='Data χ² (prior penalty excluded)',type='log');st.plotly_chart(polish(paired,'Paired data residuals · not an evidence ranking for MAP',330),theme=None)
    else:st.caption('Paired χ² comparison unavailable: this scenario has no model with the required data statistic. No values were imputed.')
    st.caption('Run '+s['identity']['run_id']+' · code revision '+s['identity']['content_revision'])
    st.download_button('Download exact scenario JSON',json_bytes({'run_identity':s['identity'],'galaxy':g,'scenario':sc}),g+'_'+pick+'.json','application/json')
    st.json(m['model_summaries'],expanded=False)

def evidence_vault():
    b=get_base();g=b['galaxy'];heading('04 / Evidence vault','Trace every result','Inspect observations, assumptions, warnings and the exact numerical records behind the interface.')
    kind=st.selectbox('Evidence collection',['Galaxy observations and results','M3 scenarios','Methodology and provenance','Manifests and validation','Scientific figures'])
    if kind=='Galaxy observations and results':
        st.dataframe(pd.DataFrame(table(b,{r['model']+'_'+r['mode']:r for r in b['results']})),hide_index=True)
        downloads(b,{r['model']+'_'+r['mode']:r for r in b['results']},'vault')
        st.download_button('Download original galaxy record',json_bytes(b),g+'_M2.json','application/json');st.json(provenance(b),expanded=False)
        st.caption('Result records include masks, units, input hashes, code revision, configuration, seed, outcome, parameters, priors and warnings. Local exports are not permission to redistribute raw data publicly.')
    elif kind=='M3 scenarios':
        s=load(scenario_path(g));st.json(s,expanded=False);st.download_button('Download complete scenario record',json_bytes(s),g+'_M3.json','application/json')
    elif kind=='Methodology and provenance':
        files=sorted(p.name for p in (ROOT/'docs').glob('*.md') if not p.name.startswith('M4_'))
        name=st.selectbox('Document',files);text=(ROOT/'docs'/name).read_text(encoding='utf-8');st.markdown(text);st.download_button('Download methodology',text,name,'text/markdown')
        st.code('python m4_check.py\npython -m pytest tests m3_tests.py m4_tests.py -q',language='powershell')
        with st.expander('Original SPARC catalog and observational reference list'):
            st.text((ROOT/'data/raw/SPARC_Lelli2016c.mrt').read_text())
    elif kind=='Manifests and validation':
        choices=['results/m2/v1/artifacts_manifest.json','results/m3/v1/artifacts_manifest.json','results/m3/v1/full_validation.json','results/m3/v1/acceptance.json','results/m3/v1/independent_metric_audit.json','results/bootstrap/v1/validation.json','results/bootstrap/v1/receipt.json','configs/m3_v1.json','configs/m2_v1.json','configs/m1_v1.json']
        choices=[name for name in choices if (ROOT/name).is_file()]
        choice=st.selectbox('Versioned record',choices);v=read(choice);st.json(v,expanded=False);st.caption('SHA-256 '+fingerprint(choice));st.download_button('Download record',json_bytes(v),Path(choice).name,'application/json')
    else:
        files=sorted((ROOT/'results/m3/v1/figures').glob('*.png'))
        if not files:st.warning('Scientific figures are unavailable in this evidence tree; run the documented complete bootstrap. No substitute images are shown.');return
        name=st.selectbox('Scientific figure',[p.name for p in files]);p=next(p for p in files if p.name==name);st.image(str(p));st.download_button('Download scientific PNG',p.read_bytes(),name,'image/png')
    source_panel(b)
