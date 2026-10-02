# Bundled research data — no runtime download

The public ARCHVIQ site does **not** download SILSO data at runtime.

Bundled files:

- `SN_d_tot_V2.0.txt` — frozen WDC-SILSO Daily Total Sunspot Number V2.0 archive used by the engine.
- `SILSO_ARCHIVE_SHA256.txt` — archive checksum supplied with the site package.
- `physical_reference_bank_w5_v01.pkl.gz` — trusted, precomputed same-width historical reference bank for 5-day packets.
- `physical_reference_bank_w7_v01.pkl.gz` — trusted, precomputed same-width historical reference bank for 7-day packets.
- `silso_context_reference_v2.pkl.gz` — trusted, precomputed SILSO context/percentile curves for Gaussian sigma 5/7 days.

The pickle files are generated from the bundled SILSO archive by the frozen engine and are loaded only from this trusted repository. If they are absent, the server can rebuild the same reference objects from `SN_d_tot_V2.0.txt`; no network access is required.

`level` is retained as context/nuisance information. Architecture inference is based on dynamic features and level-conditioned normalization rather than mean or maximum SSN.
