# The new position model spreads players too broadly

2026-10-07. Keep the certified position sources and the existing defensive
quality baselines, but do not replace individual position assignments with this
candidate. Its combined-value error improves only 0.1%, with uncertainty spanning
no improvement. Defensive-run error worsens. Player reviews show why the small
combined gain is not persuasive: the model dilutes established roles and sometimes
receives credit when a positional mistake offsets a batting mistake.

## What this comparison changes

The candidate learns next-season MLB position shares from current use at every
observed level, late-season use, two previous annual records and older position
experience. These inputs replace the previous primary-position group average.
The current sources are certified separately; tiny promotion stints do not erase
the larger minor record. All 12,432 forecasts at the 2022–2024 cutoffs remain.
The same batting forecasts, expected PA, twelve defensive-quality recipes,
individual job totals, league capacities and unknown-player reserves are held
fixed. Targets end in 2025; no new 2026 outcome access occurred.

This tests assignment and delivered contribution, not whether minor fielding
statistics identify defensive talent. The combined target is fixed batting plus
positional and native defensive runs divided by ten. It is not published full
WAR or trade value. Of 12,432 forecasts, 12,114 have complete combined targets;
318 with partial native measurements remain in the ledger without invented
complete defensive outcomes.

## Scores and their meaning

These are averages of the three origin-specific RMSEs, with equal weight per
origin. Smaller is better. The benchmark is the previous constrained joint-role
assignment, not neutral defense.

| Measure | Benchmark | Candidate | Meaning |
| --- | ---: | ---: | --- |
| Combined custom value in wins | 0.433346 | 0.432927 | 0.10% better, uncertain |
| Delivered native defense in runs | 1.561132 | 1.575061 | 0.89% worse |
| Positional adjustment in runs | 0.965248 | 0.958779 | 0.67% better, uncertain |
| Conditional position share | 0.173633 | 0.169357 | 2.46% lower point error among actual job holders |

The paired person-cluster 95% interval for combined error change is −0.002531
to +0.001717 wins. For defensive-run error it is +0.003541 to +0.024062 runs.
These are nominal development intervals, not protection against repeated model
selection or shared season shocks. Combined mean absolute error worsens slightly,
0.120662 to 0.120783. Against the separate own-repertoire reference, combined
error also changes very little and positional error is slightly worse.

The share score improves at all three origins, but total role-cell exposure error
worsens at each: 161.59 to 161.72, 156.50 to 158.98, and 162.51 to 165.03
outs-equivalent. Those cells use fielding outs and the declared origin DH job
conversion. Thus better proportions among survivors do not establish better
individual workloads or delivered defense. The single actual-job row with zero
predicted mass remains in both relevant arms, rather than being dropped.

Combined error is worse at the 2022 and 2024 cutoffs and better at 2023. Defensive
error is worse at all three. No origin crosses the predeclared 5% component
deterioration warning, but that numerical tolerance does not certify baseball
reasonability. The young current-MLB group worsens in combined value at 2022 and
2024; upper-minors gains are confined to 2024. Lower-minors next-year measured
defenders number only 10, 5 and 3. Tiny lower-minors delivered errors are not
evidence that their defensive talent is known.

## Players expose the mechanisms

The review preserves nineteen earlier focal cases and all 57 original peers,
then adds the largest combined gain/harm, native-defense gain/harm and an ordinary
defender where these were not already represented. It covers 23 focal cases and
92 calculation traces. Peers use origin-known stage, position, age and exposure,
not future success. Outcome-selected extremes diagnose errors, not independently
confirm performance.

- **Witt after 2024:** his current record is 4,181 shortstop outs and one DH
  start. The candidate assigns only 76.2% of pre-cap job share to SS, with 10.0%
  to 3B and 6.6% to 2B. Predicted SS outs fall from 3,528 to 3,115; actual next-year
  SS outs are 4,020. His old third-base record pulls against his established
  current assignment. Volpe, Henderson and De La Cruz show related leakage;
  this is not only a surprising Witt outcome.
- **Eldridge after 2024:** all current fielding is at 1B, plus DH starts; RF
  evidence is from 2023. The candidate still allocates 28.5% to RF and 9.9% to LF
  before caps. First-base outs fall from 231.5 to 138.4 and RF rises from 22.1 to
  116.5. His later MLB use is 102 outs at 1B and six DH starts, with no OF. All
  twelve quality channels remain unmeasured neutral fallbacks, not evidence of
  average talent. His exact joint profile has zero training people; the broader
  upper-minors/1B group has 28, so it permits this qualified learned allocation
  instead of the unseen-group fallback. Restored source completeness does not
  make the resulting extrapolation sensible.
- **Rafaela after 2024:** current SS and CF use both matter. The candidate moves
  toward his older CF role: CF outs rise from 1,720 to 2,700 while SS falls from
  1,295 to 264. Actual next-year use is 3,502 CF outs and 495 at 2B, with no SS.
  Delivered defense moves from +0.37 to +2.59 runs versus +21.67 actual. This is
  a useful direction, although quality remains substantially underestimated.
  It does not justify dispersing established center fielders into corner roles.
- **Rice after 2024, largest combined gain:** the substantial minor catching
  record is real, alongside current first-base use. The learned catching share
  is 70.8%; candidate catcher outs rise from 2.6 to 1,018.8, versus 689 actual.
  Positional runs move from −4.17 to +1.52, but actual is −6.39. The combined
  forecast improves from +0.31 to +0.83 wins against +2.81 actual because the
  excess catcher credit offsets low fixed batting/workload. His positional
  estimate becomes less accurate. That is not a clean defense/value success.
- **Ohtani after 2024:** current evidence is 159 DH starts and no fielding.
  The candidate nevertheless increases fielding exposure relative to the
  constrained benchmark. A finite softmax assigns small positive probabilities
  outside the DH role; reconciliation redistributes job mass without adding new
  edges. Actual next-year fielding is zero. Less-negative positional credit
  nudges an underpredicted combined value upward, but worsens positional error.
- **Bellinger after 2024, largest combined harm:** current use includes CF, RF,
  1B and DH. The candidate raises first-base outs from 617 to 1,242 and reduces
  CF from 1,652 to 370; actual use includes 80 first-base outs and substantial
  LF/CF/RF. Combined value falls 1.56 to 1.19 against 4.42 actual. Older
  first-base/minor-role indicators have too much influence on this allocation.
- **Schwarber:** after 2023, the move toward DH helps and is consistent with
  later use. After 2022, however, the same model forecasts only 520 LF outs
  against 2,617 actual, badly understating negative delivered defense. The model
  cannot receive blanket credit for forecasting DH merely because the direction
  was right a year later. Known upcoming assignment plans are still omitted.
- **Brian Anderson after 2022, ordinary final error:** candidate combined
  value nearly matches reality, +0.478 versus +0.479. It nevertheless shifts
  exposure away from his actual 3B/RF combination toward LF/DH and worsens
  positional error. A correct sum is not proof of correct components.

The full traces also retain Bailey/Raleigh/Kirk catching, Carter's promotion
profile, Chourio's tiny AAA RF stint, Buxton's restored CF, utility players,
Judge's false low, Acuña's false high and non-arrivals. Later injuries, role plans
or absence outcomes do not become model inputs retrospectively.

## Cohort checks support the player concerns

An additional diagnostic selects current MLB players with at least 200 origin
evidence PA, independently certified field/DH measurements, and at least 90% of
current starts-equivalent at one position. It contains 160, 180 and 206 origin
rows; 140, 161 and 189 have actual next-year jobs. On those matched job holders:

| Cutoff | Benchmark share at current position | Candidate | Actual |
| --- | ---: | ---: | ---: |
| 2022 | 89.9% | 79.1% | 86.2% |
| 2023 | 88.8% | 79.5% | 87.6% |
| 2024 | 88.6% | 78.9% | 83.9% |

The unconstrained seed already has this diffusion; capacity adjustment is not
its sole cause. Candidate share outside the observed full repertoire averages
4.0%, 3.5%, 2.6%, versus actual 2.2%, 0.9%, 1.2%. These are empirical warnings,
not physical bans on position switches. Historical coverage is left-truncated;
unobserved does not always mean unplayed.

Of 4,704 complete-target forecasts with improved combined squared error, 2,109
have worse positional error, 407 worse defensive error, and 202 have both worse.
These descriptive flags are not a significance test or proof every gain is
invalid. They explain why combined error alone is an inadequate component gate.

At the 2023 cutoff both constrained arms have virtually identical league role
totals because the fixed mass nearly fills the same caps. Different individual
allocations still produce different defense errors. In 2022 the candidate
underallocates SS/CF while filling other caps; in 2024 CF remains underallocated.
Combined measured totals change 493.52 to 479.84 versus 490.77 actual, 514.37 to
512.93 versus 458.24, and 476.41 to 472.58 versus 476.58. Totals are mixed and
not forced to a WAR quota. Partial targets are not filled to manufacture balance.

## What remains useful and what comes next

Retain the independently certified current/late/older source representation,
explicit missing flags and audited capacity/mass calculations. Do not promote
this individual assignment recipe or call it a new talent model. There are
11,364 sparse joint profiles among 12,432 forecasts, including 1,620 unseen
stage/current-role profiles that use own-role fallback. Those warnings remain
in the predictions. The fifteen fits converge and reproduce; that establishes
execution, not adequate training support or deployment approval.

Keep the tested MLB range, framing, throwing, blocking, arm and receiving history
baselines from their separate talent reviews. The broader defense goal remains
open. Next audit the already saved older minor fielding counts for a properly
supported later-MLB talent comparison: preserve levels and individual exposure,
pool future position-specific native quality over mature fixed windows, and
show distinct held-person support before fitting. The position-usage parquet
contains innings/starts, not putouts/errors/assists; recover actual count fields
from certified raw captures rather than pretend usage measures skill. Reconcile
this with the old traditional-stat screen, whose one-year same-position survivor
target did not establish long-run lower-minors talent. Do not reopen the closed
adjusted ground-ball-share test or run another role-weight tournament.

Frozen forecasts, explorer and 2026 selection are unchanged. Lovich's separate
batting reliability defect remains open. Evidence: [scores](../reports/model-evidence/defense-assignments-v17/report.json),
[all player traces](../reports/model-evidence/defense-assignments-v17/player-walkthrough.json),
[cohort diagnosis](../reports/model-evidence/defense-assignments-v17/diagnostic-review.json)
and [final disposition](../reports/model-evidence/defense-assignments-v17/final-review.json).
