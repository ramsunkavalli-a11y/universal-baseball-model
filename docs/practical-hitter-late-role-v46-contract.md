# Late-season role trajectory: one substantive workload test

2026-10-03. V45's fourteen player reviews are complete. This follows the
practical hitter plan's opportunity gap, not a new algorithm tournament.

## Baseball question and prior evidence

Does distinguishing a recent MLB job from an equally sized annual bench/absence
history improve next-calendar-year expected MLB PA and delivered batting-plus-
replacement value? Annual PA/game cannot tell when the opportunity happened.
This does not forecast a team's future depth chart or infer medical diagnoses.
The older recent-usage test improved rest-of-season allocation; its September
targets do not establish next-year usefulness. The older role-workload experiment
added whole-season starts/position shares and did not improve its base. Neither
experiment tests this exact within-season annual-forecast contrast.

Use official MLB byDateRange hitting responses and completed regular-season
schedules for 2010–2024. Fetch full calendar-year regular-season counts for source
reconciliation, the final 30 calendar days ending at the last completed regular-
season game, and the preceding nonoverlapping 30 days. Only sport 1, game type R;
no playoffs, future medical events, 2025 predictor records or 2026 outcomes.
Retrospective performance corrections remain a vintage qualification, not a claim
we possess archived publication snapshots. This is MLB usage only, not complete
minor-league starts, lineup jobs, promotions, contracts or prospect grades.

## Source gate before fits

Require complete returned split counts, one aggregate row per player (do not
sum aggregate plus team splits), explicit PA/games fields, nonnegative counts,
sport/season identity and actual date bounds. Confirm full-season PA exactly
against the prior official player-season MLB counts; confirm all last/preceding
counts fit inside annual counts and their nonoverlapping sum does not exceed it.
An unresolved difference blocks fitting rather than becoming zero or a silently
replaced source. Games need not equal annual summed team appearances when trade
aggregation differs; show differences rather than calling starts or health.
Persist request URLs, bytes/hashes and date/schedule denominators. Deduplicate
completed game identities. A missing response is unknown; a player absent from
a certified full-year complete MLB response has zero observed MLB usage only.
Walk the fixed nine diagnostic players through the actual windows before fitting.

## Exact contrast, chronology and estimand

Same V38 239 count/game features and same 35 chronological player-held folds,
30,506 evaluated rows, equal-origin training weights, target-2020 exclusion and
cutoff-mature outcomes. Add current/prior-year window features: availability,
late and preceding PA/games, stabilized PA per appearance (20 PA/five-game
prior), and PA per average scheduled MLB team game in each window. The eighteen
features are fixed here; no contact, park, health or pedigree expansion. Two
months' actual totals remain in inputs; per-game involvement is not a start.
League-average schedule denominators are transparent proxies, not a traded
player's exact team schedule or an enforced team budget.

Reuse the squared-error PA learner/settings from V38 exactly: 250 iterations,
depth 3, minimum leaf 30, rate .05, L2 10, seed 31, no early stopping, two threads.
Keep the source-consistent V34 batting head exact, bounded PA [0,800], identical
V44 retirement/permanent availability policies, and delivered contribution
PA × (batting wins/600 / 600 + origin replacement rate). This tests workload only;
no talent or full-WAR improvement is inferred from fixed-rate multiplication.
Working V33b, V34 and V38 anchors receive the same policy and keep all rows.
All 218 unverified roster-only rows remain; report supported diagnostic as well.
Run actual-fold preflight and distinct-player stage/debut/age/workload profiles,
plus late-exposure categories absent/1–49/50–99/100+ crossed with stage/debut.
Sparse/unseen profiles are tagged, not removed. No nested tuning is performed.

## Scoring, cases and stopping rule

Primary: equal-origin expected-PA RMSE/MAE and fixed-rate contribution RMSE;
unchanged 1,789 public matches versus Steamer and our anchors. Show all origins,
stages, brief debuts, never-debut upper minors and absent prior-debut players,
total PA/contribution and nominal player-paired intervals. No revised public
tolerance, total rescaling, post-result feature tuning or median substitution.
Require no material cohort harm hiding a pooled win. A small uncertain gain is
research evidence, not deployment or a declaration the full hitter goal is met.

Fixed cases: Kurtz 2024, Volpe 2022, Judge 2016/2024, Rooker 2022, Pujols 2021,
Swanson 2016, Dahl 2016, Tatis 2022. Add largest PA/value gains/harms, false highs/
lows and ordinary cases. Preserve all actual counts and added inputs, exact saved
tree accounting, raw/bounded means, unchanged batting/value arithmetic, fold
support and origin-selected successful/unsuccessful peers. Explain later outcomes
without feeding them back into eligibility or inputs. Every head must replay.
Manual reviews precede disposition or another model decision. If it loses, close
this bounded representation test without declaring all timing or role data useless.
Protected 2026/frozen forecasts/deployed explorer remain unchanged.

Pre-fit execution amendment: the older compact schedule omits officialDate and
labels postponed entries abstractly Final. It also repeats suspended/rescheduled
game identities on different calendar rows. A source assertion exposed this
before any usage windows or fitted models were created. Capture fifteen official
schedules with officialDate; include only actually completed F/O states and
deduplicate gamePk with consistent official date/team identity. This changes no
model or scoring choice and does not certify the older schedule's denominators.
Total historical requests are about sixty, including these schedule captures.

Source-driven amendment BEFORE fitting: all fifteen annual PA reconstructions
match the old player-season PA exactly, and both nonoverlapping PA windows fit
inside them. However, byDateRange gamesPlayed does not equal the old summed team
games for 114–567 people in most seasons (often small/zero-PA players); some
regulars differ too. Their precise definition/correction cause is not established.
Do not claim they are interchangeable or solve this by assuming trades. Retain
raw games in the source audit, but OMIT all new window-game/PA-per-appearance
features. The candidate adds TEN features: complete-year availability, late PA,
preceding PA and each divided by its average scheduled team games, for two years.
These measure reliable batting opportunity directly. Existing V38 inputs remain
unchanged for a fair contrast. No model outcome has been inspected, and no fit
exists at this amendment. Original proposed eighteen-feature design is retained
above as history, superseded only by this measured source limitation.
