# Project status and handoff

Updated 2026-09-09. This is the current start-here document.

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
- The refreshed 2026-09-08 league build contains 8,393 affiliated players and 50,226
  future-path rows for 8,371 players through 2032. All 21 multi-organization cases are
  resolved: 15 by unique official 40-man membership and six by exact transactions.
  Its complete 133-player Super Two
  pool has a calculated cutoff of
  `2.144` (488 days), with 30 selected because the cutoff is tied. FanGraphs supplies
  the 2026 opening balance; StatsAPI supplies in-season service through the as-of date.
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
  zero-MLB outcomes, uses the frozen selected one-year model when supplied, and fills
  unsupported/later years with horizon-specific age/level cohorts and labeled
  population fallbacks. It never uses team depth or a PA cap and composes directly into
  the Projection v1 WAR schema. Historical cohorts are now fitted; the current league
  snapshot and frozen selected-model parameter artifacts remain.
- Pitcher Opportunity v1 now applies the same separation to MLB arrival, conditional
  BF and starter/swingman/reliever probabilities. Sparse age/level/role cohorts shrink
  through a disclosed hierarchy, all fallback sources remain labeled, and the output
  composes with conditional WAR/800 BF and control seasons. Its historical league panel
  is now fitted; the current league snapshot remains.
- The official historical opportunity source is now collected for 2018–2024. Because
  `fullRoster` omits hundreds of players with official affiliated stats each year, the
  cohort denominator is their union. The misleading `totalSplits` field is ignored in
  favor of verified pagination. Excluding the cancelled 2020 MiLB season leaves 74,743
  hitter and 90,727 pitcher zero-inclusive cohort rows across horizons 1–6.
- The dated 2026-09-08 snapshot now produces complete 2027–2032 baseline paths for
  3,940 hitters and 5,276 pitchers. Official position evidence reduced false two-way
  classification from 436 players to 22 by excluding incidental mop-up pitching. The
  current hitter run uses historical fallbacks because frozen richer-model parameters
  are absent; no replacement coefficients were invented.
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
  FanGraphs opening balance is absent. Debuted players still fail closed. This expands
  the six-year future-control path from 1,667 to 8,371 players; unresolved service
  cases remain null rather than becoming free agents.
- Whole-player expected WAR now joins all 50,226 future-control rows, adding hitter
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
  calculates 50,167 of 50,226 future annual rows; 59 rows remain in review for option
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
  The exact-input result is 50,167 of 50,226 rows. A separate named Phase 1
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
  variance. All 50,226 future economics rows receive the bounds. The median annual
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
  input contains these 844 current rows plus 50,226 future rows.
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

The main denominator, control/cost path, static economics engine, projection
guardrails, opportunity paths, conditional-WAR assembly, annual economics-input join,
current baserunning, supported general defense, the rest-of-season path, a narrow
official-status availability boundary and Phase 1 future WAR ranges are now built.
Next, resolve the 16 remaining contract reviews: 12 future vesting decisions, three
linked Julio Rodriguez years and one missing option salary. Granular replacement of the
41 buyout estimates with exact terms is Phase 2. Current role and late-season injury return
now have narrow Phase 1 baselines. Correlated
multi-year uncertainty and empirical coverage refinement belong in Phase 2.
Modern adjacent-season pitcher aging has been tested and rejected for Phase 1; revisit
it only under a new Phase 2 test.
The market-price and Phase 1 arbitration gates are complete. The remaining economic
blockers are successor-CBA facts and the 16 remaining scenario review rows.
The 21 multi-organization ownership cases are closed by the dated 40-man/transaction
resolver. Continue only the bounded contract/CBA exceptions. Do not
publish dollar rankings from placeholder market or arbitration assumptions.

In parallel, reconnect the recovered opportunity pipeline and its frozen B2 inputs,
then declare population-prior fallbacks for inactive/no-history players. Retain O2026D
as the simple benchmark and the unchanged T2026B MLB-conditional transport component
as a developmental hitter reference. Stop global calibration searches. Do not convert
the component outputs to career value before participation, pitcher workload, aging,
rights and cost paths are integrated.

The selected B2 hitter-opportunity run is still identified by run `32142220469` and
its expected candidate hash, but GitHub's short-lived coefficient artifact has expired.
The surviving confirmation artifact contains scores, not coefficients, and the local
archive contains only a different 2024 fold fit. Do not silently refit under changed
inputs. Recover the exact frozen package if an external copy exists; otherwise keep the
current proven fallback and rerun a newly versioned selection gate. Future selected
parameter packages must be stored in durable release storage or committed when small.

The 2022–2024 seasons are disclosed development evidence. Protected 2026 remains
closed. Do not claim long-term value or publish a model from these findings.
Preserve original G0/C0/Marcel benchmarks and all failed decisions.

## Reproduction

New model primitives have chronology, gradient, probability-conservation, and
player-cluster resampling tests. The runners require existing generated research
artifacts; hashes bind the inputs. They reject overwriting an inspected candidate
run. The local implementation passed its tests before this branch was prepared;
branch-specific verification is recorded in the pull request.

Current focused verification: opportunity, guardrail, remaining-rights and current
availability tests pass; Ruff passes across the changed files. The current full run
has 1,227 passing tests.
Four pre-existing contract tests fail only because their hash-bound ignored
research artifacts are absent in this checkout. No new test failure was observed.

The prior long status file is preserved in
[project history through August 26](project-history-through-2026-08-26.md).
