"""Bounded M1 real-galaxy comparisons, profiles and separate plot rendering."""
import hashlib,json,math,sys,time
from pathlib import Path
import psutil
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m1/v1'
sys.path.insert(0,str(ROOT/'src'))
process=psutil.Process();baseline=process.memory_info().rss/2**20;begun=time.perf_counter();cpu_start=process.cpu_times()
import numpy as np
from gravity_on_trial.m1_physics import Curve,predict,signed_baryons,KPC_M
from gravity_on_trial.m1_inference import fit_curve
CONFIG=json.loads((ROOT/'configs/m1_v1.json').read_text());GATE=json.loads((ROOT/'configs/gate0r.json').read_text())

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def identity():
    files=[ROOT/'configs/m1_v1.json',ROOT/'configs/gate0r.json',ROOT/'m1_worker.py',*sorted((ROOT/'src/gravity_on_trial').glob('*.py'))]
    source={str(p.relative_to(ROOT)):sha(p) for p in files}
    source['data/raw/MassModels_Lelli2016c.mrt']=sha(ROOT/'data/raw/MassModels_Lelli2016c.mrt')
    source['data/raw/SPARC_Lelli2016c.mrt']=sha(ROOT/'data/raw/SPARC_Lelli2016c.mrt')
    return {'files':source,'content_revision':hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),'seed':CONFIG['seed']}

def load(galaxy):
    catalog=json.loads((ROOT/'results/gate0/parsed_tables.json').read_text())['catalog'];meta=next(c for c in catalog if c['ID']==galaxy)
    rows=[]
    with (ROOT/'data/raw/MassModels_Lelli2016c.mrt').open() as f:
        for line in f:
            if line[:11].strip()==galaxy: rows.append([float(line[a-1:b]) for a,b in [(20,25),(27,32),(34,38),(40,45),(47,52),(54,59)]])
    r,obs,err,gas,disk,bulge=np.array(rows).T
    return Curve(galaxy,r,obs,err,gas,disk,bulge,meta).validate()

def save(name,data):
    path=OUT/name;tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2,allow_nan=False));tmp.replace(path)

def real(galaxy,replicate):
    curve=load(galaxy); results=[]
    for mode in ['MLE','MAP']:
        for model in CONFIG['models']:
            result=fit_curve(curve,model,mode,CONFIG,GATE);results.append(result)
            # Checkpoint each completed pair atomically.
            save(f'{galaxy}_{replicate}.json',{'galaxy':galaxy,'replicate':replicate,'identity':identity(),'metadata':curve.metadata,'radius_kpc':curve.r.tolist(),'observed_km_s':curve.obs.tolist(),'error_km_s':curve.err.tolist(),'gas_signed_km_s':curve.gas.tolist(),'disk_unit_ML_km_s':curve.disk.tolist(),'bulge_unit_ML_km_s':curve.bulge.tolist(),'results':results,'complete':len(results)==8})
    if galaxy in CONFIG['profile_subset'] and replicate=='initial':
        from scipy.optimize import minimize_scalar
        best=next(r for r in results if r['model']=='nfw' and r['mode']=='MLE')
        center=best['parameters'][0];grid=[]
        for offset in CONFIG['profile_offsets_dex']:
            mass=center+offset
            def chi(c):
                z=(predict(curve,'nfw',[mass,c])-curve.obs)/curve.err;return float(z@z)
            f=minimize_scalar(chi,bounds=tuple(np.array(GATE['nfw_bounds'])[:,1]),method='bounded',options={'xatol':1e-11})
            grid.append({'log10_M200':mass,'log10_c200':float(f.x),'chi_squared':float(f.fun),'delta_chi_squared':float(f.fun-best['statistics']['chi_squared']),'success':bool(f.success)})
        save(f'{galaxy}_profile.json',{'label':'F0 one-dimensional profile likelihood; limited prespecified grid, not an interval or posterior','grid':grid,'identity':identity()})
    return {'pairs':len(results),'converged':sum(r['status']=='CONVERGED' for r in results),'failures':[{'model':r['model'],'mode':r['mode'],'status':r['status']} for r in results if r['status']!='CONVERGED']}

def references():
    # Published Table A1 rounded values: Li+2018; comparison evaluated without fitting.
    curve=load('NGC3198');ud=.77;d=10.4/curve.metadata['D'];inc=71.1
    production=predict(curve,'rar',ud=ud,d=d,inc=inc)
    independent=[]
    for r,gas,disk,bulge in zip(curve.r,curve.gas,curve.disk,curve.bulge):
        radius=r*d*3.085677581491367e19
        b=d*math.fsum([ud*disk*disk,.7*bulge*bulge,math.copysign(gas*gas,gas)])
        g=b*1e6/radius
        vp=math.sqrt(g/(1-math.exp(-math.sqrt(g/1.2e-10)))*radius)/1000
        independent.append(vp*math.sin(math.radians(inc))/math.sin(math.radians(curve.metadata['Inc'])))
    relative=max(abs(a/b-1) for a,b in zip(production,independent));assert relative<1e-9
    factor=math.sin(math.radians(inc))/math.sin(math.radians(curve.metadata['Inc']))
    # Their Eq 6 uses acceleration residuals/error propagation, not our velocity likelihood.
    vobs=curve.obs/factor;error=curve.err/factor;vphysical=production/factor
    accel_z=(vobs**2-vphysical**2)/(2*vobs*error)
    vel_z=(production-curve.obs)/curve.err
    data={'source':'https://arxiv.org/html/1803.00022 Table A1, NGC3198; equations 3–6','published_rounded_parameters':{'ud':ud,'distance_Mpc':10.4,'inclination_deg':inc,'reported_reduced_chi_squared':2.057},'our_velocity_chi_squared_at_their_parameters':float(vel_z@vel_z),'acceleration_chi_squared_at_their_parameters':float(accel_z@accel_z),'n':len(curve.r),'assumed_number_free_for_reference':3,'acceleration_reduced_chi_squared':float(accel_z@accel_z)/(len(curve.r)-3),'independent_RAR_relative_error':relative,'interpretation':'Rounded published parameter evaluation, not replication of their posterior or acceleration-space inference; source gas-sign convention and any data revision may matter. Our fitting uses normalized velocity likelihood, different coordinate prior density and explicit truncated bounds.'}
    save('reference_comparison.json',data);return data

def plots():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for galaxy in CONFIG['galaxies']:
        data=json.loads((OUT/f'{galaxy}_initial.json').read_text());r=data['radius_kpc']
        fig,axes=plt.subplots(3,2,figsize=(12,10),sharex=True,layout='constrained',gridspec_kw={'height_ratios':[3,1,1]})
        colors={'baryons':'tab:green','nfw':'tab:blue','burkert':'tab:orange','rar':'tab:red'}
        for col,mode in enumerate(['MLE','MAP']):
            ax,res,zoom=axes[:,col];ax.errorbar(r,data['observed_km_s'],yerr=data['error_km_s'],fmt='k.',markersize=3,label='SPARC observation ± catalog error')
            ax.plot(r,data['gas_signed_km_s'],':',color='gray',label='Signed gas component convention')
            ax.plot(r,np.sqrt(.5)*np.array(data['disk_unit_ML_km_s']),'--',color='tab:purple',alpha=.5,label='Fiducial disk contribution')
            ax.plot(r,np.sqrt(.7)*np.array(data['bulge_unit_ML_km_s']),'--',color='tab:brown',alpha=.5,label='Fiducial bulge contribution')
            for result in data['results']:
                if result['mode']!=mode or result['status']!='CONVERGED': continue
                model=result['model'];ax.plot(r,result['prediction_km_s'],color=colors[model],label=model.upper()+' '+('fixed baseline' if mode=='MLE' else 'prior-constrained MAP'))
                z=result['statistics']['standardized_residuals'];res.plot(r,z,'.-',color=colors[model],markersize=2)
                if model!='baryons': zoom.plot(r,z,'.-',color=colors[model],markersize=2)
            ax.set_title('F0 fixed assumptions / MLE' if mode=='MLE' else 'F1 nuisance parameters / MAP (no AIC/BIC)')
            ax.set_ylabel('Velocity / component convention (km/s)');ax.legend(fontsize=6)
            for panel in [ax,res,zoom]: panel.grid(alpha=.2)
            for panel in [res,zoom]:panel.axhline(0,color='black',lw=.5)
            res.set_ylabel('All residuals / σ');zoom.set_ylabel('Halo & RAR residuals / σ');zoom.set_xlabel('Catalog galactocentric radius (kpc)')
        fig.suptitle(galaxy+f" — Q={data['metadata']['Q']}, i={data['metadata']['Inc']}°, D={data['metadata']['D']} Mpc",fontsize=12)
        fig.get_layout_engine().set(rect=(0,.06,1,.94))
        fig.text(.025,.012,'Published derived SPARC components: Lelli, McGaugh & Schombert (2016), astroweb.case.edu/SPARC/.\nF1 shown in catalog velocity/radius frame; dotted/dashed components are fiducial references. RAR is an empirical algebraic prescription.\nSigned gas enters Vgas |Vgas|; catalog velocity errors omit inclination systematics. Local numerical fits are not theory probabilities.',fontsize=7)
        fig.savefig(OUT/f'{galaxy}_comparison.png',dpi=110);fig.savefig(OUT/f'{galaxy}_comparison.svg');plt.close(fig)
    return {'figures':len(CONFIG['galaxies'])}

if __name__=='__main__':
    if sys.argv[1]=='real': summary=real(*sys.argv[2:])
    elif sys.argv[1]=='references':summary=references()
    elif sys.argv[1]=='plots':summary=plots()
    else:raise ValueError('Unknown worker task')
    cpu=process.cpu_times();resource={'baseline_RSS_MiB':baseline,'peak_working_set_MiB':process.memory_info().peak_wset/2**20,'wall_seconds':time.perf_counter()-begun,'cpu_seconds':cpu.user+cpu.system-cpu_start.user-cpu_start.system,'summary':summary}
    save('_'.join(sys.argv[1:])+'_resource.json',resource);print(json.dumps(resource))
