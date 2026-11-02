# R0R measured runtime and memory

| Scope | Measured value |
|---|---:|
| Fresh dependency-install log span | 54.000 s |
| Independent official-source HTTP acquisition audit | 4.572 s |
| Normalization/token/schema checks | 0.109 s |
| M2 evaluation wall-time sum, including per-evaluation controls | 46.191 s |
| M3 scenario wall-time sum | 195.161 s |
| Completed monitored scientific-child wall-time sum | 391.215 s |
| Maximum monitored scientific-child tree peak upper bound | 144.039 MiB |
| Minimum sampled available RAM in completed computational runs | 2527.273 MiB |
| Application process-tree peak upper bound | 167.785 MiB |

Per-evaluation/scenario sums exclude startup, preflights and checkpoint I/O. Completed-child wall times include startup but exclude preflight windows and manual pauses. The deliberately interrupted first batch has a separate measured 13.283s whole-invocation window and 135.871 MiB tree peak; that time also contains acquisition/validation and is not added as pure fitting time. Acquisition entries after resume measure cached verification; independent HTTP timing is separately labeled. No total conversational-duration or fully observed complete-parent-lifetime peak is inferred.

Every computation child uses a five-sample >=768 MiB/range<=128 MiB preflight, 50ms active checks, >=512 MiB system headroom, <=180 MiB owned-child-tree peak and <=180 seconds per five-galaxy batch. No floor/cap was loosened. One launch refusal was honored; a fresh window later passed at >=3002 MiB with ~3 MiB range. Failed-window individual samples were not persisted; the refusal/error and successful replacement window are retained. The memory cap accounts for Windows venv redirectors/descendants. Summed individual high-water marks are conservative upper bounds, not simultaneous-RSS claims.

Storage: locally generated results 246,726,471 bytes, raw sources 408,514 bytes, remaining active staging 1,132,642 bytes, isolated dependencies 731,989,870 bytes. These generated/dependency trees are excluded from the publication package. Atomic partial checkpoints are retained locally. Actual record times and raw monitor histories remain inspectable; no long-duration leak proof or cross-platform performance guarantee is claimed.
