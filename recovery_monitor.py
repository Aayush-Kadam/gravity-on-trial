"""Windows-native preflight and bounded child-process monitoring."""
import ctypes, hashlib, importlib.util, json, os, subprocess, sys, time
from pathlib import Path
import psutil

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results/gate0r'
OUT.mkdir(parents=True,exist_ok=True)
class MemoryStatus(ctypes.Structure):
    _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong),('total',ctypes.c_ulonglong),('available',ctypes.c_ulonglong),('page_total',ctypes.c_ulonglong),('page_available',ctypes.c_ulonglong),('virtual_total',ctypes.c_ulonglong),('virtual_available',ctypes.c_ulonglong),('extended',ctypes.c_ulonglong)]
def available():
    s=MemoryStatus(); s.length=ctypes.sizeof(s)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s)): raise ctypes.WinError()
    return s.available/2**20
def save(name,data): (OUT/name).write_text(json.dumps(data,indent=2,allow_nan=False))
def run(command,label):
    samples=[available() for _ in range(1)]
    for _ in range(4): time.sleep(.5); samples.append(available())
    pre={'available_MiB':samples,'minimum_MiB':min(samples),'range_MiB':max(samples)-min(samples),'stable_definition':'five samples over 2 seconds, each >=768 MiB and range <=128 MiB'}
    save(label+'_preflight.json',pre)
    if min(samples)<768 or max(samples)-min(samples)>128:
        save(label+'_monitor.json',{'launched':False,'reason':'preflight failed','preflight':pre}); return False
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
    start=time.perf_counter(); logs=[]; killed=None; peak=0
    with (OUT/(label+'_stdout.txt')).open('w') as stdout, (OUT/(label+'_stderr.txt')).open('w') as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,env=env)
        proc=psutil.Process(child.pid)
        while child.poll() is None:
            try:
                mem=proc.memory_info(); rss=mem.rss/2**20; peak=max(peak,mem.peak_wset/2**20)
                headroom=available(); logs.append({'seconds':time.perf_counter()-start,'rss_MiB':rss,'available_MiB':headroom})
                if headroom<512 or peak>180:
                    killed='available memory below 512 MiB' if headroom<512 else 'peak working set above 180 MiB'
                    child.terminate(); child.wait(timeout=10); break
            except psutil.NoSuchProcess: break
            time.sleep(.05)
        child.wait()
    result={'launched':True,'exit_code':child.returncode,'terminated_reason':killed,'wall_seconds':time.perf_counter()-start,'max_peak_working_set_MiB':peak,'minimum_observed_available_MiB':min((s['available_MiB'] for s in logs),default=min(samples)),'samples':logs,'sample_interval_seconds':.05}
    save(label+'_monitor.json',result)
    return child.returncode==0 and killed is None

if __name__=='__main__':
    manifest=json.loads((ROOT/'data/manifests/acquisition.json').read_text())
    hashes=[]
    for item in manifest:
        path=ROOT/'data/raw'/item['url'].rsplit('/',1)[1]
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        hashes.append({'file':path.name,'sha256':digest,'matches':digest==item['sha256']})
    assert all(i['matches'] for i in hashes)
    save('checkpoint.json',{'raw_hash_checks':hashes,'numpy_available':importlib.util.find_spec('numpy') is not None,'scipy_available':importlib.util.find_spec('scipy') is not None,'visible_processes_only':[{'name':p.info['name'],'rss_MiB':p.info['memory_info'].rss/2**20 if p.info['memory_info'] else None} for p in psutil.process_iter(['name','memory_info'])]})
    command=[sys.executable,'-c',"import json,time,psutil; p=psutil.Process(); b=p.memory_info().rss/2**20; t=time.perf_counter(); import numpy,scipy.optimize,scipy.integrate; print(json.dumps({'baseline_MiB':b,'after_import_MiB':p.memory_info().rss/2**20,'peak_MiB':p.memory_info().peak_wset/2**20,'import_seconds':time.perf_counter()-t})); time.sleep(.2)"] if len(sys.argv)==1 else [sys.executable,str(ROOT/'scientific_probe.py'),*sys.argv[1:]]
    if sys.argv[1:]==['plots']:
        command=[sys.executable,str(ROOT/'render_recovery.py')]
    label='import_probe' if len(sys.argv)==1 else '_'.join(sys.argv[1:])
    ok=run(command,label); print(json.dumps({'label':label,'passed':ok})); sys.exit(0 if ok else 2)
