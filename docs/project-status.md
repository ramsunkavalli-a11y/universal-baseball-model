# Project status and handoff

Last updated: 2026-08-25

This is the **canonical start-here file for a new chat, coding agent, or contributor**.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Canonical branch: protected `main`.
- The completed `source-certification-poc` program was integrated through PR
  `#2` at merge commit `dcaf8f7a2382e836fb6624c16e06319c3e6518f5`.
- Start new work from current `main` on a focused feature branch and merge it
  through a passing pull request.
- Public position-player release `v1.0.0` was published from merge commit
  `b204572d9bd394c77bc40650c31750a0d6a9443d`; its frozen scientific outputs
  must not be rewritten by later release or maintenance work.
- Hitter v2 is the active post-release model program on branch
  `hitter-v2-pbp-outcomes`. Its two frozen PBP-only Stage 2 candidates failed
  the disclosed 2022-2024 promotion gate. Stage 2b now has a frozen, versioned
  calibration/contact-shape contract and verified implementation. All three
  Stage 2b candidates have now failed the frozen disclosed-development gate.
  Stage 2c has completed a source-only semantics/stability audit, frozen a
  narrow nested pulled-outfield-fly contract, verified its unscored
  implementation without loading offensive targets, and froze the E1-only
  scorer before evaluation. E1 then failed its incremental future-HR gate in
  three of four required fold/weighting views; the ladder is stopped and E2 is
  not authorized. A post-E1 independent review now recommends a future joint
  contextual terminal-outcome architecture and documents the repo's source
  readiness. The Stage 2d J0 contract, pre-fit implementation, and input audit
  are now frozen. The authorized real-data J0 fit failed closed when its frozen
  batter-variance estimator did not converge. A distinct Stage 2e J0R contract
  is now frozen before implementation; scoring remains unauthorized.
  Protected 2026 outcomes, tracking fusion,
  Stage 3, and full WAR remain closed. Stage 2d's terminal labels are now
  certified, J0's pre-fit mechanics and chronology-safe inputs are implemented,
  and its real-data execution contract is frozen. J0 was attempted once, failed
  closed numerically, and was never scored;
  the next gate is authorization of the real-data fit only.
- New Pitching v1 development is paused. Completed foundation/source work is
  preserved unchanged for later resumption.
- Work in small verified batches and inspect branch head before editing.
- Prefer certified/reusable public data, mature parsers, and existing adapters over rebuilding raw-source cleanup.
- Preserve every Player Value component as an explicit layer with provenance.

## Governing methodology record

`docs/player-value-v1-war-literature-review.md`

A broader WAR literature review was completed before final aggregation. It caused one material course correction: fixed 20.5 replacement runs/600 PA was superseded by a FanGraphs league-WAR-pool construction. It also promoted baserunning, MLB-reference centering, and a park-neutrality audit to required pre-WAR gates.

## Current state

- **Position-player v1:** **DONE / FROZEN / HISTORICAL PROTOTYPE**
- **Hitter v2 Stage 0:** **DONE LOCALLY — SOURCE AUDIT AND DEVELOPMENT CONTRACT FROZEN**
- **Hitter v2 Stage 1:** **DONE / PUSHED — UNIVERSAL TERMINAL-PA SOURCE GATE PASSED; NO CANDIDATE SCORED**
- **Hitter v2 Stage 2:** **COMPLETE / FAILED PROMOTION GATE — C0 AND C1 PRESERVED AS FAILED CHALLENGERS**
- **Hitter v2 Stage 2b:** **COMPLETE / FAILED DISCLOSED-DEVELOPMENT GATE — NO CANDIDATE SELECTED**
- **Hitter v2 Stage 2c:** **E1 FAILED FROZEN GATE — LADDER STOPPED; E2 NOT AUTHORIZED**
- **Hitter v2 post-E1 review:** **DONE — NEXT GATE IS SOURCE-ONLY MATCHUP-CONTEXT READINESS**
- **Hitter v2 Stage 2f H0:** **FAILED FINAL DISCLOSED-DEVELOPMENT GATE — NO RETUNING; H1 CLOSED**
- **Hitter v2 Stage 3+:** **NOT AUTHORIZED — NO PBP-ONLY BATTING CANDIDATE PASSED**
- **Performance v1:** DONE / FROZEN
- **Current Talent v1:** DONE / FROZEN
- **Projection v1 batting:** DONE / FROZEN
- **Playing Time v1:** DONE / FROZEN
- **Position / Role v1:** DONE / FROZEN
- **Defense v1:** DONE / FROZEN
- **Positional adjustment:** DONE / FROZEN / VERIFIED
- **Batting projected runs:** DONE / FROZEN / VERIFIED
- **Runs per win:** DONE / FROZEN / VERIFIED
- **Replacement level:** DONE / REFROZEN / VERIFIED
- **Baserunning:** **DONE / FROZEN / VERIFIED**
- **GIDP:** **RAW TERM NON-ADDITIVE; RESIDUAL OMITTED FOR v1**
- **MLB-reference centering:** **DONE / FROZEN / VERIFIED**
- **Park-neutrality audit:** **DONE / FROZEN / VERIFIED — `Rpark = 0`**
- **Required pre-WAR sensitivities:** **DONE / VERIFIED OR CONTRACTUALLY UNAVAILABLE**
- **WAR/value aggregation:** **DONE / FROZEN / VERIFIED**
- **Final ranking:** **DONE / FROZEN / VERIFIED**
- **Formal forecast uncertainty:** **DONE / FROZEN / VERIFIED**
- **Pitching v1:** **PAUSED — COMPLETED FOUNDATION/SOURCE WORK PRESERVED**

## Frozen upstream models

- Current Talent: `translated_multiseason_recency_empirical_bayes_v1`
- Projection batting: `frozen_current_talent_carry_forward_v1`
- Playing Time: `playing_time_recent_opportunity_40man_b2_hurdle_v1`
- Position / Role: `primary_share_thresholded_transition_mean_v1`
- Steal attempt propensity: `B2_k5`
- Steal success skill: `B2_k45`
- Non-steal advancement: `A2_k25`

These remain frozen and authoritative for position-player v1. Hitter v2 uses
new namespaces/contracts and does not rewrite or silently relabel them.

## Active post-v1 program — Hitter v2

Hitter v2 repairs the v1 construct-validity failure without rewriting v1.
Stage 0 is frozen in:

- `docs/hitter-v2-methodology-review.md`;
- `docs/hitter-v2-source-contract.md`;
- `docs/hitter-v2-development-contract.md`;
- `docs/hitter-v2-v1-external-validity-result.json`;
- `docs/hitter-v2-workflow-status.json`.

Stage 1 is recorded in:

- `docs/hitter-v2-stage1-checkpoint.md`;
- `docs/hitter-v2-stage1-source-result.json`;
- `reports/generated/hitter-v2-stage1-universal/report.json` (ignored generated
  evidence, identified by a committed SHA-256).

Stage 2 source readiness is recorded in:

- `docs/hitter-v2-stage2-authorization.json`;
- `docs/hitter-v2-stage2-source-readiness-checkpoint.md`;
- `docs/hitter-v2-stage2-source-readiness-result.json`;
- `reports/generated/hitter-v2-stage2-2024-universal/report.json` (ignored
  generated evidence, identified by a committed SHA-256).

Stage 2's pre-score evaluation freeze is recorded in:

- `docs/hitter-v2-stage2-neutral-evaluation-contract.json`;
- `docs/hitter-v2-stage2-prescore-checkpoint.md`;
- `docs/hitter-v2-stage2-prescore-result.json`;
- `docs/hitter-v2-stage2-forecast-membership-correction.md`;
- `docs/hitter-v2-stage2-forecast-membership-correction.json`;
- `docs/hitter-v2-stage2-gidp-opportunity-checkpoint.md`;
- `docs/hitter-v2-stage2-gidp-opportunity-result.json`;
- `docs/hitter-v2-stage2-park-context-checkpoint.md`;
- `docs/hitter-v2-stage2-park-context-result.json`;
- `docs/hitter-v2-stage2-c1-implementation-contract.json`;
- `reports/generated/hitter-v2-stage2-prescore/report.json` (ignored generated
  evidence, identified by a committed SHA-256).

Stage 2's disclosed final-validation result is recorded in:

- `docs/hitter-v2-stage2-final-validation-checkpoint.md`;
- `docs/hitter-v2-stage2-final-validation-result.json`;
- `reports/generated/hitter-v2-stage2-final-validation/report.json` (ignored
  generated evidence, bound by committed SHA-256
  `4695d9a7c6b13b67271c52f1bcd2efaf195d64bc423a4c39e7c72934fb8150c9`).

Stage 2b's versioned development boundary is recorded in:

- `docs/hitter-v2-stage2-failure-diagnostic-result.json`;
- `docs/hitter-v2-stage2b-contact-shape-source-result.json`;
- `docs/hitter-v2-stage2b-development-contract.md`;
- `docs/hitter-v2-stage2b-development-contract.json`;
- `docs/hitter-v2-stage2b-unscored-result.json`;
- ignored generated diagnostic/source reports identified by committed hashes.

Stage 2c's source/design boundary is recorded in:

- `docs/hitter-v2-stage2c-source-audit.md`;
- `docs/hitter-v2-stage2c-source-result.json`;
- `docs/hitter-v2-stage2c-development-contract.md`;
- `docs/hitter-v2-stage2c-development-contract.json`;
- `scripts/audit_hitter_v2_stage2c_shape_stability.py`;
- `docs/hitter-v2-stage2c-unscored-checkpoint.md`;
- `docs/hitter-v2-stage2c-unscored-result.json`;
- `docs/hitter-v2-stage2c-e1-scoring-contract.json`;
- `docs/hitter-v2-stage2c-e1-prescore-checkpoint.md`;
- `docs/hitter-v2-stage2c-e1-development-result.json`;
- `docs/hitter-v2-stage2c-e1-development-checkpoint.md`;
- `docs/hitter-v2-post-e1-independent-design-review.md`;
- `docs/hitter-v2-post-e1-source-readiness.json`;
- `src/universal_baseball/hitter_v2_stage2c.py`;
- `scripts/materialize_hitter_v2_stage2c_unscored.py`;
- ignored generated stability tables identified by committed hashes.

The clean `main` baseline reproduced Ruff and all 819 tests. The immutable v1
pure-batting export reproduced all 3,985 player rows with maximum runs/600 delta
`0.0`. The attached independent external-validity audit is preserved as
verification evidence; no new official outcome scoring was performed in Stage
0 and no Hitter v2 candidate was fit or scored.

The universal source contract promotes the existing terminal-contact parser
into the exhaustive 14-outcome PA foundation. Stage 1 materialized 721,636
player-game rows and 19,074 unique player-league-season rows across 2021–2023.
It reconciles 2,813,883 / 2,837,295 official PA (99.1748479%) as model-ready;
5,716 player-games and 23,412 PA with unresolved source ambiguity remain
retained and failed closed. MLB required-field reconciliation has zero blocking
mismatches. Coverage is reported by season, league, level, team, capability,
and source status. The source was reproduced from public checksum-verified
artifacts without GitHub authentication.

The earlier 99.97% figures described supported contacts inside the screened
contact-target slice, not all official PA. Stage 1 explicitly corrects that
denominator interpretation. Tracking remains an optional reliability-weighted
increment with exact PBP fallback, but no tracking increment or batting model
was fit or scored in this gate.

2025 is diagnostic-only because PA, PBP, Position/Role and Defense outcomes
have already been accessed. Completed 2026 offense is the protected one-shot
confirmation and remains closed. Stage 1 was reviewed and pushed at
`674cbed941368e14772e4aaa2b53069c70d38ba5`. The user then authorized Stage 2
PBP-only development and disclosed rolling-origin validation. Before any score,
the disclosed 2024 terminal-outcome target and neutral historical weights must
be checksum-frozen and all pre-score invariants must pass. Tracking, 2026
access, baserunning, defense, playing time and WAR remain unauthorized.

The disclosed 2024 source is now checksum-frozen: 243,735 player-games and
966,808 official PA, of which 960,362 PA (99.3332699%) are model-ready. The
remaining 1,614 player-games / 6,446 PA remain explicitly failed closed. MLB
has zero blocking reconciliation mismatches. Candidate scoring is still closed
pending the separate pre-score evaluation freeze and candidate-specific
invariants.

The neutral weights and exact folds are now frozen. All folds use the common
FanGraphs 2016–2020 mean environment (`wOBA=0.3188`, scale `1.193`), which
predates every disclosed target. The training populations are not filtered by
future participant membership. Ruff and all 843 tests pass. Candidate scoring
has still not started. B0, B1 and C0 are implemented; C1 source enrichment and
its remaining invariants are next.

Before fitting, a forecast-membership invariant found that target rosters must
not be used to decide who receives a forecast. The original pre-score report is
preserved but superseded by schema `0.2`. Corrected forecast populations are
defined only from prior evidence (4,705 / 5,568 / 6,381 players), then joined
to target outcomes for evaluation (3,176 / 3,172 / 3,088 overlaps). The pinned
Chadwick snapshot supplies exact birth dates for 100% of those forecast
populations.

The C1 GIDP-opportunity source is now ready on 932,024 exactly reconciled
player-games and 3,672,168 PA (97.2844% player-game and 97.2954% PA coverage).
MLB Savant uses direct pre-PA base state; the affiliated MiLB export exposes
post-play state, so its PA-start occupancy is reconstructed by shifting the
prior PA's state within each half-inning. All 26,017 excluded player-games are
retained with explicit failed-closed reasons, including 29 MiLB rows where
official GIDP exceeds reconstructed opportunity.

Chronology-safe park context is also ready. Completed official 2021–2023
schedules cover 714,474 player-games and 2,808,923 PA (99.7980% and 99.8237%)
across 185 venues. The capture stops before the 2024 target and uses the
existing `codedGameState == F` authority to ignore stale postponed entries.
The remaining 1,446 player-games are retained and failed closed for absent,
missing, or conflicting official venue context. C1 now has all declared source
inputs but remains unfit and unscored pending implementation and its
candidate-specific invariant freeze.

The exact C1 estimator is now frozen before fit or score. It adds separately
pooled visiting-hitter venue residuals, adjacent-season player-movement
translations anchored at MLB, one fixed age/translation separation pass, and
an opportunity-adjusted GIDP decomposition to C0. Missing enrichment produces
an explicit zero offset or exact C0 component fallback, never a zero-valued
observation. The search grid is unchanged from the development contract and
cannot expand after scoring. A pre-fit review superseded contract schema `0.1`
with `0.2`: the absolute-age hinge basis is now explicitly centered
componentwise on the league-season-level median-age hinge basis. This prevents
the 20/24/28/32 knots from collapsing under an ambiguous scalar
age-minus-median interpretation. The superseded SHA-256 is retained in the
contract; no C1 fit, prediction, or score preceded the amendment.

The C1 unscored checkpoint now passes for the 4,705 / 5,568 / 6,381
predeclared forecast players. No target outcomes or evaluation membership were
loaded. All probability, chronology, membership, zero-offset, GIDP fallback,
and MLB-anchor invariants passed. V2022 correctly exposes the source boundary:
with only 2021 predictor history it has zero adjacent-season movement pairs, so
age remains neutral and 3,923 non-MLB histories use the disconnected-level
fallback. V2023 and V2024 have 3,176 and 6,297 movement pairs and no age or
translation fallback. These sentinel forecasts are unscored and
non-decisional; the next authorized gate is frozen-grid training selection and
disclosed 2022–2024 validation scoring.

A final pre-score consistency check found that the C1 implementation record's
tie wording conflicted with the controlling development contract. Schema `0.3`
now restores the pre-registered rule: ties choose the longer half-life, then
stronger component/movement/park pooling and the larger ridge penalty. The
schema `0.2` hash and timing are preserved. The already-materialized sentinel
was non-decisional, so no selection or result changed; no target outcome had
been scored.

At the pre-score checkpoint, the scoring foundation supported the predeclared PA- and player-weighted
proper event scores, future wOBA/runs errors, correlations, and calibration.
Nested C0/C1 histories also support component-specific half-lives and pooling,
with conditional-node event log loss available for training-only selection.
No disclosed target score had been run at that checkpoint.

Contract schema `0.4` records the controlling tie order literally—larger
component prior, longer half-life, larger movement/park pooling prior, then
larger ridge—before the first selection or score. Schema `0.3` expressed the
same preferences in a different order; its hash is retained and it produced no
selection.

Training-origin component selection is now frozen. V2022 had no earlier origin
and therefore uses the literal tie default (`3`-season half-life, `800` PA
prior) for every node. V2023 selected from V2022 only; V2024 selected from
V2022–V2023 only. The complete 135-row grids for each selectable fold are
retained under generated-report SHA-256
`a1cc7ffe900a77925ca0d0743be4b2e116832fd0c18fcd545a623a21a4db9358`.
Final validation remained unscored at that checkpoint. The component choices
and grid became immutable before C1 park/movement/age adjustment selection.

C1 adjustment selection is also frozen. V2022 uses the no-origin default;
V2023 selected park/movement/age priors `2000/500/100`; V2024 selected
`2000/500/1`, each strictly from earlier-origin PA-weighted terminal log loss.
The two complete 27-row grids are bound by generated-report SHA-256
`f1cd77c12d7cf529c6a6bc430ba9e9386c851e2bede41604c850d6d56deffb71`.
All candidate parameters were immutable before final validation opened. The
remaining work at that checkpoint was bootstrap, calibration-decile, aggregate,
and subgroup gate reporting before one-pass disclosed scoring.

The final validation scorer was completed, tested, committed, and pushed before
its one-pass run. It implements both weighting views, every primary metric,
metric-wise strongest baselines, pooled relative thresholds, 10,000 paired
player bootstraps at seed `20260823`, correlation guardrails, wOBA and terminal
component calibration, ten deterministic predicted-wOBA bins, supported level
aggregates, and all required subgroup reversals for both C0 and C1.

Both candidates failed. C0 improved pooled PA-weighted wOBA MAE by 1.1487% and
RMSE by 1.1682%, with favorable paired-bootstrap evidence, but failed V2022,
proper-score thresholds, player-weighted RMSE, calibration, and supported
subgroup guardrails. C1 was materially worse: pooled PA-weighted wOBA MAE and
RMSE degraded by 15.37% and 14.94%, and it failed every promotion-gate family.
No post-result tuning was performed. Protected 2026 remains unopened, and
tracking, Stage 3, and WAR are not authorized. The exact next gate is review of
the failed result; any new candidate requires a new versioned contract and an
independent future evaluation boundary.

That review is now complete and the new boundary is frozen. The failure
decomposition proves that C0 and B0 were exactly identical across all 4,705
V2022 forecasts, while C0 improved proper scores in V2023 and V2024. C1's
largest damage came from combined context-driven movement among `OTHER_OUT`,
UBB, ROE, and HBP. The scored C1 never used direction or trajectory.

The reused ten-bin PBP surface contains 2,328,735 shape events across 6,793
players, 50,563 games, and 16 leagues in 2021-2024. It covers 99.4188% of
player-games with terminal contact and 97.1073% of terminal-contact events.
Stage 2b separately tests node calibration, trajectory, and direction within
trajectory. Shape can affect only contact-conditional nodes, has smoothly
shrunk reliability, and returns the exact outcome-only forecast when absent.
The constants and development advance rule are frozen with no hyperparameter
search. V2022-V2024 are disclosed development evidence only; even a successful
result cannot promote without a later one-shot protected confirmation.

The Stage 2b implementation and unscored checkpoint are now complete. Identity
node calibration and a zero shape residual reproduce C0 probabilities exactly.
Shape evidence covers 4,481 / 4,705, 5,323 / 5,568, and 6,132 / 6,381 forecast
players in V2022 / V2023 / V2024; every unsupported player takes an exact base
fallback. Future shape rows cannot affect an earlier cutoff, supported
reliability remains strictly between zero and one, and shape residuals cannot
alter K, UBB, or HBP branches. Ruff and all 875 tests pass. No target outcomes
were loaded and no Stage 2b coefficient was fit or scored at this checkpoint.

The disclosed-development scoring interpretation is also frozen before fit or
score in `docs/hitter-v2-stage2b-scoring-contract.json`. It makes every
remaining phrase numerical: strict `1e-8` proper-score improvement, pooled
wOBA/runs RMSE improvement, a dimensionless intercept/slope calibration
distance, the existing supported-level reversal thresholds, and the 0.25%
richer-model wOBA-RMSE guardrail. The executable scorer and tests are committed
as a separate pre-result gate; no disclosed result can redefine these rules.

The first scoring execution at commit `406062d` stopped during the V2023
calibration fit, before any V2023 prediction or score, because the deterministic
optimizer reached its 2,000-iteration ceiling. V2022's identity training
diagnostic had run; it is explicitly non-selecting. A diagnostic using the same
authorized V2022 training origin showed all nine convex node fits converging in
1,541-2,689 iterations under the unchanged objective. The repair raises only
the numerical ceiling to 20,000; the model, penalty, features, folds, metrics,
and gates did not change. The incident is preserved in
`docs/hitter-v2-stage2b-scoring-execution-incident.json`; the repair was
committed at `80bf449` before the scorer restarted.

The restarted scorer completed twice with the identical generated report hash
`1b54190d21304fe25c14e1751ab5bc4fb2e8e33cb4d77869a6db7ce846830428`.
All three candidates failed. D1 trajectory was genuinely informative: it beat
the simple baselines on both proper scores in both required folds/views and
passed its incremental ablation over D0. It still worsened pooled calibration
versus C0 and produced a material V2023 AAA PA-weighted rate reversal. D2's
full direction-within-trajectory detail failed its ablation, including 0.8027%
PA-weighted wOBA-RMSE worsening versus D0. This means the evidence supports a
small trajectory signal but not a safe universal forecast. No candidate was
selected, no retuning occurred, and protected 2026, tracking, Stage 3, and WAR
remain closed.

A post-result contact-direction literature review is now recorded in
`docs/hitter-v2-contact-direction-literature-review.md`. It finds strong
support for the value and partial repeatability of pulled air contact, but only
mixed support for incremental future prediction after outcome history. The
failed Stage 2b design was broader than the baseball hypothesis: ten shape
shares adjusted six contact nodes, while the evidence favors a nested,
level-aware pulled-air skill aimed first at future HR/XBH, with ground-ball
direction treated separately. This review changes no candidate or gate and
does not authorize new modeling.

The Stage 2c source/design audit now measures the exact nested hypotheses
without loading offense: `OFFB / contact`, `pulled OFFB / OFFB`, `GB / contact`,
and `opposite GB / GB`. Raw all-player same-level Pearson correlations are only
0.187, 0.182, 0.267, and 0.271, but stability rises materially with evidence;
for example, pulled-OFFB persistence is 0.519 at 50-99 OFFB and 0.546 at
100-199. Cross-level mean shifts remain material, especially at the lowest
levels. The frozen Stage 2c design therefore uses two separately shrunk,
league-season-level-centered pulled-fly features only at future HR/XBH nodes.
Ground-ball direction is a separate secondary ablation and cannot rescue a
failed power candidate. The later frozen E1 test found that pulled-air shape
did not add repeatable future-HR information beyond C0: three of four required
fold/weighting comparisons worsened. Protected 2026 was not opened.

The Stage 2c unscored implementation is now verified for the same 4,705 / 5,568
/ 6,381 forecast populations. Shape features are available for 4,481 / 5,323 /
6,132 players; 224 / 245 / 249 players take the exact outcome-only fallback.
Contract schemas 0.2-0.3 clarify before fit that season/context EB residuals
are averaged by component opportunities times recency and that E1 preserves
the nested non-HR reach branch. Reliability is reported but not multiplied a
second time. Synthetic invariants prove that the power layer
can change only HR and XBH contrasts, the ground layer only non-HR reach, and
zero/missing increments reproduce the base exactly. These target-free
invariants passed before the E1-only scorer was frozen and committed.

The one authorized E1 run then passed terminal proper scores against the
simple baselines, pooled wOBA/runs RMSE, and supported-level guardrails, but
failed the decisive incremental HR log-loss test against C0 in three of four
views. Coefficients were near zero and the largest terminal probability change
on the selection folds was only `0.00005595`. Per the frozen contract, E2
cannot rescue E1, the ladder is stopped, and disclosed results cannot be used
for retuning. The auxiliary coverage table had a non-decisional three-player
V2023 inner-join omission; the actual gate used all 3,172 V2023 and 3,088 V2024
evaluable players, so the run was preserved rather than repeated.

The independent post-E1 review does not rescue that result. It identifies a
forward design problem: Stage 2c's raw-coefficient L2 penalty was not invariant
to feature units and forced already-shrunk `0.10–0.14` SD predictors toward an
almost-zero effect. A future candidate must state priors in standardized or
baseball-effect units. More broadly, the review recommends a joint contextual
terminal-outcome model that separates batter skill from prior-only pitcher
quality, platoon, park, league/level, and source context before applying
component-specific aging and translations. Direction and tracking become
optional reliability-weighted measurements with exact PBP fallback.

This is documentation and design evidence only. No candidate or Stage 2d
contract was frozen, no target was scored, and protected 2026 remains closed.

The source-only matchup audit is now complete. Across 3,811,570 regular-season
2021-2024 affiliated PAs, all rows contain batter identity, pitcher identity,
observed batter side, observed pitcher hand, and game date. A fail-closed
within-PA consistency screen retains 3,810,808 rows (99.9800%); the other 762
rows contain at least one participant or handedness conflict. Strictly
prior-date pitcher history reaches 88.85% of PAs at 50 prior BF and 79.83% at
100, with the main sparsity in the initial 2021 window and rookie/complex
leagues. Same-day evidence, outcomes, targets, candidate predictions, and 2026
were not used.

The matchup sidecar is now materialized and reconciled. It contains 3,810,001
unique certified terminal PAs; 3,809,992 have conflict-free terminal batter,
pitcher and handedness context. Of those, 3,691,876 also belong to one of
937,255 accepted player-games whose sidecar PA count exactly equals the existing
Hitter v2 outcome authority. All four MLB seasons reconcile at 100%. MiLB
modeling-join readiness ranges from 94.50% to 97.14%; most rejected games differ
from official authority by exactly one terminal sequence, which cannot be
assigned to an individual PA from aggregated player-game outcomes.

The sidecar therefore fails closed for 31,922 player-game reconciliation rows.
Those PAs and players remain in the universal batting baseline and receive an
exact neutral opponent-context fallback; none is dropped or zero-filled. The
artifact separately records raw matchup history and strictly prior-date
outcome-ready pitcher evidence, excluding the entire current date. It does not
estimate pitcher quality.

The Stage 2d joint contextual contract is now frozen and hashed before event-label
implementation, candidate fit, or score. `J0_JOINT_CONTEXTUAL_NESTED` isolates
prior-only pitcher quality and observed platoon context against the strong
`B1_MARCEL_345_K1200` outcome forecast. A matched uncontextual event model uses
identical rows; their batter-effect difference is the only increment applied to
B1. Missing or failed-closed context returns B1 exactly. Contact shape, tracking,
park, estimated distance, lineup, physical, and demographic inputs cannot rescue
this test.

`J1_CONTEXTUAL_COMPONENT_DEVELOPMENT` may add scale-invariant component-specific
age/level development only after J0 passes and cannot rescue failed J0. The frozen
rolling folds, comparators, proper-score and rate-value thresholds, calibration,
subgroup guardrails, and fallback invariants are recorded in
`docs/hitter-v2-stage2d-development-contract.md` and its machine-readable JSON.

The terminal-outcome label source gate now passes. It directly labels 3,796,988
of 3,810,001 sidecar PAs (99.6585%). The stricter whole-player-game rule retains
3,657,915 PAs in 929,254 games (96.0082%) only when all 14 direct category counts
exactly match independent outcome authority and the prior matchup gate passed.
MLB is 100% ready. The lowest MLB-through-Single-A cell is 2024 Single-A at
94.2576%, above the frozen 90% floor; the lowest rookie/complex cell is 2024 at
93.6710%, above its 85% floor.

The first source-only attempt failed because the literal source phrase `called
out on strikes` was absent from the conservative K vocabulary. That unambiguous
phrase was added before candidate implementation, fit, score, or target
evaluation, and the failed report hash is preserved. Official totals were never
used to assign individual labels. Runner-only records remain unresolved, and
39,923 non-exact reconciliation rows retain exact B1 fallback.

The exact next gate is review of the certified label source, followed only if
authorized by J0 implementation and synthetic/chronology invariant tests.
Candidate fit, scoring, 2026 access, tracking, Stage 3, and WAR remain
unauthorized. See `docs/hitter-v2-terminal-outcome-label-sidecar-checkpoint.md`
and `docs/hitter-v2-terminal-outcome-label-sidecar-result.json`.

That review is now complete and authorized J0 implementation only. The frozen
nested mechanics, matched contextual/uncontextual empirical-Bayes fitters, and
exact B1 fallback are implemented and covered by synthetic invariants. The
chronology-safe input audit accepted 3,657,915 certified PAs with all four
platoon cells, no null residuals, no join loss, and an exact zero residual for
no prior pitcher evidence. The input artifact hash is
`a6cd82a5ac8c9382dc474a968bad6b5e6b48599b7ccfc1c6cfbe7a9a1cba515d`.

The implementation detected and corrected a target-free numerical issue before
any real fit: recency exponents were rebased from absolute calendar years to the
earliest source season, preserving normalized weights while preventing huge
intermediate values. Same-date and future-event exclusion now tests exactly.

The real-data fit package is frozen in
`docs/hitter-v2-stage2d-j0-fit-execution-contract.json`. The subsequent explicit
fit-only authorization is recorded in
`docs/hitter-v2-stage2d-j0-fit-authorization.json`; the fit has not yet been run.
The frozen J0 fit was executed once from commit `b093edf` and failed before
publishing an artifact because a binary-node batter-variance iteration did not
converge within 20 iterations. The runner did not expose the active node, so the
failure cannot honestly be attributed more narrowly. No tolerance was changed,
the fit was not rerun, and no target was loaded. The exact next gate is an
independent method-and-observability review before any new candidate contract;
candidate scoring, J1, 2026, Stage 3, and WAR remain unauthorized. See
`docs/hitter-v2-stage2d-j0-fit-failure-checkpoint.md` and
`docs/hitter-v2-stage2d-j0-fit-incident.json`.

The independent numerical-method review is now recorded in
`docs/hitter-v2-post-j0-numerical-method-review.md`. It rejects a larger
iteration limit as a rescue of failed J0 and recommends that any future candidate
use a distinct identity and a non-iterative component scale derived from frozen
prior PA and predictor-history event information. Before another real fit, the
new package must add durable node/iteration observability, synthetic recovery,
grouped-versus-event equivalence, deterministic reruns, and intentional-failure
tests. No new candidate contract, implementation, fit, or score is authorized by
the review itself.

The distinct `J0R_FIXED_INFORMATION_SHRINKAGE` Stage 2e contract is now frozen
and hashed. It preserves J0 as a final failure, retains the matched contextual
versus uncontextual question, and replaces only the unstable variance iteration
with a component scale derived deterministically from frozen prior PA and
predictor-history Fisher information. It also requires durable node/phase and
per-iteration diagnostics plus intentional failure tests before a real fit.

The contract has now been reviewed and target-free Stage 2e implementation and
synthetic numerical certification are authorized. Real-data fitting remains
closed until certification passes; candidate scoring remains closed until all
chronology-safe fits complete and the scorer is committed frozen. J1, tracking,
protected 2026, Stage 3, and WAR remain unauthorized. The conditional sequence
through a single disclosed Marcel comparison is recorded in
`docs/hitter-v2-stage2e-authorization.json`.

The target-free J0R implementation and certification runner are now frozen in
`docs/hitter-v2-stage2e-implementation-checkpoint.json`. Focused lint passed and
all seven implementation/certification tests passed. The runner loads only the
certified design shape, removes every real response/target field, and generates
seeded synthetic responses. Real-data fitting remains closed until this exact
implementation passes the preregistered numerical certification.

That exact implementation passed certification on the full 3,657,915-row
source shape. All six component fits converged; seeded recovery passed at 1%,
5%, 25%, and 60% event rates; high-evidence player-effect recovery correlated
0.940 with truth; deterministic reruns matched; and grouped versus event-level
fits agreed to floating-point precision. No real response, forecast target, or
protected 2026 field was loaded. The conditional authorization now opens only
the V2022-V2024 chronology-safe fit gate. Scoring remains closed until the fits,
prediction hashes, and exact scorer are committed frozen.

The fit-only execution package is frozen in
`docs/hitter-v2-stage2e-fit-execution-contract.json`. It binds the exact runner,
implementation, event input, three Marcel base files, and cutoff seasons before
execution. It can persist fits and predictions but has no target path or scoring
operation.

The exact runner then completed all three fits without loading targets. Every
node converged, forecast membership remained identical to B1, and the largest
probability-sum error was `4.44e-16`. Prediction, increment, batter-effect, and
fixed-effect hashes for V2022-V2024 are frozen in
`docs/hitter-v2-stage2e-fit-result.json`. No post-fit tuning is permitted.

The one-shot disclosed comparison is now frozen before target access in
`docs/hitter-v2-stage2e-scoring-contract.json`. It binds the exact scorer and
all fit, comparator, training, age, and target hashes; inherits the Stage 2d
fold, metric, calibration, context-ablation, and subgroup gates; and keeps 2026,
J1, tracking, Stage 3, and WAR closed.

The one-shot comparison is complete and J0R failed. Although the contextual
model improved matched training-event likelihood in every node and fold, its
future forecasts were slightly worse than Marcel on pooled log loss, Brier,
wOBA RMSE, and runs/600 RMSE in both player- and PA-weighted views. Against the
strongest metric-wise comparator, every fold/view primary gate failed; all
three folds failed calibration and supported-subgroup guardrails, and V2023 and
V2024 also failed the correlation guardrail. J0R is a final documented failure:
no retuning, J1, protected 2026 access, tracking, Stage 3, or WAR is authorized.
Exact results are in `docs/hitter-v2-stage2e-comparison-result.json`.

The frozen diagnostic-only postmortem confirms that C0 has broad useful signal
but lacks a valid common-level target, forward development, and stable
calibration. Across the three folds it beat Marcel on future-wOBA RMSE in 17 to
24 of 24/25 supported subgroup cells per view, with recurring weaknesses among
older players, AAA, demotions, and low-evidence rows. J0R improved only three to
eight supported cells and repeatedly harmed UBB, K, and HBP component scores.
The exact diagnostic and interpretation are recorded in
`docs/hitter-v2-stage2e-postmortem-result.json` and
`docs/hitter-v2-stage2e-postmortem.md`.

The distinct Stage 2f contract is now frozen. `H0_NEUTRAL_HIERARCHICAL_OUTCOMES`
retains component-specific outcome shrinkage while placing history and scoring
outcomes on a chronology-safe neutral MLB reference scale, learning partially
pooled level translations from movers, and modeling forward age-relative-to-
level development. `H1_CONTACT_SHAPE_INCREMENT` remains closed unless H0 passes
and is limited to five predeclared, evidence-shrunk contact contrasts with exact
H0 fallback. Implementation, fitting, scoring, H1, tracking, protected 2026,
Stage 3, and WAR are not authorized.

On 2026-08-25 the user explicitly authorized target-free H0 implementation and
synthetic invariants only. The authorization is recorded in
`docs/hitter-v2-stage2f-authorization.json`. Real source fitting, disclosed
target scoring, H1, tracking, protected 2026, Stage 3, and WAR remain closed.

That target-free checkpoint is now implemented and documented in
`docs/hitter-v2-stage2f-H0-target-free-checkpoint.md` and its machine-readable
companion. It includes nested probability links, partially pooled mover-based
translations to MLB by component and broad age band, a nonzero disconnected-edge fallback with wider
uncertainty, forward age-relative-to-level development, earlier-origin
calibration, exact no-increment fallback, and common-reference wrappers for the
permanent baselines. Synthetic invariants pass without any real player rows.
No source was materialized, no candidate was fit or scored, and no disclosed or
protected target was opened. The next gate is review followed by explicit
authorization for source materialization and real-data fit without scoring.

On 2026-08-25 the user explicitly authorized that fit-only gate. The binding
record is `docs/hitter-v2-stage2f-H0-fit-authorization.json`. Historical
predictor-source auditing, chronology-safe materialization, H0 fitting, and
non-evaluative numerical/coverage diagnostics are open. Validation-outcome
loading, metric or comparator scoring, H1, tracking, protected 2026, Stage 3,
and WAR remain closed.

The authorized fit-only gate is complete. The source audit and findings are in
`docs/hitter-v2-stage2f-H0-fit-checkpoint.md` and its machine-readable
companion. Certified predictor artifacts were reused without reacquisition;
their hashes match prior checkpoints. V2022 correctly uses the exact C0
fallback, V2023 fits translation/development from 3,176 adjacent pairs, and
V2024 fits translation/development from 6,297 pairs plus calibration from a
strictly earlier origin. All 16,654 forecasts are finite and normalized on
unchanged populations. These are fit-health findings, not accuracy evidence:
no validation outcome or metric was opened. Training-origin configuration
selection and final parameter freeze are the next closed review gate; disclosed
validation scoring must remain a later separate authorization.

On 2026-08-25 the user explicitly authorized training-origin selection and the
final parameter freeze only. The binding scope is recorded in
`docs/hitter-v2-stage2f-H0-selection-authorization.json`. An origin may be used
only when its season already belongs to the outer fold's predictor history and
is strictly earlier than that outer target. Stage 2 target/evaluation tables,
the disclosed comparison, promotion, H1, tracking, protected 2026, Stage 3,
and WAR remain closed.

That selection gate is complete and documented in
`docs/hitter-v2-stage2f-H0-selection-checkpoint.md` and its machine-readable
companion. Component-specific half-lives and prior strengths were selected on
strictly earlier origins. The common-reference surface retained the strongest
translation shrinkage and tighter development shrinkage in V2024; its
calibration prior was tied and resolved by the frozen conservative tie-break.
Observed event targets were held fixed across candidates, all 16,654 prescore
forecasts pass probability and membership invariants, and a clean rerun
reproduced the exact report hash. No disclosed validation outcome was loaded,
no H0/Marcel comparison was computed, and no promotion decision was made. The
next gate is review followed by separate authorization for one frozen disclosed
validation comparison without retuning.

On 2026-08-25 the user explicitly authorized that one-shot disclosed
comparison. The binding record is
`docs/hitter-v2-stage2f-H0-scoring-authorization.json`. The scorer and all
input hashes must be frozen and committed before any validation target is
loaded. After that commit, exactly one V2022-V2024 comparison against the
permanent wrapped baselines is open. Model changes, retuning, grid expansion,
H1, tracking, protected 2026, Stage 3, and WAR remain closed.

The disclosed-comparison scorer is now frozen before target loading in
`docs/hitter-v2-stage2f-H0-scoring-contract.json`. It hashes the selected H0,
all three wrapped baselines, each target/training/age input, the target
translation offsets, and the raw Marcel diagnostic. Synthetic and contract
tests pass, canonical lint passes, and all 988 repository tests pass. The next
action is the authorized one-shot run; no model or acceptance rule may change
after this checkpoint.

The first execution stopped before writing a report because the translated
target's fractional counts differed from PA by machine roundoff and an older
diagnostic required exact equality. The incident is preserved in
`docs/hitter-v2-stage2f-H0-scoring-execution-incident.json`. No metric or
promotion result was published or used. The numerical-only amendment assigns
that residual to `OTHER_OUT`, leaves PA and substantive probability mass
unchanged, and adds an exact reconciliation invariant. Model parameters and
acceptance rules remain frozen.

The completed frozen comparison is documented in
`docs/hitter-v2-stage2f-H0-comparison-result.md` and its machine-readable
companion. H0 failed every fold and both weighting views: it did not improve
any of the four primary metrics over the metric-wise strongest wrapped
baseline. V2023 was close but still uniformly worse; V2024 materially collapsed
rare-outcome probabilities and failed rate, proper-score, correlation,
calibration, and subgroup guardrails. Pooled player-weighted wOBA/runs RMSE was
0.51% worse and pooled PA-weighted RMSE was 3.92% worse. H0 is a final failed
challenger. H1 cannot rescue it, and tracking, protected confirmation, Stage 3,
and WAR remain closed. Further batting work requires a distinct preregistered
candidate contract after review.

On 2026-08-25 the user authorized all ten post-H0 next steps through a new
preregistration boundary. The binding diagnostic scope is
`docs/hitter-v2-post-H0-diagnostic-authorization.json`: compare raw C0 with
Marcel by outcome and frozen subgroup, isolate H0's translation, development,
and calibration layers in a predeclared order, then use the disclosed findings
only to write a distinct one-increment-at-a-time contract. H0 rescue, candidate
fit/score, H1, tracking fit, protected confirmation, Stage 3, and WAR remain
closed.

The authorized post-H0 diagnostic is complete. Raw C0 beat Marcel on future
wOBA and runs/600 RMSE in every disclosed fold/view and beat both proper scores
in 2023-2024, while losing those scores in 2022. The H0 ablation attributed the
failure to its additions: age-conditioned translation and development degraded
future rate accuracy, and 2024 calibration severely damaged proper scores and
PA-weighted rate accuracy through rare-outcome distortions. The replacement
plan is preregistered in `docs/hitter-v2-stability-increment-ladder-contract.json`:
first test one global C0/Marcel stability blend, then test level, aging, contact
shape, and tracking only as separate residual increments. No new candidate has
been fit or scored, and the protected confirmation season remains sealed.
The post-H0 checkpoint passed all 993 repository tests and canonical lint.

## Paused post-v1 program — Pitching v1

Pitching v1 began from the completed position-player v1 release without
rewriting it. The pre-outcome methodology review is
`docs/pitching-v1-methodology-review.md`; the binding development contract is
`docs/pitching-v1-development-contract.md`.

New pitching candidate development is paused while Hitter v2 establishes the
terminal-outcome, translation, shrinkage, chronology, exposure and
run-conservation architecture. The completed synthetic Performance foundation,
MiLB inventory, and official MLB source gate below remain valid provenance and
must not be rewritten.

The universal rate profile is frozen as `K`, unintentional walk, HBP, HR and a
neutral residual BF component. Rate talent, one-year Projection, future
workload, starter/reliever role, leverage, replacement and run conversion remain
separate layers. The first implementation gate is synthetic-data validation of
the exact BF profile followed by an inventory of immutable 2021–2024 pitching
source artifacts. The 2025 confirmation surface remains untouched.

Foundation PR `#7` merged at
`f4235e7bd6c1711ab79b610ceaf8ebb53e2f3d1f`. Required CI run
`32398705507` and CodeQL run `32398705518` passed. The synthetic universal
Performance implementation now enforces exact positive-BF accounting for `K`,
`UBB`, `HBP`, `HR`, and `OTHER_BF`.

Source-inventory PR `#8` merged at
`3e384dbf2ef3edf0dc38b4a1611769694f6e21f7`; required CI run
`32399605124` and CodeQL run `32399605319` passed. Independent main-branch
workflow run `32399807939` then reproduced all five previously certified 2024
hashes and all 20 frozen 2021–2024 affiliated MiLB pitching source hashes. Its
artifact `9418056648` has digest
`sha256:74131ff186058d8fddd6609ff32ae1369bed3d4eec97e00f4301b0b4137bb45e`.
The verified inventory contains 26,488 player/actual-league/season rows,
132,440 long-profile rows, 8,497 distinct pitchers, 14 actual leagues, and
3,073,606 BF with unique canonical grains. Raw source CSVs remain in ignored
quarantine and were not uploaded; 2025 was not accessed. Exact evidence is
frozen in `docs/pitching-v1-source-inventory-result.json`.

The official MLB pitching source gate is now staged against the same bulk,
paginated AL/NL Stats API contract already used for batting. Before any
Pitching v1 candidate scoring, it froze eight exact 2021–2024 response hashes.
Local reproduction produced 3,713 player/actual-league/season rows, 18,565
five-bin profile rows, 1,569 distinct pitchers, and 730,423 BF with unique
canonical grains. The 2024 pitching total is exactly 182,449 BF, independently
reproducing the existing official MLB PA accounting anchor; no historical
count change was accepted. This batch remains provisional until the protected
main-branch workflow reproduces every response hash and total.

## Defense v1 — frozen

Final skill hierarchy:

- general range: tracked MLB T1 -> affiliated U1 -> neutral B0;
- catcher throwing: repaired C2 -> B0;
- catcher blocking: repaired C2 -> B0;
- framing: eligible MLB F1 -> F0; MiLB framing remains F0.

Important catcher throwing implementation: fitted repaired C2 weights by **steal attempts** and requires original steal-attempt eligibility, despite an older metadata-only `fielding_outs` label.

General defensive exposure is prior-season MLB defensive-out persistence with prior-position shares. Catcher opportunity forecasts remain:

- throwing `sb_attempts`: fixed 50/50 persistence / Playing-Time-ratio hybrid;
- blocking pitches: fixed 50/50 hybrid;
- framing pitches: raw persistence.

Native run conversion:

`component_runs = frozen_skill_z * projected_native_opportunities * run_rate_per_z_opportunity`

Binding parameters: `docs/player-value-v1-defense-native-run-conversion-parameters.json`.

Key verification records include runs `32266007594`, `32266817048`, `32267920355`, `32268659408`, and `32269076231`.

## Positional adjustment — frozen / verified

Binding FanGraphs 162-game schedule:

- C `+12.5`
- 1B `-12.5`
- 2B `+2.5`
- 3B `+2.5`
- SS `+7.5`
- LF `-7.5`
- CF `+2.5`
- RF `-7.5`
- DH `-17.5`

Non-DH:

`Rpos[p] = schedule_runs[p] * projected_position_fielding_outs[p] / 4374`

DH:

`Rpos[DH] = -17.5 * projected_DH_role_events / 162`

Verification: Actions run `32270697293`.

Do not center inside the positional layer. Baseball-Reference's raw current schedule remains a final sensitivity.

## Batting projected runs — frozen / verified

The 12 projected batting bins are a mutually exclusive simplex conditional on a core event. Player Value uses one pooled certified MLB reference environment and common core-event coverage:

`Rbat_i = projected_expected_mlb_pa_i * coverage_mlb * (RV_i_core - RV_ref_core)`

Verification: Actions run `32275192829`.

Do not add player-specific taxonomy/source coverage as talent.

## Runs per win — frozen / verified

Binding method:

`RPW = 1.5 * MLB_runs_per_9_innings + 3`

2024 certified MLB reference:

- runs: `21343`
- innings: `43116.333333333336`
- RPW: `9.682629939156854`

Verification: Actions run `32275833614`.

Baseball-Reference/PythagenPat remains a non-binding sensitivity.

## Replacement level — refrozen / verified

Binding contract: `docs/player-value-v1-replacement-level-contract.md`.

Binding convention: `fangraphs_570_war_pool_projected_pa_v1`.

`WARrep_pool_ref = 570 * (MLB_games_ref / 2430)`

`replacement_runs_per_pa_ref = WARrep_pool_ref * RPW_ref / MLB_PA_ref`

`Rrep_i = projected_expected_mlb_pa_i * replacement_runs_per_pa_ref`

2024 certified reference:

- completed MLB games: `2429`
- MLB PA: `182449`
- RPW: `9.682629939156854`
- prorated position-player replacement pool: `569.7654320987654 WAR`
- replacement runs/PA: `0.030237643566893475`
- replacement runs/600 PA: `18.142586140136086`

Materialization: `docs/player-value-v1-replacement-level-2024.json`.

Verification: Actions run `32280808517`.

Required replacement sensitivities already materialized:

- 590-WAR position-player allocation: `18.779168109965422` runs/600 PA;
- legacy fixed convention: `20.5` runs/600 PA.

The earlier 20.5 implementation remains in history/provenance but is **not authorized for final WAR**.

## Baserunning / GIDP — frozen / verified

### Source / overlap gate

Binding source/overlap contract: `docs/player-value-v1-baserunning-source-audit-contract.md`.

The live source audit established:

- official 2024 MLB season hitting output has complete `groundIntoDoublePlay` counts but **no `gidpOpp` field in any of 780 pooled AL/NL player rows**;
- therefore the preferred official bulk source cannot directly support an opportunity-adjusted MLB GIDP residual;
- public Baseball Savant runner-level baserunning-run-value CSV is certified for **2019–2024** with all required advancement fields complete, zero duplicate runner IDs, and internally consistent component opportunity counts;
- certified Savant runner-row counts by season are `659, 517, 680, 625, 611, 608` for 2019 through 2024;
- raw GIDP run value is **not additive** because PA-level RE24 already feeds the frozen ground-ball bin values used in `Rbat`.

Source materialization: `docs/player-value-v1-baserunning-source-audit-result.json`.

### Portable steal projection

The chronological steal gate used 2022–2023 development targets and held out 2024. Frozen methods:

- attempt propensity: `B2_k5` — three-season recency empirical Bayes, prior strength 5;
- success skill: `B2_k45` — three-season recency empirical Bayes, prior strength 45.

Both beat the neutral baseline in development and confirmed on 2024. Result: `docs/player-value-v1-steal-projection-selection-result.json`.

### Non-steal advancement projection

The predeclared Savant persistence gate used 2019–2024 source seasons, 2022–2023 development targets, and held out 2024. Frozen method:

- advancement rate: `A2_k25` — up to three prior MLB Savant seasons with `1.00 / 0.50 / 0.25` recency weights and a prior of 25 non-steal advancement opportunities.

Development equal-year primary score improved from `0.0035781987760809303` for `A0_neutral` to `0.0026695655379876298` for `A2_k25`. On held-out 2024 it improved from `0.0032647343977582704` to `0.0023445732494996718`, so the preselected player-specific method confirmed without opening alternative 2024 candidates.

Result: `docs/player-value-v1-advancement-projection-selection-result.json`.

### Run conversion and final v1 baserunning definition

Binding contract: `docs/player-value-v1-baserunning-run-conversion-contract.md`.

Materialization: `docs/player-value-v1-baserunning-run-conversion-2024.json`.

Verified 2024 reference constants include:

- MLB PA: `182449`;
- steal opportunity proxy: `42342`;
- steal attempts: `4578`;
- stolen bases: `3617`;
- caught stealing: `961`;
- common steal opportunity rate: `0.2320758129669113` per MLB PA;
- common steal attempt rate: `0.1081195975627037` per portable steal opportunity;
- MLB steal success probability: `0.790083005679336`;
- Savant non-steal advancement opportunities: `12931`;
- common advancement opportunity rate: `0.0708746005733109` per MLB PA.

Frozen production form:

`Rbr_i = Rsteal_i + Radvance_i`

Steal opportunity exposure and advancement opportunity exposure both scale from **common fixed MLB reference rates per projected MLB PA**, not from the player's projected batting outcomes.

The steal conversion uses the public wSB-style opportunity-centering convention with `runSB = +0.2` and the certified 2024 MLB runs/out environment. Mechanical verification shows a neutral steal player produces `-2.220446049250313e-16` runs at 600 PA, effectively zero within the `1e-10` tolerance.

For advancement, the source-defined frozen `A2_k25` rate is multiplied by the common reference advancement-opportunity rate. MiLB-only/unsupported advancement history remains neutral rather than receiving an invented proxy.

### GIDP decision for v1

Do **not** build a conventional raw GIDP penalty. It would double-count value already present inside the frozen RE24 ground-ball bins.

The separate opportunity-adjusted residual is also now **omitted for v1**:

`Rgidp_residual_i = 0`

The preferred official MLB bulk opportunity denominator is unavailable, and this project will not create a custom play-by-play denominator solely to force a familiar WAR component into the model. Reopen only through a new predeclared gate if a mature, reproducible direct source or reusable implementation is certified first.

## COMPLETED STAGE — fixed-reference MLB centering

Binding contract: `docs/player-value-v1-mlb-centering-contract.md`.

### Membership / exposure gate — VERIFIED

The fixed reference population is now anchored to the certified pooled 2024 MLB Stats API population, not to the Playing Time validation target:

- official positive-PA reference players: **651**;
- official pooled MLB PA membership anchor: **182,449**;
- frozen Playing Time 2023-10-15 snapshot rows: **3,985**;
- Playing Time target players with positive observed 2024 PA: **645**;
- Playing Time observed-PA diagnostic total: **181,190**;
- aggregate frozen projected reference PA after membership reconciliation: **148,948.26306286638**.

Six official 2024 MLB hitters are outside the frozen eligible Playing Time/B2 snapshot and therefore have no authorized chronology-safe Playing Time prediction row: `543518`, `593934`, `622491`, `656555`, `666158`, `808982`. They remain in the official 651-player reference cohort with the predeclared structural fallback `projected_expected_mlb_pa = 0.0`; realized 2024 PA is not used to backfill exposure.

Binding membership materialization: `docs/player-value-v1-mlb-centering-2024-membership.json`.

Verification Actions run: **`32320525700`**. Tests, source-artifact download, membership materialization, and artifact upload all passed.

### Numerical centering reference — FROZEN / VERIFIED

With the v1 GIDP residual omitted, assemble the existing frozen historical 2024 component surfaces for the fixed 651-player membership:

`Ravg_raw_ref = aggregate(Rbat + Rbr + Rdef + Rpos)`

Then:

`centering_runs_per_pa = -Ravg_raw_ref / 148948.26306286638`

`Rlg_i = projected_expected_mlb_pa_i * centering_runs_per_pa`

Do **not** use 182,449 observed official PA as the centering denominator; it is the membership/accounting anchor. The numerical centering denominator is frozen projected reference PA.

Before freezing the constant, reuse the existing frozen batting/B2, baserunning, Defense, defensive-position allocation, and DH-role artifacts. Do not build a ranking-specific player population, refit an upstream model, or use 2024 realized component outcomes as projected values. The six outside-snapshot members must remain explicit zero-exposure/fallback rows rather than being dropped.

The concrete numerical materializer and immutable input/column map are now present:

- `scripts/materialize_player_value_v1_mlb_centering_2024.py`;
- `src/universal_baseball/player_value_defense_projection.py`;
- `docs/player-value-v1-mlb-centering-source-map-2024.json`;
- `.github/workflows/player-value-v1-mlb-centering-materialize-2024.yml`.

Verified artifact-only component aggregates for the 651-player reference are:

- `Rbat = 258.49014809587965` runs;
- `Rdef = 28.094732669019656` runs;
- `Rpos = -470.90992226794697` runs;
- projected centering exposure remains exactly `148948.26306286638` PA.

The Savant byte drift was resolved through the narrow, predeclared source re-certification in `docs/player-value-v1-advancement-source-recertification-contract.md`. Actions run **`32378956567`** froze 3,700 projection-relevant player-season rows in artifact **`9410189065`** with canonical model-input SHA-256 `dfbd52dfaccd1cc20d2bf710c27755f169a7873fcd0efb45339debbb3ad4bbc8`. The largest primary-score relative drift was `0.0002302112248237264`, below the `0.001` gate; `A2_k25` remained the unique development winner and retained its 2024 confirmation verdict. No model was refit or reselected.

The first numerical materialization exposed a concrete integration contradiction during final component-subtotal QA: the catcher-opportunity artifact uses component keys `catcher_throwing`, `catcher_blocking`, and `catcher_framing`, while the materializer had looked up the shorter model-family labels. That made all catcher opportunities zero despite C2/F1 eligibility. Commit `21b1151` corrected only this schema mapping; no model, coefficient, exposure formula, population, or source was changed.

Corrected numerical materialization Actions run **`32384563289`** passed every workflow step and refroze `docs/player-value-v1-mlb-centering-2024.json`. Its component artifact is **`9412396481`**, digest `sha256:d7f7a055002597200805f40ef4ccbef75fd9c0db773294133873abc80b8714b7`. The verified reference is:

- `Rbat = 258.49014809587965` runs;
- `Rbr = 35.008603291041524` runs;
- `Rdef = 28.094732669019656` runs;
- `Rpos = -470.90992226794697` runs;
- raw total `Ravg_raw_ref = -149.31643821200615` runs;
- `centering_runs_per_pa = 0.0010024718324441579`;
- aggregate `Rlg = 149.31643821200612` runs;
- post-centering residual `= -2.842170943040401e-14` runs, within the binding `1e-10` tolerance.

All 651 component rows are explicit. The six outside-snapshot members remain present with projected exposure and all four components equal to zero. Replacement and realized 2024 player components are excluded, and the official `182,449` PA accounting anchor is preserved without being used as the centering denominator. The obsolete fail-closed blocker was removed by the verified workflow.

Legacy advancement-selection run **`32378956317`**, triggered by the shared projection-helper edit, failed at its intentional original-byte hash lock for the already-adjudicated 2019 Savant drift. Its 18 code tests passed before that source lock fired. This does not supersede or invalidate the successful re-certification; the frozen model remains `A2_k25`.

## COMPLETED STAGE — park-neutrality audit

Binding pre-outcome contract: `docs/player-value-v1-park-neutrality-audit-contract.md`.

Verified result: `docs/player-value-v1-park-neutrality-audit-result.json`.

Actions run **`32381035435`** passed all workflow steps, downloaded the four exact frozen source artifacts, and uploaded diagnostic artifact **`9411024828`** with digest `sha256:9a85d711b2d68ac553df35055b0d7c74edd90c07563b00925e6f911ba2171738`.

The predeclared primary test compared each same-team incumbent's 2023 home-minus-away signal with the frozen B2 projection minus 2024 away-only performance. It retained 251 players, 28 teams, and 55,988 away PA after all player/team exposure gates. Results were decisively below every material retained-context threshold:

- full-season retention slope: `-0.012703125674` versus required `>= 0.25`;
- fitted retained-context weighted SD: `0.072080770764` runs/600 PA versus required `>= 1.0`;
- one-sided 10,000-permutation p-value: `0.549945005499` versus required `<= 0.05`;
- first-/second-half slopes: `-0.047819950981` / `0.05284180674`, failing the same-positive-sign gate.

Realized 2024 venue context remained visible as expected: the 30 primary venues had a weighted residual SD of `3.799161849204` runs/600 PA. That secondary diagnostic does not show retained prior-park bias because it uses realized venue outcomes; it was predeclared as non-decisional. The primary out-of-time away-only retention test failed four of five gates, so no park-correction design gate opens and **`Rpark = 0` is frozen for Player Value v1**.

The audit reproduced the binding 645-player / 181,190-PA positive-observed-PA diagnostic before context assignment. One four-PA player-game for MLBAM `643376` was excluded because its frozen rows map the batter to both teams, making a single batting-team assignment false; the final contextual diagnostic surface is 645 players / 181,186 PA. This exclusion affects only the park audit, not the 651-player centering cohort or its frozen denominator.

No live Savant source was fetched, no B2 probability was changed, realized 2024 data were used only as audit targets, numerical centering was unchanged, and no 2025 data or WAR result was accessed.

## COMPLETED STAGE — required pre-WAR sensitivities

Park neutrality and every predeclared sensitivity are resolved. Comparable frozen surfaces were materialized; the one alternate-season sensitivity lacking a complete surface was explicitly closed as unavailable under its predeclared contract.

### Baseball-Reference positional schedule — DONE / VERIFIED

`docs/player-value-v1-positional-adjustment-sensitivity-2024.json` applies the documented Baseball-Reference raw schedule to the exact frozen 3,046-player position/DH exposure surface. Actions run **`32381604496`** passed and uploaded artifact **`9411231308`**, digest `sha256:8f16bd1e4686c306e70586c103824ac85749fd01655952a29ee5385191756aa1`.

- binding FanGraphs aggregate: `-473.74028349337` positional runs;
- Baseball-Reference sensitivity aggregate: `-440.9744444444445` runs;
- aggregate difference: `+32.76583904892546` runs;
- player median / mean absolute difference: `0.0` / `0.06353248512895247` runs;
- player range: `-2.1774759945130313` to `+2.1908367626886136` runs.

This is diagnostic only. The binding `fangraphs_fixed_162_game_v1` schedule and all frozen exposures remain unchanged. Companion implementation verification run **`32381604402`** also passed.

### Baseball-Reference player-aware/PythagenPat conversion — DONE / VERIFIED

`docs/player-value-v1-runs-per-win-pythagenpat-sensitivity-2024.json` applies the pre-outcome method in `docs/player-value-v1-runs-per-win-pythagenpat-sensitivity-contract.md` to the corrected exact 651-player numerical-centering component surface. Actions run **`32384803016`** passed and uploaded artifact **`9412468709`**, digest `sha256:6e863c22ef7648c8420c99e0ddad17050fd2c7ecc70a191702f32f97f8aea957`.

- binding common-divisor aggregate: `465.1468161753401` WAR;
- player-aware PythagenPat aggregate: `478.08987545054936` WAR;
- aggregate sensitivity difference: `+12.943059275209217` WAR;
- player median / mean absolute difference: `+0.01279717756736326` / `0.02255035452526801` WAR;
- player range: `-0.06789256135656863` to `+0.12783583765981366` WAR;
- all 651 rows, the `148948.26306286638` projected-PA denominator, and the six explicit zero-exposure rows reconciled.

This is diagnostic only. The binding `9.682629939156854` common RPW, frozen components, centering, and replacement rate remain unchanged.

Replacement sensitivities were already completed in `docs/player-value-v1-replacement-level-2024.json`. No predeclared sensitivity remains open.

## Final WAR aggregation and ranking — DONE / FROZEN / VERIFIED

Intended final decomposable form:

`RAR = Rbat + Rbr + Rdef + Rpos + Rlg + Rpark_if_required + Rrep`

`WAR = RAR / RPW`

Completed before the final WAR freeze:

- Baseball-Reference positional sensitivity;
- alternate recent certified MLB batting reference when available;
- replacement sensitivities above;
- PythagenPat run-to-win sensitivity if practical;
- any baserunning/centering sensitivities predeclared before outcomes.

The alternate recent centering sensitivity was closed as unavailable by
`docs/player-value-v1-alternate-centering-sensitivity-feasibility.json`; Actions run
**`32383260384`** passed and uploaded artifact **`9411870714`**, digest
`sha256:0755279274cfa0440f29cf48db4186d70b0cc28f99a71afaf0c287f76e03cc18`.
The frozen surface has 2023 B2, baserunning, defense, position, and DH machinery,
but lacks both a certified official 2023 positive-PA cohort/outside-snapshot audit
and the certified 2023 MLB batting run-reference tables. The centering contract
forbids manufacturing a partial alternative, so no alternate constant was computed.

The pre-outcome final method and 3,051-player complete-component population are
frozen in `docs/player-value-v1-final-aggregation-contract.md`. Actions run
**`32385002209`** passed every step and uploaded final artifact **`9412571491`**,
digest `sha256:e1dd002d03cccf61345b806a323ec67acacf83a99c8badc7cfe1d3da8f164b71`.
The workflow froze `docs/player-value-v1-final-2024.json` and the complete ranked
Parquet table.

Final aggregate values across 3,051 rows:

- projected component surface: 3,045 complete frozen players plus the six explicit zero rows;
- `Rbat = -147.189347986084` runs;
- `Rbr = 33.16264877734028` runs;
- general range / catcher throwing / blocking / framing = `73.28812216345528` / `-21.476703642600523` / `20.44617985788917` / `-53.60093988024389` runs;
- `Rdef = 18.656658498500054` runs after exact subtotal reconciliation;
- `Rpos = -473.74028349336993` runs;
- `Rlg = 166.21292938234564` runs;
- `Rpark = 0.0` runs;
- `Rrep = 5013.494795777783` runs;
- `RAR = 4610.597400956516` runs;
- aggregate `WAR = 476.17201420774313` at binding RPW `9.682629939156854`.

Mechanical QA reproduced all 651 corrected centering rows with maximum component
delta `0.0`, retained all six zero rows, reconciled defense subtotals within
`1.7763568394002505e-15` runs, and reconciled the RAR identity within
`7.105427357601002e-15` runs. The final ordering uses unrounded WAR descending
and ascending MLBAM ID only as a deterministic tie-break.

## Formal forecast uncertainty — DONE / FROZEN / VERIFIED

The pre-output method was frozen in
`docs/player-value-v1-uncertainty-contract.md` at commit `9d6e5ad`, before any
interval result was materialized. It adds deterministic equal-tail 80% and 95%
model-based forecast intervals around the final 3,051 point estimates using the
frozen Playing Time hurdle/NB2 distribution, the B2 empirical-Bayes evidence
surface, and Defense family residual MSEs. It does not change point components,
rank order, population, or any upstream selection.

Actions run **`32388953065`** passed all steps, including 33 focused tests in
the workflow's selected suites, exact frozen-artifact downloads, the complete
3,051-player simulation, and a byte-for-byte deterministic rerun. Artifact
**`9414064136`**, digest
`sha256:412baa74c72532e76f97f09da742a657d15c7b3d70407c0926337946aae146f3`,
contains the complete Parquet interval table and the frozen result
`docs/player-value-v1-uncertainty-2024.json`.

Mechanical QA verified:

- all 3,051 rows and the original point rank/WAR are unchanged;
- all six outside-snapshot structural-zero rows retain zero-width intervals;
- Playing Time expected-PA reconciliation delta is exactly `0.0`;
- maximum batting point reproduction delta is
  `9.381384558082573e-15` runs;
- maximum point-WAR identity delta is exactly `0.0`;
- maximum component variance-share sum residual is
  `2.220446049250313e-16`;
- every interval is finite and nested.

Across players, mean 80% / 95% interval widths are
`0.4837201039184545` / `0.9595463558223047` WAR; 95th-percentile widths are
`3.0470708095058248` / `5.679540011257353` WAR. The median variance share is
`0.686922382072843` Playing Time, `0.2676183130576742` batting, and `0.0`
Defense. The hurdle model produces zero-width 80% / 95% intervals for 2,273 /
1,848 low-participation rows because the corresponding central interval is
entirely at zero; no cap, floor, or post-result repair was applied.

These intervals are conditional on the frozen v1 uncertainty surfaces. They do
not invent independent baserunning-skill, future position/DH-mix, league-constant,
source-revision, or cross-component covariance error. Those omissions are
explicit in the result and remain possible v2 gates.

## Repository integration audit — DONE / VERIFIED

A full integration audit was completed on 2026-08-20. Packaging now exposes an
explicit `playing-time` extra, the `dev` extra includes every runtime imported by
the complete test suite, PR CI runs Ruff before tests, warnings are promoted to
errors, and repository-level tests enforce JSON parsing, local Markdown-link
resolution, unique workflow names, dependency coverage, workflow lifecycle, and
the frozen Player Value arithmetic.

The audit also caught a post-freeze reproducibility defect. Cleanup-only edits
triggered eight historical writer workflows. All eight runs completed
mechanically, but they rewrote frozen provenance and several numerical surfaces.
In particular, Defense run `32391048359` refit against live Savant leaderboard
responses even though its inputs were described as frozen. Comparison with the
original immutable freeze artifact from run `32198603779`, artifact
`9346716010`, digest
`sha256:b45493f8014c52eafbea0ab4dca18e99394ca7d11318052b60204198fc711acf`,
showed:

- three 2022 general-range target rows changed by exactly `-1.0` raw run;
- 65 of 72 catcher-throwing rows changed, with maximum absolute raw drift
  `0.03209811233209861`;
- 44 of 70 catcher-blocking rows changed, with maximum absolute raw drift
  `0.057441866089979005`;
- the catcher responses were repeated across requested target years, confirming
  that this superseded live target path is not an acceptable frozen source.

Those bot-written result changes were rejected and the pre-audit binding files
were restored exactly. The accepted Defense parameter package remains the
original run `32198603779` freeze, while the repaired catcher machinery remains
the later production authority documented elsewhere in this handoff. No final
Player Value component, WAR, rank, interval, or binding population changed.

The Stage 2c design has now been amended before any candidate score. A second
Tango/Chamberlain/Judge/direct-PBP review separates completed-play value from
forecastable player talent and narrows the first pulled-air test to future HR
only. Non-HR XBH and ground-direction effects are separate, ordered ablations
that cannot rescue a failed HR test. The prior schema 0.3 unscored
implementation is superseded and may not be scored.

Schema 0.4 was implemented and verified target-free. E1 can alter only the
HR/contact contrast; E2 requires E1 during fitting and prediction and can alter
only non-HR XBH composition; E3 requires E1 or E2 and can alter only non-HR
reach. The chained zero-increment ladder exactly reproduces C0 for all 4,705,
5,568, and 6,381 V2022-V2024 forecasts, including 224, 245, and 249 exact
missing-shape fallbacks. The generated report reproduced byte-for-byte before
the E1 scorer was frozen.

The E1 scorer was committed at `5983237` before its single disclosed-outcome
run. E1 failed: HR-conditional log loss improved only in the V2023 equal-player
view and worsened in V2023 contact-weighted plus both V2024 views. Its tiny
increment did not add stable power information beyond C0. E2 is unauthorized,
post-result tuning is forbidden, and the next gate is documentation and
independent design review only.

A source-only scan of 113 disclosed 2021-2024 affiliated PBP files found
`hit_distance_sc` on 360,929 / 1,954,502 classified batted-ball PAs (18.47%).
It co-occurred with exit velocity on 99.936% of those PAs and had zero or near-
zero coverage in High-A and AA versus 96.97% in 2024 AAA. Distance is therefore
a later capability-aware tracking/enriched-PBP residual, not part of the
universal PBP base. Protected 2026 remains unopened. Ruff and all 893 tests
pass after the frozen E1 result was documented.

Because every v1 gate is complete, all 211 historical research/materialization
workflows are now manual-only. `.github/workflows/ci.yml` is the sole automatic
workflow, runs on pull requests and `main`, and supports explicit branch-level
manual verification. The lifecycle policy is frozen in
`docs/workflow-lifecycle.md`; a manual historical rerun is diagnostic and cannot
silently redefine a binding v1 result.

Branch-level integration run `32392573145` verified the archived lifecycle on
commit `e1535d36ee35ecb2bd873451589bc0c9c0ee7626`: project installation, Ruff,
and all `798` tests completed successfully.

## Governing read order

1. `docs/project-status.md`
2. `docs/hitter-v2-methodology-review.md`
3. `docs/hitter-v2-source-contract.md`
4. `docs/hitter-v2-development-contract.md`
5. `docs/hitter-v2-workflow-status.json`
6. `docs/hitter-v2-stage2b-development-contract.md`
7. `docs/hitter-v2-stage2b-development-contract.json`
8. `docs/hitter-v2-stage2b-contact-shape-source-result.json`
9. `docs/hitter-v2-stage2b-unscored-result.json`
10. `docs/hitter-v2-stage2b-scoring-contract.json`
11. `docs/hitter-v2-stage2b-scoring-execution-incident.json`
12. `docs/hitter-v2-stage2b-development-checkpoint.md`
13. `docs/hitter-v2-stage2b-development-result.json`
14. `docs/hitter-v2-contact-direction-literature-review.md`
15. `docs/hitter-v2-distance-source-audit.md`
16. `docs/hitter-v2-distance-source-result.json`
17. `docs/hitter-v2-next-research-plan.md`
18. `docs/hitter-v2-stage2c-development-contract.md`
19. `docs/hitter-v2-stage2c-development-contract.json`
20. `docs/hitter-v2-stage2c-e1-scoring-contract.json`
21. `docs/hitter-v2-stage2c-e1-development-checkpoint.md`
22. `docs/hitter-v2-stage2c-e1-development-result.json`
23. `docs/hitter-v2-post-e1-independent-design-review.md`
24. `docs/hitter-v2-post-e1-source-readiness.json`
25. `docs/hitter-v2-matchup-context-source-audit.md`
26. `docs/hitter-v2-matchup-context-source-result.json`
27. `docs/hitter-v2-matchup-context-sidecar-checkpoint.md`
28. `docs/hitter-v2-matchup-context-sidecar-result.json`
29. `docs/hitter-v2-stage2d-development-contract.md`
30. `docs/hitter-v2-stage2d-development-contract.json`
31. `docs/hitter-v2-terminal-outcome-label-sidecar-checkpoint.md`
32. `docs/hitter-v2-terminal-outcome-label-sidecar-result.json`
33. `docs/hitter-v2-stage2d-implementation-checkpoint.md`
34. `docs/hitter-v2-stage2d-input-result.json`
35. `docs/hitter-v2-stage2d-j0-fit-execution-contract.json`
36. `docs/hitter-v2-stage2d-j0-fit-authorization.json`
37. `docs/hitter-v2-stage2d-j0-fit-failure-checkpoint.md`
38. `docs/hitter-v2-stage2d-j0-fit-incident.json`
39. `docs/hitter-v2-post-j0-numerical-method-review.md`
40. `docs/hitter-v2-stage2e-development-contract.md`
41. `docs/hitter-v2-stage2e-development-contract.json`
42. `docs/hitter-v2-stage2e-authorization.json`
43. `docs/hitter-v2-stage2e-implementation-checkpoint.json`
44. `docs/hitter-v2-stage2e-certification-result.json`
45. `docs/hitter-v2-stage2e-fit-authorization.json`
46. `docs/hitter-v2-stage2e-fit-execution-contract.json`
47. `docs/hitter-v2-stage2e-fit-result.json`
48. `docs/hitter-v2-stage2e-scoring-contract.json`
49. `docs/hitter-v2-stage2e-comparison-result.json`
50. `docs/hitter-v2-stage2e-postmortem-contract.json`
51. `docs/hitter-v2-stage2e-postmortem.md`
52. `docs/hitter-v2-stage2e-postmortem-result.json`
53. `docs/hitter-v2-stage2f-development-contract.md`
54. `docs/hitter-v2-stage2f-development-contract.json`
55. `docs/hitter-v2-stage2f-authorization.json`
56. `docs/hitter-v2-stage2f-H0-target-free-checkpoint.md`
57. `docs/hitter-v2-stage2f-H0-target-free-checkpoint.json`
58. `docs/hitter-v2-stage2f-H0-fit-authorization.json`
59. `docs/hitter-v2-stage2f-H0-fit-checkpoint.md`
60. `docs/hitter-v2-stage2f-H0-fit-checkpoint.json`
61. `docs/hitter-v2-stage2f-H0-selection-authorization.json`
62. `docs/hitter-v2-stage2f-H0-selection-checkpoint.md`
63. `docs/hitter-v2-stage2f-H0-selection-checkpoint.json`
64. `docs/hitter-v2-stage2f-H0-scoring-authorization.json`
65. `docs/hitter-v2-stage2f-H0-scoring-contract.json`
66. `docs/hitter-v2-stage2f-H0-scoring-execution-incident.json`
67. `docs/hitter-v2-stage2f-H0-comparison-result.md`
68. `docs/hitter-v2-stage2f-H0-comparison-result.json`
69. `docs/hitter-v2-post-H0-diagnostic-authorization.json`
70. `docs/hitter-v2-post-H0-diagnostic-contract.json`
71. `docs/hitter-v2-post-H0-diagnostic-result.md`
72. `docs/hitter-v2-post-H0-diagnostic-result.json`
73. `docs/hitter-v2-stability-increment-ladder-contract.json`
74. `docs/hitter-v2-stability-increment-ladder-checkpoint.json`
75. `docs/hitter-v2-stage2-failure-diagnostic-result.json`
44. `docs/hitter-v2-stage2-final-validation-checkpoint.md`
45. `docs/hitter-v2-stage2-final-validation-result.json`
46. `docs/hitter-v2-v1-external-validity-result.json`
47. `docs/player-value-v1-war-literature-review.md`
48. `docs/player-value-v1-architecture-contract.md`
49. `docs/player-value-v1-mlb-centering-contract.md`
50. `docs/player-value-v1-mlb-centering-2024-membership.json`
51. `docs/player-value-v1-mlb-centering-2024.json`
52. `docs/player-value-v1-park-neutrality-audit-contract.md`
53. `docs/player-value-v1-park-neutrality-audit-result.json`
54. `docs/player-value-v1-mlb-centering-verification.json`
55. `docs/player-value-v1-runs-per-win-pythagenpat-sensitivity-contract.md`
56. `docs/player-value-v1-runs-per-win-pythagenpat-sensitivity-2024.json`
57. `docs/player-value-v1-alternate-centering-sensitivity-feasibility.json`
58. `docs/player-value-v1-final-aggregation-contract.md`
59. `docs/player-value-v1-final-2024.json`
60. `docs/player-value-v1-uncertainty-contract.md`
61. `docs/player-value-v1-uncertainty-2024.json`
62. `docs/player-value-v1-replacement-level-contract.md`
63. `docs/player-value-v1-replacement-level-2024.json`
64. `docs/player-value-v1-replacement-level-verification.json`
65. `docs/player-value-v1-runs-per-win-contract.md`
66. `docs/player-value-v1-mlb-run-environment-2024.json`
67. `docs/player-value-v1-batting-runs-contract.md`
68. `docs/player-value-v1-positional-adjustment-contract.md`
69. `docs/player-value-v1-defense-production-handoff.md`
70. `docs/player-value-v1-defense-native-run-conversion-parameters.json`
71. `docs/player-value-v1-baserunning-source-audit-contract.md`
72. `docs/player-value-v1-baserunning-source-audit-result.json`
73. `docs/player-value-v1-steal-projection-selection-contract.md`
74. `docs/player-value-v1-steal-projection-diagnostic-thresholds.md`
75. `docs/player-value-v1-steal-projection-selection-result.json`
76. `docs/player-value-v1-advancement-projection-selection-contract.md`
77. `docs/player-value-v1-advancement-projection-selection-result.json`
78. `docs/player-value-v1-baserunning-run-conversion-contract.md`
79. `docs/player-value-v1-baserunning-run-conversion-2024.json`
80. `docs/projection-batting-v1-development-result.json`
81. `docs/current-talent-results-only-baseline-freeze.md`

## Working rules

- Work in small verified batches.
- Preserve immutable source evidence and provenance.
- Keep all position-player v1 artifacts frozen; Hitter v2 uses new namespaces.
- Do not score a Hitter v2 candidate until Stage 1 is reviewed and the frozen
  development-contract hash is verified.
- Do not access completed 2026 hitter outcomes until the selected development
  candidate and one-shot confirmation scorer are frozen and review explicitly
  authorizes the boundary.
- Reuse certified artifacts where scope matches.
- Freeze exact model/source decisions before opening genuinely unused confirmation evidence.
- Do not tune downstream decisions to already-accessed 2025 confirmation residuals.
- Do not center against the universal ranking population.
- Do not add park adjustment without evidence of residual park context.
- Do not revise the frozen final aggregation method or population from ranking outcomes.
