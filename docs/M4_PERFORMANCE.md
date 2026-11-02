# M4 measured performance

Application-process peak: **164.719 MiB**, below the 600 MiB target. Minimum observed available system memory across retained M4 server measurements: **1174.711 MiB**. Browser and supervisor processes are separate; this is not a whole-machine RSS claim.

First measured dashboard render: **2.353 s**; ordinary NGC3198→NGC2403 switch: **1.139 s**. Timings include actual browser-render waits, not just Python imports. They are observed local samples, not universal latency guarantees. Server health startup and dependency installation are separate.

Four repeated complete navigation cycles / sixteen module visits: {'cycles': 4, 'module_visits': 16, 'RSS_after_cycles_MiB': [159.39453125, 161.0625, 161.58203125, 161.640625], 'growth_last_minus_first_MiB': 2.24609375}. Bounded caches, per-galaxy loading and noncached figures limit accumulation. This short test cannot prove the absence of leaks during days of use or many simultaneous sessions. The app is a local single-user instrument, not a multi-user capacity claim.

One explicit NGC3198 NFW exploratory fit at disk Υ=0.55 converged: **2.008 s**, child peak **70.945 MiB**. Five-sample preflight and active child/system/time limits were enforced. A low-memory UI admission simulation passed; OS exhaustion was not induced. No M1–M3 campaign was recomputed for the interface.

Raw measurements: results/m4/v1/performance_summary.json, browser_workflows.json, server monitor histories and live_fit_verification.json. App supervisor retains a bounded latest-9000-sample window plus lifetime extrema. The test server was stopped before final artifact hashing.
