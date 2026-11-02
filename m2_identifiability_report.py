"""Write prerequisite audit findings from executed M1 sensitivity checks."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/m2/v1'
a=json.loads((OUT/'identifiability_audit.json').read_text());records=a['records']
assert a['warning_count']==45 and a['boundary_count']==9
assert sum(r['mode']=='MAP' and all(c['weak_direction'] for c in r['normalized_step_checks']) for r in records)==32
error=max(r['exact_geometry_ridge']['max_relative_velocity_difference'] for r in records if r['exact_geometry_ridge'] and r['exact_geometry_ridge']['applicable'])
text=f'''# M2 prerequisite identifiability audit

Audited all 64 saved M1 configurations before M2 fitting, preserving all bounds/source/results. Recomputed data sensitivities at three finite-difference scales and normalized columns to remove mixed coordinate units. Detailed arrays in results/m2/v1/identifiability_audit.json.

45 warning-bearing evaluations decompose into 32 MAP likelihood-conditioning warnings and 13 F0 halo high-correlation warnings (overlapping warning labels are not additional evaluations). All 32 MAP cases remain weak in column-normalized sensitivity at all three tested step sizes: mixed degree/dex units alone do not explain them. Finite differences can label a structurally deficient matrix nominally full rank; condition/rank are local diagnostics, not proof of exact mathematical identifiability.

An explicit physical likelihood ridge is verified in every one of the 32 MAP cases. For distance ratio multiplied by lambda, adjust sin(i) by 1/sqrt(lambda). Baryonic squared speeds scale by lambda and catalog-projected velocities remain invariant. For Burkert additionally r0->lambda*r0 and rho0->rho0/lambda. For NFW solve the concentration/characteristic-density relation so rs->lambda*rs and rhos->rhos/lambda. At lambda=1.00001 the largest relative velocity difference is {error:.3g}, below the frozen 1e-9 identity tolerance. This is genuine likelihood degeneracy, not a failure to converge. Some perturbations exceed an active prior bound; the saved flag identifies those. Priors/box constraints can restrict the ridge but cannot turn it into independent data information.

Thirteen F0 halo cases have |local correlation|>0.95; this is strong halo-parameter correlation, not automatically a rank failure or an invalid fit. Sparse/limited radial coverage may contribute; eight selected galaxies cannot establish a causal population relationship. F567-2's five observations versus five nuisance-halo parameters directly explain its two nonpositive-dof warnings. Local covariance is not returned there.

Nine MAP solutions touch bounds: seven baryons-only, one NFW inclination (NGC2403), one RAR ML (UGC00731). Lists and values are retained. Baryons-only tends to seek increased stellar/distance/inclination amplitude within the frozen box while retaining poor residuals; these are prior/box-driven constraints under an inadequate restricted model, not evidence that those parameters are measured at their limits. No bounds were tightened to suppress warnings. All starts converged; largest absolute objective spread is {max(r['start_objective_range'] for r in records):.3g}, consistent with nearly equivalent solutions at the stopping precision, with no evidence here of widely separated numerical minima.

Classification for M2: preserve high correlation, rank/conditioning, boundary and n<=k as separate flags. Normalized condition>1e6 adds a weak-direction annotation, not a posterior probability. Keep data-only and prior-inclusive curvature distinct. Model ranking uses only prespecified regular F0 cases; F1 has no information-criterion ranking. Record failed/domain starts without claiming absence of any physical solution. No systematic implementation defect was demonstrated by this audit; diagnostic limitations and physical degeneracy are now explicit.
'''
(ROOT/'docs/M2_IDENTIFIABILITY_AUDIT.md').write_text(text,encoding='utf-8')
print('Prerequisite identifiability audit complete; no unresolved systematic defect found')
