"""Independent token-boundary and clean-process ingestion checks, not physics tests."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parent
before=json.loads((root/'results/gate0/ingestion_validation.json').read_text())
tables=json.loads((root/'results/gate0/parsed_tables.json').read_text())
catalog_lines=(root/'data/raw/SPARC_Lelli2016c.mrt').read_text().splitlines()[98:]
checks=[]
for source, parsed in zip(catalog_lines,tables['catalog'],strict=True):
    tokens=source.split()
    assert tokens[0]==parsed['ID']
    for name,index in [('D',2),('e_D',3),('Inc',5),('e_Inc',6),('Vflat_source',15),('e_Vflat_source',16),('Q',17)]:
        assert float(tokens[index])==parsed[name], (parsed['ID'],name)
checks.append('All 175 catalog rows: independently tokenized IDs, D/e_D, inclination/error, Vflat/error and Q equal fixed-width output')
mass_lines=(root/'data/raw/MassModels_Lelli2016c.mrt').read_text().splitlines()[25:]
for source,parsed in zip(mass_lines,tables['mass_models'],strict=True):
    tokens=source.split()
    assert tokens[0]==parsed['ID']
    for j,name in enumerate(['D','R','Vobs','e_Vobs','Vgas','Vdisk','Vbul','SBdisk','SBbul'],1):
        assert float(tokens[j])==parsed[name]
checks.append('All 3391 mass-model rows: independent tokenization equals all fixed-width fields, including signed gas')
subprocess.run([sys.executable,str(root/'src/gravity_on_trial/gate0_ingestion.py')],check=True,capture_output=True,text=True)
after=json.loads((root/'results/gate0/ingestion_validation.json').read_text())
assert before['canonical_parsed_sha256']==after['canonical_parsed_sha256']
checks.append('Fresh Python process: canonical parsed table SHA-256 identical')
out={'checks_passed':checks,'scope':'Ingestion verification only. No numerical model or optimizer tests executed.','canonical_parsed_sha256':after['canonical_parsed_sha256']}
(root/'results/gate0/verification.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
