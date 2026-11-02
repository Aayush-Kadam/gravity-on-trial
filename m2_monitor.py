"""Unchanged low-memory supervisor, with isolated M2 output paths."""
import os,sys
from pathlib import Path
import recovery_monitor as monitor
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m2/v1'
monitor.OUT=OUT/'monitor';monitor.OUT.mkdir(parents=True,exist_ok=True)
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';os.environ['PYTHONPATH']=str(ROOT/'src')
if sys.argv[1]=='tests':command=[sys.executable,'-m','pytest',str(ROOT/'tests'),'-q','--junitxml='+str(OUT/'tests.xml')]
elif sys.argv[1]=='checks':command=[sys.executable,str(ROOT/'m2_checks.py')]
elif sys.argv[1]=='controls':command=[sys.executable,str(ROOT/'m2_controls.py')]
elif sys.argv[1]=='plots':command=[sys.executable,str(ROOT/'m2_plots.py')]
elif sys.argv[1]=='aggregate':command=[sys.executable,str(ROOT/'m2_aggregate.py')]
elif sys.argv[1]=='resume':command=[sys.executable,str(ROOT/'m2_resume_check.py')]
else:command=[sys.executable,str(ROOT/'m2_worker.py'),*sys.argv[1:]]
label='_'.join(sys.argv[1:]);ok=monitor.run(command,label)
print(label,'PASS' if ok else 'STOP');sys.exit(0 if ok else 2)
