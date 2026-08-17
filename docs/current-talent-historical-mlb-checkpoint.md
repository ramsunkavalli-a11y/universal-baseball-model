# Historical MLB Current Talent evidence checkpoint

Status: **2021–2023 certified**

This checkpoint records the MLB historical player-game evidence gate used to connect the Current Talent environment-translation graph to its MLB reporting anchor. It is evidence infrastructure only; it is not a Current Talent estimate, projection, WAR model, or ranking.

## Certified scope

Workflow: `.github/workflows/current-talent-historical-mlb-season.yml` — manual-only after certification.  
Actual league IDs: **103 / 104**  
Temporal semantics: `retrospective_event_cutoff_corrected_history_not_vintage_information_set`

Certified workflow runs:

- 2021: `31986504169`
- 2022: `31988255280`
- 2023: `31989561396`

## Source / authority roles

- **Baseball Savant CSV**: game-grain pitch, terminal-result, participant, and physical-contact/profile evidence.
- **MLB Stats API schedule**: official regular-season date bounds and game inventory.
- **MLB Stats API team metadata**: season-specific team-to-AL/NL assignment.
- **Bulk MLB Stats API season hitting totals**: independent player × actual-league × season outcome reconciliation authority.

Exact source bytes are retained in workflow artifacts with hashes and request metadata. Savant is fetched in small cached date chunks and retryable 429/5xx transport failures use bounded backoff; retries do not change evidence semantics.

## Certified evidence totals

| Season | Players | Player-games | Profile rows | PA | BB+HBP | K | Expected contacts | Observed contacts | Contact residual | Special non-contact |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 1,049 | 51,476 | 147,053 | 181,818 | 17,906 | 42,145 | 121,705 | 121,707 | +2 | 62 |
| 2022 | 693 | 48,325 | 147,376 | 182,052 | 16,899 | 40,812 | 124,267 | 124,269 | +2 | 74 |
| 2023 | 656 | 48,763 | 148,702 | 184,104 | 17,931 | 41,843 | 124,234 | 124,236 | +2 | 96 |

Additional 2022 metrics:

- outcome-batter reassignments: **2**
- core profile events: **177,413**
- unknown contacts: **47**
- PA-accounting residual: **0**
- regular-season games represented: **2,430 / 2,430**

Additional 2023 metrics:

- outcome-batter reassignments: **4**
- core profile events: **179,597**
- unknown contacts: **57**
- PA-accounting residual: **0**
- regular-season games represented: **2,430 / 2,430**

The +2 physical-contact residual in every certified season is diagnostic by design under ADR 024. It is not repaired into the official result-contact denominator.

## Exact official season reconciliation

For **2021, 2022, and 2023**, the accepted evidence reconciles exactly to the independent official season backbone at player × actual league × season grain:

- PA mismatch rows: **0**
- BB/HBP mismatch rows: **0**
- K mismatch rows: **0**
- expected-contact mismatch rows: **0**
- special-noncontact mismatch rows: **0**
- exact outcome mismatch rows: **0**
- PA-accounting residual: **0**

## Historical source semantics frozen by the gates

### 1. Two-strike mid-PA batter substitution

Savant updates batter identity on each pitch. When a substitute completes a strikeout after entering an already two-strike PA, the terminal Savant pitch can carry the substitute ID while official scoring charges the PA/K to the original batter.

Policy: `two_strike_mid_pa_substitution_v1`

The correction is derived only from game-grain pitch sequence evidence:

- exactly two observed batter IDs in the PA;
- terminal event is a strikeout-family event;
- terminal batter differs from initial batter;
- at least two strike-coded pitches occurred before the terminal batter's first pitch.

The PA/K result is assigned to the initial batter. A substitution before two strikes remains with the substitute. More-than-two-batter strikeout sequences or incomplete prior pitch-result evidence fail closed.

Observed reassignments:

- 2021: **7**
- 2022: **2**
- 2023: **4**

Physical-contact identity is not rewritten by this rule; result evidence and observed contact evidence remain separate.

### 2. Interference-error `field_error`

Savant can emit a terminal `field_error` result whose text explicitly says the batter reached on an interference error while still exposing a real batted-ball contact.

Policy: `known_event_or_field_error_interference_narrative_v2`

Only `field_error` + explicit `interference error` result text is added to the special non-contact outcome family. A normal result-contact event such as `fielders_choice` is not reclassified merely because the narrative later mentions interference.

The batted-ball observation remains in physical-contact/profile evidence, preserving ADR 024's separate denominators.

### 3. Historical Oakland abbreviation

Current Savant output can relabel historical Oakland rows as `ATH` while season-specific official team metadata uses `OAK`.

The mapping is explicit and season-scoped, not fuzzy: `ATH -> OAK` for 2021–2024. Unknown team abbreviations remain hard failures.

### 4. Historical Savant result recovery

Historical Savant source oddities are handled only through narrow, evidence-backed recovery rules with regression tests. The independent official PA/BB-HBP/K/contact-opportunity accounting gate is never weakened to make a season pass.

## Transport resilience

The first 2021 live attempt hit a transient Baseball Savant `502`. The materializer retries only retryable transport statuses (`429`, `500`, `502`, `503`, `504`) with bounded backoff and reuses already captured chunks. This is transport resilience only and does not relax data acceptance.

## Implementation

Key files:

- `src/universal_baseball/current_talent_mlb_evidence.py`
- `src/universal_baseball/current_talent_mlb_history.py`
- `src/universal_baseball/mlb_performance.py`
- `scripts/materialize_current_talent_historical_mlb_game_evidence.py`
- `tests/test_current_talent_mlb_evidence.py`
- `tests/test_current_talent_mlb_history.py`
- `.github/workflows/current-talent-historical-mlb-season.yml`

## Next gate

1. Combine **certified 2021 MLB + affiliated-MiLB evidence** before the existing 2021-08-01 cutoff.
2. Fit the first real **MLB-connected environment-translation surface** using training-period data only.
3. Inspect graph support, offsets, residuals, promotion/demotion directionality, and stability across later cutoffs before freezing a translation form.
4. Only then fit Baseline 0 / Baseline 1.
