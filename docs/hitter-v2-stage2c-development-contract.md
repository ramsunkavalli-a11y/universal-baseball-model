# Hitter v2 Stage 2c nested pulled-fly development contract

Status: **SCHEMA 0.4 PRE-REGISTERED BEFORE STAGE 2c CANDIDATE FIT OR SCORE**
Date: 2026-08-24  
Machine contract: `docs/hitter-v2-stage2c-development-contract.json`

## Question

Does a player's shrunk tendency to hit outfield flies—and to pull those flies—
add out-of-time information about future HR skill beyond the frozen
outcome-only forecast? Only after that narrow test passes may the same evidence
be tested separately against extra-base-hit composition.

Stage 2b did not test that narrow question. It let ten shape percentages adjust
six contact nodes simultaneously. Stage 2c separates opportunity from direction
and limits the power signal to the nodes it can plausibly inform.

## Evidence and independence boundary

The source-only audit used 2021-2024 shape histories but loaded no offensive
target. Its stability findings justify shrinkage and level centering; they do
not establish forecast value.

V2022-V2024 offense is already disclosed. V2023 and V2024 may diagnose Stage
2c, but cannot promote it to production. Previously accessed 2025 remains
diagnostic-only and is excluded from selection, rejection, reweighting, and
confirmation. Completed 2026 offense remains the protected one-shot
confirmation and cannot be opened without a separately frozen implementation,
scorer, refit package, hashes, and explicit review authorization.

## Frozen candidate ladder

`E0_OUTCOME_ONLY_REFERENCE` is the unchanged C0 outcome-only forecast. It is a
reference, not a relabelled successful candidate.

`E1_NESTED_PULLED_OFFB_POWER` adds exactly two batter-relative PBP skills:

1. `P(OFFB | classified contact)`; and
2. `P(pull | OFFB)`.

Each share uses a two-season half-life, a Beta prior of 100 denominator events
centered on its historical league-season-level, and reliability
`n_eff / (n_eff + 100)`. The Beta posterior already performs the shrinkage, so
it is not multiplied by reliability a second time. Context-centered posterior
log odds are the only shape features; reliability is reported for provenance.
Missing evidence equals the context prior, making both features and the
increment exactly zero.

Schema 0.2 clarifies the previously frozen but underspecified multiseason
operation: compute the context-centered Beta-posterior log-odds residual within
each player-season-league-level, then average those residuals using that
component's denominator multiplied by the two-season recency weight. The
superseded schema 0.1 SHA-256 is preserved in the machine contract. This
clarification occurred during implementation before any candidate fit, target
load, or score.

Schema 0.3 additionally removes an ambiguity in the phrase “total reach.” E1
must leave the nested `P(REACH | non-HR contact)` branch unchanged; changing
the authorized HR contrast necessarily changes the derived unconditional
terminal reach total. It also makes the already-declared E2-on-E1 ordering an
executable invariant. Schema 0.2's SHA-256 is preserved in the machine
contract. No candidate fit, target load, or score preceded this clarification.

Schema 0.4 follows a second practitioner/PBP literature pass and a target-free
distance-source audit. It splits HR and non-HR XBH into separate ablations,
because the public evidence is strongest for pulled-air HR power and does not
justify letting one coefficient pair move both contrasts at once. The prior
schema 0.3 JSON SHA-256 is
`53c30e0819dee62b5420cd365cd2f9b140fa4972cded0fae6637b517cc9e35ec`.
The already-built schema 0.3 unscored implementation is superseded and cannot
be scored. No offensive target, evaluation membership, or protected 2026
outcome was loaded before this amendment.

E1 can alter only `P(HR | contact)`.

It cannot alter K, UBB, IBB, HBP, `P(REACH | non-HR contact)`, the composition
of ROE versus FC_REACH, the composition of non-reach outs, or SH/special
outcomes. Changing `P(HR | contact)` necessarily changes unconditional terminal
reach probability; the frozen restriction is on the unaffected nested branch,
not that derived terminal total. At each affected binary contrast,
the frozen E0 log odds are an offset. Two coefficients (OFFB tendency and pull
within OFFB) are fit with fixed mean-loss L2 penalty `1.0`; there is no
hyperparameter search.

`E2_PULLED_OFFB_XBH_ABLATION` is built only on a passing E1. It uses the same
two pulled-air features but can alter only the conditional extra-base-hit
contrast within non-HR hits (`2B/3B` versus `1B`). It cannot rescue failed E1.

`E3_SEPARATE_GROUND_DIRECTION` is a secondary ablation built on the least
complex passing air candidate. It adds
`P(GB | classified contact)` and `P(opposite | GB)` under the same shrinkage,
centering, reliability, and penalty. It may alter only the non-HR-contact
reach-versus-out contrast. E3 cannot advance unless E1 independently passes;
ground-ball direction cannot rescue failed pulled-fly power evidence.

No full ten-bin vector, player name/identity, tracking availability, target
membership, or missingness flag is a predictor.

## Chronology-safe fit

- V2022: E1/E2/E3 equal their immediate base; no earlier forecast-target origin
  exists.
- V2023: coefficients use only V2022 forecast-target pairs.
- V2024: coefficients use only pooled V2022-V2023 forecast-target pairs.
- Shape rows must predate the forecast cutoff. Each historical season is
  centered in its own league-season-level before multiseason aggregation.
- No target-season participant membership, outcomes, parks, run values,
  centering cohort, or playing time may enter predictors.
- A later confirmation refit, if separately authorized, uses V2022-V2024 pairs
  under this unchanged protocol. It may not use 2025.

## Required reporting and gate

All comparisons use identical forecast/outcome rows, including exact-fallback
rows, in PA- and player-weighted views. Report terminal log loss and Brier,
HR-conditional log loss/Brier, future wOBA and runs/600 errors/correlations,
calibration, coverage, evidence bands, levels, and promotions/demotions.

E1 advances only if, in each V2023 and V2024 fold and both weighting views, it
strictly improves total terminal log loss and Brier over the strongest simple
outcome baseline. It must also improve HR-conditional log loss over E0 in each
fold/view, improve pooled wOBA and runs/600 RMSE over the strongest simple
baseline, and have no material supported-level reversal under the already
frozen Stage 2 thresholds. Strict improvement tolerance is `1e-8`.

E2 additionally must improve both total proper scores and the conditional XBH
proper score over E1 on identical rows and worsen pooled wOBA RMSE by no more
than 0.25%. E3 is judged separately against the selected air candidate and
must improve both total proper scores and non-HR reach proper scores without a
material level reversal. The least complex candidate clearing every applicable
rule is selected. A failure is preserved and stops; constants cannot be tuned
on the disclosed result.

## Distance and richer-data boundary

The source-only audit found distance for 18.47% of affiliated classified
batted-ball PAs, with 99.936% of distance-bearing PAs also carrying exit
velocity and extreme level/season coverage differences. `hit_distance_sc` is
therefore tracking/enriched PBP, not a universal PBP feature. It is excluded
from E1-E3. After a PBP-only candidate passes and freezes, a separate contract
may test an air-distance residual conditional on the PBP HR forecast, using
venue calibration, identical overlap, evidence-derived reliability, and exact
fallback. Tracking availability can never be a talent predictor.

Even a disclosed-development pass authorizes only preparation of a frozen 2026
confirmation package. It does not authorize opening 2026, tracking fusion,
Stage 3, or WAR.
