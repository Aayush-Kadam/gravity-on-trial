# R0R official data acquisition

Authoritative site: [SPARC](https://astroweb.case.edu/SPARC/). Frozen references in data/manifests/acquisition.json identify the official catalog, mass-model table and Rotmod archive. The latter is retained for the unchanged scientific input identity; fitting uses the mass-model/catalog tables. No substitute dataset or synthetic observation is used.

| File | Bytes | SHA-256 |
|---|---:|---|
| SPARC_Lelli2016c.mrt | 28259 | 5aa0501f6b0d881fa579030e315e7b5b6ef561a5bd3a07472f9929c7e5728243 |
| MassModels_Lelli2016c.mrt | 269518 | 9108994b12cc401b94a1768beca61c53ec354779385c9c9cc571049f3043244c |
| Rotmod_LTG.zip | 110737 | 0a80cc90714828cc28b7dd57923576714d209f2490328c087c4a4ad607faf588 |

The clean room fetched these bytes directly. An independent official HTTP retrieval audit also recorded URLs, final URLs, HTTP statuses, actual UTC retrieval timestamps, sizes and checksums in official_retrieval_audit.json. Resume acquisition entries explicitly describe existing-checkpoint verification; their timestamps are verification times, not invented original-request timestamps. No successful acquisition is claimed from partial inputs.

Normalization verifies 175 real IDs and 3391 radii, catalog/mass joins, finite and ordered positive radii, positive quoted velocity errors, valid geometry metadata and 361 signed negative-gas rows. Published unit-M/L stellar components and signed gas are preserved. Units: distance Mpc, radius kpc, velocities/errors km/s, inclination degrees, stellar M/L solar at 3.6 μm. The known catalog separator/byte-description discrepancy uses the existing validated parser and an independent token check. The normalized catalog byte hash exactly matches the original local validated artifact.

Credit [Lelli, McGaugh & Schombert (2016)](https://arxiv.org/abs/1606.09251), SPARC, and original observational references in catalog Ref codes. Citation is not asserted to grant redistribution. Source tables, per-galaxy arrays, observational figures and astrophotography are excluded from the public ZIP; the bootstrap retrieves and derives them locally. Code Apache-2.0 does not relicense those materials. No data-owner contact or external distribution occurred.
