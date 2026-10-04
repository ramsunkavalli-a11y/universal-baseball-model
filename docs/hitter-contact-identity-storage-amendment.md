# Compressed storage for historical contact controls

2026-10-04. The control capture stopped before downloading because the available
disk space did not cover 1.29 GB of source files plus the reserved working space.
Keep the original measurement contract unchanged. Store each complete source CSV
in lossless gzip form instead of keeping an additional uncompressed copy.

Count and hash the original bytes while downloading, verify the byte count
against the captured release inventory, and record the compressed file hash
separately. Before reuse, decompress and verify the original hash and byte count.
The selected columns, snapshots, resolver and identity decisions are unchanged.
Check available space before each capture and reserve 1 GB. Preserve completed
captures if a later download or projection fails. No source rows are discarded
to save space and no forecast or protected outcome is touched.
