# Current model plan

Updated 2026-09-06. The user wants the model made credible before further interface
work. This is the active plan; earlier experiment contracts remain historical records.

## Goal

Build toward KATOH-style prospect evaluation by answering three distinct questions:
MLB batting ability, probability and amount of MLB opportunity, and development
over the chosen value horizon. A useful first model needs material predictive
evidence and honest uncertainty, not perfect reconciliation of every source row.

## What we have learned

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

1. Keep the competition-normalized ability component; stop global calibration
   experiments. C2026C is closed and all results are preserved.
2. The completed error audit finds much larger optimism among brief MLB call-ups
   than among players with 100+ MLB PA. This motivates the opportunity cohort;
   observed future PA remains diagnostic, never a predictor or exclusion rule.
3. Build an MLB-arrival/retention/exposure target that includes non-arrivals and
   no-history cases. Conditional performance among MLB participants cannot substitute
   for this. Verify zero labels against complete official MLB participation, rather
   than treating missing model-ready PBP as zero. Use earlier cohorts to avoid
   protected outcomes. Freeze one simple opportunity baseline before alternatives.
4. Specify the long-term value horizon and label availability, then compose value
   only after component behavior is understood. Do not attach unvalidated WAR labels.
5. Define prospective confirmation before examining its outcomes. The repeatedly
   inspected 2022–2024 seasons remain development evidence. Protected 2026 stays closed.

## What can wait

Website changes, presentation polish, pitching, and full defensive/value integration
are paused. Quarantine bounded data exceptions; stop only for identity, leakage,
denominator, coverage, scale, or material forecast errors. Track known omissions,
including the players outside the original G0 forecast population.
