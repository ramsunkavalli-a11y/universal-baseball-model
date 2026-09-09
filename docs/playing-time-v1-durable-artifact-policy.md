# Playing-time model artifact policy

## What is preserved

The original independent 2025 confirmation output is stored under
`model_artifacts/playing-time-v1-confirmation-2025/`. It includes the candidate
and baseline player-level scores, diagnostic strata, reports, and a hash manifest.
These files came from GitHub Actions run `32146445795` before its artifact expired.

The evidence confirms that the selected B2 hitter-opportunity form beat the simple
baseline on the untouched 2025 test. It does **not** contain the fitted coefficients
or standardization parameters. The expired production package therefore remains
unrecoverable unless an external copy is found.

## Rule for future selected models

Any model promoted beyond development must commit, or attach to a durable release,
all small files needed to score it:

1. coefficients and intercepts;
2. standardization means and scales;
3. feature names and order;
4. distribution or dispersion parameters;
5. model/version and training-input hashes;
6. selection and confirmation reports; and
7. a manifest with file sizes and SHA-256 hashes.

A workflow artifact with a retention deadline is a transfer copy, not durable model
storage. Production code must not claim a promoted model is active unless its complete
scoring package is available and hash-verified.

## Current decision

Keep the existing labeled fallback in production. Do not recreate the B2 coefficients
from partial evidence or silently refit them. If the exact external package is not
found, rebuild the opportunity model under a new version and rerun the selection and
untouched confirmation gates.
