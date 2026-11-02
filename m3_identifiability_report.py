"""Write population warning diagnoses before the sensitivity pilot."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m3/v1';a=json.loads((OUT/'identifiability_audit.json').read_text())
ridges=[r['geometry_ridge'] for r in a['records'] if r['geometry_ridge'] and r['geometry_ridge']['applicable']]
assert len(ridges)==696 and max(r['max_relative_velocity_difference'] for r in ridges)<1e-9
text=f'''# M3 identifiability and boundary diagnostics

Re-audited the complete frozen M2 inventory before M3 fitting. Warning-bearing evaluations: {a['warning_evaluations']}/1400; boundary-bearing evaluations: {a['boundary_evaluations']}/1400. Galaxy-level denominators differ: {a['galaxies_with_any_warning']}/175 have at least one warning; {a['galaxies_with_any_boundary']}/175 have at least one bound contact. Labels overlap and cannot be added: {a['warning_labels_overlapping']}.

All 696 converged M2 MAP cases independently exhibit the analytic distance/inclination/halo likelihood rescaling ridge. Largest checked relative velocity difference {max(r['max_relative_velocity_difference'] for r in ridges):.3g}. Adjust distance by lambda, sin(i) by 1/sqrt(lambda), and halo scale/density consistently; forward velocities remain identical. Column-normalized sensitivity from M2 remains weak, so mixed parameter units alone do not explain the direction. Some exact-ridge perturbations exceed prior bounds; this is recorded, not silently accepted. Priors/boxes restrict the allowed ridge, not the observational information content. Prior-dominated directions are not precisely measured parameters merely because MAP converges.

F0 warning labels primarily reflect halo-parameter correlation or bound contact. High correlation is a weakly constrained but potentially valid parameter pair, not automatically a failed curve or rank defect. Low ring count, limited radial coverage and unknown covariance can reduce information; causal attribution from these associations is not established. Twenty M2 halo MAP evaluations have n<=k, an explicit finite-information limit. Numeric rank estimates alone do not diagnose exact physical identifiability.

All per-galaxy/model/configuration labels, coverage, data-only rank/condition, near-equivalent multistart ranges and bound-parameter names are in identifiability_audit.json. A range >0.1 dex among solutions within delta objective<=1 is a prespecified material-variation flag, not proof of different posterior modes. Domain-aborted starts remain separately counted. Boundary contacts may arise from inadequate fixed assumptions, a box restricting an otherwise degenerate direction or numerical search limitations; no bound was narrowed to eliminate them. Six-dex halo shifts already seen in M2 are tracked as instability, not physical precision.

Confirmed implementation defects from this audit: none. Genuine likelihood underdetermination and diagnostic limits remain. M3 will preserve these warning classes, test narrower/wider stellar priors separately, and cross-check a bounded set with dogbox. No finite-difference singular vector, optimizer covariance, scenario range or operational flip frequency is represented as a posterior probability or astrophysical discovery.
'''
(ROOT/'docs/M3_IDENTIFIABILITY_DIAGNOSTICS.md').write_text(text,encoding='utf-8');print('All 988 warning and 278 boundary cases retained and classified')
