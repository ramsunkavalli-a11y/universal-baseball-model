# Historical MLB Current Talent evidence checkpoint

Status: **2021 certified; 2022–2023 not yet run**

This checkpoint records the first MLB historical player-game evidence gate used to connect the Current Talent environment-translation graph to its MLB reporting anchor. It is evidence infrastructure only; it is not a Current Talent estimate, projection, WAR model, or ranking.

## Certified scope

Certified workflow run: `31986504169`  
Workflow: `.github/workflows/current-talent-historical-mlb-season.yml`  
Season: **2021 MLB regular season**  
Actual league IDs: **103 / 104**  
Temporal semantics: `retrospective_event_cutoff_corrected_history_not_vintage_information_set`

The workflow is manual-only after certification.

## Source / authority roles

- **Baseball Savant CSV**: game-grain pitch, terminal-result, participant, and physical-contact/profile evidence.
- **MLB Stats API schedule**: official regular-season date bounds and game inventory.
- **MLB Stats API team metadata**: season-specific team-to-AL/NL assignment.
- **Bulk MLB Stats API season hitting totals**: independent player × actual-league × season outcome reconciliation authority.

Exact source bytes are retained in the workflow artifact with hashes and request metadata. Savant is fetched in small cached date chunks and retryable 429/5xx transport failures use bounded backoff; retries do not change evidence semantics.

## Certified 2021 evidence totals

- players: **1,049**
- player-game rows: **51,476**
- profile rows: **147,053**
- true PA terminal events / PA: **181,818**
- BB + HBP: **17,906**
- strikeouts: **42,145**
- expected result-contact opportunities: **121,705**
- observed physical contacts: **121,707**
- physical-contact residual: **+2** across 2 player × league rows
- special non-contact outcomes: **62**
- core profile events: **176,948**
- unknown contacts: **82**
- PA-accounting residual: **0**
- scheduled regular-season games: **2,430**
- games represented by positive player-game evidence: **2,429**

The +2 physical-contact residual is diagnostic by design under ADR 024. It is not repaired into the official result-contact denominator.

## Exact official season reconciliation

The accepted 2021 evidence reconciles exactly to the independent official season backbone at player × actual league × season grain:

- PA mismatch rows: **0**
- BB/HBP mismatch rows: **0**
- K mismatch rows: **0**
- expected-contact mismatch rows: **0**
- special-noncontact mismatch rows: **0**
- exact outcome mismatch rows: **0**

Totals match official authority exactly for PA, BB/HBP, K, expected result contacts, and special non-contact outcomes.

## Historical source semantics frozen by the gate

### 1. Two-strike mid-PA batter substitution

Savant updates the batter identity on each pitch. In seven 2021 PAs, a substitute completed a strikeout after entering with two strikes; the Savant terminal pitch carries the substitute ID while official scoring charges the PA/K to the original batter.

Policy: `two_strike_mid_pa_substitution_v1`

The correction is derived only from game-grain pitch sequence evidence:

- exactly two observed batter IDs in the PA;
- terminal event is a strikeout family event;
- terminal batter differs from the initial batter;
- at least two strike-coded pitches occurred before the terminal batter's first pitch.

The PA/K result is then assigned to the initial batter. A substitution before two strikes remains with the substitute. More-than-two-batter strikeout sequences or incomplete prior pitch-result evidence fail closed rather than being guessed.

2021 outcome-batter reassignments: **7**.

Physical-contact identity is not rewritten by this rule; result evidence and observed contact evidence remain separate.

### 2. Interference-error `field_error`

Savant can emit a terminal `field_error` result whose result text explicitly says the batter reached on an interference error, while still exposing a real batted-ball contact.

Policy: `known_event_or_field_error_interference_narrative_v2`

Only `field_error` + explicit `interference error` result text is added to the special non-contact outcome family. A normal result-contact event such as `fielders_choice` is **not** reclassified merely because the narrative later mentions an interference error.

The 2021 gate found one qualifying PA. Its batted-ball contact remains in observed physical-contact/profile evidence, producing the intended signed contact residual rather than redefining the result-contact denominator.

### 3. Historical Oakland abbreviation

Current Savant output can relabel historical Oakland rows as `ATH` while season-specific official team metadata uses `OAK`.

The mapping is explicit and season-scoped, not fuzzy: `ATH -> OAK` for 2021–2024. Unknown team abbreviations remain hard failures.

## Transport issue found during certification

The first 2021 live attempt hit a transient Baseball Savant `502` on one date chunk. The materializer now retries only retryable transport statuses (`429`, `500`, `502`, `503`, `504`) with bounded backoff and reuses already captured chunks. This is transport resilience only and does not relax data acceptance.

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

1. Run the same independent historical MLB certification for **2022**, then **2023**, without weakening the 2021 rules.
2. Combine certified MLB + affiliated-MiLB training evidence and fit the first real **MLB-connected** translation surface using training-period data only.
3. Inspect support/stability/residuals before freezing a translation form or fitting Baseline 0 / Baseline 1.
