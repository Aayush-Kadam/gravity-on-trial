# M3 observational-quality composition sensitivity

All five samples use original catalog metadata. Changing a population definition never changes an individual galaxy's source radii, fit, or fragility classification. Perturbed inclinations do not change membership in these catalog-defined cuts. No radial uncertainty filter was introduced. Lower-quality systems remain in the complete inventory.

| Sample | Galaxy denominator | M2 baseline classifications | M3 operational classes |
|---|---:|---|---|
| all175 | 175 | {'NO_VALID_COMPARISON': 44, 'PREFERENCE': 107, 'INCONCLUSIVE': 24} | {'UNASSESSABLE': 49, 'INCONCLUSIVE': 29, 'STABLE': 79, 'SENSITIVE': 18} |
| Q_le2 | 163 | {'NO_VALID_COMPARISON': 40, 'PREFERENCE': 101, 'INCONCLUSIVE': 22} | {'UNASSESSABLE': 44, 'INCONCLUSIVE': 26, 'STABLE': 76, 'SENSITIVE': 17} |
| Q_eq1 | 99 | {'NO_VALID_COMPARISON': 17, 'PREFERENCE': 71, 'INCONCLUSIVE': 11} | {'UNASSESSABLE': 20, 'STABLE': 56, 'INCONCLUSIVE': 12, 'SENSITIVE': 11} |
| incl_ge30 | 163 | {'NO_VALID_COMPARISON': 42, 'PREFERENCE': 100, 'INCONCLUSIVE': 21} | {'UNASSESSABLE': 47, 'INCONCLUSIVE': 25, 'STABLE': 73, 'SENSITIVE': 18} |
| Q_le2_and_incl_ge30 | 153 | {'NO_VALID_COMPARISON': 38, 'PREFERENCE': 94, 'INCONCLUSIVE': 21} | {'UNASSESSABLE': 42, 'INCONCLUSIVE': 24, 'STABLE': 70, 'SENSITIVE': 17} |

quality_composition.json additionally supplies per-sample valid physical comparison counts, preferred-model counts, planned model-slot denominators, warning/bound counts, unavailable assessments, residual distributions and luminosity/surface-brightness/HI-to-light/inclination/ring-count/coverage distributions. Successful-only summaries disclose their valid n and missing n. Warning and boundary sets overlap; null/invalid slots must not be called assessed negatives.

Differences between these population tables are composition effects, not individual preference flips. Q/inclination cuts do not establish independence, remove every systematic, or calibrate theory probabilities. Residuals remain conditional on the declared independent Gaussian catalog-error approximation. The HI-to-light quantity is a proxy, not a directly measured total gas fraction.
