# Read-only inventory recovery

2026-10-05. The first inventory executable stopped before the first saved-head
replay because `storage.sha256_file` expects a Path and the saved model manifest
stores strings. Preserve the executable and its source seal. No fits or forecast
changes occurred; no completed inventory exists. Version 2 converts saved paths
to Path, verifies the original seal, and appends a recovery receipt before
reconstructing the same 266 rows and same retained focal/peer IDs. The contract,
sources, models, comparison definitions and settings do not change. No overwrite
of prior receipts is allowed. A completed version cannot be rerun silently.
