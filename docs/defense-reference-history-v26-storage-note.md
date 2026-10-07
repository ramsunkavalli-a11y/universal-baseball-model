# Preserve evidence while using available research storage

The first preparation stopped when C: filled while writing the first quality
prediction file. That file is empty; no preflight, scores or comparison report
were produced. It is retained as `failed-empty-quality-predictions.parquet`.
The same unchanged executable can now run against the original contract.

Filesystem access to `D:/UBMResearch/ubm-audit-v3` was granted. This task's
generated older-quality folder was moved there; all 29 files were hash-verified
before and after relocation. A junction preserves the original repository
paths and source receipts. New comparison outputs use another path-preserving
junction into that dedicated folder. No source, forecast, data definition or
eligibility changed. No data were deleted and no user-authored files moved.

Physical generated-data locations are
`D:/UBMResearch/ubm-audit-v3/generated/defense-older-quality-v24` and
`D:/UBMResearch/ubm-audit-v3/generated/defense-reference-history-v26`.
Both remain private ignored outputs, not bulk source publication. Subsequent
restricted environments may need access to that same D: folder to follow the
junctions. Code, contracts and compact review reports stay in the repository.

The first independent replay also reached its receipt-writing step while C:
was full. Its zero-byte partial receipt is preserved as
`failed-disk-full-independent-review.json.gz`. After available storage was
confirmed, the unchanged verifier reran and saved a successful independent
receipt. This recovery did not change the executed contract, code, scores,
selection or prediction files. Neither failed file is a successful receipt.
