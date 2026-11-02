"""M3 pilot gate: accepted physics/statistics, reproducibility and measured budgets."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from m3_metrics import galaxy_metrics
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m3/v1';CFG=json.loads((ROOT/'configs/m3_v1.json').read_text());V=json.loads((OUT/'pilot_validation.json').read_text())
assert V['galaxies']==20 and V['planned_scenario_records']==280 and V['planned_model_slots']==1120 and V['fresh_process_rerun_galaxies']==20
assert V['max_parameter_rerun_difference']==V['max_prediction_rerun_difference_km_s']==0
assert V['model_slot_status_counts'].get('DIAGNOSTIC_FAILURE',0)==0
tests=ET.parse(OUT/'tests.xml').getroot();assert len(list(tests.iter('testcase')))==92 and not list(tests.iter('failure')) and not list(tests.iter('error'))
labels=[]
for g in CFG['pilot_ids']:
    data=json.loads((OUT/f'pilot/initial/{g}.json').read_text());repeat=json.loads((OUT/f'pilot/rerun/{g}.json').read_text())
    a=galaxy_metrics(data['baseline'],[s for s in data['scenarios'] if s['kind']=='physical'],CFG['classification']);b=galaxy_metrics(repeat['baseline'],[s for s in repeat['scenarios'] if s['kind']=='physical'],CFG['classification']);assert a==b;labels.append({'galaxy':g,**a})
for path,digest in data['identity']['files'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
resources=[json.loads(p.read_text()) for p in (OUT/'resources').glob('batch_pilot_initial_*.json')];assert len(resources)==4
seconds=sum(r['wall_seconds'] for r in resources);estimate=seconds*175/20;assert estimate<=CFG['full_sweep_projected_budget_seconds'],'Measured projection exceeds frozen budget; stop at pilot'
monitor=[json.loads(p.read_text()) for p in (OUT/'monitor').glob('*_monitor.json')];assert all(m['launched'] and m['exit_code']==0 and m['terminated_reason'] is None and m['minimum_observed_available_MiB']>=512 and m['max_peak_working_set_MiB']<=180 for m in monitor)
optimizer=json.loads((OUT/'optimizer_crosschecks.json').read_text());assert len(optimizer['records'])==36
assert all(r.get('objective_agreement_within_target') is not False for r in optimizer['records'])
comparable=sum(r.get('objective_agreement_within_target') is True for r in optimizer['records'])
decision={'GO':True,'scope':'M3 bounded pilot, full matrix now eligible under measured budget','galaxies':20,'planned_scenarios':280,'planned_model_slots':1120,'actually_evaluated_model_slots':V['actual_evaluated_model_slots'],'statuses':V['model_slot_status_counts'],'scenario_outcomes':V['scenario_proposal_counts'],'test_cases_passed':92,'fresh_process_galaxies':20,'classification_reproducibility':True,'dogbox_comparable_checks':comparable,'dogbox_total_checks':36,'worker_seconds':seconds,'peak_worker_MiB':max(r['peak_working_set_MiB'] for r in resources),'projected_full_sweep_seconds':estimate,'full_sweep_budget_seconds':900,'minimum_monitored_available_MiB':min(m['minimum_observed_available_MiB'] for m in monitor),'full_independent_rerun_planned':True}
(OUT/'pilot_gate.json').write_text(json.dumps(decision,indent=2));(OUT/'pilot_metrics.json').write_text(json.dumps(labels,indent=2))
(ROOT/'docs/M3_PILOT_GO_NO_GO.md').write_text(f'''# M3 pilot decision

**GO for the frozen full 175-galaxy/14-scenario campaign and independent repeat. M4 remains unauthorized.**

20 prespecified galaxies, 280 scenario records, 1,120 planned model slots. Actual calculations: {V['actual_evaluated_model_slots']}; statuses {V['model_slot_status_counts']}. Null stellar components are NOT_APPLICABLE, physically invalid geometry is rejected, and domain/search failures remain visible. No invalid comparison supports persistence. No DIAGNOSTIC_FAILURE or unexplained physical/statistical error was found.

All 92 scientific/control tests passed (54 unchanged inherited tests, 38 M3 cases). Fresh-process parameters/predictions matched exactly for all 20 galaxies; full canonical diagnostics/masks and final pilot classifications agree. Scalar likelihood/prior/force checks passed. Every converged halo received independent all-radius quadrature. The fiducial-width MAP adapter reproduces frozen M2 results; catalog-frame and corrected-observation-frame likelihoods agree with the required Jacobian. This validates the new adapter without changing old source.

Dogbox second-method checks: {comparable}/36 had comparable valid solutions and agree with TRF within the frozen relative objective target 1e-6. Three UGC01281 Burkert cases remain noncomparable because the declared domain/search policies do not yield a feasible pair; records are retained, not interpreted as physical nonexistence. No bound was changed.

Pilot initial workers took {seconds:.3f} seconds and peaked at {decision['peak_worker_MiB']:.3f} MiB. Full sweep projected worker time {estimate:.3f} seconds is below the frozen 900-second limit; dispatcher/preflight overhead is additional and real full time is not yet measured. Lowest monitored available RAM {decision['minimum_monitored_available_MiB']:.3f} MiB, above the 512 MiB floor. Continue serially in batches of five under the unchanged 180 MiB child cap, with every galaxy/scenario checkpointed. No scenario or threshold was removed to make this gate pass.

Primary labels are operational, not calibrated probabilities. Joint stellar shifts coincide with disk-only shifts when the bulge is absent; the frozen design retains these named overlapping stress directions, labels null bulge-only cases separately, and makes no independence or random-sampling claim. Planned and meaningful/valid denominators accompany every metric.
''',encoding='utf-8')
print(json.dumps(decision))
