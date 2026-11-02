"""Read-only whole-catalog M4 verification; writes only the M4 evidence folder."""
import csv,hashlib,io,json,time
from pathlib import Path
import numpy as np
from m4_adapter import *
def main():
    start=time.perf_counter();out=ROOT/'results/m4/v1';out.mkdir(parents=True,exist_ok=True)
    m=read('results/m3/v1/artifacts_manifest.json');bad=[]
    for path,want in m.items():
        p=ROOT/path
        # Shared pointers are archived before M4 documentation updates.
        if path in ['README.md','docs\\GATE_LEDGER.md','docs/GATE_LEDGER.md'] and (out/('previous_'+p.name)).exists():p=out/('previous_'+p.name)
        if not p.is_file() or digest(p)!=want:bad.append(path)
    assert not bad,bad
    from m1_worker import load
    checks=0;points=0;unsupported=0;models=0;negative=0
    for g in catalog():
        b=read(baseline_path(g));original=load(g);c=curve(b);negative+=int(np.sum(c.gas<0));points+=len(c.r)
        for a,key in [(original.r,'radius_kpc'),(original.obs,'observed_km_s'),(original.err,'error_km_s'),(original.gas,'gas_signed_km_s'),(original.disk,'disk_unit_ML_km_s'),(original.bulge,'bulge_unit_ML_km_s')]:np.testing.assert_array_equal(a,b[key]);checks+=1
        for r in b['results']:
            models+=1
            if r['status']!='CONVERGED':unsupported+=1;continue
            pred=predict(c,r['model'],r['parameters'][:2] if r['model'] in ['nfw','burkert'] else [],**assumptions(b,r))
            np.testing.assert_allclose(pred,r['prediction_km_s'],rtol=1e-10,atol=1e-8)
            np.testing.assert_allclose((pred-c.obs)/c.err,r['statistics']['standardized_residuals'],rtol=1e-9,atol=1e-8)
            if r['model'] in ['nfw','burkert']:
                try:removed=remove_halo(b,r);expected=predict(c,'baryons',[],**assumptions(b,r));np.testing.assert_array_equal(removed['prediction_km_s'],expected)
                except DomainError:pass # Explicitly unsupported, never clamped.
    rows=read('results/m3/v1/atlas_metrics.json');summary=read('results/m3/v1/atlas_summary.json')
    from collections import Counter
    assert dict(Counter(r['classification'] for r in rows))==summary['primary_classification_counts']
    assert sum(r['counts']['retained'] for r in rows)==906
    assert sum(r['counts']['flipped'] for r in rows)==52
    assert sum(r['counts']['to_inconclusive'] for r in rows)==70
    report={'status':'PASS','M3_manifest_files':len(m),'M3_mismatches':bad,'galaxies':len(catalog()),'observational_radii':points,'negative_gas_rows':negative,'exact_source_array_checks':checks,'baseline_model_records':models,'nonconverged_records_retained':unsupported,'preview_uses_validated_engine':True,'vertical_slice':validate_vertical(),'seconds':time.perf_counter()-start}
    (out/'data_integrity.json').write_bytes(json_bytes(report));print(json.dumps(report))
if __name__=='__main__':main()
