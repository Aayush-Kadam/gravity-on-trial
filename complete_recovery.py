"""Complete only the conditional five-galaxy Gate 0R numerical campaign."""
import json,math,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'results/gate0r'
def compare(g,m):
    a=json.loads((OUT/f'{g}_{m}_initial.json').read_text()); b=json.loads((OUT/f'{g}_{m}_rerun.json').read_text())
    differences={}
    for key in ['parameters_log10','prediction_km_s','standardized_residuals']:
        differences[key]=max(abs(x-y) for x,y in zip(a[key],b[key],strict=True))
        assert all(math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-12) for x,y in zip(a[key],b[key],strict=True)),key
    assert a['success'] and b['success']
    for rep in ['initial','rerun']:
        monitor=json.loads((OUT/f'{g}_{m}_{rep}_monitor.json').read_text())
        assert monitor['exit_code']==0 and monitor['terminated_reason'] is None
        assert monitor['minimum_observed_available_MiB']>=512
        fit=json.loads((OUT/f'{g}_{m}_{rep}.json').read_text())
        assert fit['resource']['peak_working_set_MiB']<=180
    return {'galaxy':g,'model':m,'max_absolute_rerun_differences':differences,'chi_squared':a['chi_squared'],'boundary_limited':a['boundary_limited']}
summary=[compare('NGC3198',m) for m in ['nfw','burkert']]
for galaxy in ['NGC2403','NGC3741','DDO154','NGC2841']:
    for model in ['nfw','burkert']:
        for replicate in ['initial','rerun']:
            result=subprocess.run([sys.executable,str(ROOT/'recovery_monitor.py'),galaxy,model,replicate])
            if result.returncode:
                (OUT/'campaign_status.json').write_text(json.dumps({'completed':summary,'stopped_at':[galaxy,model,replicate],'reason':'monitored process or preflight failed'},indent=2))
                sys.exit(result.returncode)
        summary.append(compare(galaxy,model))
        (OUT/'campaign_status.json').write_text(json.dumps({'completed':summary,'numerical_campaign_complete':len(summary)==10},indent=2))
print(json.dumps(summary,indent=2))
