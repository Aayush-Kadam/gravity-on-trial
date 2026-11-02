"""M3 uses the preserved 512 MiB floor and stricter 180 MiB child cap."""
import os,sys
from pathlib import Path
import recovery_monitor as monitor
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m3/v1';monitor.OUT=OUT/'monitor';monitor.OUT.mkdir(parents=True,exist_ok=True)
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';os.environ['PYTHONPATH']=str(ROOT/'src')+os.pathsep+str(ROOT)
if sys.argv[1]=='tests':command=[sys.executable,'-m','pytest',str(ROOT/'tests/test_m1.py'),str(ROOT/'m3_tests.py'),'-q','--junitxml='+str(OUT/'tests.xml')]
elif sys.argv[1]=='aggregate':command=[sys.executable,str(ROOT/'m3_aggregate.py')]
elif sys.argv[1]=='plots':command=[sys.executable,str(ROOT/'m3_plots.py')]
else:command=[sys.executable,str(ROOT/'m3_worker.py'),*sys.argv[1:]]
ok=monitor.run(command,'_'.join(sys.argv[1:]));print('_'.join(sys.argv[1:]),'PASS' if ok else 'STOP');sys.exit(0 if ok else 2)
