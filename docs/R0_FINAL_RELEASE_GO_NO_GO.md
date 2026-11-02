# R0 final release-readiness assessment — 3 November 2026

## Verdict: PARTIAL

The validated local flagship remains intact. An essential public-snapshot reproducibility requirement is incomplete, so this is not a ready-to-publish flagship package. No new scientific milestone or expensive benchmark was run.

- **Baseline:** 175 SPARC galaxies /3,391 radii; all 1,326 M3 and 87 M4 protected entries match. Exact legacy M4 content revision is in R0_RELEASE_BASELINE.md.
- **Tests:** original environment 107 passed; clean relocated declared environment 107 passed; patched isolated candidate 107 passed. No failed tests are concealed: source-only candidate achieved 71 passes before three missing-evidence failures stopped the run.
- **Clean install:** declared dependencies installed in an isolated venv; pip check passed; official downloader acquired all three checksum-matching files. With private evidence supplied, real Windows startup, twelve browser workflows, offline-origin blocking, exports and restart passed. Without that evidence, the public source snapshot cannot initialize the flagship.
- **Code license:** owner approved Apache-2.0 and confirmed rights. LICENSE and NOTICE included; data/third-party materials excluded from that grant.
- **Data rights:** official site/paper/table inspection established citation expectations, not blanket redistribution permission. Raw/per-galaxy data-bearing outputs, observational figures and screenshots remain outside publication inventory. Permission-request draft is unsent.
- **Security:** no token/private-key/user-home-path pattern findings in the publication snapshot. Declared dependencies had advisory matches; separately tested pinned updates return zero OSV matches at audit time. A venv-launcher monitoring gap was corrected in the separate candidate with owned-process-tree accounting/termination. This is not a complete security guarantee or internet-deployment review.
- **Performance:** corrected candidate process-tree peak upper bound 168.168 MiB; browser render 3.399s; switch 1.165s. Initial ~4 MiB launcher readings are invalid as app measurements and retained only as diagnostic evidence.
- **Repository quality:** concise candidate README, actual feature/method/limits summaries, Windows commands, locked dependencies, citations, notices, contributor guidance and explicit file inventory prepared. Data-bearing screenshots are retained privately; no fictional public screenshots added. This is a source review candidate, not a self-contained scientific release. No Git history exists to audit or rewrite.

Exact publication proposal: release/r0_candidate/; results/r0/v1/public_release_manifest.json and public_release_manifest.csv list every proposed file/hash/category. release/r0_source_review_candidate.zip is a local, unpublished source-only review archive. The complete local research tree and the original M4 archive remain preserved. Raw audit logs and private test copies are not in this proposal.

## Remaining work and decisions

1. Provide and verify a complete authoritative-data-to-evidence bootstrap, or obtain a rights-cleared benchmark bundle. This is essential technical reproduction work, not a minor README fix. It was not silently substituted by tests using the private local evidence tree.
2. Decide whether to keep downloader-only distribution or seek specific permission for data/result/figure redistribution. A draft is ready; no contact is authorized or sent. Code licensing is resolved; it does not settle data rights.
3. Review/promote the bounded R0 security/monitor patches in a dedicated candidate revision, preserving the scientific source and rechecking integrity. Do not publish using the old advisory-matched dependency pins.
4. After the above checks pass, review the exact new manifest and obtain separate publication authorization. R0 itself authorizes no remote creation, push, website or external file distribution.

Recommended later procedure: freeze a new candidate → verify clean public-source setup without private input copies → rerun required tests/browser/integrity/security/license checks → approve the exact publication file inventory → separately authorize remote repository creation/push. No destructive Git operations are needed. Stop here pending those decisions; no public release claim is made.
