# M3 distance/inclination sensitivity

Six fixed geometry cases per galaxy: D +/-eD, i +/-eI, two joint same-sign corners. Catalog uncertainties provide scales; these are deterministic stress cases, not posterior draws or an empirical covariance model. Covariance between errors is unknown; the selected corners neither estimate it nor exhaust all joint combinations. D<=0 or i outside (0,90] is INVALID_PROPOSAL, never clipped/replaced. Error-bar values remain unchanged in the saved catalog-frame likelihood.

Geometry scenario outcomes among the 107 decisive baselines (each row denominator 107):

| Scenario | Retained | Different preference | Inconclusive | Unavailable | Invalid proposal | Not applicable |
|---|---:|---:|---:|---:|---:|---:|
| distance_minus1sigma | 94 | 6 | 7 | 0 | 0 | 0 |
| distance_plus1sigma | 85 | 5 | 5 | 12 | 0 | 0 |
| inclination_minus1sigma | 97 | 4 | 5 | 1 | 0 | 0 |
| inclination_plus1sigma | 84 | 2 | 6 | 8 | 7 | 0 |
| joint_geometry_minus1sigma | 89 | 7 | 9 | 2 | 0 | 0 |
| joint_geometry_plus1sigma | 65 | 6 | 11 | 18 | 7 | 0 |

For ratio d=Dnew/Dcat, physical radii and signed baryonic squared speeds scale by d; halos are evaluated at rescaled radius. Physical model speed projects to catalog frame by sin(inew)/sin(icat). The alternate computation view divides both observations and errors by that factor. The full log-likelihood transformation includes the density Jacobian, not merely residual equivalence. All applicable accepted predictions were checked against explicit geometry evaluation; all catalog-frame likelihoods independently recomputed. 71100 scalar baryons/RAR force-point checks and all-radius halo quadrature checks passed, in addition to the 92 tests including independent injected-geometry recovery.

All original 3,391 measurements remain present. Rejected proposals reduce valid coverage and remain in the meaningful-scenario denominator; they cannot support a baseline preference. Parameter changes and bound/identifiability transitions are saved. Distance-inclination likelihood ridges do not become physical measurements because an optimizer or prior picks a single point. No inclination correction was applied twice.
