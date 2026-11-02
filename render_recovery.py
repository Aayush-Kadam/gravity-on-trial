"""Separate low-memory static plots and author-table cross-checks."""
import json,math,time,zipfile
from pathlib import Path
import psutil
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'results/gate0r'
p=psutil.Process(); begun=time.perf_counter(); baseline=p.memory_info().rss/2**20
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
galaxies=['NGC3198','NGC2403','NGC3741','DDO154','NGC2841']
evidence=[]
with zipfile.ZipFile(ROOT/'data/raw/Rotmod_LTG.zip') as archive:
    for galaxy in galaxies:
        nfw=json.loads((OUT/f'{galaxy}_nfw_initial.json').read_text()); bur=json.loads((OUT/f'{galaxy}_burkert_initial.json').read_text())
        published=[[float(x) for x in line.split()] for line in archive.read(galaxy+'_rotmod.dat').decode().splitlines() if line and not line.startswith('#')]
        assert len(published)==nfw['n']
        keys=['r_kpc','observed_km_s','error_km_s','gas_signed_km_s','disk_unit_ML_km_s','bulge_unit_ML_km_s']
        for row_index,row in enumerate(published):
            for col,key in enumerate(keys): assert row[col]==nfw[key][row_index],(galaxy,row_index,key)
        independent_bar=[math.fsum([.5*row[4]*row[4],.7*row[5]*row[5],math.copysign(row[3]*row[3],row[3])]) for row in published]
        error=max(abs(x-y) for x,y in zip(independent_bar,nfw['bar_squared_km2_s2']))
        assert error<1e-9
        r=nfw['r_kpc']; bar=[math.sqrt(x) for x in independent_bar]
        bar_res=[(pred-obs)/err for pred,obs,err in zip(bar,nfw['observed_km_s'],nfw['error_km_s'])]
        baseline_chi=math.fsum(x*x for x in bar_res)
        fig,(ax,res)=plt.subplots(2,1,figsize=(9,7),sharex=True,gridspec_kw={'height_ratios':[3,1]},layout='constrained')
        ax.errorbar(r,nfw['observed_km_s'],yerr=nfw['error_km_s'],fmt='.',color='black',label='SPARC observations ± catalog error',markersize=4)
        ax.plot(r,nfw['gas_signed_km_s'],':',label='Gas: signed contribution convention')
        ax.plot(r,[math.sqrt(.5)*v for v in nfw['disk_unit_ML_km_s']],'--',color='tab:red',label='Disk contribution (M/L=0.5)')
        ax.plot(r,[math.sqrt(.7)*v for v in nfw['bulge_unit_ML_km_s']],'--',color='tab:purple',label='Bulge contribution (M/L=0.7)')
        ax.plot(r,bar,label='Baryons-only prediction',color='tab:green')
        ax.plot(r,nfw['prediction_km_s'],label='Our NFW + fixed baryons fit',color='tab:blue')
        ax.plot(r,bur['prediction_km_s'],label='Our Burkert + fixed baryons fit',color='tab:orange')
        ax.set(ylabel='Circular speed / component convention (km/s)',title=galaxy+' — published derived components; fixed catalog geometry')
        ax.legend(fontsize=7); ax.grid(alpha=.2)
        for values,label,color in [(bar_res,'Baryons','tab:green'),(nfw['standardized_residuals'],'NFW','tab:blue'),(bur['standardized_residuals'],'Burkert','tab:orange')]: res.plot(r,values,'.-',label=label,color=color,markersize=3)
        res.axhline(0,color='black',linewidth=.5); res.set(xlabel='Galactocentric radius (kpc)',ylabel='(model−obs) / error'); res.grid(alpha=.2)
        fig.get_layout_engine().set(rect=(0,.06,1,.94))
        fig.text(.05,.015,'Source: Lelli, McGaugh & Schombert (2016), SPARC / Rotmod_LTG.zip.\nGas contributes Vgas |Vgas|; signed gas curve is not an observed total speed. Errors omit inclination systematics.',fontsize=7)
        fig.savefig(OUT/f'{galaxy}_curves.png',dpi=130); fig.savefig(OUT/f'{galaxy}_curves.svg'); plt.close(fig)
        evidence.append({'galaxy':galaxy,'published_archive_rows_verified':len(published),'fields_match_exactly':True,'maximum_independent_baryonic_absolute_error':error,'baryons_only_chi_squared':baseline_chi,'baryons_only_n':nfw['n'],'baryons_only_k':0,'baryons_only_prediction':bar,'baryons_only_standardized_residuals':bar_res})
(OUT/'published_table_crosscheck.json').write_text(json.dumps({'source':'Official SPARC Rotmod_LTG.zip linked as Newtonian mass models from Lelli+2016c; same derivation, not independent observations','evidence':evidence,'resource':{'baseline_RSS_MiB':baseline,'peak_working_set_MiB':p.memory_info().peak_wset/2**20,'wall_seconds':time.perf_counter()-begun}},indent=2))
print('Five PNG/SVG plots and independent published-table comparisons saved')
