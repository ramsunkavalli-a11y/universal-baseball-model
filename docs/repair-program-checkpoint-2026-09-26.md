# Repair-program checkpoint: what actually changed

The first three milestones of the [repair program](methodology-repair-program-2026-09-25.md)
now have evidence-backed dispositions. That is completion of a bounded repair/
diagnostic goal, NOT completion of the baseball model or certification of all
defensive skill. The program explicitly allows an unsupported source gate to
end with a bounded blocker instead of another learner.

## Changes and decisions

| Priority | What was done | Decision |
|---|---|---|
| Catcher measurement | Replaced terminal-PA event detection with full-event accounting; reconstructed event-time battery; tested a separately selected 128-game sample with frozen code. | Counts are credible on the sample. Battery is certified for 127/128 games and 662/673 events, with the remaining game explicitly quarantined. Reopen old negative claims; no catcher skill refit until exposure denominators pass. |
| Infield measurement | Built a 2,026,088-ball ledger, retained hits that pass infielders and unknowns, and separated first touch from assumed responsibility. Checked 5,742 same-game official GB keys. | Archive ball accounting passes. Individual range does not: hitter direction/interception difficulty and responsibility remain uncertain. Preserve the candidate and explicit blocker; do not say defense failed. |
| Playing time | Replayed the existing conditional-workload model and changed only its training weights; retained non-arrivers and 2021; tested Years 1–3 and totals. | Small cumulative improvement, but worse Year 1/conditional errors and worse 2022 totals. Keep the reference rather than tune a new blend after seeing results. |
| Batting/value connection | Compared all eight already specified combinations on identical archived predictions, without fitting new models. Separated own-component errors from other-component error interactions. | Inherited baseline accounting caused most of the earlier loss. Primary playing-time transfer was tied. Do not promote the minimum-error secondary combination as independently validated. |

## Why the earlier conclusions needed correction

**Catcher:** a steal can happen before the batter finishes. Reading only the
final batter description lost successful steals much more often than caught
stealings. In the first sample it found at most 18 of 268 SB versus 30 of 90
ordinary CS. That is not a fair sample for testing throwing or deterrence.

**Infield:** a grounder passing the shortstop and retrieved in LF was counted
as an OF touch, not an infield range opportunity. The new ledger retains it.
Assigning that ball to SS versus 3B is still an assumption; conservation alone
cannot settle that. The benchmark now also distinguishes singles from extra-
base hits rather than spreading both identically.

**Playing time:** consistent training weights are statistically motivated but
do not guarantee better forecasts. Three-year prospect PA RMSE moves from
121.67 to 120.85, but Year 1 worsens and 2022 prospect PA rises from 98,994 to
108,015 against 97,303 actual. A small average improvement is not enough to
declare the new weighting generally better. The 2021 shortfall persists.

**Batting:** at fixed workload/rate, removing an inherited baseline-value
residual improves three-year batting-value RMSE from 1.21044 to 1.12944.
The residual hurts in all three complete origins. Separately, changing only
playing time in the primary anchor/product comparison is essentially tied:
1.13984 versus 1.13999. Those are two different conclusions, not a claim that
the playing-time system created the large batting improvement.

**Outfield:** the proposed MiLB replacement affected only 1,525 of 3,929 players.
On the changed players, its own-component and total errors worsened. Better
whole-arm results versus neutral came from retained predictions, not evidence
that this replacement worked. That rejection remains; it is not reopened just
because other defensive measurements had flaws.

## What remains genuinely unresolved

1. Catcher pitch/runner-at-risk exposure, then population-wide historical
   reconstruction with failure coverage by level/year. The timeline sample is
   not certification of every historical game. A delayed LF change presently
   fails one complete game; do not silently retime it or call missing events zero.
2. A defensible coarse individual-range proxy or better comparable ball evidence.
   Specify sensitivity to assignment, park/level movers and roster turnover
   before any predictive refit. Exact tracking is not mandatory, but predicting
   another biased first-touch label would not answer the talent question.
3. A separately locked release/transport check for the explicit batting connector,
   with the validated reference, existing component units and subgroup totals
   unchanged. The factorial itself is finished; do not refit it until it wins.
4. Later joint career/control/cost validation. Six calendar years still are not
   six years of team control, and dollar/trade rankings remain unsupported.

The next best source task is item 1, not another broad engine comparison. The
next best integration task is item 3, with a fresh contract that clearly marks
all exposed historical results as development evidence. Neither uses protected
2026 outcomes or changes the frozen forecast by implication.

## Reproduction and verification

- [Catcher event source result](defensive-event-source-repair-v1-result.md)
- [Frozen timeline validation](defensive-timeline-v1-result.md)
- [Full ground-ball ledger and bounded range blocker](ground-ball-ledger-v2-result.md)
- [Single workload-weight comparison](hitter-workload-common-weight-v1-result.md)
- [Fixed batting factorial and error attribution](hitter-batting-factorial-v1-result.md)

This checkpoint: 59 focused regression tests pass, including 15 new timeline/
ledger tests. Both independent repair verifiers pass. The original 31-file,
3,907-player forecast freeze and the 43-fit/188,080-row arrival-coherence delivery
remain verified unchanged. No protected 2026 performance was used. Full raw
feeds/yearly ledgers are local ignored data; tracked manifests, code and reports
record inputs, hashes, comparisons and limitations. No improvement claim depends
on silently dropping 2021, failed games, non-arrivers or unknown outcomes.
