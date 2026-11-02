"""Freeze unchanged Gate 0 checkpoint, audit residuals, and preregister M1."""
import hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'results/m1/v1'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((ROOT/'results/gate0r/artifacts_manifest.json').read_text())
assert all(digest(ROOT/k)==v for k,v in manifest.items())
raw=json.loads((ROOT/'data/manifests/acquisition.json').read_text())
assert all(digest(ROOT/'data/raw'/v['url'].rsplit('/',1)[1])==v['sha256'] for v in raw)
freeze={str(p.relative_to(ROOT)):digest(p) for folder in ['src','configs','results/gate0','results/gate0r','docs'] for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in str(p)}
(OUT/'gate0_baseline_freeze.json').write_text(json.dumps(freeze,indent=2))
audit=[]
for f in sorted((ROOT/'results/gate0r').glob('*_initial.json')):
    a=json.loads(f.read_text()); residual=[p-o for p,o in zip(a['prediction_km_s'],a['observed_km_s'])]; z=a['standardized_residuals']; mid=len(z)//2
    signs=[1 if v>0 else -1 for v in z if v!=0]
    audit.append({'galaxy':a['galaxy'],'model':a['model'],'n':a['n'],'k':a['k'],'parameters':dict(zip(a['parameter_order'],a['parameters_physical'])),'parameter_note':'Physical values (not log10); units encoded in source parameter names','chi_squared':a['chi_squared'],'degrees_of_freedom':a['n']-a['k'],'reduced_chi_squared':a['reduced_chi_squared'],'maximum_absolute_residual_km_s':max(map(abs,residual)),'maximum_absolute_standardized_residual':max(map(abs,z)),'inner_mean_standardized_residual':sum(z[:mid])/mid,'outer_mean_standardized_residual':sum(z[mid:])/len(z[mid:]),'same_sign_runs':1+sum(x!=y for x,y in zip(signs,signs[1:])),'optimizer_success':a['success'],'boundary_limited':a['boundary_limited'],'physical_admissibility':all(math.isfinite(v) and v>=0 for v in a['prediction_km_s']) and all(v>0 for v in a['parameters_physical']),'source_mismatch':'Published 2018/2020 analyses vary nuisance parameters and use priors/MCMC, unlike this fixed-baryon maximum-likelihood baseline; no matched halo posterior comparison claimed.'})
(OUT/'baseline_audit.json').write_text(json.dumps(audit,indent=2))
catalog=json.loads((ROOT/'results/gate0/parsed_tables.json').read_text())['catalog']
original=['NGC3198','NGC2403','NGC3741','DDO154','NGC2841']; remaining=[c for c in catalog if c['ID'] not in original]
criteria=[('largest_catalog_MHI_to_L36',max(remaining,key=lambda c:(c['MHI']/c['L36'],c['ID']))),('largest_catalog_disk_surface_brightness',max(remaining,key=lambda c:(c['SBdisk'],c['ID']))),('lowest_inclination_Q3',min([c for c in remaining if c['Q']==3],key=lambda c:(c['Inc'],c['ID'])))]
extras=[]
for reason,c in criteria:
    if c['ID'] not in original+extras: extras.append(c['ID'])
config={'version':'m1-v1','scope':'M1 only; no all-catalog fitting','galaxies':original+extras,'additional_selection':[{'criterion':r,'catalog':c} for r,c in criteria],'models':['baryons','nfw','burkert','rar'],'configurations':['F0_MLE','F1_MAP'],'seed':20261102,'upsilon_disk':.5,'upsilon_bulge':.7,'a0_m_s2':1.2e-10,'ML_prior_dex_sigma':.1,'ML_bounds_solar':[.05,2.0],'distance_prior':'Gaussian in D/Dcat centered 1 with sigma eD/D; truncated to [max(0.1,1-3sigma),1+3sigma]','inclination_prior':'Gaussian degrees centered catalog i with sigma catalog e_i, truncated to [max(1,i-3e_i),min(90,i+3e_i)]','ML_prior':'Gaussian in log10 ML centered log10(0.5/0.7), sigma 0.1 dex; MAP density defined in these log coordinates','prior_justification':'Li+2018 use lognormal stellar ML scatter 0.1 dex and catalog geometry errors. Here tails are explicitly bounded engineering/sensitivity policy; not identical posterior inference. No cosmological halo prior.','geometry_frame':'Project physical model into catalog deprojected velocity frame: sin(i_new)/sin(i_catalog). Observed velocities and quoted errors unchanged.','identity_rtol':1e-9,'asymptotic_rtol':2e-6,'synthetic_log_parameter_atol':1e-5,'reproducibility_rtol':1e-10,'reproducibility_atol':1e-10,'covariance_warning_condition':1e8,'profile_subset':['NGC3198','DDO154'],'profile_offsets_dex':[-.2,-.1,0,.1,.2],'profile_type':'F0 NFW log10 M200 fixed grid, refit log10 c; truncated grid, no interval endpoints implied','domain_policy':'No silent radius exclusions. F0 unsupported model records invalid indices; comparability only on identical successful masks. F1 invalid-domain proposals rejected/recorded; if a feasible prior box cannot be evaluated, fit reports failure.','preflight_MiB':768,'system_floor_MiB':512,'hard_child_peak_MiB':180,'target_MiB':250,'single_BLAS_thread':True,'numerical_tolerance_rationale':'Keep Gate0 identity/limit tolerances; synthetic noiseless known-model log parameters must recover within 1e-5 dex; reruns 1e-10. Values frozen before M1 scientific execution.'}
(ROOT/'configs/m1_v1.json').write_text(json.dumps(config,indent=2))
table='\n'.join(f"| {r['galaxy']} | {r['model']} | {r['n']} | {r['reduced_chi_squared']:.3f} | {r['maximum_absolute_residual_km_s']:.3f} | {r['maximum_absolute_standardized_residual']:.3f} | {r['inner_mean_standardized_residual']:.3f} / {r['outer_mean_standardized_residual']:.3f} |" for r in audit)
(ROOT/'docs/M1_BASELINE_AUDIT.md').write_text('''# M1 baseline audit (before scientific changes)

No Git repository exists. Every Gate 0R manifest hash and raw data hash verified. gate0_baseline_freeze.json records original source/config/results/docs hashes; existing halo source will be imported unchanged. Detailed original fit parameter values/units, n/k/dof, physical/boundary status and residual summaries are in results/m1/v1/baseline_audit.json. Original reports remain unchanged.

| Galaxy | Model | n | Reduced chi² | Max abs residual km/s | Max abs standardized | Inner / outer mean standardized |
|---|---|---:|---:|---:|---:|---:|
'''+table+'''

All original best fits are converged, physically admissible and away from declared parameter bounds. Large standardized residuals and coherent radial residuals, especially NGC2403, persist with exact archive/MRT agreement and independent quadrature. Evidence does not point to units/sign errors in the implemented selected cases. This is model inadequacy conditional on fixed geometry/stellar ratios and incomplete Gaussian-error assumptions; its astrophysical cause is not identified. M1 will compare declared nuisance treatment without changing the baseline or increasing errors.

Implicit assumptions made explicit: spherical additive halos; unit-ML published stellar components; fixed H0=73; independent velocity errors with no covariance/systematic scatter; least-squares convergence is local; finite box constraints affect solutions; numerical Jacobian conditioning alone gives no calibrated parameter precision. Reference-study disagreement cannot be assigned to physics without matching nuisance parameters, priors, objectives, masks and halo parameterization. Prior checks were numerical integration checks by this implementation, not independent human replication.
''',encoding='utf-8')
print(json.dumps({'baseline_preserved_files':len(freeze),'selection':config['galaxies']}))
