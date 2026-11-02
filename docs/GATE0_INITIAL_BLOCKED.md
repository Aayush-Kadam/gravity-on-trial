# Gate 0 report — 2 November 2026

## 1. Verdict

**BLOCKED — meaningful partial ingestion evidence exists; Gate 0 has not passed.**
Authorization: `GATE_0_AUTHORIZED`; `M1–M4_NOT_YET_AUTHORIZED`.
The stop is a conservative resource decision, not evidence of invalid astrophysics.

## 2. What was built

A lightweight official-data acquisition and fixed-width parsing pilot, frozen local raw files, SHA-256 manifest, validation outputs, 15 independent decimal arithmetic spot checks, and a clean-process ingestion verification script. This is not an installable scientific platform. No halo implementation, fit engine, scientific plot, benchmark, sensitivity campaign, or interface was built.

## 3. Scientific evidence

Acquired the official galaxy table (28,259 bytes), mass-model table (269,518 bytes), and rotation-model ZIP (110,737 bytes, 175 archive members, ZIP CRC test passed). Initial successful network responses were HTTP 200. Table responses supplied no Content-Type header; accepted bodies start with the author table title. ZIP response was application/zip. Original network attempts first failed DNS in the restricted environment; the permitted retry succeeded.

Parsed 175 unique catalog IDs and 3,391 radius rows with matching ID sets. Q counts: 99 high, 64 medium, 12 low. Retained 361 negative Vgas rows in 48 galaxies. No nonfinite numerical values, nonpositive measured radii/errors, non-increasing radii, or catalog/mass distance discrepancies beyond 0.01 Mpc were found by the executed checks. No radial points were excluded.

The downloaded catalog has a genuine header/layout discrepancy: one separator before each field after its 11-character ID is omitted from the documented byte positions. The first row is 131 characters rather than the described 113. The parser uses explicit corrected fixed-width intervals; a separate token-based verifier confirms IDs and key metadata on all 175 rows. All ten mass-model fields agree with independent tokenization across all 3,391 rows.

The preferred five galaxies have source metadata and point counts saved in ingestion_validation.json. Three radii per galaxy were checked using independent decimal arithmetic for 0.5 Vdisk² + 0.7 Vbul² + Vgas |Vgas|; all differences were below the predefined 1e-9 (km/s)² absolute tolerance. These are arithmetic checks, not a completed physical reconstruction or independent astrophysical validation. Vflat zero sentinels and bulge absence semantics remain unresolved and explicitly preserved as source values.

A fresh Python process reproduced the exact canonical parsed-table hash ec0a76e0a8f012ef1096fcce4f45d279def6dba8246f5e78fa1df9916afb4fb4. Fit reproducibility remains untested.

## 4. Computational evidence

Python 3.12.10; NumPy 2.2.1, SciPy 1.18.1, Pandas 2.2.3, Pytest 8.3.4, psutil 7.0.0, Matplotlib 3.11.1 are installed; no new packages installed. Initial machine memory availability was about 739 MiB, 95.4% used; disk free about 41.5 GiB. CIM inventory was unavailable; psutil supplied memory measurements.

The final recorded ingestion rerun took 0.408 seconds wall time, 0.125 seconds process CPU time, and 34.434 MiB peak process working set. Available RAM at its end was 776.824 MiB. These metrics exclude the network acquisition and verification parent process; they do not measure fitting, plotting, or dashboard resources. CPU only; no GPU, Docker, or heavy astronomy stack used.

Before fitting, a conservative minimum of 1,024 MiB available memory was recorded in configs/gate0.json. This is an engineering reserve, not a requirement established by profiling the unbuilt fitting engine. Actual headroom failed this rule. No user applications were closed.

## 5. Failures and limitations

Mandatory G0-D01–D04 have substantive acquisition/ingestion evidence. G0-D05 remains partial (arithmetic only; no figures or published-figure checks). G0-P01/P02, G0-F01/F02 and fit-level G0-R01 are unverified. G0-R02 is measured for ingestion only; G0-A01 is satisfied by this honest report. No GO is warranted.

Raw-file redistribution licensing is unresolved; retain local files and do not publish them. The archive was checked for integrity, not compared scientifically against MRT values. No literature model-fit comparison or independent physics tests were executed. No model rankings or astrophysical findings are claimed.

## 6. Artifacts

Project root: outputs/gravity-on-trial relative to the chat workspace. See data/manifests/acquisition.json; results/gate0/{parsed_tables,ingestion_validation,negative_gas_rows,manual_checks,verification,resources}.json; configs/gate0.json; src/gravity_on_trial/gate0_ingestion.py; verify_ingestion.py.

## 7. Decision

Stop advancement. After available RAM exceeds the recorded 1 GiB reserve, rerun ingestion and verify frozen hashes, then resume Gate 0 physical models, independent quadrature/limits, five-galaxy multi-start fits, plots, literature checks, and clean-process fit reproducibility. No payment, external account, publication or researcher contact is needed. Remaining time and peak fitting RAM have not been measured; do not promise a completion estimate. Lowering the reserve would require an explicit documented policy revision and bounded profiling rather than silently treating this run as passed.
