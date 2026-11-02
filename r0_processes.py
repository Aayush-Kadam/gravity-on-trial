"""Owned-process-tree accounting for Windows venv redirectors."""
import psutil
def usage(proc):
    try:members=[proc,*proc.children(recursive=True)]
    except psutil.NoSuchProcess:return 0.,0.
    rss=peak=0.
    for p in members:
        try:
            m=p.memory_info();rss+=m.rss/2**20;peak+=getattr(m,'peak_wset',m.rss)/2**20
        except psutil.NoSuchProcess:pass
    return rss,peak
def stop_tree(proc):
    try:members=list(reversed(proc.children(recursive=True)))+[proc]
    except psutil.NoSuchProcess:return
    for p in members:
        try:p.terminate()
        except psutil.NoSuchProcess:pass
    gone,alive=psutil.wait_procs(members,timeout=5)
    for p in alive:
        try:p.kill()
        except psutil.NoSuchProcess:pass
    psutil.wait_procs(alive,timeout=5)
