# Provenance and derivation boundary

Sources: https://astroweb.case.edu/SPARC/ and its SPARC_Lelli2016c.mrt, MassModels_Lelli2016c.mrt, Rotmod_LTG.zip. Acquisition date: 2 November 2026 UTC. Exact retained bytes and SHA-256 values are in data/manifests/acquisition.json. Subsequent offline runs label the entries as existing frozen local files; their timestamps are verification times, not new network fetches. Initial HTTP 200 responses and byte counts were observed during execution; subsequent runs do not reconstruct lost HTTP headers.

Credit: F. Lelli, S. S. McGaugh, J. M. Schombert (2016), SPARC, https://arxiv.org/abs/1606.09251. Original rotation-curve references remain in the parsed catalog Ref field and the raw table bibliography. This project ingests published derived components, not raw telescope data. Gas includes the authors' 1.33 helium factor; stellar component speeds assume unit mass-to-light ratio. Quoted velocity errors exclude inclination systematics.

Mass-model units: D Mpc, R kpc, velocities km/s, surface brightness solar luminosity/pc². Catalog inclination and error are degrees; Q is 1/2/3 for high/medium/low. Source Vflat zero values are retained without asserting measured zero; confirming their missing-value convention remains outstanding. A zero Vbul contribution is not independent proof of absence of a bulge.

Catalog parsing uses documented field widths plus the actual one-byte separator preceding each field after ID; all key metadata were checked by independent whitespace tokenization. No raw bytes were edited. No data exclusions were made. Negative gas is retained, never unconditionally squared in the spot calculation.

The site requests citation but this audit did not establish an explicit redistribution license. Raw files are local and git-ignored. No public redistribution is authorized by this work.
