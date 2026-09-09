# Project status and handoff

Updated 2026-09-09. This is the current start-here document.

Latest: official StatsAPI Rule 4 draft history is now a structured, replayable source.
A nested later-cohort audit supports draft pedigree for hitter arrival and meaningful
role research, but not for the stricter established-role outcome; pitcher arrival
gains are directionally positive but uncertain. Pre-MLB FV is
now bracketed: the year-by-year paths are too conservative for true elite prospects,
while the six-full-seasons override is too generous across the long tail.

The first closed-system audit also finds that aggregate capacity is not exceeded, but
independent hitter and pitcher paths disagree by as much as 5.4% of the same league
PA/BF pool. A symmetric league-level reconciliation is specified for research; team
and role allocation remains the next step before production use.

## Active plan

The user has prioritized model quality and paused interface development. Read the
[authoritative product roadmap](product-roadmap.md) first. It supersedes narrower
component-specific next-experiment lists for prioritization while preserving their
results and frozen decisions.

The clarified end goal is every-player trade value updated with each game.
The [direction review](trade-value-direction-review.md) finds useful foundations
but missing career/control/cost and continuous-update integration. It also identifies
older opportunity/roster models to reuse before building another challenger.
The broader roadmap now includes pitcher and whole-player value integration;
website work remains paused. No player dollar ranking has been promoted.
A private, generated results explorer now makes the current research checkpoint easy
to inspect without publishing it. It exposes filters, sortable player results,
year-by-year paths, review rows and CSV export while retaining the model warnings.

## Active Phase 2 preview

The [Model FV and workload preview](phase2-model-fv-and-workload-2026-09-09.md)
is now the active continuation. Historical, time-ordered models replace the old
pre-MLB arrival shortcut and separately estimate any debut and a meaningful MLB role.
Both beat a level-only baseline in every evaluation fold. The arrival probability now
enters expected WAR; meaningful-role probability is diagnostic. The top prospect list
is still too crowded because conditional-on-arrival WAR is too generous. Historical
MLB outcome quality and durable draft/signing evidence are the next P0 work.

The first [demographic feature search](phase2-demographic-feature-search-2026-09-09.md)
now retains official profiles for 24,328 players and tests stable and full demographic
groups without outside FV inputs. Narrower searches named stable-interaction and
birth-country development leaders, but neither is promoted because the same periods
were searched to find them. Current-recorded physical measurements remain exploratory
until their historical timing is safe.

A stricter [nested robustness audit](prospect-arrival-nested-robustness-result.md) now
supersedes that initial ranking. It normalizes 313 equivalent StatsAPI country labels
and tests 176 combinations across demographics, baseball development/role interactions,
logistic shrinkage, and production-rate regression. It embargoes incomplete two-year
outcomes, evaluates proper scores/calibration with paired uncertainty, and checks
supported subgroups. Structured draft evidence materially improves hitter arrival and
meaningful-role log loss, but is not selected for the stricter established-role
outcome. Pitcher pedigree gains remain uncertain. No input changes production values.
The reusable rules now govern all StatsAPI/PBP feature searches through the
[model-search policy](model-search-validation-policy.md), not demographics alone.

The first [mature post-debut workload study](prospect-outcome-quality-workload-result.md)
now quantifies the larger Model FV flaw. Actual six-calendar-year workload averages
61 PA for fringe hitter arrivals versus 1,986 PA for hitters with a meaningful season;
meaningful pitchers average 948 BF as relievers, 1,154 as swingmen and 2,505 as
starters. The existing preview assumes far more workload after any arrival. A binary
fringe/meaningful replacement nevertheless overcorrects—hitter 50+ counts fall from
320 to 18 and external Top-100 diagnostic error worsens—so it is rejected. Production
values stay unchanged while regular/impact probabilities and durable pedigree are
built next.

This work builds on the recovered-opportunity commit `7c2a874`. Main now contains the
current model foundations, experiment records and plan. It does not change a website
or promote a player ranking; the public v1 release remains historical.

## Phase 1 foundation progress

- The player-rights universe contract now preserves every required player, represents
  missing evidence as `unknown / prior_only`, rejects future observations and fails
  closed on ownership conflicts. Certified dated 40-man membership is connected as
  one narrow evidence family. A separate candidate inventory unions broad discovery
  sources with provenance while preventing candidate presence from asserting an owner.
- The official `fullRoster` source is the primary player-discovery source: 7,891
  players, with 99.80% having one candidate organization. Its 16 cross-organization
  outliers prevent using it alone as final rights proof, not using it as the denominator.
  A chronology-safe official transaction ledger now supports a bounded ownership gate:
  unique 40-man membership is direct evidence, then exact structured acquisition and
  MLB-rights transactions resolve only the remaining multi-organization cases.
- The career-outcome panel makes completed-season absence an observed zero and later
  seasons right-censored. A real official 2015–2024 inventory contains 10,585 batting
  player-seasons, 8,095 pitching player-seasons and 3,777 distinct MLB players.
- A transparent pitcher component baseline now separates K, UBB, HBP, HR and other-BF
  rate skill from opportunity. It beat a global population comparator in every rolling
  2018–2024 fold; equal-fold log loss was 0.98044 versus 0.98500.
- Team-control arithmetic and the conservative StatsAPI replay are implemented. A
  Padres working sample plus Giants holdout confirms FanGraphs as the dated
  service/options baseline, StatsAPI for forward changes and Rule 5, and transactions
  as a bounded exception layer. Broad comparison coverage is 95.2% and 98.4%; Rule 5
  year agreement is 180/186 where both values are available.
- All 30 payroll workbooks normalize into 915 player records, 3,720 annual terms, 180
  clauses and 417 other payments. Stable IDs attach 870 players; current official
  roster entries corroborate the remaining 45 exact-name identities. Payroll identity
  review is now zero, while liabilities for former roster members remain separate from
  current team control.
- The refreshed 2026-09-08 league build contains 8,393 affiliated players and 50,058
  future-path rows for 8,343 players through 2032. Exact official release evidence now
  separates 37 players with no incumbent rights, while one same-day transaction conflict
  remains in review. All prior multi-organization cases are
  resolved: 15 by unique official 40-man membership and six by exact transactions.
  Its complete 133-player Super Two
  pool has a calculated cutoff of
  `2.144` (488 days), with 30 selected because the cutoff is tied. FanGraphs supplies
  the 2026 opening balance; StatsAPI supplies in-season service through the as-of date.
- The control build now retains all 230 official responses used by the current
  checkpoint as hash-verified canonical JSON. This makes the parsed source values
  reproducible after the live API changes. An offline league rebuild reproduced
  all core tables, summary and manifest byte for byte. The manifest does not claim
  original HTTP-byte fidelity or an unavailable retrieval timestamp.
- Historical FanGraphs Opening Day Tracker captures add MLBAM-keyed 2024 and 2025
  service/options baselines for 2,012 and 2,024 players. They cover all 30 teams and
  avoid name matching. Because the pages were retrieved later, they are accepted for
  retrospective event-cutoff replay, not true vintage-information claims. Historical
  contract obligations remain the material Step 8 source gap. Member workbooks
  independently reproduce every overlapping 2024–2025 control field, add Opening Day
  PA/IP projections, and extend the source back to 2,065 players in 2023. Their raw
  and normalized bulk data remain private.
- A 30-team Cot's-derived 2025 extract has now been inspected as a potential private
  retrospective contract bridge. It includes 2025–2029 salary/control columns but was
  created after the season and has names rather than MLBAM IDs. Use requires a
  same-team name match corroborated by service; it is not vintage or primary authority.
  Its implemented parser produces 1,289 players and 6,445 annual terms; 1,192 players
  attach to MLBAM by exact team/name/service agreement. Ninety-seven remain review.
  The annual valuation gate accepts 1,308 guaranteed salary rows, routes 1,125
  arbitration rows to the CBA calculation, ends control on 473 free-agent rows and
  holds back 118 option rows. Only seven exact-identity numeric cells remain unclear.
- The first 2025 historical projection path now covers 3,891 hitters and 5,090
  pitchers through 2029. The one-year opportunity models were refit using targets
  only through 2024; later years use pre-2025 historical fallbacks. FanGraphs PA/IP
  are external scale checks, not model inputs. The full 2025 universe receives
  183,343 expected hitter PA and 180,383 expected pitcher BF. Eight hitters and 24
  pitchers added by the Opening Day workbook retain labeled population fallbacks.
- The first historical control/value join now connects 7,998 of 8,946 projected
  players to an incumbent owner. FanGraphs supplies 2,019 Opening Day owners; dated
  official 40-man and transaction evidence resolve 199; 5,780 use the unique October
  2024 official full-roster owner. The remaining 948 players stay talent-only. Of
  39,990 owned annual rows, 39,648 calculate and 342 remain review for 33 missing
  service balances, 118 option years, 52 2025 Super Two cases and seven unclear
  contract cells. This is retrospective research evidence, not a ranking.
- The frozen 2025 replay is now scored. Hitter PA is 0.2% high and pitcher BF is
  0.9% low at league scale. Both models improve RMSE over carrying 2024 workload
  forward but lose on MAE; FanGraphs is materially better on its projected-player
  subset. Hitter and pitcher components beat their population log-loss references.
  Whole-player neutral WAR is 1,061.71 projected versus 995.75 observed, 6.6% high.
- The March 2025 value output passes the sequential checkpoint contract with 8,946
  players, 7,803 available values and 1,143 reviews. Joined to the September 2026
  current checkpoint, all 3,850 material deltas have declared reasons. Model and
  universe changes mean this proves mechanics, not same-model value stability.
- The exact March models now also run at an October 15 checkpoint without refitting.
  Official ownership and service evidence produces 7,749 usable October values. Among
  5,660 shared usable players, value correlation is 0.691; all 4,049 material changes
  have declared reasons. Every usable March and October value carries a Phase 1
  reference range. Median remaining-WAR width narrows from 2.76 to 2.07 WAR. These
  ranges are not calibrated coverage guarantees and omit cross-season covariance.
- Contract Economics v0 now keeps WAR, free-agent-equivalent value, contract/control
  value and later trade value separate. It values guaranteed, tender, club-option and
  player-option states, preserves optionality premium, discounts future values and
  fails closed on unresolved option triggers. Official 2022–2026 minimum salaries live
  in a versioned CBA ruleset. FanGraphs' published 2026 three-tier market curve is now
  the main reference; future growth and arbitration remain named assumptions rather
  than hidden constants.
- Projection v1 now has a common guardrail contract and executable audit. Every player-
  year must decompose expected WAR into MLB-active probability, conditional WAR rate
  and conditional PA/BF workload. Current-team depth is forbidden, hitter/pitcher
  components for two-way players remain separate, controlled WAR is summed directly,
  and pre-cutoff historical extremes are flagged without clipping. This is an
  interface and diagnostic layer; it does not claim the missing projection models are
  complete.
- Hitter Opportunity v1 now implements the first universal forecast input. It preserves
  zero-MLB outcomes, can use a frozen selected one-year model when supplied, and fills
  unsupported/later years with horizon-specific age/level cohorts and labeled
  population fallbacks. It never uses team depth or a PA cap and composes directly into
  the Projection v1 WAR schema. Historical cohorts and the current league snapshot are
  fitted. The confirmed B2 form's scoring parameters are not available, so the current
  materialization honestly uses the cohort fallback.
- Pitcher Opportunity v1 now applies the same separation to MLB arrival, conditional
  BF and starter/swingman/reliever probabilities. Sparse age/level/role cohorts shrink
  through a disclosed hierarchy, all fallback sources remain labeled, and the output
  composes with conditional WAR/800 BF and control seasons. Its historical league panel
  and current league snapshot are fitted.
- The official historical opportunity source is now collected for 2018–2024. Because
  `fullRoster` omits hundreds of players with official affiliated stats each year, the
  cohort denominator is their union. The misleading `totalSplits` field is ignored in
  favor of verified pagination. Excluding the cancelled 2020 MiLB season leaves 74,743
  hitter and 90,727 pitcher zero-inclusive cohort rows across horizons 1–6.
- The dated 2026-09-08 snapshot now produces complete 2027–2032 paths for
  3,940 hitters and 5,276 pitchers. Official position evidence reduced false two-way
  classification from 436 players to 22 by excluding incidental mop-up pitching. The
  current hitter and pitcher runs use their new provisional universal models for 2027
  and labeled historical fallbacks for 2028–2032.
- A newly versioned universal hitter-opportunity candidate now replaces the expired-
  artifact dead end without claiming to recreate B2. The precommitted rolling gate
  retains inactive, unknown-level and missing-age players and uses only level, age,
  current MLB/MiLB PA and exact-date 40-man membership. It beat the universal level-only
  model in all four 2022–2025 evaluations; pooled Brier error fell 20.5% and PA RMSE
  fell 26.1%. Its complete scoring package is committed, but it remains a provisional
  2026 candidate until a future protected-outcome confirmation.
- A matching universal pitcher gate now retains zero outcomes and current role while
  adding age, current MLB/minor-league BF and exact-date 40-man membership. The selected
  form won all four rolling folds; pooled Brier error fell 10.5%, BF MAE 15.1% and BF
  RMSE 10.5% against level/role only. Its exact package is committed and remains
  provisional pending protected 2026 confirmation.
- Direct horizon 2–4 models also passed every gate against both their parametric
  baselines and the incumbent cohort method. Hitter PA MAE improves 12–20% and pitcher
  BF MAE 6–8%. Incomplete 2003–2008 sources cannot support honest horizon 5–6 tests,
  so those years retain their labeled historical fallbacks.
- The selected models now score the current universe and connect through WAR,
  uncertainty, current remaining rights and contract economics. They add 564.59 future
  WAR through 2030; 2031–2032 are unchanged. The separate remaining-2026 estimate falls
  1.46 WAR. The scenario still
  has 50,898 annual rows, 8,332 complete controlled-player paths and the same 16 contract reviews.
  Its $5.89 billion discounted point total versus the retained $1.66 billion baseline
  is a research sensitivity, not a promoted ranking.
- The protected 2026 one-year confirmation is now locked before season end. Immutable
  selected, U0/P0 and incumbent forecasts cover the exact 2025-10-15 universe of 3,907
  hitters and 5,206 pitchers. No 2026 outcome file was read. The fixed confirmation
  rule waits for final official regular-season PA/BF and cannot be changed by subgroup
  results.
- The remaining-rights timeline now prevents live valuation from counting WAR already
  produced or salary already paid. Current-season rows require an explicit remaining
  salary obligation and cannot receive a fictional midseason non-tender option. Future
  rows retain full-season production, cost and decision states. Rest-of-season WAR and
  unpaid salary sources are the remaining live-2026 inputs.
- A current Phase 1 conditional-WAR baseline now joins recent official MLB skill
  evidence to all 2027–2032 opportunity rows: 23,640 hitter and 31,656 pitcher
  player-years. Recent-MLB players receive regressed component estimates; all others
  retain explicit population priors. Hitters include batting, primary position and
  replacement while missing defense/running begin as average-zero fallbacks. Pitchers
  use the validated five-part BF baseline and a disclosed Tango adjacent-aging
  fallback. No team depth or rate clipping is used.
- Official 2023–2026 affiliated components now feed a provisional MLB-anchored
  translation fitted on 3,204 hitter and 4,495 pitcher same-player/same-season mover
  pairs from completed 2023–2025. All six levels connect to MLB. Level-based evidence
  discounting plus 1,200-PA hitter and 800-BF pitcher priors replaces most pure
  population fallbacks without allowing raw lower-level rates to dominate a
  conditional-on-future-MLB estimate.
- The affiliated translation improved component log loss and Brier score against the
  same no-translation model in both 2024 and 2025 future-MLB folds for hitters and
  pitchers, and beat the MLB population prior in all four comparisons. It is retained
  as the simple Phase 1 rate fallback; longer replay and subgroup calibration are
  Phase 2 rather than blockers to the coherent baseline.
- Official no-debut evidence now supplies a zero opening service balance only when a
  FanGraphs opening balance is absent. A first debut during the current season also
  proves a zero opening balance; this safely adds Felix Reyes. Earlier debuts without
  a verified balance still fail closed. The six-year future-control path now covers
  8,343 players; unresolved service cases remain null rather than becoming free agents.
- Whole-player expected WAR now joins all 50,058 future-control rows, adding hitter
  and pitcher value for two-way players. Accepted payroll terms supply 610 known
  player-year salaries. The 4,938 projection rows without resolved control stay in the
  talent universe but do not receive invented incumbent rights. All 86 potential
  payroll buyouts map to stable player IDs. With the small dated Spotrac exception
  overlay, 97 projected option rows carry a buyout and 56 remain missing. The ten
  projected Super Two cases now advance
  through all four arbitration classes. Arbitration pay, post-2026 minimums and the
  remaining option exceptions stay explicit rather than becoming hidden defaults.
- The public 2020–2026 FanGraphs tracker supplies 335 reported contracts and all 350
  sampled rows map to MLBAM through the pinned Chadwick register. An independent 143-
  deal one-year reconstruction uses only prior StatsAPI history. On 18 clean 2026
  deals it projects 27.05 WAR versus FanGraphs' 25.40, but the one-year sample does not
  identify the multi-year star premium. The published $6.74M/$8.51M/$12.84M tiers
  therefore remain the main 2026 market reference.
- Arbitration cost now uses the externally tested FanGraphs 15%/35%/50%/75% class
  shares and prior-season projected WAR value. There are 23,291 true prior-season
  basis rows and 393 labeled first-horizon proxies. A complete research scenario now
  calculates 49,999 of 50,058 future annual rows; 59 rows remain in review for option
  buyouts, vesting triggers or one missing salary.
  Three linked Julio Rodriguez structure rows are machine-enforced reviews, so a
  later dollar-term fill cannot silently value the wrong option type.
  Official MLB reporting corrects Tatsuya Imai's 2027–2028 states to player opt-outs;
  a current official report confirms FanGraphs' Pivetta club-option conversion.
  All 13 vesting rows now have sourced, machine-readable triggers. The live evaluator
  reuses retained official StatsAPI totals and the official schedule calendar. As of
  2026-09-08, Yandy Diaz's 500-PA trigger is vested (620 PA), Chapman's 120-out
  threshold is met but its physical is pending (146 outs), and Freeland remains
  pending at 373 of 510 outs. Medical and alternate conditions remain explicit.
  Yandy's final result now changes his 2027 state to a guaranteed $13M season before
  economics are calculated; pending triggers do not alter their contract states.
  The exact-input result is 49,999 of 50,058 rows. A separate named Phase 1
  buyout estimate uses observed option-type median shares for 43 rows with no reported
  buyout. Official MLB reporting also corrects Kyle Tucker's 2028–2029 states to
  player opt-outs, raising the research scenario to 50,210 available rows and leaving
  16 reviews across 11 players. Estimated rows are labeled and do not become source facts.
  Twenty-nine fully specified mutual options now use the conservative normal-expiration
  outcome instead of waiting for a separate decision model.
  The post-2026 minimum and unchanged service rules are explicitly a planning scenario,
  not a claimed successor CBA.
- All 55,164 future whole-player seasons now have a Phase 1 uncertainty reference
  range based on historical positive-workload variance plus event and posterior-rate
  variance. All 50,058 future economics rows receive the bounds. The median annual
  width is 0.51 WAR, and opportunity accounts for 56.2% of modeled variance. The
  range is not yet an out-of-time coverage guarantee or correlated career simulation.
- The frozen Player Value v1 baserunning models now supply current hitter rates from
  official 2023–2026 steal counts and four league-wide Savant advancement files. In
  2027, 3,776 of 3,940 hitters have recent evidence; the three-year model then fades
  to its centered neutral fallback by 2030.
- Frozen U1 general-range defense now covers 1,519 hitters for 2027 using 13,192
  official current fielding rows, prior MLB position outs and the frozen native run
  conversion. Expected defense is position-centered to zero. Unsupported hitters,
  catcher-specific components and 2028–2032 remain explicit neutral fallbacks.
- A modern pitcher-aging challenger was fit on regressed same-pitcher adjacent MLB
  profiles and tested on 2,442 later-period pairs covering 618,983 BF. It lost to both
  no aging and Tango overall; Tango beat no aging in three of four seasons and remains
  the Phase 1 curve. The failed challenger is closed rather than tuned after inspection.
- A dated 2026 rest-of-season baseline projects 114.35 WAR before current availability
  and 105.10 after 247 official season-out statuses plus the narrow historical
  injury-return adjustment over the final 250
  scheduled games. CBA championship-season-day proration produces $535.96 million of
  remaining base salary. Exact current-team matches connect 844 salary rows and
  $508.08 million to the remaining-rights interface; 70 unresolved or conflicting
  rows remain explicit rather than being forced into value. The combined economics
  input contains these 840 current rows plus 50,058 future rows.
- The combined current-and-future economics run now values all 50,898 annual rows in
  one path. It produces complete discounted point and sensitivity totals for 8,332
  players, while the same 16 known contract rows keep 11 players in review. Current
  partial-season WAR uses FanGraphs' published overall 2026 rate rather than an invalid
  full-season player tier. The result remains a research scenario because post-2026 CBA
  rules, opportunity recovery and interval calibration are not final.
- Ordinary IL and rehab status does not itself supply a return date. Official current
  status and transaction replay agree for 263 players; 261 projected players receive
  the 2022-2025 activation-timing factor. Their 10.92 unadjusted WAR becomes 1.84 WAR.
  Unmatched injuries retain their point and zero-to-baseline range. Among matched
  current rights, the combined 80.08 WAR point has an availability-only 78.37 to
  87.72 range. Minor assignment is not used as team-depth blocking.
- A 30-day official workload challenger now redistributes the existing late-season
  league total without adding PA/BF or using team depth. It improved 2025 confirmation
  MAE from 14.76 to 12.01 PA and 16.08 to 13.49 BF. The live build keeps 21,596.6 PA
  and 20,597.7 BF unchanged while moving work toward recently used players.
- The Phase 1 sequential-replay contract and engine are now implemented. The first
  current checkpoint retains all 8,393 rights-universe players, provides 8,369 usable
  records and keeps 24 review players visible. The usable set contains 8,332 controlled
  values plus 37 talent-only rows with zero incumbent trade rights. It validates event cutoffs, true-vintage labels,
  universe/owner coverage, value bounds and material-change reasons. This proves the
  present integration interface; it is not yet a historical accuracy result.

Contracts and results: [rights universe](player-rights-universe-contract.md),
[full-roster source decision](affiliated-full-roster-source-result.md),
[transaction ledger](rights-transaction-ledger-contract.md),
[current organization resolution](current-organization-resolution-2026-09-09.md),
[career panel](career-outcome-panel-contract.md),
[career inventory](career-mlb-outcome-inventory-result.md),
[pitcher baseline](pitcher-component-baseline-result.md).

## Completed research

- Recovered the original 2024 opportunity forecast and verified exact IDs and
  official targets against O2026D. Its lower errors support reuse of the older
  model, with documented subgroup limits. [Comparison](recovered-opportunity-comparison.md).

- Tango-focused review executed: saved translation forecasts still improve
  common-MLB-centered absolute error; historical-support subgroups remain
  descriptive and selection risk remains. The old richer opportunity model has
  promising recorded results and should be recovered for an identical-target
  comparison. [Evidence and next work](tango-focused-model-work.md).

- C2026A: two all-level output-calibration candidates failed.
  [Result](hitter-v2-C2026A-result.md).
- T2026B: one competition-normalized history candidate failed its prospective
  all-level gate. Its presaved MLB-conditional component materially improves
  prediction for prior-minor players but still needs calibration and confirmation.
  [Result](hitter-v2-T2026B-result.md).
- C2026C: two MLB-specific calibration candidates failed. The error audit shows
  much larger optimism among brief MLB call-ups than among players with 100+ PA.
  Future exposure is a diagnostic label, never a preseason predictor or exclusion
  rule. [Result and next step](hitter-v2-C2026C-result.md).

## Next modeling task

The main denominator, control/cost path, integrated current-plus-future economics
engine, projection
guardrails, opportunity paths, conditional-WAR assembly, annual economics-input join,
current baserunning, supported general defense, the rest-of-season path, a narrow
official-status availability boundary and Phase 1 future WAR ranges are now built.
The one-year confirmation forecast and scoring rule are frozen. Do not inspect partial
2026 targets or tune the completed gates; run confirmation only after official regular-
season totals are final. Horizons 5–6 remain on the incumbent until better older
evidence exists. The Phase 1 coherent research path is complete under its declared
boundaries: the 2025 projection, control, value and reference-range paths run together,
outcome scoring is recorded and the multi-checkpoint sequence passes. The same-model
later projection checkpoint now exists:
the exact pre-2025 opportunity fits are committed and hash-verified, and the October
15 update uses completed 2025 evidence without refitting. The matching October
owner/control/economics join and same-method value comparison now pass. They resolve
8,079 owners, produce 7,749 usable values and explain all 4,049 material value moves.
Do not treat this descriptive update as an outcome-accuracy score or authorization to
publish player rankings. The next hard evidence gates are the protected 2026 score
after the regular season and the successor CBA. Remaining service, Super Two and option
exceptions should be resolved only when their value impact warrants it; granular
calibration and component improvements belong in Phase 2.
The 948 missing-owner players and bounded contract/service exceptions stay separate
rather than forced. In the current snapshot, 16
annual contract reviews remain: 12 future vesting
decisions, three linked Julio Rodriguez years and one missing option salary. Granular replacement of the
43 buyout estimates with exact terms is Phase 2. Current role and late-season injury return
now have narrow Phase 1 baselines. Correlated
multi-year uncertainty and empirical coverage refinement belong in Phase 2.
Modern adjacent-season pitcher aging has been tested and rejected for Phase 1; revisit
it only under a new Phase 2 test.
The market-price and Phase 1 arbitration gates are complete. The remaining economic
blockers are successor-CBA facts and the 16 remaining scenario review rows.
The 21 multi-organization ownership cases are closed by the dated 40-man/transaction
resolver. Continue only the bounded contract/CBA exceptions. Do not
publish dollar rankings from placeholder market or arbitration assumptions.

The lost B2 package has now been replaced for forward development by a reproducible
universal v2 candidate. Its current scoring and provisional downstream integration are
complete. Retain O2026D as a simple benchmark and T2026B as a developmental hitter-rate
reference. Stop global hitter calibration searches until the protected confirmation.

The selected B2 hitter-opportunity run is still identified by run `32142220469` and
its expected candidate hash, but GitHub's short-lived coefficient artifact has expired.
The surviving independent 2025 confirmation artifact has now been preserved in
`model_artifacts/playing-time-v1-confirmation-2025/`, with a hash manifest and tests.
It contains scores, not coefficients, and the local archive contains only a different
2024 fold fit. The old run log also contains no coefficient values. Do not silently
refit under changed inputs. Recover the exact frozen package if an external copy exists;
otherwise keep the current proven fallback and rerun a newly versioned selection gate.
All future selected parameter packages must follow
`docs/playing-time-v1-durable-artifact-policy.md`.

The 2022–2024 seasons are disclosed development evidence. Protected 2026 remains
closed. Do not claim long-term value or publish a model from these findings.
Preserve original G0/C0/Marcel benchmarks and all failed decisions.

## Reproduction

New model primitives have chronology, gradient, probability-conservation, and
player-cluster resampling tests. The runners require existing generated research
artifacts; hashes bind the inputs. They reject overwriting an inspected candidate
run. The local implementation passed its tests before this branch was prepared;
branch-specific verification is recorded in the pull request.

Current focused verification: opportunity, economics, guardrail, remaining-rights and
current-availability tests pass; Ruff passes across the changed files. The latest full
run has 1,358 passing tests. Four pre-existing hitter research-contract tests fail only
because their hash-bound ignored research artifacts are absent in this checkout. No new
test failure was observed.

The prior long status file is preserved in
[project history through August 26](project-history-through-2026-08-26.md).
