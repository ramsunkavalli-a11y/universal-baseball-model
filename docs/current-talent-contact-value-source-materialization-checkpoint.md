# Current Talent challenger 2 — source materialization checkpoint

Status: **ACCEPTED FOR PRE-SCORING DEVELOPMENT IMPLEMENTATION**  
Date accepted: 2026-08-17  
Authoritative workflow run: **`32070152452`**  
Tested commit: **`e0a7f118af3c03559c185ecfb8fd07ed668664a6`**

This checkpoint accepts the source-only 2021–2022 MiLB terminal-contact materialization for the frozen challenger:

`baseline2_plus_ev_sweet_spot_contact_value_residual_v1`

It does **not** authorize 2023 access and does not record any 2022 model-performance score.

## Gate boundaries verified

Every one of the 10 season/level jobs reported:

- `accepted_source_materialization = true`;
- `model_scoring = false`;
- `accessed_2023 = false`;
- `terminal_values_attached = false`;
- `baseline_fitted = false`;
- `richer_residual_fitted = false`;
- exact expected actual-league coverage;
- the same target-table schema SHA-256:
  `f874c1dd6e68075a6324bc92d0776e793b776c1d07020adee0bb0640c08147c5`.

The source gate reuses the certified historical Current Talent source path: player-game same-game league authority, historical PBP physical-contact resolver, official participant overlay for residual games, and the frozen ten-bin contact classifier. Terminal PA results come from one terminal pitch per PA plus the source-reconciled conservative narrative mapping.

## Coverage review

Across all 10 slices:

- terminal core contacts: **901,015**
- supported target contacts: **900,742**
- supported target rate: **99.9697008%**
- unsupported/special/ambiguous terminal contacts excluded: **273**
- physical contacts: **936,579**
- terminal physical contacts: **936,546**
- summed game counts across slices: **20,057**

Excluded terminal core contacts were fully surfaced in the artifacts:

- `unsupported_special_result`: **219**
- `ambiguous_narrative_groups`: **20**
- `unsupported_narrative_result`: **20**
- `unsupported_bunt`: **9**
- `unsupported_blank_description`: **5**

This exclusion is accepted because the frozen challenger plan explicitly places bunts and ambiguous/special terminal outcomes outside the target for **both** comparator and richer candidate. No excluded row was guessed into a terminal group after observing development performance.

The 20 ambiguous descriptions are compound hit-plus-runner-out plays (for example a single followed by the batter being retired in a continuation double play). They remain excluded rather than choosing between the hit label and `MULTI_OUT`. The special-result set is dominated by batter/catcher interference. Odd runner-only/error descriptions and blank descriptions also remain excluded fail-closed.

## Frozen target outcome distribution

All nine frozen groups are represented in every season/level slice. Aggregate supported target counts:

| Terminal group | Contacts |
|---|---:|
| `OUT` | 524,692 |
| `1B` | 204,176 |
| `2B` | 63,828 |
| `HR` | 36,353 |
| `MULTI_OUT` | 27,746 |
| `ROE` | 20,493 |
| `SF` | 10,933 |
| `3B` | 9,131 |
| `FC_REACH` | 3,390 |

Aggregate frozen contact-bin counts:

| Contact bin | Contacts |
|---|---:|
| `PULL_GB` | 204,909 |
| `CENTER_GB` | 133,322 |
| `CENTER_OFFB` | 111,811 |
| `OPPO_OFFB` | 82,389 |
| `CENTER_LD` | 72,357 |
| `PULL_LD` | 69,470 |
| `OPPO_GB` | 68,142 |
| `PULL_OFFB` | 61,627 |
| `IFFB` | 52,544 |
| `OPPO_LD` | 44,171 |

Participant authority among supported targets:

- historical source default: **790,304**
- official exception overlay: **110,438**

## Slice accounting

| Slice | Supported targets | Core terminal contacts | Supported rate |
|---|---:|---:|---:|
| 2021 AAA | 91,011 | 91,034 | 99.9747% |
| 2021 AA | 78,581 | 78,604 | 99.9707% |
| 2021 A+ | 79,298 | 79,315 | 99.9786% |
| 2021 A | 79,516 | 79,551 | 99.9560% |
| 2021 Rookie | 93,217 | 93,258 | 99.9560% |
| 2022 AAA | 108,019 | 108,039 | 99.9815% |
| 2022 AA | 95,455 | 95,478 | 99.9759% |
| 2022 A+ | 88,142 | 88,162 | 99.9773% |
| 2022 A | 88,214 | 88,239 | 99.9717% |
| 2022 Rookie | 99,289 | 99,335 | 99.9537% |

## Artifact digests

- 2021 AAA: `sha256:fd6a51a42d6f112168bfba2505acaa1f9547bb268528002cd92349a77d1e2543`
- 2021 AA: `sha256:a3d970f20b4efcb58c88aa9182a2be69db19d1893bff51ccabdaeaf7ba1349e0`
- 2021 A+: `sha256:82f78a583cda7b290972f3f812996ef3eb040a32ea8670b8f3e24304782f7eb7`
- 2021 A: `sha256:c83a0566dcec085fc87967c2302bbdabb5ab2b26b69afb60688a8736ff9f4e70`
- 2021 Rookie: `sha256:f711201b8861e98d34955052c7673c56b5204f50b7f20f5cac3a3ac896b51672`
- 2022 AAA: `sha256:3b7e339efb195516c9191ce9d4e8a081dd326ad265c3e6bc00ea08eadc7d1053`
- 2022 AA: `sha256:c11cbc3fcf83fbe91b5c41c3f41413b0da9e0a7fdf5943630e0518554e2de9bd`
- 2022 A+: `sha256:84ce2c22d18b1797ececff2305c03a7fcab089ceace030423f7ddb150518eda7`
- 2022 A: `sha256:66391d02890aea3cfd3bc46f2040793570f787d8c7b46b7b567436f6c5af0649`
- 2022 Rookie: `sha256:25efe974cbe01d10af06bcc6c2821c4840ac805557875679f886143e0b903dde`

## Decision

**Source materialization passes.**

The 2021–2022 MiLB source table is accepted for deterministic chronology-safe pre-scoring implementation. Unsupported/special rows remain outside the target exactly as frozen.

Next allowed work:

1. attach the already-frozen nine-value MLB terminal scale to accepted source rows;
2. combine accepted MiLB contacts with the already-certified MLB historical contact surface needed by the `MLB` reference level;
3. prove cutoff-safe baseline/future-window construction and identical comparator/richer coverage with deterministic tests;
4. only after those tests are green, build/run the frozen 2022 development evaluator.

Still forbidden:

- any 2023 input;
- changing the nine outcome groups from development feedback;
- changing the fixed value scale;
- changing the additive `contact_bin + level_group` baseline;
- changing richer features, eligibility threshold, or two-coefficient model form based on 2022 scores.
