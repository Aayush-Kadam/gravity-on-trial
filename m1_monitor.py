"""M1 uses the unchanged Gate 0R 180 MiB cap (stricter than 250 MiB target)."""
import os,sys
from pathlib import Path
import recovery_monitor as monitor
ROOT=Path(__file__).resolve().parent
monitor.OUT=ROOT/'results/m1/v1/monitor'
monitor.OUT.mkdir(exist_ok=True)
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
os.environ['PYTHONPATH']=str(ROOT/'src')
if sys.argv[1]=='tests':
    command=[sys.executable,'-m','pytest',str(ROOT/'tests'),'-q','--junitxml='+str(ROOT/'results/m1/v1/tests.xml')]
elif sys.argv[1]=='controls':
    command=[sys.executable,str(ROOT/'m1_controls.py')]
elif sys.argv[1]=='preview':
    command=[sys.executable,str(ROOT/'m1_visual_check.py')]
else: command=[sys.executable,str(ROOT/'m1_worker.py'),*sys.argv[1:]]
label='_'.join(sys.argv[1:])
ok=monitor.run(command,label)
print(label, 'PASS' if ok else 'STOP')
sys.exit(0 if ok else 2)
