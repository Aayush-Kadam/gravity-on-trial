"""Explicit official-data acquisition, hash checked, never overwrites frozen files."""
import argparse,hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--fetch',action='store_true',help='Download only missing source files from the official URLs');args=parser.parse_args()
    entries=json.loads((ROOT/'data/manifests/acquisition.json').read_text());results=[]
    for e in entries:
        path=ROOT/'data/raw'/e['url'].rsplit('/',1)[1]
        if not path.exists():
            if not args.fetch:results.append({'file':path.name,'status':'MISSING; use --fetch after reviewing provenance'});continue
            with urllib.request.urlopen(e['url'],timeout=30) as response:raw=response.read(5_000_001)
            if len(raw)>5_000_000 or hashlib.sha256(raw).hexdigest()!=e['sha256']:raise ValueError('Source bytes changed; no file saved: '+e['url'])
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        if actual!=e['sha256']:raise ValueError('Existing source hash mismatch; file was not overwritten: '+str(path))
        results.append({'file':path.name,'status':'VERIFIED','sha256':actual})
    print(json.dumps(results,indent=2))
if __name__=='__main__':main()
