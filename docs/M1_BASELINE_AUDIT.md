# M1 baseline audit (before scientific changes)

No Git repository exists. Every Gate 0R manifest hash and raw data hash verified. gate0_baseline_freeze.json records original source/config/results/docs hashes; existing halo source will be imported unchanged. Detailed original fit parameter values/units, n/k/dof, physical/boundary status and residual summaries are in results/m1/v1/baseline_audit.json. Original reports remain unchanged.

| Galaxy | Model | n | Reduced chi² | Max abs residual km/s | Max abs standardized | Inner / outer mean standardized |
|---|---|---:|---:|---:|---:|---:|
| DDO154 | burkert | 12 | 1.244 | 3.277 | 2.521 | 0.389 / 0.447 |
| DDO154 | nfw | 12 | 11.771 | 5.674 | 6.189 | 2.298 / 1.087 |
| NGC2403 | burkert | 73 | 24.540 | 15.480 | 12.562 | -2.851 / -1.228 |
| NGC2403 | nfw | 73 | 10.013 | 10.481 | 10.631 | 1.894 / -0.790 |
| NGC2841 | burkert | 50 | 6.994 | 39.753 | 5.623 | -0.807 / -0.215 |
| NGC2841 | nfw | 50 | 3.340 | 30.575 | 4.325 | -0.574 / -0.173 |
| NGC3198 | burkert | 43 | 1.707 | 21.024 | 3.621 | -0.423 / 0.051 |
| NGC3198 | nfw | 43 | 1.392 | 28.393 | 2.506 | 0.845 / -0.387 |
| NGC3741 | burkert | 21 | 1.214 | 5.637 | 2.551 | -0.538 / -0.010 |
| NGC3741 | nfw | 21 | 0.344 | 2.708 | 1.225 | 0.217 / -0.150 |

All original best fits are converged, physically admissible and away from declared parameter bounds. Large standardized residuals and coherent radial residuals, especially NGC2403, persist with exact archive/MRT agreement and independent quadrature. Evidence does not point to units/sign errors in the implemented selected cases. This is model inadequacy conditional on fixed geometry/stellar ratios and incomplete Gaussian-error assumptions; its astrophysical cause is not identified. M1 will compare declared nuisance treatment without changing the baseline or increasing errors.

Implicit assumptions made explicit: spherical additive halos; unit-ML published stellar components; fixed H0=73; independent velocity errors with no covariance/systematic scatter; least-squares convergence is local; finite box constraints affect solutions; numerical Jacobian conditioning alone gives no calibrated parameter precision. Reference-study disagreement cannot be assigned to physics without matching nuisance parameters, priors, objectives, masks and halo parameterization. Prior checks were numerical integration checks by this implementation, not independent human replication.
