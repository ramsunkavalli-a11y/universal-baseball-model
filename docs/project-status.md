# Project status and handoff

Last updated: 2026-08-17

This is the **start-here file for a new chat, coding agent, or contributor**.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Working branch: `source-certification-poc`
- Draft PR: **#1 — Build and certify universal baseball foundation layer**
- Inspect the current branch head before editing.
- `main` is used only when a manual workflow dispatcher is necessary; source/model work stays on `source-certification-poc`.

## Working rules

- Work in small verified batches.
- Prefer mature public datasets/parsers/packages over rebuilding raw-source cleanup.
- Surface source/model errors early and fail closed rather than silently dropping or guessing evidence.
- Keep **Performance**, **Current Talent**, **Projection**, and **Player Value / Overall Ranking** separate.
- Never retune frozen Baseline 2 or a frozen richer challenger after seeing its development scores.
- Do not impute structurally unavailable tracking evidence.
- Keep live-source capture separate from deterministic/offline evaluation.
- **Do not inspect 2023 richer performance unless challenger 2 first passes every frozen 2022 development gate.**

## Current stage

The universal results-only **Current Talent Baseline 2 remains frozen and is the comparator/fallback**.

Richer challenger 1 completed its fixed 2022 development gate and **failed**. It is closed; no 2023 confirmation is authorized for that candidate.

Richer challenger 2 is frozen before development scoring:

`baseline2_plus_ev_sweet_spot_contact_value_residual_v1`

Its source/value-scale and 2021–2022 MiLB terminal-contact materialization gates are now **accepted**. Deterministic math primitives are implemented and unit-tested. No challenger-2 2022 model-performance score exists yet.

The immediate task is now the **chronology-safe pre-scoring assembly**: attach the frozen value table to accepted historical contacts, combine MiLB + the already-certified MLB historical contact surface, prove cutoff/future-window boundaries, and prove identical comparator/richer coverage before the development evaluator is allowed to score 2022.

## Frozen Current Talent Baseline 2

Method:

`translated_multiseason_recency_empirical_bayes_v1`

- up to 1,095 days of eligible results history;
- 180-day exponential recency half-life;
- empirical-Bayes prior strength 100 effective core events;
- training-only MLB-anchored environment translation;
- frozen age/current-level Baseline 0 prior;
- frozen 12-component Current Talent profile;
- 90-day future target.

B2 beat B1 on all six frozen development/confirmation folds for both log loss and Brier.

Key freeze:

`docs/current-talent-results-only-baseline-freeze.md`

## Richer challenger 1 — CLOSED / REJECTED

Method:

`baseline2_plus_ev_sweet_spot_contact_residual_v1`

Development run: **`32053829482`**

Persisted result:

- `docs/current-talent-batted-ball-development-checkpoint.md`
- `docs/current-talent-batted-ball-development-result.json`

Equal-fold means:

| Model | Log loss | Brier |
|---|---:|---:|
| B2 | 2.267336438 | 0.872739291 |
| richer 1 | 2.267363114 | 0.872744733 |

Richer 1 was worse on both means and won log loss only 1/3 folds. Any-observed-MiLB evidence also worsened. Calibration/optimizer checks passed, so this was a predictive/transport rejection, not a pipeline failure.

**Do not tune, rerun, or create 2023 confirmation for challenger 1.**

## Richer challenger 2 — FROZEN, NOT YET SCORED

Governing plan:

`docs/current-talent-batted-ball-contact-value-challenger-plan.md`

Method:

`baseline2_plus_ev_sweet_spot_contact_value_residual_v1`

### Interpretation

B2's 12-component probability vector is untouched. Challenger 2 tests whether the same observed EV + sweet-spot features predict a **separate scalar contact-value residual after conditioning on realized contact shape and level environment**.

Frozen richer features:

- 180-day recency-weighted mean EV;
- 180-day recency-weighted sweet-spot share, LA 8–32 degrees inclusive;
- >=20 complete canonical tracked BBE;
- source epoch `2021-01-01`;
- no imputation and no feature search.

Frozen development cutoffs:

- training snapshot `2021-07-15`;
- evaluation snapshots `2022-07-15`, `2022-08-01`, `2022-09-01`;
- fixed 90-day future target window at each snapshot.

Primary loss: event-weighted MSE.  
Secondary guardrail: event-weighted MAE.

The full promotion, calibration, and MiLB transport rules are frozen in the governing plan.

## Challenger 2 source/value-scale gate — PASSED

Authoritative checkpoint:

`docs/current-talent-contact-value-scale-checkpoint.md`

Machine-readable result:

`docs/current-talent-contact-value-scale-result.json`

Authoritative workflow run: **`32056682313`**, attempt **5**.

Accepted Retrosheet scale:

| Group | Frozen value |
|---|---:|
| `1B` | 0.4651970407443663 |
| `2B` | 0.7665843002990237 |
| `3B` | 1.0004100521698496 |
| `HR` | 1.3834396983847337 |
| `ROE` | 0.43273757678346964 |
| `FC_REACH` | 0.1558534038205505 |
| `SF` | -0.06260868067734615 |
| `MULTI_OUT` | -0.8151401718384932 |
| `OUT` | -0.24975231369042597 |

Source checks:

- 1,348 games;
- 103,534 state transitions;
- 24/24 base-out states;
- 65,572 frozen contact targets;
- zero unsupported targets;
- zero targets missing RE24;
- only events strictly before `2021-07-15`;
- no player/model scoring and no 2022/2023 development evidence.

Important correction already resolved: Retrosheet `bip` excludes most over-the-fence HR, so this narrow result-producing contact scale uses `pa AND (bip OR hr)`, still excluding bunts/SH. Attempt 4 was rejected; attempt 5 is authoritative.

## Challenger 2 terminal source semantics — PASSED

Relevant source contracts:

- `src/universal_baseball/current_talent_contact_value_source.py`
- `docs/current-talent-contact-value-source-checkpoint.md`

Historical armstjc PBP does not safely expose the PA-level structured result code in its exported `events` column. The accepted path therefore uses one terminal pitch per PA plus a conservative PA-result-description fallback, with structured official event types used to reconcile ambiguous semantics before freezing the mapper.

Frozen distinctions include:

- `force_out` -> `OUT`;
- `fielders_choice_out` -> `OUT`;
- plain `fielders_choice` -> `FC_REACH`.

Exact duplicated historical pitch rows are harmless under the existing resolver. Formatting-only whitespace differences in repeated PA descriptions are normalized for source identity; substantive description disagreements still fail closed.

## Challenger 2 2021–2022 MiLB source materialization — PASSED

Authoritative run: **`32070152452`**  
Accepted checkpoint:

`docs/current-talent-contact-value-source-materialization-checkpoint.md`

All 10 matrix slices passed:

- 2021: AAA, AA, A+, A, Rookie
- 2022: AAA, AA, A+, A, Rookie

Aggregate source-only target accounting:

- terminal core contacts: **901,015**
- supported target contacts: **900,742**
- supported target rate: **99.9697008%**
- excluded unsupported/special/ambiguous terminal contacts: **273**
- all nine frozen terminal groups represented in every slice
- same canonical target schema SHA across all 10 slices
- exact expected actual-league coverage in every slice
- `model_scoring = false`
- `accessed_2023 = false`

Excluded source rows are exactly surfaced rather than guessed:

- 219 special/interference results;
- 20 ambiguous compound result narratives;
- 20 unsupported odd narratives;
- 9 bunts;
- 5 blank descriptions.

This is consistent with the frozen challenger plan: bunts and ambiguous/special terminal outcomes are excluded symmetrically for comparator and richer candidate.

## Deterministic Challenger 2 math — IMPLEMENTED / GREEN

Module:

`src/universal_baseball/current_talent_contact_value.py`

Implemented before development scoring:

- frozen nine-value assignment with fail-closed unsupported handling;
- additive event-weighted OLS `terminal_value ~ contact_bin + level_group`;
- fixed references `IFFB` and `MLB`;
- cutoff check requiring max fitted event date < cutoff;
- deterministic two-feature no-intercept WLS residual fit;
- finite/full-rank guards;
- zero richer fallback when richer evidence is unavailable.

Contract CI previously passed, including run **`32065963702`**; later source commits also kept the contract CI green.

Do not change these forms after seeing 2022 scores.

## Reusable richer tracking layer

Historical tracking V2 authoritative run: **`32046012977`**, attempt 2.

Checkpoint facts:

- source epoch `2021-01-01`;
- full 2021 prior season complete through `2021-10-03`;
- 2022 development history through `2022-08-31`;
- 2021 canonical tracked BBE: **142,201**;
- 2022 canonical tracked BBE: **164,689**;
- `development_tracking_ready = true`.

Coverage is capability-limited. Do not generalize partial 2022 AAA tracking to all AAA. Preserve exact `source_capability_tier` provenance for transport checks.

## Reuse requirements for the next step

Prefer existing solved infrastructure:

- `src/universal_baseball/current_talent_contact_value.py` for frozen scale/baseline/WLS math;
- accepted MiLB target source materialization above;
- `docs/current-talent-historical-mlb-checkpoint.md` and the already-certified historical MLB contact builder for the required `MLB` reference-level events;
- existing B2/Performance ten-bin contact classifier;
- tracking materialization run `32046012977` for richer EV/LA features and capability provenance;
- existing Current Talent cutoff/future-window utilities where their chronology semantics match.

Do **not** build another raw PBP cleanup path unless a concrete gap is proven.

## Exact next batch

1. Build one deterministic historical contact-value evidence frame from accepted MLB + MiLB contacts and attach the frozen nine-value table.
2. Add chronology utilities/tests that prove, for each frozen cutoff:
   - baseline events are strictly `< cutoff`;
   - future target events are strictly `>= cutoff` and `< cutoff + 90 days`;
   - unsupported/special/bunt events never re-enter;
   - required contact bins/level groups are supported;
   - comparator and richer are scored on identical paired rows.
3. Reuse the already-certified richer tracking snapshots to attach the two frozen standardized features/eligibility and prove exact zero fallback.
4. Only after this pre-scoring contract is green should an offline 2022 development workflow be created/run.

**Do not touch 2023.**

## Governing docs for a new chat

Read in this order:

1. `docs/project-status.md`
2. `docs/current-talent-batted-ball-contact-value-challenger-plan.md`
3. `docs/current-talent-contact-value-scale-checkpoint.md`
4. `docs/current-talent-contact-value-source-checkpoint.md`
5. `docs/current-talent-contact-value-source-materialization-checkpoint.md`
6. `docs/current-talent-batted-ball-development-checkpoint.md`
7. `docs/current-talent-batted-ball-development-result.json`
8. `docs/current-talent-batted-ball-tracking-history-contract.md`
9. `docs/current-talent-savant-minors-source-checkpoint.md`
10. `docs/current-talent-results-only-baseline-freeze.md`
11. `docs/current-talent-validation-contract.md`

Do not redo B1/B2 selection or challenger-1 development absent a concrete implementation bug.
