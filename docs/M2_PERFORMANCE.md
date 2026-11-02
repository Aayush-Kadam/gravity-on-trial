# M2 measured performance

Serial CPU/single BLAS thread; native Windows monitoring every 50 ms; preflight five samples over two seconds each >=768 MiB and range<=128 MiB; sampled execution available-memory floor 512 MiB and child peak cap 180 MiB. No GPU, Docker/WSL, parallel fits, process killing or paging changes. Initial M2 inspection available memory was about 1,448 MiB; exact stage preflights and histories are saved. System headroom is sampled, not continuously guaranteed.

20-galaxy initial pilot workers: 10.887 seconds, peak 76.738 MiB. Its estimate authorized attempting a full rerun under the frozen <=600-second rule, not a promise about unseen cases.

175-galaxy initial sweep: 35 workers, combined worker wall time 96.177 seconds; dispatcher wall time 184.223 seconds including preflights/startup/coordination. Complete fresh-process sweep: 97.938 seconds worker time, 186.234 seconds dispatcher time. Each sweep stayed below the aspirational 10-minute deterministic campaign target. This target result applies to the declared 8-evaluation-per-galaxy configuration, not MCMC/UI performance.

Maximum core worker peak 77.137 MiB. Overall observed peak, including plotting/tests/aggregation, 117.891 MiB; lowest monitored available system memory 1517.184 MiB. All recorded tasks passed safety limits. Per-evaluation RSS and elapsed time are recorded, but process_lifetime_peak_so_far is the serial worker's high-water mark through that evaluation, not a fabricated isolated per-fit peak. Full batch and current-RSS monitor histories disambiguate scope.

All computations checkpointed per galaxy atomically. Main resume was explicitly tested on one completed five-galaxy batch without recomputation (resume_check.json). The initial clipped-footer plotting pass was preserved separately, then corrected using the same data. Total conversational/development time is not estimated from summing nested worker times. No runtime for M3/M4 or other hardware is claimed.
