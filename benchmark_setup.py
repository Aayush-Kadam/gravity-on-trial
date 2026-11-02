"""Source-only, checkpointed, atomic benchmark bootstrap. No developer data imports."""
import argparse,collections,datetime,hashlib,importlib.metadata,json,math,os,shutil,subprocess,sys,time,urllib.request,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SCHEMA='gravity-source-bootstrap-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,data):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.tmp');tmp.write_text(json.dumps(data,indent=2,sort_keys=True,allow_nan=False),encoding='utf-8');os.replace(tmp,p)
def require(condition,message):
    if not condition:raise RuntimeError(message)
def source_identity(root):
    cfg=read(root/'configs/r0r_source_contract.json')
    for name,want in cfg['files'].items():require(sha(root/name)==want,'Frozen scientific source/config mismatch: '+name)
    files={name:sha(root/name) for name in cfg['files']}
    for name in ['benchmark_setup.py','m3_aggregate.py','m3_validate.py','m3_independent_audit.py','m3_plots.py','requirements-r0-lock.txt','data/manifests/acquisition.json']:
        files[name]=sha(root/name)
    return {'schema':SCHEMA,'files':files,'revision':hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()}
def check_environment(root):
    require(sys.version_info[:2]==(3,12) and os.name=='nt','This validated bootstrap requires Windows and Python 3.12; other environments are not validated')
    for line in (root/'requirements-r0-lock.txt').read_text(encoding='utf-8-sig').splitlines():
        if '==' in line and not line.startswith('#'):
            name,version=line.strip().split('==');require(importlib.metadata.version(name)==version,'Dependency mismatch: '+name+'; install requirements-r0-lock.txt in an isolated environment')
def fetch(url):
    with urllib.request.urlopen(url,timeout=30) as r:
        body=r.read(5_000_001);status=r.status;final=r.url
    require(len(body)<=5_000_000,'Official source exceeds bounded 5 MB size')
    return body,status,final
def acquire(build,fetcher=fetch):
    started=time.perf_counter();entries=read(build/'data/manifests/acquisition.json');report=[]
    for e in entries:
        p=build/'data/raw'/e['url'].rsplit('/',1)[1];p.parent.mkdir(parents=True,exist_ok=True)
        row={'url':e['url'],'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        if p.exists():body=p.read_bytes();row['retrieval']='verified existing checkpoint'
        else:
            body,status,final=fetcher(e['url']);row.update(retrieval='official HTTP acquisition',HTTP_status=status,final_url=final)
        require(hashlib.sha256(body).hexdigest()==e['sha256'],'Unexpected source hash; no replacement saved: '+p.name)
        require(len(body)==e['bytes'],'Unexpected source byte count: '+p.name)
        if not p.exists():tmp=p.with_suffix(p.suffix+'.download');tmp.write_bytes(body);os.replace(tmp,p)
        row.update(bytes=len(body),sha256=hashlib.sha256(body).hexdigest());report.append(row)
        save(build/'results/bootstrap/v1/acquisition.json',{'complete':len(report)==len(entries),'files':report,'seconds':time.perf_counter()-started})
    return report
def normalize(build):
    sys.path.insert(0,str(build/'src'));from gravity_on_trial.gate0_ingestion import parse_table,CAT,MASS
    start=time.perf_counter();cat=parse_table(build/'data/raw/SPARC_Lelli2016c.mrt',CAT,'CamB');mass=parse_table(build/'data/raw/MassModels_Lelli2016c.mrt',MASS,'CamB')
    require(len(cat)==175 and len({r['ID'] for r in cat})==175 and len(mass)==3391,'Unexpected 175-galaxy /3391-radius schema')
    ids={r['ID'] for r in cat};require(ids=={r['ID'] for r in mass},'Catalog/mass galaxy mismatch')
    for filename,spec,rows in [('SPARC_Lelli2016c.mrt',CAT,cat),('MassModels_Lelli2016c.mrt',MASS,mass)]:
        lines=(build/'data/raw'/filename).read_text().splitlines();startline=max(i for i,l in enumerate(lines) if l.startswith('---'))+1;tokens=[l.split() for l in lines[startline:] if l.strip()]
        require(len(tokens)==len(rows),'Raw token/parsed row mismatch')
        for t,row in zip(tokens,rows):
            require(len(t)==len(spec),'Unexpected source token schema')
            for value,(name,lo,hi,kind) in zip(t,spec):require(kind(value)==row[name],'Independent token mismatch: '+name)
    by={r['ID']:r for r in cat};previous={};negative=0;features=[]
    for r in mass:
        require(all(math.isfinite(v) for v in r.values() if isinstance(v,(int,float))),'Nonfinite observation')
        require(r['R']>previous.get(r['ID'],0) and r['e_Vobs']>0,'Unordered radius or invalid published uncertainty');previous[r['ID']]=r['R']
        require(abs(r['D']-by[r['ID']]['D'])<=.05,'Catalog/mass distance mismatch');negative+=r['Vgas']<0
    require(negative==361,'Signed gas inventory mismatch')
    for c in cat:
        require(c['D']>0 and c['e_D']>=0 and 0<c['Inc']<=90 and c['e_Inc']>=0 and c['Q'] in [1,2,3],'Invalid catalog metadata')
        rows=[r for r in mass if r['ID']==c['ID']]
        features.append({**c,'n':len(rows),'radius_min_kpc':min(r['R'] for r in rows),'radius_max_kpc':max(r['R'] for r in rows),'negative_gas_rows':sum(r['Vgas']<0 for r in rows),'nonpositive_bar_rows':[i for i,r in enumerate(rows) if .5*r['Vdisk']**2+.7*r['Vbul']**2+r['Vgas']*abs(r['Vgas'])<=0],'bulge_max_squared':max(r['Vbul']**2 for r in rows),'gas_to_light_proxy':c['MHI']/c['L36']})
    save(build/'results/gate0/parsed_tables.json',{'catalog':cat,'mass_models':mass});save(build/'results/m2/v1/inventory.json',{'galaxies':features})
    report={'galaxies':175,'radii':3391,'signed_negative_gas_rows':negative,'independent_token_validation':True,'units':'D Mpc; R kpc; speeds/errors km/s; inclinations degrees; stellar components unit solar M/L at 3.6 microns','seconds':time.perf_counter()-start};save(build/'results/bootstrap/v1/data_validation.json',report);return report
def verify_checkpoint(build,path,identity):
    data=read(path);require(data.get('bootstrap_identity')==identity['revision'],'Checkpoint source identity mismatch')
    seal=path.with_suffix('.sha256');require(seal.exists() and seal.read_text()==sha(path),'Incomplete/corrupted checkpoint: '+path.name)
    return data
def seal(path):path.with_suffix('.sha256').write_text(sha(path))
def commit_checkpoint(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);raw=json.dumps(data,indent=2,sort_keys=True,allow_nan=False).encode('utf-8')
    tmp=path.with_name(path.name+'.tmp');tmp.write_bytes(raw);sealpath=path.with_suffix('.sha256');sealtmp=sealpath.with_name(sealpath.name+'.tmp');sealtmp.write_text(hashlib.sha256(raw).hexdigest());os.replace(sealtmp,sealpath);os.replace(tmp,path)
def worker(build,stage,ids):
    build=Path(build);sys.path.insert(0,str(build));sys.path.insert(0,str(build/'src'))
    import m2_worker as m2
    from m1_worker import load
    from m2_compare import comparison
    identity=read(build/'bootstrap_identity.json')
    if stage=='m3':
        import m3_worker as m3
        ident=m3.identity();comparisons={r['galaxy']:r for r in read(build/'results/m2/v1/comparison_records.json')}
    else:ident=m2.identity()
    for g in ids:
        path=build/f'results/{stage}/v1/full/initial/{g}.json'
        if path.exists():
            old=verify_checkpoint(build,path,identity);(m2.validate_file(old) if stage=='m2' else m3.validate_data(old));continue
        c=load(g)
        if stage=='m2':
            data={'galaxy':g,'stage':'full','replicate':'initial','metadata':c.metadata,'n_inventory':len(c.r),'radius_kpc':c.r.tolist(),'observed_km_s':c.obs.tolist(),'error_km_s':c.err.tolist(),'gas_signed_km_s':c.gas.tolist(),'disk_unit_ML_km_s':c.disk.tolist(),'bulge_unit_ML_km_s':c.bulge.tolist(),'identity':ident,'results':[],'source_url':'https://astroweb.case.edu/SPARC/MassModels_Lelli2016c.mrt','quality_flags':{'Q3':c.metadata['Q']==3,'low_inclination':c.metadata['Inc']<30},'bootstrap_identity':identity['revision']}
            for mode in m2.CFG['modes']:
                for model in m2.CFG['models']:data['results'].append(m2.evaluate(c,model,mode));save(path.with_suffix('.partial.json'),data)
            m2.validate_file(data)
        else:
            base=read(build/f'results/m2/v1/full/initial/{g}.json');data={'galaxy':g,'stage':'full','replicate':'initial','identity':ident,'metadata':c.metadata,'n_inventory':len(c.r),'radius_catalog_kpc':c.r.tolist(),'observed_km_s':c.obs.tolist(),'error_km_s':c.err.tolist(),'gas_signed_km_s':c.gas.tolist(),'disk_unit_ML_km_s':c.disk.tolist(),'bulge_unit_ML_km_s':c.bulge.tolist(),'baseline':comparisons[g]['four_way'],'baseline_results':base['results'],'scenarios':[],'bootstrap_identity':identity['revision']}
            for scenario in m3.CFG['scenarios']:data['scenarios'].append(m3.one_scenario(c,scenario));save(path.with_suffix('.partial.json'),data)
            m3.validate_data(data)
        data['complete']=True;commit_checkpoint(path,data);print(stage,g,'complete',flush=True)
def manifest(build,stage):
    folder=build/f'results/{stage}/v1';paths=[p for p in folder.rglob('*') if p.is_file() and p.name!='artifacts_manifest.json' and not p.name.endswith(('.tmp','.partial.json'))]
    save(folder/'artifacts_manifest.json',{str(p.relative_to(build)):sha(p) for p in sorted(paths)})
def m2_summary(build):
    sys.path.insert(0,str(build));from m2_compare import comparison
    cfg=read(build/'configs/m3_v1.json');records=[]
    for g in cfg['population_ids']:
        b=read(build/f'results/m2/v1/full/initial/{g}.json');m=b['metadata'];records.append({'galaxy':g,'higher_quality':m['Q']<=2 and m['Inc']>=30,'four_way':comparison(b['results']),'NFW_Burkert':comparison(b['results'],['nfw','burkert'])})
    save(build/'results/m2/v1/comparison_records.json',records);manifest(build,'m2')
def monitor(command,build,label):
    from recovery_monitor import available
    from r0_processes import usage,stop_tree
    import psutil
    head=[]
    for i in range(5):
        head.append(available())
        if i<4:time.sleep(.5)
    require(min(head)>=768 and max(head)-min(head)<=128,'Memory preflight refused; no child launched. Resume the same command later.')
    start=time.perf_counter();peak=0;low=min(head);reason=None;env=dict(os.environ,PYTHONPATH='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
    logdir=build/'results/bootstrap/v1/monitor';logdir.mkdir(parents=True,exist_ok=True);name=label+'_'+uuid.uuid4().hex[:8]
    with (logdir/(name+'.stdout')).open('w') as out,(logdir/(name+'.stderr')).open('w') as err:
        p=subprocess.Popen(command,cwd=build,env=env,stdout=out,stderr=err);proc=psutil.Process(p.pid)
        try:
            while p.poll() is None:
                rss,hwm=usage(proc);peak=max(peak,hwm);low=min(low,available())
                if peak>180 or low<512 or time.perf_counter()-start>180:reason='180 MiB process-tree /512 MiB system floor /180 second batch bound';stop_tree(proc);break
                time.sleep(.05)
            p.wait(timeout=10)
        finally:
            if p.poll() is None:stop_tree(proc)
    report={'label':label,'seconds':time.perf_counter()-start,'tree_peak_MiB_conservative_upper_bound':peak,'minimum_available_MiB':low,'exit_code':p.returncode,'stopped_reason':reason,'preflight_MiB':head};save(logdir/(name+'.json'),report)
    require(p.returncode==0 and reason is None,'Computation failed or stopped: '+label+'; inspect '+str(logdir/(name+'.stderr')))
    return report
def validate_results(root):
    cfg=read(root/'configs/m3_v1.json');identity=read(root/'bootstrap_identity.json');counts=collections.Counter();n=0
    for g in cfg['population_ids']:
        for stage in ['m2','m3']:
            p=root/f'results/{stage}/v1/full/initial/{g}.json';d=verify_checkpoint(root,p,identity)
            require(d.get('complete') is True and d['galaxy']==g,'Incomplete/wrong galaxy record')
            if stage=='m2':require(len(d['results'])==8,'Missing M2 evaluation');n+=d['n_inventory']
            else:
                require(len(d['scenarios'])==14,'Missing M3 scenario')
                for s in d['scenarios']:
                    require(len(s['results'])==4,'Missing scenario model');counts.update(r['status'] for r in s['results'])
    require(n==3391 and sum(counts.values())==9800,'Incomplete benchmark inventory')
    for stage in ['m2','m3']:
        m=read(root/f'results/{stage}/v1/artifacts_manifest.json');require(bool(m),'Missing result manifest')
        for rel,want in m.items():require(sha(root/rel)==want,'Generated artifact corruption: '+rel)
    summary=read(root/'results/m3/v1/atlas_summary.json');require(summary['galaxies']==175,'Invalid atlas schema')
    return {'schema':SCHEMA,'galaxies':175,'radii':n,'M2_model_evaluations':1400,'M3_scenario_records':2450,'M3_model_slots':9800,'M3_status_counts':dict(counts),'classification_counts':summary['primary_classification_counts']}
def state(root):
    receipt=root/'results/bootstrap/v1/receipt.json'
    if not receipt.exists():return False,'Setup required: run python benchmark_setup.py bootstrap --from-official-sources'
    try:
        r=read(receipt);require(r['schema']==SCHEMA and r['complete'] is True,'Invalid/incomplete receipt')
        for rel,want in r['required_hashes'].items():require(sha(root/rel)==want,'Missing/corrupt required input: '+rel)
        for stage,want in r['manifest_hashes'].items():require(sha(root/f'results/{stage}/v1/artifacts_manifest.json')==want,'Missing/corrupt benchmark manifest')
        return True,'Complete locally regenerated benchmark'
    except Exception as e:return False,'Setup validation failed: '+str(e)+'; run python benchmark_setup.py verify'
def bootstrap(args):
    check_environment(ROOT);identity=source_identity(ROOT);ready,_=state(ROOT)
    if ready:
        require(read(ROOT/'bootstrap_identity.json')==identity,'Existing benchmark source revision differs; use a separate source directory')
        report=validate_results(ROOT);print(json.dumps({'status':'ALREADY_COMPLETE','validation':report}));return
    require(not (ROOT/'results/bootstrap/v1/receipt.json').exists(),'Existing receipt is invalid; do not overwrite. Restore evidence or use a new directory.')
    require(not (ROOT/'results').exists() or not any(p.is_file() for p in (ROOT/'results').rglob('*')),'Existing result files are protected; use a separate fresh source directory')
    for e in read(ROOT/'data/manifests/acquisition.json'):
        p=ROOT/'data/raw'/e['url'].rsplit('/',1)[1]
        if p.exists():require(sha(p)==e['sha256'],'Existing source hash mismatch; file not overwritten: '+p.name)
    lock=ROOT/'.bootstrap/active.lock';lock.parent.mkdir(exist_ok=True)
    try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError:
        import psutil
        old=read(lock)
        require(not psutil.pid_exists(old['pid']),'Bootstrap already active; no concurrent initialization permitted')
        lock.unlink();fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    os.write(fd,json.dumps({'pid':os.getpid(),'source_revision':identity['revision']}).encode());os.close(fd);build=ROOT/'.bootstrap/build-v1';begin=time.perf_counter()
    try:
        if not build.exists():
            build.mkdir()
            for p in ROOT.glob('*.py'):shutil.copyfile(p,build/p.name)
            for folder in ['src','configs','data/manifests']:shutil.copytree(ROOT/folder,build/folder,ignore=shutil.ignore_patterns('__pycache__'))
            save(build/'bootstrap_identity.json',identity)
        require(read(build/'bootstrap_identity.json')==identity,'Interrupted build source identity changed; use a separate source distribution')
        acquire(build);normalize(build);ids=read(build/'configs/m3_v1.json')['population_ids']
        for stage in ['m2','m3']:
            for i in range(0,len(ids),5):
                batch=ids[i:i+5]
                for g in batch:
                    p=build/f'results/{stage}/v1/full/initial/{g}.json'
                    if p.exists():verify_checkpoint(build,p,identity)
                if all((build/f'results/{stage}/v1/full/initial/{g}.json').exists() for g in batch):continue
                monitor([sys.executable,str(build/'benchmark_setup.py'),'worker',str(build),stage,*batch],build,stage+'_'+str(i//5+1));print(stage,i+len(batch),'/175',flush=True)
            if stage=='m2':m2_summary(build)
            else:
                monitor([sys.executable,str(build/'m3_aggregate.py')],build,'aggregate')
                monitor([sys.executable,str(build/'m3_independent_audit.py')],build,'independent_metrics')
                monitor([sys.executable,str(build/'m3_validate.py'),'full'],build,'scalar_validation')
                monitor([sys.executable,str(build/'m3_plots.py')],build,'scientific_figures')
                manifest(build,'m3')
        report=validate_results(build);save(build/'results/bootstrap/v1/validation.json',report)
        required={'results/gate0/parsed_tables.json':sha(build/'results/gate0/parsed_tables.json'),'bootstrap_identity.json':sha(build/'bootstrap_identity.json')}
        required.update({p.relative_to(build).as_posix():sha(p) for p in (build/'data/raw').iterdir()})
        receipt={'schema':SCHEMA,'complete':True,'source_revision':identity['revision'],'manifest_hashes':{s:sha(build/f'results/{s}/v1/artifacts_manifest.json') for s in ['m2','m3']},'required_hashes':required,'validation':report,'active_invocation_seconds':time.perf_counter()-begin,'rights':'Locally generated evidence; not bundled in source release'}
        save(build/'results/bootstrap/v1/receipt.json',receipt)
        target=ROOT/'results'
        if target.exists():
            require(not any(p.is_file() for p in target.rglob('*')),'Existing result files prevent non-destructive promotion; use a fresh source directory')
            target.rename(ROOT/'.bootstrap'/('pre-setup-empty-results-'+uuid.uuid4().hex[:8]))
        for name in ['bootstrap_identity.json']:shutil.copyfile(build/name,ROOT/name)
        # Source raw bytes stay local and are excluded by the publication manifest.
        (ROOT/'data/raw').mkdir(parents=True,exist_ok=True)
        for p in (build/'data/raw').iterdir():
            dest=ROOT/'data/raw'/p.name
            if dest.exists():require(sha(dest)==sha(p),'Existing raw file mismatch; no overwrite')
            else:shutil.copyfile(p,dest)
        os.replace(build/'results',target)
        print(json.dumps({'status':'COMPLETE','receipt':'results/bootstrap/v1/receipt.json','validation':report}),flush=True)
    finally:lock.unlink(missing_ok=True)
def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('bootstrap');p.add_argument('--from-official-sources',action='store_true',required=True)
    sub.add_parser('verify');p=sub.add_parser('worker');p.add_argument('build');p.add_argument('stage');p.add_argument('ids',nargs='+')
    args=parser.parse_args()
    if args.command=='worker':worker(args.build,args.stage,args.ids)
    elif args.command=='verify':require(state(ROOT)[0],state(ROOT)[1]);print(json.dumps(validate_results(ROOT)))
    else:bootstrap(args)
if __name__=='__main__':
    try:main()
    except Exception as e:print('BOOTSTRAP STOPPED: '+str(e),file=sys.stderr);sys.exit(2)
