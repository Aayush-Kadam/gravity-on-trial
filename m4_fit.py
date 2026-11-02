"""Explicit, serial, bounded exploratory fitting; never writes M1–M3."""
import json,os,subprocess,sys,time,uuid
from pathlib import Path
import psutil
from r0_processes import usage,stop_tree
from m4_adapter import ROOT,json_bytes,read,baseline_path,curve,provenance
from recovery_monitor import available
def admitted(headrooms):return min(headrooms)>=1024 and max(headrooms)-min(headrooms)<=128
def bounded_fit(galaxy,model,values):
    out=ROOT/'results/m4/v1/exploratory';out.mkdir(parents=True,exist_ok=True)
    lock=out/'active.lock'
    try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError:return {'status':'BUSY','label':'EXPLORATORY FIT','reason':'A local fit is active. No second job was launched.'}
    os.close(fd);p=None
    try:
        heads=[]
        for i in range(5):
            heads.append(available())
            if i<4:time.sleep(.5)
        if not admitted(heads):return {'status':'REFUSED','label':'EXPLORATORY FIT','preflight_MiB':heads,'reason':'Requires ≥1024 MiB stable available memory (range ≤128 MiB). No job launched.'}
        run=uuid.uuid4().hex;request=out/(run+'_request.json');dest=out/(run+'_result.json');request.write_bytes(json_bytes({'galaxy':galaxy,'model':model,'assumptions':values}))
        env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
        start=time.perf_counter();peak=0;low=min(heads);reason=None
        with (out/(run+'_stdout.txt')).open('w') as log,(out/(run+'_stderr.txt')).open('w') as err:
            p=subprocess.Popen([sys.executable,str(ROOT/'m4_fit.py'),'worker',str(request),str(dest)],env=env,stdout=log,stderr=err);proc=psutil.Process(p.pid)
            while p.poll() is None:
                try:
                    rss,tree_peak=usage(proc);peak=max(peak,tree_peak);low=min(low,available())
                    if peak>180 or low<768 or time.perf_counter()-start>20:reason='Stopped by 20-second / 180 MiB child / 768 MiB system safety bound';stop_tree(proc);break
                except psutil.NoSuchProcess:break
                time.sleep(.05)
            p.wait(timeout=5)
        report={'run_id':run,'label':'EXPLORATORY FIT · not frozen benchmark','input_provenance':provenance(read(baseline_path(galaxy))),'requested_assumptions':values,'configuration':'M3 fixed-assumption MLE; configs/m1_v1.json + configs/gate0r.json','seconds':time.perf_counter()-start,'peak_MiB':peak,'minimum_available_MiB':low,'termination_reason':reason,'status':'STOPPED' if reason else ('COMPLETE' if p.returncode==0 and dest.exists() else 'FAILED'),'preflight_MiB':heads}
        if report['status']=='COMPLETE':report['result']=json.loads(dest.read_text())
        (out/(run+'_monitor.json')).write_bytes(json_bytes(report));return report
    finally:
        if p is not None and p.poll() is None:stop_tree(psutil.Process(p.pid));p.wait(timeout=5)
        lock.unlink(missing_ok=True)
def worker(req,dest):
    from m3_science import fit_fixed
    r=json.loads(Path(req).read_text());b=read(baseline_path(r['galaxy']));v=r['assumptions']
    spec={'kind':'physical','upsilon_disk':v['ud'],'upsilon_bulge':v['ub'],'distance_ratio':v['d'],'inclination_deg':v['inc'],'catalog_inclination_deg':b['metadata']['Inc'],'physical_distance_Mpc':b['metadata']['D']*v['d']}
    result=fit_fixed(curve(b),r['model'],spec,read('configs/m1_v1.json'),read('configs/gate0r.json'))
    Path(dest).write_bytes(json_bytes(result))
if __name__=='__main__':worker(sys.argv[2],sys.argv[3])
