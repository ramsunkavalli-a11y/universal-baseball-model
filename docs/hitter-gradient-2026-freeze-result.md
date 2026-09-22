# Frozen 2026 hitter-gradient forecast

Status: **frozen and sealed; do not score or alter with 2026 evidence**

The leading development hitter model has been trained on completed outcomes through
2025 and used to forecast 3,115 affiliated hitters for 2026. The forecast universe
requires at least 30 official terminal contacts in 2025.

The frozen package contains:

- `forecast-2026.parquet`: player ID, 2025 level and workload, the contact-only
  comparison forecast, and the gradient forecast for all nine terminal-contact
  outcomes.
- `forecast-inputs-2025.parquet`: the exact 155 inputs supplied to the model.
- `manifest.json`: the complete recipe, source hashes, feature list, fallback rule,
  coverage, and output hashes.

## Coverage

| Item | Coverage |
|---|---:|
| Official 2025 terminal contacts | 479,839 |
| Forecast players | 3,115 |
| Exact batter/pitcher/hand/outcome context | 99.95% |
| Venue | 100.00% |
| Known park factor | 99.98% |

The average player moved 0.0194 in total probability mass relative to contact-only,
or roughly 0.00216 per outcome. The largest single outcome adjustment was 0.0195.
Every forecast probability vector sums to one.

## Locked limitation

The official 2025 contact file supports current-season HR, non-HR reach, and hit
composition opponent histories. It does not contain the non-contact plate
appearances needed to update pitcher strikeout, walk, and hit-batter history. Those
three opponent measures are therefore carried forward from their latest strictly
prior 2024 values. No 2026 evidence is used to fill the gap.

Forecast SHA-256:
`2766cde0e605e09e2c878d7e58a48cfb0c0b2bfb55b2347fb4ccfe428879e61b`

Forecast-input SHA-256:
`ce3e4239af5e4124a0db3d708f3a2035343ec5103d516e067d6d034c939d1d4e`

This package is the protected final confirmation forecast. It must remain unchanged
until the 2026 season is declared complete and the evaluation procedure is run once.
