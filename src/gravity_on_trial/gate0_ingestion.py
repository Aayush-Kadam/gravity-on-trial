"""Bounded official-source acquisition and fixed-width ingestion; no fitting."""
import collections
import datetime
import decimal
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import time
import urllib.request
import zipfile
import io
import psutil

ROOT = Path(__file__).resolve().parents[2]

def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False), encoding='utf-8')

def parse_table(path, specifications, first_row):
    lines = path.read_text(encoding='ascii').splitlines()
    # Data follow the last full horizontal separator, per the source format.
    start = max(i for i, line in enumerate(lines) if line.startswith('---')) + 1
    rows = []
    for line in lines[start:]:
        if not line.strip():
            continue
        row = {}
        for name, lo, hi, conversion in specifications:
            value = line[lo-1:hi].strip()
            row[name] = conversion(value) if value else None
        rows.append(row)
    if not rows or rows[0]['ID'] != first_row:
        raise ValueError('Unexpected first row or missing table data')
    return rows

MASS = [('ID',1,11,str),('D',13,18,float),('R',20,25,float),('Vobs',27,32,float),('e_Vobs',34,38,float),('Vgas',40,45,float),('Vdisk',47,52,float),('Vbul',54,59,float),('SBdisk',61,67,float),('SBbul',69,76,float)]
CAT = [('ID',1,11,str),('T',12,13,int),('D',14,19,float),('e_D',20,24,float),('f_D',25,26,int),('Inc',27,30,float),('e_Inc',31,34,float),('L36',35,41,float),('e_L36',42,48,float),('Reff',49,53,float),('SBeff',54,61,float),('Rdisk',62,66,float),('SBdisk',67,74,float),('MHI',75,81,float),('RHI',82,86,float),('Vflat_source',87,91,float),('e_Vflat_source',92,96,float),('Q',97,99,int),('Ref',100,113,str)]
# This acquired author's catalog inserts one separator before EACH field after ID,
# unlike its byte-description. Preserve the raw file and record this discrepancy.
CAT = [(name,lo+max(0,i-1),hi+i,kind) if i else (name,lo,hi,kind)
       for i,(name,lo,hi,kind) in enumerate(CAT)]

def main():
    begun=time.perf_counter(); process=psutil.Process(); cpu=process.cpu_times()
    initial=psutil.virtual_memory().available
    config=json.loads((ROOT/'configs/gate0.json').read_text())
    attempts=[]
    original_manifest=ROOT/'data/manifests/acquisition.json'
    previous_entries=json.loads(original_manifest.read_text()) if original_manifest.exists() else []
    for filename in ['SPARC_Lelli2016c.mrt','MassModels_Lelli2016c.mrt','Rotmod_LTG.zip']:
        url='https://astroweb.case.edu/SPARC/'+filename
        entry={'url':url,'attempt_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        path=ROOT/'data/raw'/filename
        try:
            if path.exists():
                body=path.read_bytes(); entry['retrieval']='existing frozen local file'
                previous=next((p for p in previous_entries if p['url']==url and p.get('accepted')),None)
                if previous and hashlib.sha256(body).hexdigest()!=previous['sha256']:
                    raise ValueError('Frozen raw file hash changed')
            else:
                with urllib.request.urlopen(url, timeout=30) as response:
                    body=response.read(10_000_001)
                    entry.update(status=response.status,content_type=response.headers.get('Content-Type'),final_url=response.url)
                if len(body)>10_000_000:
                    raise ValueError('Acquisition exceeds 10 MB bounded pilot cap')
                if filename.endswith('.mrt') and not body.startswith(b'Title:'):
                    raise ValueError('Not an author MRT table')
                if filename.endswith('.zip'):
                    with zipfile.ZipFile(io.BytesIO(body)) as archive:
                        if archive.testzip() is not None:
                            raise ValueError('Corrupt ZIP')
                        entry['archive_members']=len(archive.namelist())
                path.write_bytes(body)
            entry.update(bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),accepted=True)
        except Exception as error:
            entry.update(accepted=False,error=str(error))
        attempts.append(entry)
        save(ROOT/'data/manifests/acquisition.json',attempts)
    if not all(x['accepted'] for x in attempts[:2]):
        raise RuntimeError('Essential official data acquisition blocked; manifest retained')
    cat=parse_table(ROOT/'data/raw/SPARC_Lelli2016c.mrt',CAT,'CamB')
    mass=parse_table(ROOT/'data/raw/MassModels_Lelli2016c.mrt',MASS,'CamB')
    ids=[r['ID'] for r in cat]; by_id={r['ID']:r for r in cat}
    errors=[]
    if len(ids)!=len(set(ids)): errors.append('Duplicate catalog IDs')
    if set(ids)!={r['ID'] for r in mass}: errors.append('Catalog/mass ID mismatch')
    previous={}; negative=[]; distance_mismatches=[]
    for index,row in enumerate(mass):
        if any(not math.isfinite(v) for v in row.values() if isinstance(v,float)): errors.append(f'Nonfinite row {index}')
        if row['R']<=0 or row['e_Vobs']<=0: errors.append(f'Nonpositive radius/error row {index}')
        if row['R']<=previous.get(row['ID'],-1): errors.append(f'Non-increasing radius row {index}')
        previous[row['ID']]=row['R']
        if row['Vgas']<0: negative.append({'row_index':index,**row})
        if abs(row['D']-by_id[row['ID']]['D'])>config['distance_tolerance_Mpc']: distance_mismatches.append(index)
    manual=[]
    D=decimal.Decimal
    for galaxy in config['selected_galaxies']:
        rows=[r for r in mass if r['ID']==galaxy]
        for row in [rows[0],rows[len(rows)//2],rows[-1]]:
            ordinary=.5*row['Vdisk']**2+.7*row['Vbul']**2+row['Vgas']*abs(row['Vgas'])
            gas=D(str(row['Vgas']))
            independent=D('0.5')*D(str(row['Vdisk']))**2+D('0.7')*D(str(row['Vbul']))**2+gas*abs(gas)
            difference=abs(ordinary-float(independent))
            if difference>config['independent_signed_force_absolute_tolerance_km2_s2']: errors.append('Signed force discrepancy')
            manual.append({'ID':galaxy,'R_kpc':row['R'],'signed_vbar_sq_km2_s2':ordinary,'decimal_independent':str(independent),'absolute_difference':difference})
    snapshot={'catalog':cat,'mass_models':mass}
    canonical=json.dumps(snapshot,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    save(ROOT/'results/gate0/parsed_tables.json',snapshot)
    save(ROOT/'results/gate0/manual_checks.json',manual)
    save(ROOT/'results/gate0/negative_gas_rows.json',negative)
    report={'galaxies':len(cat),'radial_rows':len(mass),'negative_gas_rows':len(negative),'negative_gas_galaxies':len({r['ID'] for r in negative}),'quality_counts':dict(collections.Counter(str(r['Q']) for r in cat)),'distance_mismatch_indices':distance_mismatches,'errors':errors,'canonical_parsed_sha256':hashlib.sha256(canonical).hexdigest(),'selection':[{**by_id[g],'radial_points':sum(r['ID']==g for r in mass)} for g in config['selected_galaxies']],'missingness_policy':'Source Vflat=0 retained as Vflat_source, not interpreted as a measured zero or converted without authoritative confirmation. Vbul=0 remains a source component value, not a claim of independently observed bulge absence.','units':'D Mpc; R kpc; velocities km/s; surface brightness solar luminosities/pc^2; inclination degrees; Q dimensionless'}
    save(ROOT/'results/gate0/ingestion_validation.json',report)
    mem=process.memory_info(); end_cpu=process.cpu_times()
    available=psutil.virtual_memory().available
    resource={'python':sys.version.split()[0],'platform':platform.system(),'elapsed_seconds':time.perf_counter()-begun,'cpu_seconds':end_cpu.user+end_cpu.system-cpu.user-cpu.system,'initial_available_MiB':initial/2**20,'final_available_MiB':available/2**20,'peak_process_working_set_MiB':getattr(mem,'peak_wset',mem.rss)/2**20,'current_process_RSS_MiB':mem.rss/2**20,'disk_free_GiB':psutil.disk_usage(str(ROOT)).free/2**30,'GPU_used':False,'fitting_resource_gate_passed':available>=config['minimum_available_memory_before_scientific_imports_MiB']*2**20}
    save(ROOT/'results/gate0/resources.json',resource)
    print(json.dumps({'validation':{k:v for k,v in report.items() if k not in ['selection','missingness_policy','units']},'resources':resource}))

if __name__=='__main__': main()

