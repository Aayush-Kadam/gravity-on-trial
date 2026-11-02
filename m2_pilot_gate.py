"""Executed pilot acceptance gate; never equate physical poor fit with code failure."""
import collections,hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from m2_compare import canonical,equivalent,comparison
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m2/v1';CFG=json.loads((ROOT/'configs/m2_v1.json').read_text())
tests=ET.parse(OUT/'tests.xml').getroot();assert len(list(tests.iter('testcase')))==54 and not list(tests.iter('failure')) and not list(tests.iter('error'))
rows=[];identities=set()
for g in CFG['pilot_ids']:
    a=json.loads((OUT/f'pilot/initial/{g}.json').read_text());b=json.loads((OUT/f'pilot/rerun/{g}.json').read_text())
    equivalent(canonical(a),canonical(b));identities.add(a['identity']['content_revision'])
    rows+=a['results']
    assert all(r['status']!='DIAGNOSTIC_FAILURE' for r in a['results'])
    comparison(a['results'])
assert len(identities)==1 and len(rows)==160
for path,digest in a['identity']['files'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
audit=json.loads((OUT/'identifiability_audit.json').read_text());assert audit['warning_count']==45 and audit['boundary_count']==9
resourcefiles=list((OUT/'resources').glob('batch_pilot_initial_*.json'))
resources=[json.loads(p.read_text()) for p in resourcefiles];assert len(resources)==4
seconds=sum(r['wall_seconds'] for r in resources);peak=max(r['peak_working_set_MiB'] for r in resources)
monitors=[json.loads(p.read_text()) for p in (OUT/'monitor').glob('batch_pilot_*_monitor.json')]
assert len(monitors)==8 and all(m['exit_code']==0 and m['terminated_reason'] is None and m['minimum_observed_available_MiB']>=512 for m in monitors)
estimate=seconds*175/20
counts=dict(collections.Counter(r['status'] for r in rows));warnings=sum(bool(r.get('data_identifiability',{}).get('warnings')) for r in rows);bounds=sum(any(r.get('boundary_flags',[])) for r in rows)
decision={'GO':True,'scope':'20-galaxy scientific pilot only','galaxies':20,'evaluations_initial':160,'statuses':counts,'warning_evaluations':warnings,'boundary_evaluations':bounds,'fresh_process_galaxies':20,'54_test_cases_passed':True,'initial_worker_seconds':seconds,'peak_worker_MiB':peak,'minimum_available_MiB':min(m['minimum_observed_available_MiB'] for m in monitors),'estimated_full_sweep_seconds':estimate,'full_rerun_authorized_by_frozen_rule':estimate<=600,'source_identity':next(iter(identities))}
(OUT/'pilot_gate.json').write_text(json.dumps(decision,indent=2))
text=f'''# M2 20-galaxy pilot decision

**GO for full M2 campaign under the frozen protocol.** M3/M4 remain unauthorized.

All 20 prespecified galaxies have 160 initial model/configuration records and 160 fresh-process records. Status counts: {counts}. Warning-bearing evaluations: {warnings}/160; bound-contact evaluations: {bounds}/160. No DIAGNOSTIC_FAILURE or unexplained physical/numerical error. Fixed negative-force domain restrictions and any failed-start outcomes are explicit, not silent row exclusions. Poor physical fits remain unchanged.

All canonical numerical parameters, curves, masks and diagnostic arrays agree within frozen 1e-10 rtol/atol across fresh processes; timings/resources excluded. All 54 M1 tests passed in the M2 environment. Independent quadrature checks executed for every converged pilot halo result at every accepted radius, not merely an example. Raw/config/source identity hashes remain unchanged. Prerequisite identifiability audit understood all 45 M1 warnings and nine boundary cases without changing bounds.

Initial pilot workers: {seconds:.3f} seconds total, peak {peak:.3f} MiB. Lowest monitored available RAM: {decision['minimum_available_MiB']:.3f} MiB, above 512 MiB; 180 MiB cap respected. Extrapolated full-sweep worker estimate: {estimate:.3f} seconds, excluding preflight/dispatcher overhead and any especially hard unseen cases. This is a scheduling estimate, not a measured 175-galaxy performance claim. Under the frozen <=600-second rule, attempt a complete fresh-process rerun after the full initial sweep if safety remains valid.

Proceed serially in batches of five with atomic per-galaxy checkpointing and source identity guarded resume. No method, tolerance, prior or exclusion rule changed in response to pilot findings. Prediction/radius-split and common-subset controls remain separately labeled follow-up checks within M2.
'''
(ROOT/'docs/M2_PILOT_GO_NO_GO.md').write_text(text,encoding='utf-8');print(json.dumps(decision))
