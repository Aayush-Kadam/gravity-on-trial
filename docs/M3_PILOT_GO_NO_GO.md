# M3 pilot decision

**GO for the frozen full 175-galaxy/14-scenario campaign and independent repeat. M4 remains unauthorized.**

20 prespecified galaxies, 280 scenario records, 1,120 planned model slots. Actual calculations: 984; statuses {'CONVERGED': 954, 'NOT_APPLICABLE': 128, 'UNSUPPORTED_DOMAIN': 16, 'NO_VALID_START': 14, 'INVALID_PROPOSAL': 8}. Null stellar components are NOT_APPLICABLE, physically invalid geometry is rejected, and domain/search failures remain visible. No invalid comparison supports persistence. No DIAGNOSTIC_FAILURE or unexplained physical/statistical error was found.

All 92 scientific/control tests passed (54 unchanged inherited tests, 38 M3 cases). Fresh-process parameters/predictions matched exactly for all 20 galaxies; full canonical diagnostics/masks and final pilot classifications agree. Scalar likelihood/prior/force checks passed. Every converged halo received independent all-radius quadrature. The fiducial-width MAP adapter reproduces frozen M2 results; catalog-frame and corrected-observation-frame likelihoods agree with the required Jacobian. This validates the new adapter without changing old source.

Dogbox second-method checks: 33/36 had comparable valid solutions and agree with TRF within the frozen relative objective target 1e-6. Three UGC01281 Burkert cases remain noncomparable because the declared domain/search policies do not yield a feasible pair; records are retained, not interpreted as physical nonexistence. No bound was changed.

Pilot initial workers took 35.497 seconds and peaked at 81.340 MiB. Full sweep projected worker time 310.599 seconds is below the frozen 900-second limit; dispatcher/preflight overhead is additional and real full time is not yet measured. Lowest monitored available RAM 1516.363 MiB, above the 512 MiB floor. Continue serially in batches of five under the unchanged 180 MiB child cap, with every galaxy/scenario checkpointed. No scenario or threshold was removed to make this gate pass.

Primary labels are operational, not calibrated probabilities. Joint stellar shifts coincide with disk-only shifts when the bulge is absent; the frozen design retains these named overlapping stress directions, labels null bulge-only cases separately, and makes no independence or random-sampling claim. Planned and meaningful/valid denominators accompany every metric.
