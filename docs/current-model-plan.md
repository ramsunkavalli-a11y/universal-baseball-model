# Current model plan

Updated 2026-09-10. The user wants the model made credible before further interface
work. The [product roadmap](product-roadmap.md) is now the authoritative active plan;
this document retains detailed evidence from the current hitter/opportunity workstream.
Earlier experiment contracts remain historical records.

## Goal

Build a comparable trade-value estimate for every player, updated after each game
and material transaction. The recommended common measure is expected remaining
surplus value of transferable team rights, with projected MLB wins and uncertainty
shown separately. KATOH-style prospect production is one component of that goal.

Execution now follows the roadmap's ten steps: eight Phase 1 foundations leading to a
complete universal research valuation and two Phase 2 granular-improvement steps.

Read the [repo and literature direction review](trade-value-direction-review.md).
It governs the broader sequence: player/rights coverage; reuse of existing models;
career paths and control/cost data; integrated research valuation; historical
game-by-game replay. Next-season batting refinement alone cannot deliver the goal.

## What we have learned

The active production-focused execution sequence and completed Tango-style
diagnostic are in [Tango-focused model work](tango-focused-model-work.md).
Career production is the main modeling effort. The financial/control layer must
have a clear interface, but should not displace batting/pitching development.
Recover the existing richer opportunity model before designing another challenger.

All new broad feature searches now follow the binding
[model-search and validation policy](model-search-validation-policy.md). The framework
is not limited to demographics: it covers legitimate forecast-date StatsAPI, PBP, and
derived performance, development, role, workload, process, defense, baserunning, and
context inputs. It requires time-ordering, an outcome embargo, nested selection,
regression for sparse evidence, proper scores, calibration, uncertainty, and supported
subgroup review. Skill, opportunity, workload, and contract value remain separate
until final assembly.

**Recovery completed for 2024:** original forecasts were found and hash-verified.
All 3,985 player IDs and official PA targets match O2026D. The recovered model
improves participation Brier by 12.6% and PA RMSE by 12.5%; lower-level exceptions
remain. [Verified comparison and next step](recovered-opportunity-comparison.md).
Next recover its dated feature pipeline and resolve B2-dependent inputs before
integration. O2026D remains the simple benchmark; no release promotion occurred.

- v1's batting representation is not a sound product foundation.
- G0's terminal-outcome history is useful but mixes competition levels.
- Two final-output calibration fixes failed; do not revisit their tuning.
- Competition-normalized history materially improves the MLB-conditional batting
  estimate for prior-minor players. Its all-level prospective mixture still failed.
- Remaining MLB-conditional problems include optimism, weak individual separation,
  and selection into MLB/playing time. The 29% improvement is not career-value accuracy.

## Completed batch: C2026C

Calibrate the already saved MLB-conditional estimates using ONLY earlier MLB
forecast/results pairs. Test two fixed alternatives: a probability-score calibration
and a direct batting-value calibration. Compare to the unchanged transport component,
G0, C0, and Marcel on identical players. Examine minor-origin players explicitly.
See [the exact experiment contract](hitter-v2-MLB-calibration-contract.md).

Both candidates failed: minor-origin pooled improvements were 1.18% and 1.87%,
with uncertainty intervals spanning zero and damage to established MLB players
in 2023. [Results and error audit](hitter-v2-C2026C-result.md).

The reason for testing the second alternative was substantive: fitting every
terminal event equally under log loss need not optimize the batting-value estimate.
Keep coherent probabilities and use event-score guardrails to detect harmful tradeoffs.

## Next sequence

**Current P0:** use the corrected playable-build chain
`current-opportunity-paths-v2 -> phase2-workload-paths ->
phase2-conditional-war-paths -> phase2-war-uncertainty/model-fv -> current value`.
The prior explorer silently joined the older generic opportunity paths. That defect
reduced projected six-year WAR for 940 debuted pitchers from 1,325.5 to 1,108.1.
The corrected materializer records both input hashes and the opportunity model ID;
the explorer refuses to open a stale or changed source. See the
[pitcher funnel audit](pitcher-value-funnel-audit-result.md).

The correction materially repairs MLB pitchers but not prospect pitchers. The current
nested result totals only 68.1 expected WAR across 3,849 pre-MLB pitchers and tops out
at 2.66 WAR. Do not repair that output with an FV floor, a changed grade mapping, or
the weak age/level/hand adjustment. A four-year replay finds the existing constant-
hazard probabilities are already optimistic, so low arrival odds are not the cause.
The next test targets conditional MLB WAR and linked career production, with failures
retained, earlier-cohort selection, and one untouched later cohort. See the
[horizon audit](prospect-horizon-extrapolation-result.md).

The first [conditional-quality test](prospect-pitcher-conditional-quality-result.md)
also rejects the available aggregate-feature challenger. Minor-league component rates,
age, level, workload, role, hand, origin and official draft pedigree do not beat a
population mean on later successful pitchers. A tier-quality relationship also
reverses across periods. The next input class must add genuinely new cutoff-safe
pitch/process or batted-ball evidence, or a broader mature cohort; do not rescue the
same features through more tuning.

**Direction correction:** the sequence below is the batting/opportunity workstream,
not the whole project roadmap. Before another opportunity challenger, inventory
the existing `playing_time_model.py` and dated 40-man source adapter; reuse and
revalidate them on repaired inputs. The player-rights contract, dated 40-man adapter,
censored career-outcome panel and first pitcher-component baseline are now implemented.
The broader official `fullRoster` source is now the primary candidate denominator:
99.80% of players have one candidate organization. Its 0.20% multi-team outliers must
be reconciled through dated transactions or another rights authority. Financial/control
sources and whole-player integration remain open.

O2026D is now complete: official MLB batting-PA labels include non-arrivals,
and a frozen level-aware opportunity baseline improves pooled any-PA Brier error
by 10.0% over prior-exposure-only means, with improvement in both active years.
Playing-time gains are modest. [Results and scope](hitter-v2-O2026D-result.md).
This is a prior-season-active cohort, not complete roster/no-history coverage.

1. Keep the competition-normalized ability component; stop global calibration
   experiments. C2026C is closed and all results are preserved.
2. The completed error audit finds much larger optimism among brief MLB call-ups
   than among players with 100+ MLB PA. This motivates the opportunity cohort;
   observed future PA remains diagnostic, never a predictor or exclusion rule.
3. Keep O2026D as the opportunity benchmark. Audit the participants outside its
   cohort and prior-date roster, role, and age availability. Expand inactive and
   no-history coverage explicitly; the full prospect denominator remains unverified.
   Then freeze one player-specific opportunity alternative. Preserve verified
   official batting-PA zero labels and evaluate against the same baseline.
4. Specify the long-term value horizon and label availability, then compose value
   only after component behavior is understood. Do not attach unvalidated WAR labels.
5. Define prospective confirmation before examining its outcomes. The repeatedly
   inspected 2022–2024 seasons remain development evidence. Protected 2026 stays closed.

## What can wait

Website changes and presentation polish are paused. Pitching, defense and value
integration remain required modeling milestones. Quarantine bounded data exceptions;
stop only for identity, leakage,
denominator, coverage, scale, or material forecast errors. Track known omissions,
including the players outside the original G0 forecast population.
