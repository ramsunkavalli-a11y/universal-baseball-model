# Current Talent challenger 2 — richer feature attachment checkpoint

Status: **ACCEPTED FOR FROZEN 2021 RESIDUAL FIT**  
Date accepted: 2026-08-17  
Authoritative workflow run: **`32075892988`**  
Tested commit: **`09d2dc1af49e547882bf3c1043d0e42aa0706729`**

This checkpoint accepts the pre-scoring EV / sweet-spot feature and provenance attachment for:

`baseline2_plus_ev_sweet_spot_contact_value_residual_v1`

No MSE/MAE, calibration, promotion decision, or 2023 evidence was computed.

## Accepted inputs

- valued chronology: run `32074805618`
- certified richer tracking: run `32046012977`
- tracking contract: `result_producing_non_bunt_pitch_grain_v1`
- tracking rows: 2021 `142,201`; 2022 `164,689`
- `development_tracking_ready = true`

The implementation reuses challenger 1's existing:

- 180-day exponential recency weighting;
- recency-weighted mean EV;
- recency-weighted sweet-spot share, LA 8–32 inclusive;
- >=20 raw complete canonical tracked BBE eligibility;
- observed source capability provenance.

Module:

`src/universal_baseball/current_talent_contact_value_features.py`

## Frozen training-only standardization

Standardization was fit exactly once from richer-eligible **2021-07-15** player feature rows and reused unchanged for all 2022 snapshots.

- fitted players: **649**
- mean EV: **88.09960095932205**
- EV scale (population SD): **2.887465116853261**
- mean sweet-spot share: **0.3470054876008983**
- sweet-spot scale (population SD): **0.06391355546209573**

No 2022 feature row entered the fitted moments.

## Snapshot / paired target accounting

| Cutoff | Observed tracking players | Richer-eligible players | Full future targets | Paired richer targets | Paired players | Zero-fallback targets | Any-MiLB paired targets |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021-07-15 | 1,030 | 649 | 300,398 | **69,382** | **621** | 231,016 | 12,797 |
| 2022-07-15 | 1,646 | 1,139 | 250,398 | **97,004** | **976** | 153,394 | **49,247** |
| 2022-08-01 | 1,677 | 1,157 | 187,687 | **77,859** | **957** | 109,828 | **39,401** |
| 2022-09-01 | 1,787 | 1,237 | 65,050 | **37,629** | **933** | 27,421 | **18,400** |

For every cutoff:

- feature attachment preserved every canonical future target row/key;
- the paired cohort is one exact key surface to be used by both comparator and richer predictions;
- ineligible/untracked target rows remain present in the full attachment and encode unavailable richer residual as **exactly `0.0`**;
- eligible paired rows do not carry a pre-fit fallback value.

## Capability provenance

Exact source capability tiers remain attached per player and are counted at paired-event grain.

2022 paired evidence includes:

- `MILB_SAVANT_TRACKED:2021:123:SINGLE_A`
- `MILB_SAVANT_TRACKED:2022:112:AAA`
- `MILB_SAVANT_TRACKED:2022:117:AAA`
- `MILB_SAVANT_TRACKED:2022:123:SINGLE_A`
- MLB AL/NL 2021 and 2022 Savant tiers.

The sparse 2022 league-117 AAA evidence is therefore not generalized to all AAA.

The any-observed-MiLB paired cohort exceeds the frozen 1,000-future-contact transport threshold in every 2022 fold.

## Boundary flags

Authoritative report:

- `network_requests_performed = false`
- `model_scoring = false`
- `baseline_predictions_applied = false`
- `richer_coefficients_fitted = false`
- `richer_predictions_applied = false`
- `losses_computed = false`
- `calibration_computed = false`
- `accessed_2023 = false`
- `zero_fallback_encoded = true`
- `paired_target_rows_materialized = true`

Artifact digest:

`sha256:0bdfa7b683053ee498f993c5f302dc49f58cb54a734dcd6b89d1311f12a1412b`

All four paired-future parquet tables have the same schema SHA-256:

`d5d8d6ae6587f954e864aaf77fd48bd85f29f59f1f7b3961989cdd1f5608896a`

## Decision

**Richer feature/provenance attachment passes.**

Next allowed work:

1. use only the `2021-07-15` paired table;
2. apply the already-accepted `2021-07-15` additive contact baseline;
3. form `contact_value_residual = terminal_value - baseline_contact_value`;
4. aggregate to the frozen player-level sufficient WLS table;
5. fit exactly two no-intercept coefficients (`z_EV`, `z_SS`) weighted by supported future target contacts;
6. require finite/full-rank fit and persist it;
7. then apply those unchanged coefficients to the three 2022 paired surfaces and prove prediction geometry/coverage before computing any loss.

Still forbidden: any 2022 future outcome in coefficient fitting, any 2023 access, or any tuning of feature/eligibility/value/baseline/model form from development performance.
