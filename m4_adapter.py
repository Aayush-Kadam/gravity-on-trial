"""Read-only M4 adapter v1. Frozen records are authoritative; no optimization here."""
import csv, hashlib, io, json, math, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from gravity_on_trial.m1_physics import Curve, predict, DomainError, signed_baryons
from m2_compare import comparison
ADAPTER_VERSION = 'm4_adapter_v1'
MODELS = ['baryons', 'nfw', 'burkert', 'rar']
LABELS = {'baryons': 'Baryons only', 'nfw': 'NFW', 'burkert': 'Burkert', 'rar': 'Empirical RAR'}

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(relative): return json.loads((ROOT / relative).read_text())
def fingerprint(relative):
    p = ROOT / relative
    return digest(p)
def checked_read(relative, expected):
    raw = (ROOT / relative).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected: raise ValueError('Input changed during loading; reload application')
    return json.loads(raw)
def catalog(): return sorted(r['ID'] for r in read('results/gate0/parsed_tables.json')['catalog'])
def baseline_path(g):
    if g not in catalog(): raise ValueError('Unknown catalog ID')
    return f'results/m2/v1/full/initial/{g}.json'
def scenario_path(g):
    baseline_path(g)
    return f'results/m3/v1/full/initial/{g}.json'
def curve(b):
    return Curve(b['galaxy'], *[np.array(b[k], float) for k in ['radius_kpc','observed_km_s','error_km_s','gas_signed_km_s','disk_unit_ML_km_s','bulge_unit_ML_km_s']], dict(b['metadata'])).validate()
def result(b, model, mode='MLE'): return next(r for r in b['results'] if r['model']==model and r['mode']==mode)
def assumptions(b, r):
    if r.get('fixed_assumptions',{}).get('kind')=='physical':
        s=r['fixed_assumptions'];return {'ud':s['upsilon_disk'],'ub':s['upsilon_bulge'],'d':s['distance_ratio'],'inc':s['inclination_deg']}
    p = dict(zip(r.get('parameter_names', []), r.get('parameters', [])))
    return {'ud':10**p.get('log10_upsilon_disk',math.log10(.5)), 'ub':10**p.get('log10_upsilon_bulge',math.log10(.7)), 'd':p.get('distance_ratio',1.), 'inc':p.get('inclination_deg',b['metadata']['Inc'])}
def preview(b, model, values, halo=None):
    """Use the validated engine; preserve original observations and masks."""
    for name,want in b['identity']['files'].items():
        if name.replace('\\','/').startswith('src/gravity_on_trial/') and digest(ROOT/name)!=want:raise ValueError('Validated physics source has changed; preview refused')
    if halo is None:
        r=result(b,model)
        halo=r.get('parameters',[])[:2] if model in ['nfw','burkert'] else []
    v=predict(curve(b),model,halo,**values)
    return {'label':'INTERACTIVE PREVIEW','galaxy':b['galaxy'],'model':model,'assumptions':values,'halo_parameters':list(halo),'prediction_km_s':v.tolist(),'residual_model_minus_observed_km_s':(v-np.array(b['observed_km_s'])).tolist(),'optimization':'NOT REQUESTED; no refit','identifiability':'NOT ASSESSED for preview'}
def remove_halo(b,r):
    return preview(b,'baryons',assumptions(b,r),halo=[])
def table(b, records):
    rows=[]
    for i,x in enumerate(b['radius_kpc']):
        row={'galaxy':b['galaxy'],'radius_catalog_kpc':x,'observed_km_s':b['observed_km_s'][i],'error_km_s':b['error_km_s'][i], 'gas_signed_km_s':b['gas_signed_km_s'][i]}
        for name,r in records.items():
            if 'prediction_km_s' in r:
                row[name+'_prediction_km_s']=r['prediction_km_s'][i]
                row[name+'_residual_model_minus_observed_km_s']=r['prediction_km_s'][i]-b['observed_km_s'][i]
        rows.append(row)
    return rows
def csv_bytes(rows):
    if not rows:return b''
    keys=list(dict.fromkeys(k for r in rows for k in r)); out=io.StringIO(newline='');w=csv.DictWriter(out,keys);w.writeheader();w.writerows(rows);return out.getvalue().encode('utf-8')
def json_bytes(data): return json.dumps(data,indent=2,allow_nan=False).encode()
def provenance(b):
    return {'adapter_version':ADAPTER_VERSION,'galaxy':b['galaxy'],'source':'SPARC / Lelli, McGaugh & Schombert (2016)','observational_reference_codes':b['metadata']['Ref'],'source_url':b['source_url'],'baseline_file':baseline_path(b['galaxy']),'baseline_sha256':fingerprint(baseline_path(b['galaxy'])),'identity':b['identity'],'model_version':'unchanged M1 physics / M2 benchmark','configuration_id':'configs/m2_v1.json','statistical_method':'Normalized Gaussian likelihood; MLE AICc with frozen full-mask eligibility; MAP unranked','observation_mask':list(range(len(b['radius_kpc']))),'seed':b['identity'].get('seed'),'frame':'catalog radius and velocity; model minus observed residuals'}
def score_rows(records):
    rows=[]
    for r in records:
        s=r.get('statistics',{}); ident=r.get('data_identifiability',{})
        rows.append({'model':LABELS[r['model']], 'mode':r['mode'],'status':r['status'],'n':s.get('n'), 'k':s.get('k'),'chi_squared':s.get('chi_squared'),'reduced_chi_squared':s.get('reduced_chi_squared'), 'AIC':s.get('AIC') if r['mode']=='MLE' else None,'AICc':s.get('AICc') if r['mode']=='MLE' else None,'BIC':s.get('BIC') if r['mode']=='MLE' else None,'rank':ident.get('rank'),'condition':ident.get('condition'),'warnings':'; '.join(ident.get('warnings',[])),'boundary_parameters':'; '.join(n for n,f in zip(r.get('parameter_names',[]),r.get('boundary_flags',[])) if f)})
    return rows
def scientific_state(b,mode='MLE'):
    rs=[r for r in b['results'] if r['mode']==mode]
    c=comparison(rs) if mode=='MLE' else {'status':'NOT_A_LIKELIHOOD_COMPARISON','winner':None,'reasons':['MAP penalties are not ordinary likelihood evidence']}
    return rs,c
UNITS={'log10_M200_Msun':'log10(M200 / M☉)','log10_c200':'log10(c200), dimensionless','log10_rho0_Msun_kpc3':'log10(ρ0 / [M☉ kpc⁻³])','log10_r0_kpc':'log10(r0 / kpc)','log10_upsilon_disk':'log10(Υdisk / solar, 3.6 μm)','log10_upsilon_bulge':'log10(Υbulge / solar, 3.6 μm)','distance_ratio':'D / Dcatalog','inclination_deg':'degrees'}
def parameter_rows(records):
    return [{'model':LABELS[r['model']],'parameter':n,'value':v,'units':UNITS.get(n,'See model definition'),'boundary':f} for r in records for n,v,f in zip(r.get('parameter_names',[]),r.get('parameters',[]),r.get('boundary_flags',[]))]
def validate_vertical():
    b=read(baseline_path('NGC3198')); c=curve(b)
    for m in MODELS:
        r=result(b,m);v=predict(c,m,r['parameters'][:2] if m in ['nfw','burkert'] else [],**assumptions(b,r))
        np.testing.assert_allclose(v,r['prediction_km_s'],rtol=1e-12,atol=1e-10)
        np.testing.assert_allclose((v-c.obs)/c.err,r['statistics']['standardized_residuals'],rtol=1e-11,atol=1e-10)
    saved=json_bytes(b); r=result(b,'nfw');removed=remove_halo(b,r)
    np.testing.assert_allclose(removed['prediction_km_s'],result(b,'baryons')['prediction_km_s'],rtol=1e-12)
    assert json_bytes(b)==saved
    exported=list(csv.DictReader(io.StringIO(csv_bytes(table(b,{'nfw':r})).decode())))
    assert len(exported)==43 and float(exported[0]['nfw_prediction_km_s'])==r['prediction_km_s'][0]
    return {'galaxy':'NGC3198','observations':43,'models_verified':MODELS,'residuals_verified':True,'remove_halo_verified':True,'observations_unchanged':True,'export_roundtrip':True,'baseline_sha256':fingerprint(baseline_path('NGC3198'))}

if __name__=='__main__': print(json.dumps(validate_vertical(),indent=2))
