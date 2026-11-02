# M2 20-galaxy pilot decision

**GO for full M2 campaign under the frozen protocol.** M3/M4 remain unauthorized.

All 20 prespecified galaxies have 160 initial model/configuration records and 160 fresh-process records. Status counts: {'CONVERGED': 154, 'UNSUPPORTED_DOMAIN': 2, 'NO_VALID_START': 4}. Warning-bearing evaluations: 110/160; bound-contact evaluations: 32/160. No DIAGNOSTIC_FAILURE or unexplained physical/numerical error. Fixed negative-force domain restrictions and any failed-start outcomes are explicit, not silent row exclusions. Poor physical fits remain unchanged.

All canonical numerical parameters, curves, masks and diagnostic arrays agree within frozen 1e-10 rtol/atol across fresh processes; timings/resources excluded. All 54 M1 tests passed in the M2 environment. Independent quadrature checks executed for every converged pilot halo result at every accepted radius, not merely an example. Raw/config/source identity hashes remain unchanged. Prerequisite identifiability audit understood all 45 M1 warnings and nine boundary cases without changing bounds.

Initial pilot workers: 10.887 seconds total, peak 76.738 MiB. Lowest monitored available RAM: 1777.047 MiB, above 512 MiB; 180 MiB cap respected. Extrapolated full-sweep worker estimate: 95.258 seconds, excluding preflight/dispatcher overhead and any especially hard unseen cases. This is a scheduling estimate, not a measured 175-galaxy performance claim. Under the frozen <=600-second rule, attempt a complete fresh-process rerun after the full initial sweep if safety remains valid.

Proceed serially in batches of five with atomic per-galaxy checkpointing and source identity guarded resume. No method, tolerance, prior or exclusion rule changed in response to pilot findings. Prediction/radius-split and common-subset controls remain separately labeled follow-up checks within M2.
