# Current Talent challenger 2 — combined chronology checkpoint

Status: **ACCEPTED FOR BASELINE/TRACKING PRE-SCORING IMPLEMENTATION**  
Date accepted: 2026-08-17  
Authoritative workflow run: **`32074805618`**  
Tested commit: **`296c522ace108066a30a86ce98a35b0bde9b5719`**

This checkpoint accepts the source-agnostic, valued 2021–2022 MLB + MiLB contact surface and the four frozen chronology windows for:

`baseline2_plus_ev_sweet_spot_contact_value_residual_v1`

It contains **no development MSE/MAE**, no richer tracking features, and no 2023 evidence.

## Accepted upstream source gates

- MiLB terminal-contact materialization: run `32070152452`
- MLB terminal-contact materialization: run `32074097045`
- frozen terminal-value scale: Retrosheet run `32056682313`, attempt 5

The combined gate downloaded only those already-accepted artifacts. It made no historical source requests.

## Combined valued evidence

- accepted source target tables: **12** (10 MiLB + 2 MLB)
- supported valued target contacts: **1,137,338**
- first event date: **2021-04-01**
- last event date: **2022-10-05**
- duplicate canonical target keys: **0**
- source years: exactly **2021, 2022**
- terminal values attached: **yes**, using the previously frozen nine-value scale
- all nine frozen terminal-outcome groups present
- all ten frozen contact bins present
- observed level groups:
  - `MLB`
  - `AAA`
  - `AA`
  - `HIGH_A`
  - `SINGLE_A`
  - `ROOKIE_COMPLEX`

Combined valued parquet:

- row count: `1,137,338`
- file SHA-256: `da1e0faf1e8c3d6cc7997583312e74688fe590d44ca2f3b20df12415061f7a98`
- schema SHA-256: `6888c67cdfb5c7c57115e8f9ff5425ebefbbeb87f890a5d5d47ea1a6711a6938`

Workflow artifact digest:

`sha256:8fa0362b59d6d3c14aae916a2e1828eedd7a3b4d5bbb2ac7b62027dbc94679bb`

## Frozen chronology surfaces

Target membership is the existing Current Talent half-open convention:

`event_date >= cutoff AND event_date < cutoff + 90 calendar days`

Baseline membership is strictly:

`event_date < cutoff`

| Cutoff | Baseline contacts | Baseline last date | Future contacts | Future first date | Future last date | Exclusive end |
|---|---:|---|---:|---|---|---|
| 2021-07-15 | 238,119 | 2021-07-14 | 300,398 | 2021-07-15 | 2021-10-03 | 2021-10-13 |
| 2022-07-15 | 886,940 | 2022-07-14 | 250,398 | 2022-07-15 | 2022-10-05 | 2022-10-13 |
| 2022-08-01 | 949,651 | 2022-07-31 | 187,687 | 2022-08-01 | 2022-10-05 | 2022-10-30 |
| 2022-09-01 | 1,072,288 | 2022-08-31 | 65,050 | 2022-09-01 | 2022-10-05 | 2022-11-30 |

For every cutoff:

- all ten frozen contact bins are present in the baseline;
- every future contact bin is supported by the baseline;
- all six level groups are present in the baseline, including frozen reference `MLB`;
- every future level group is supported by the baseline;
- all **60 contact-bin × level-group cells** are populated in the baseline;
- future target key count exactly equals future target row count;
- baseline and future keys do not overlap.

At the 2022-09-01 cutoff, `ROOKIE_COMPLEX` remains present in the baseline but is absent from the future target because the accepted Rookie Complex source has no remaining supported target contacts after that date. This is valid: no future level is unsupported by baseline history.

## Boundary flags

The accepted report records:

- `network_requests_performed = false`
- `model_scoring = false`
- `richer_features_attached = false`
- `richer_residual_fitted = false`
- `accessed_2023 = false`
- `terminal_values_attached = true`
- `baseline_fitted = false`

The baseline was deliberately **not** fit in this gate. The frozen baseline formula is already implemented, but its original row-wise normal-equation accumulation is unnecessarily expensive for four million-row-scale fits. This gate instead persisted/verified the exact event support needed to implement the mathematically equivalent sufficient-statistics fit in the next batch, before any development score exists.

## Decision

**Combined valued chronology passes.**

Next allowed work:

1. implement/prove the exact sufficient-statistics form of the frozen event-weighted additive baseline (`terminal_value ~ contact_bin + level_group`), with fixed references `IFFB` and `MLB`;
2. verify on the accepted combined source that all four baseline fits are full rank and cutoff-safe;
3. attach the already-certified richer tracking snapshot features/eligibility to the canonical player surfaces, preserving exact zero fallback;
4. prove comparator and richer use the same future target event keys;
5. only then create the offline 2022 development evaluator.

Still forbidden: 2023 access or any development-feedback change to outcome groups, terminal values, baseline form, richer features, thresholds, or evaluation gates.
