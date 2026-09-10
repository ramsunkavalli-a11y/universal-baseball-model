# Current cycle stopping point — updated 2026-09-10

Status: clean handoff; private preview works, publication remains blocked.

## September 10 continuation

- The playable prospect-arrival model now distinguishes highest level touched from
  workload-weighted primary level. The combined exposure model beat the old core on
  both pooled proper scores without losing either score in any required time-ordered
  fold for hitter and pitcher arrival and meaningful-role outcomes. See
  `docs/prospect-primary-level-exposure-result.md`.
- A primary-level-only replacement was rejected because it made aggregate historical
  accuracy worse. Highest level remains evidence; it no longer stands alone.
- Advancement, stagnation, inactivity gap, and accumulated affiliated history were
  tested together. They improve only pitcher established-role probability under the
  fixed gate; the other five outcome models remain simpler. See
  `docs/prospect-development-path-result.md`.
- A predeclared declining-hazard/exit-risk test selected the existing constant hazard
  for all six hitter/pitcher outcomes on 2019 and did not lose on the completed 2021
  four-year check. Do not add an arbitrary long-horizon decay. The third two-year
  window remains an explicit extrapolation; see
  `docs/prospect-declining-hazard-result.md`.
- Official 2021-2025 home/road results showed a repeatable minor-league park signal,
  but the runs-only test used scheduled rather than actual innings. Treat it as
  superseded preliminary evidence, not an approved source or player adjustment.
- Exact home/away component splits then passed a team/venue persistence test, but
  failed the future MLB-player gate. Hitters lost 2025 log loss; pitchers lost 2025
  Brier. Keep the level-only player translation and do not rescue-tune this result.
- Controlling actual home/road opponent mix does not rescue the player gate; the same
  hitter log-loss and pitcher Brier reversals remain. Park work is closed on these
  seasons until exact matchup exposure, venue-era evidence, or a new season exists.
- The first coherent prospect-state challenger predicts four exclusive next-season
  states. It fails for hitters and is mixed for pitchers, so the direct cap remains.
  Its main design lesson is to retain ordered hazards and condition later transitions
  on the state already reached rather than fit one flat multinomial shortcut.
- A real four-year forward-only transition table is now built: 39,352 hitter and
  44,208 pitcher annual rows. The ordered path wins both scores for both groups on
  the later 2021 cohort but loses both on the 2019 cohort whose horizon crosses 2020.
  Keep the architecture in research and the current direct safeguard in production.
- Pooling post-arrival progression down to age and elapsed time leaves the same
  cohort reversal. This closes further transition-complexity tuning on the disclosed
  paths; current values remain unchanged.

- The repo plan now includes lessons from comparable GitHub projection systems:
  component-specific reliability must earn its complexity, attrition belongs in the
  score, and downstream WAR matters more than an isolated component gain.
- The complete next-season denominator is implemented and tested. It retains 5,018
  observed non-returners instead of silently removing them from aging evaluation.
- Component-specific pitcher shrinkage failed 2025 stability; keep 800 BF.
- Component-specific hitter shrinkage improved point scores but missed the fixed
  uncertainty gate; keep 1,200 PA.
- Tango pitcher aging beat no aging in the frozen 2025 joint replay. Retain it.
- The generic Marcel hitter age adjustment lost to no aging in the same type of replay.
  No current value changed; no aging is the frozen 2026 challenger.
- Both 2026 aging comparisons are stored as immutable, hash-checked forecasts. Do not
  open partial 2026 results or alter their gates.

Next: after the completed regular season, run the already frozen opportunity and aging
confirmations. Before then, useful model work requires broader historical affiliated
data or a genuinely new cutoff-safe process source; do not mine more 2024–2025
shrinkage combinations.

## What is now in place

- One playable local explorer for 8,393 rights-universe players, guarded by 46 model
  identity checks.
- A nested pre-MLB career model: arrival, meaningful given arrival, and established
  given meaningful. Probabilities are ordered by construction.
- Workload-only prospect P10/P50/P90 outcomes for all 6,719 pre-MLB paths. Their means
  exactly match current point WAR and do not alter value.
- Clear player detail for skill rate, expected workload, batting/running/defense/
  position components, pitcher RAA, and the source-limited workload range.
- Current contract/control economics using the downloaded FanGraphs depth-chart and
  payroll workbooks as private reference inputs, with bounded reviews left explicit.
- A separate dependent career simulation for all 6,719 pre-MLB players. It keeps
  arrival, whole career workload, skill uncertainty, annual noise, control, cost and
  value in the same path and appears only as a research comparison in player detail.

## Accepted or retained

- Hitter conditional workload distribution is usable as a labeled empirical reference;
  it is not historically confirmed.
- The translated hitter and pitcher component baselines remain.
- Hitter component regression remains 1,200 PA: a 400-PA challenger improved point
  scores but missed the predeclared bootstrap gate.
- Pitcher role probabilities remain; broad suppression and hard role caps were not
  supported.
- The private pitcher age/hand adjustment was provisional at this stopping point. It
  was removed on September 10 after the full funnel audit exposed its disproportionate
  current top-end effect relative to its weak validation.

## Rejected or blocked

- No catcher preference, position quota, manual prospect floor, or outside player FV.
- Hitter age-for-level and batting-side component bonuses reversed on 2025.
- Separate/pooled pitcher extra-base-hit components worsened proper scores.
- Simple pitcher workload recency weighting and always pooling roles did not jointly
  improve accuracy and coverage.
- Component-plus-workload prospect ranges are research-only, not calibrated intervals.
- Birth country and its age/hand combinations failed five-fold pitcher development
  scoring. Current height/weight cannot be used in historical tests without dated
  measurements.
- Platoon is source-ready but waits for the certified sidecar to be rematerialized.
  Lineup slot and universal times-through-order are not yet certified.

## Main finding to carry forward

Pitcher projection remains the most important modeling issue, but the valid as-of
conditional workload replay passed: its nominal 80% range covered 81.1%. The deeper
problem is top-end pitcher production before value mapping. The old pre-MLB top 100
already had 99 hitters and one pitcher, so the dependent simulator did not cause the
imbalance. Earlier tests retained role probabilities and 800-BF regression and
rejected simple recency weighting, role pooling and birth-country adjustments.

The next performance challenger should add genuinely new, chronology-safe process or
pitch-quality evidence. Minor-league Statcast is allowed only as a coverage-limited
tier. Its accepted materialization artifact and required upstream workflow artifacts
have expired, so the source chain must be rebuilt first. Never raise workload, change
FV cutoffs or add a manual pitcher bonus to create a familiar ranking.

## Verification and known limitation

Latest full suite: 1,520 passed. Four older research-contract tests fail because their
hash-bound generated artifacts are intentionally absent from this checkout; no new
failure is present. The private build passes all 46 structural, statistical and accounting model-law checks.

Contract-review display is improved without weakening that gate. The eleven players
with unresolved future option rows now show a labeled subtotal from calculated years
and the exact unresolved reasons; they remain unranked. Gary Sanchez's 2027 mutual-
option salary remains undisclosed across the official Brewers announcement, FanGraphs
(`TBD`) and Spotrac, so it is not estimated.

The other twelve reviews are now labeled as missing opening service balances rather
than generic contract failures. All are off the 40-man roster; the largest projects
0.302 six-year WAR and a $2.02M separate talent benchmark. Leave them unranked until a
dated service source exists or their roster/value materiality changes.

The September 10 official-debut correction is also active: 104 hitter and 154 pitcher
historical cohort records were removed, the arrival model was refit without retuning,
and the downstream value/explorer lineage is hash-checked.

Protected partial-2026 outcomes remain closed. The next clean statistical stopping
gate is a frozen pitcher environment/role candidate or a later complete historical
cohort—not more tuning against the already inspected cohort-stability comparison.

The frozen development-state test is now complete. Development-history facts do not
improve hitters. A joint pitcher version wins both later proper-score comparisons with
favorable paired intervals, but misses the earlier development Brier requirement. It
is retained only as an unchanged future-confirmation candidate; current values did not
move.

The follow-up post-arrival test provides the next build direction. Prior-season MLB
workload improves fringe-to-higher progression for both player types across selection
and both later years, with all later paired intervals below zero. The signal is not
precise enough for meaningful-to-established progression. Next, carry simulated annual
workload into the following fringe-state transition while retaining the pooled upper-
state fallback; do not change current values until that complete path is validated.

The next pitcher-role increment was also closed cleanly. Prior games, starts, start
share and batters faced per game do not consistently improve career-state advancement
after total workload is known. Do not add a role bonus to advancement; preserve role
only in the separate workload and WAR-rate paths.

One validation rule was corrected before further linked-path work. MAE targets a
median and therefore favors zero in the mostly-zero prospect cohort; it cannot veto
an expected-WAR/value forecast. The old pitcher path remains unpromoted because its
paired MSE interval crossed zero and it lacks both a proper full-distribution score and
fresh confirmation. The next replay must score the exact zero mass and positive path
together with CRPS, plus arrival probability and expected-WAR gates.

That first full-distribution score is complete for the exposed 2021 pitcher replay.
The linked zero-plus-path mixture scores 0.1035 CRPS and reliably beats always zero at
0.1134. The equal uncertainty comparison is now complete: the incumbent scores 0.1048
after tiered workload, event variance and posterior-rate variance, versus 0.1035 linked.
The linked-minus-incumbent interval crosses zero. Stop tuning this exposed cohort;
retain the challenger without changing values and wait for genuinely new evidence plus
fresh confirmation.

The protected 2026 aging gates were also repaired before outcomes. Hitter and pitcher
forecast parquets are unchanged; their reports now bind amended contracts that use
paired squared error for expected WAR instead of median-targeting MAE. Component log
loss, aggregate bias and supported age-band safeguards remain frozen.

The protected 2026 opportunity gate now follows the same rule without changing any
forecast row: full hurdle-count likelihood remains primary, and expected PA/BF is
guarded by mean squared error plus aggregate bias. MAE remains descriptive only.
The forecast package and future evaluator now verify the amended contract hash.
