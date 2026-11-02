# M4 deployment and release boundary

**Local release candidate ready. Public release remains HOLD and unauthorized.** No GitHub push, publication, hosting, external messaging or public data upload occurred.

The existing local validated tree supports all four modules offline after installation/setup. Run Start-Gravity.ps1 or the documented local supervisor command. This is a single-user local research application; there is no authentication, internet-exposed service hardening or multi-user load-test claim. Binding remains 127.0.0.1. Use the managed supervisor to retain memory safeguards.

The source-only staging ZIP excludes raw astronomical files, per-galaxy numerical result arrays, screenshots containing observations, caches, virtual environments and logs. It includes source, configurations, scientific documentation, source references and the explicit hash-checking data downloader. It is a reviewable source candidate, not a self-contained populated scientific release. Downloading the three SPARC files alone does not recreate all frozen M1–M3 campaigns; the app also requires the existing validated evidence tree or a separately validated campaign regeneration. Do not present missing frozen results as synthetic defaults.

Licensing: no owner-approved open-source code license was invented. LICENSE_NOTICE.md explicitly records this pending decision. SPARC raw/cached data redistribution rights remain unresolved, so no data-bearing public package is prepared. The downloader uses official URLs and verifies frozen SHA-256 values before saving missing files. It refuses changed bytes and never overwrites existing data. Its verification mode was executed locally; fresh acquisition was not repeated merely for packaging.

Remaining public-release work: approve a code license; establish data/result redistribution and provenance policy; review a concrete public package; separately authorize publication/push/deployment. Local M4 GO does not authorize any of these actions. Dependency installation and browser availability are prerequisites, not evidence of deployment.
