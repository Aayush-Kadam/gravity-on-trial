"""Local-only M4 server supervisor. Explicit engineering cap, not an M3 campaign."""
import json,os,subprocess,sys,time
from pathlib import Path
import psutil
from collections import deque
from r0_processes import usage,stop_tree
from recovery_monitor import available
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m4/v1';OUT.mkdir(parents=True,exist_ok=True)
def main():
    app=sys.argv[1] if len(sys.argv)>1 else 'streamlit_app.py';port=sys.argv[2] if len(sys.argv)>2 else '8507'
    samples=[]
    for i in range(5):
        samples.append(available())
        if i<4:time.sleep(.5)
    pre={'samples_MiB':samples,'minimum_required_MiB':1024,'maximum_range_MiB':128}
    if min(samples)<1024 or max(samples)-min(samples)>128:
        (OUT/'server_refusal.json').write_text(json.dumps(pre));print('Preflight refused; no server launched');return 2
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',STREAMLIT_BROWSER_GATHER_USAGE_STATS='false')
    with (OUT/'server_stdout.txt').open('w') as log,(OUT/'server_stderr.txt').open('w') as err:
        p=subprocess.Popen([sys.executable,'-m','streamlit','run',str(ROOT/app),'--server.port',port,'--server.address','127.0.0.1'],cwd=ROOT,env=env,stdout=log,stderr=err)
        proc=psutil.Process(p.pid);start=time.perf_counter();peak=0;lowest=min(samples);reason=None;history=deque(maxlen=9000);ticks=0
        (OUT/'server_pid.json').write_text(json.dumps({'pid':p.pid,'supervisor_pid':os.getpid(),'port':port,'app':app}))
        try:
            while p.poll() is None:
                rss,tree_peak=usage(proc);peak=max(peak,tree_peak);free=available();lowest=min(lowest,free)
                history.append({'seconds':round(time.perf_counter()-start,3),'rss_MiB':rss,'peak_MiB':peak,'available_MiB':free})
                ticks+=1
                data={'app':app,'port':port,'preflight':pre,'peak_MiB':peak,'minimum_available_MiB':lowest,'seconds':time.perf_counter()-start,'samples':list(history),'history_policy':'latest 9000 samples; lifetime extrema retained; owned process tree; summed per-process peaks are a conservative upper bound','termination_reason':reason}
                if ticks%5==0:(OUT/'server_monitor.json').write_text(json.dumps(data))
                if free<768 or peak>600:reason='system floor 768 MiB or app peak 600 MiB exceeded';stop_tree(proc);break
                if (OUT/'STOP_SERVER').exists():(OUT/'STOP_SERVER').unlink();reason='requested stop';stop_tree(proc);break
                time.sleep(.2)
        finally:
            if p.poll() is None:stop_tree(proc)
            p.wait(timeout=10);data.update(termination_reason=reason,exit_code=p.returncode,peak_MiB=peak,minimum_available_MiB=lowest)
            (OUT/'server_monitor.json').write_text(json.dumps(data));print(json.dumps({k:v for k,v in data.items() if k not in ['samples','preflight']}))
    return 0
if __name__=='__main__':sys.exit(main())
