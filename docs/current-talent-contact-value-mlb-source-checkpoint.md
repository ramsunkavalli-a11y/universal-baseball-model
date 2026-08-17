# Current Talent challenger 2 — MLB source checkpoint

Status: **ACCEPTED FOR PRE-SCORING ASSEMBLY**  
Date accepted: 2026-08-17  
Authoritative workflow run: **`32074097045`**  
Tested commit: **`2c48aba6e40a0669cfc1f5ce021e9b062a801787`**

This checkpoint accepts the 2021–2022 MLB terminal-contact source for the frozen challenger:

`baseline2_plus_ev_sweet_spot_contact_value_residual_v1`

No 2023 input or 2022 model-performance score is included here.

## Source lineage and boundary

The workflow did not refetch historical baseball data. It seeded from the already-certified historical Current Talent MLB artifacts:

- 2021 source run: `31986504169`
- 2022 source run: `31988255280`

The source-only materializer reused:

- cached Baseball Savant pitch/contact rows;
- cached season-specific MLB team -> AL/NL authority;
- the certified Savant projection;
- the certified AL/NL league assignment;
- the shared frozen ten-bin contact classifier;
- structured Savant terminal `events` for the nine-group Challenger-2 result target.

Both final reports state:

- `offline_cached_historical_source = true`
- `network_requests_performed = false`
- `model_scoring = false`
- `accessed_2023 = false`
- `terminal_values_attached = false`
- `baseline_fitted = false`
- `richer_residual_fitted = false`

## Accepted target coverage

| Season | Core terminal contacts | Supported targets | Unsupported core targets | Dates |
|---|---:|---:|---:|---|
| 2021 | 116,897 | 116,894 | 3 | 2021-04-01 through 2021-10-03 |
| 2022 | 119,702 | 119,702 | 0 | 2022-04-07 through 2022-10-05 |
| **Total** | **236,599** | **236,596** | **3** | |

Both seasons preserve AL + NL league coverage and `level_group = MLB`.

The target parquet schema SHA-256 is the same as the accepted MiLB target schema:

`f874c1dd6e68075a6324bc92d0776e793b776c1d07020adee0bb0640c08147c5`

That exact schema match is intentional so the next chronology/value layer can concatenate MLB and MiLB without source-specific model logic.

## The three excluded 2021 core-shaped contacts

These were inspected before acceptance; they are not missing frozen value categories.

- two structured `sac_bunt_double_play` outcomes whose Savant narrative says `ground bunts` and whose generic historical contact shape therefore appears as an ordinary ground ball upstream;
- one terminal `field_error` with the already-certified explicit interference-error narrative.

All three are outside the frozen Challenger-2 target by construction: bunts and special/interference outcomes are excluded symmetrically for comparator and richer candidate.

The Challenger-2 MLB adapter now labels structured `sac_bunt` / `sac_bunt_double_play` outcomes explicitly as `unsupported_bunt`; it does **not** alter Baseline 2 or retroactively change the general historical MLB profile classifier.

Final all-terminal-contact diagnostics:

- 2021: `unsupported_bunt = 766`, `unsupported_special_result = 2`
- 2022: `unsupported_bunt = 390`, `unsupported_special_result = 2`

Only the three 2021 rows above were both core-shaped and unsupported. No 2022 core terminal contact was unsupported.

## Aggregate supported outcome counts

| Terminal group | Contacts |
|---|---:|
| `OUT` | 145,258 |
| `1B` | 50,182 |
| `2B` | 15,795 |
| `HR` | 11,097 |
| `MULTI_OUT` | 7,498 |
| `ROE` | 2,376 |
| `SF` | 2,290 |
| `3B` | 1,312 |
| `FC_REACH` | 788 |

All nine frozen groups are present.

## Aggregate contact-bin counts

| Contact bin | Contacts |
|---|---:|
| `PULL_GB` | 52,615 |
| `CENTER_GB` | 39,569 |
| `CENTER_OFFB` | 29,181 |
| `CENTER_LD` | 25,832 |
| `OPPO_OFFB` | 19,194 |
| `PULL_LD` | 19,068 |
| `PULL_OFFB` | 13,576 |
| `OPPO_LD` | 13,190 |
| `OPPO_GB` | 13,095 |
| `IFFB` | 11,276 |

All ten frozen contact bins are present.

## Final artifact provenance

Authoritative run `32074097045`:

- 2021 artifact digest: `sha256:e08ee45c5d2e28fea11f72b8f8bcd9e524df7e6233a7ca1e17dedc9fab8540e2`
  - target parquet SHA-256: `9bff5967d72d8a34ba895650e502c3c9321e81caac6050b8d472ee0a8b8c47af`
- 2022 artifact digest: `sha256:c620301973e0de76103de1b01bf696a1152673c6ce1cbbc8b5d1a4e65290759d`
  - target parquet SHA-256: `9ddb33b740dce4e121bdf507166be4040d90275da76c4c301934cae807309b44`

Contract CI for the final structured-bunt rule also passed in run `32074097194`.

## Decision

**MLB source gate passes.**

The accepted MLB target can now be combined with the accepted 2021–2022 MiLB target surface for chronology-safe pre-scoring implementation.

Next allowed work:

1. concatenate the accepted MLB + MiLB target schema;
2. attach the frozen nine-value MLB-scale terminal values;
3. prove baseline rows are strictly `< cutoff`;
4. prove future target rows are exactly `[cutoff, cutoff + 90 days)`;
5. prove the additive baseline has required contact-bin / level-group support;
6. prove comparator and richer candidate use identical paired target rows;
7. only then attach the already-certified richer tracking snapshots and prepare the offline 2022 development evaluator.

Still forbidden: 2023 access, development-feedback changes to the value scale/outcome groups/baseline/features, or any 2022 model scoring before the pre-scoring contract is green.
