"""Explicit rerun after input-schema hardening; earlier evidence archived."""
import json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
config=json.loads((root/'configs/m1_v1.json').read_text())
for command in [['tests'],*[['real',g,rep] for g in config['galaxies'] for rep in ['initial','rerun']],['controls'],['references'],['plots'],['preview']]:
    result=subprocess.run([sys.executable,str(root/'m1_monitor.py'),*command])
    if result.returncode:sys.exit(result.returncode)
subprocess.run([sys.executable,str(root/'m1_campaign.py')],check=True)
