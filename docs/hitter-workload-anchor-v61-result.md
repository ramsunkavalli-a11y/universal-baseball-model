# Demonstrated workload helps some returns but fails as a universal forecast

2026-10-03. Retain corrected V53. Both global playing-time replacements are
withheld after all 70 heads replayed and fourteen actual player reviews.
No frozen 2026 projection or deployed explorer changed. The hitter goal stays
active; this is a completed comparison, not a finished model.

## Exact comparison

The [locked contract](hitter-workload-anchor-v61-contract.md) keeps all 30,506
evaluation identities, source histories, chronological player folds and hitting
talent fixed. Both new models receive identical corrected availability inputs
and demonstrated prior MLB workload. The direct model predicts PA; the anchored
model predicts the adjustment to that workload reference. This isolates their
architecture contrast. Differences versus V53 combine source and architecture;
they cannot be attributed entirely to repaired health information.

The reference is the largest annualized MLB workload in three years, with a
fixed 100 floor and 800 ceiling. Short 2020 workload is normalized only for this
opportunity reference. Actual batting counts remain actual samples. A reference
is neither a promised job nor an observed full-season workload.

| Identical population and score | V53 | Direct | Anchored |
| --- | ---: | ---: | ---: |
| All hitters PA RMSE | 60.686 | 60.930 | 61.853 |
| Public matches PA RMSE | 138.488 | 138.501 | 140.498 |
| Public matches PA MAE | 106.871 | 106.752 | 108.768 |
| Public matches offense RMSE | 1.06136 | 1.06218 | 1.06495 |
| Absent former regulars PA RMSE | 168.029 | 146.924 | 130.192 |
| Absent former regulars PA MAE | 77.171 | 80.431 | 93.691 |
| Current 600 PA regulars PA RMSE | 136.423 | 134.811 | 135.288 |

The same 2,627 public matches retain Steamer PA RMSE 135.379 and MAE 92.083.
Snapshot dates remain unknown. Offense is batting plus replacement, not full
WAR, park-neutral true talent or trade value. Direct MAE improves only 0.12 PA,
not a meaningful public improvement or satisfaction of the practical target.

Nominal player-cluster intervals confirm the global anchored workload loss:
all-hitter MSE change +143.09, interval +77.51 to +206.75; public +560.90,
interval +54.96 to +1,013.61. Direct differences are small and uncertain.
These repeatedly exposed historical comparisons remain development evidence.

## The apparent comeback win fails an important aggregate check

There are 103 absent-former-regular player-years and 4,556 actual next-year PA.
V53 predicts 2,883, direct 4,579, anchored **7,974**. The anchored RMSE improves
because it catches some large returns, while increasing many smaller false
positives. Its total is about 75% too high and its MAE worsens. The paired
absence-group interval also includes no improvement. This is not a sound
reason to route every absent former regular into the anchored model.

Tatis improves from 35 to 322 versus 635 PA, with a hitting estimate close to
reality. But Lux falls 217 to 197 versus 487; McLain rises 174 to 233 versus
577 with only two broadly matching training people. McLain's older offense
forecast was accidentally close through offsetting PA and hitting errors.
Those cases distinguish useful preserved capacity from validated recovery.

Direct better matches comeback-group totals and improves RMSE, but its uncertainty
is large, MAE worsens and the wider model still loses. Preserve that observation
without manufacturing a subgroup winner or tuned blend.

## Growth and adverse outcomes remain important

- Votto improves 540 to 619 direct or 639 anchored versus 707 PA. Back-to-back
  near-full seasons and strong hitting support this sensible established-role gain.
- Judge after his brief debut falls 281 to 181 direct or 209 anchored versus
  678. The 410-PA/19-HR AAA record and scouting evidence are present, but the
  forecast still misses both readiness and the hitting breakout.
- Soler falls about 367 to 220 anchored versus 679. His limited past MLB use
  becomes too much of a reference, despite AAA power and current hitting evidence.
- Langford rises 43 to 133 direct or 102 anchored versus 557. This does not
  solve fast entry; broad age/stage peers are not equal draft/power prospects.
- Established Judge reaches almost exact anchored PA, but offense gets worse
  because fixed hitting talent undershoots his realized season. Correct workload
  alone cannot validate the product.
- Yordan after 2022 receives worse PA but better offense through the opposite
  offset. After 2024 he remains a major false high, as does Acuna after 2023.
  Later adverse realizations are not automatically origin-known information.
- Franco's unresolved restriction produces 465 anchored PA versus zero, still
  an inadequate normal-role mean. It cannot be repaired by backdating a later ban.
- Diaz and Pillar show ordinary close offense totals hiding separate PA/rate errors.

The [complete walkthrough](../reports/model-evidence/hitter-workload-anchor-v61/player-walkthrough.md)
contains actual three-year counts, independently reconstructed pooled K/HR
inputs, annualization, actual tree terms, corrected availability, intermediate
arithmetic, support and origin-selected successful and unsuccessful peers.

## Cohort and numerical checks

Lower-minor expected PA rises from 8,129 to 10,440 direct or 11,031 anchored
versus 6,072 actual. Neither makes that allocation reasonable. Upper-minor
totals get closer, but MAE worsens. The 2021-origin deficit improves but remains
about 7,850 PA in either new arm; 2023-origin overforecast gets larger.

Direct raw forecasts are negative in 8,847 rows, anchored in 3,053. Both use
the declared zero bound; no 800 upper clipping occurs. This is not nine thousand
predicted retirements or learned appearance probabilities. The negative-output
frequency limits interpreting direct squared-error means near non-arrival.
Sparse and unobserved profiles stay scored, not discarded.

## Direction after this comparison

Keep the better-supported batting forecast and V53 opportunity baseline. Close
the peak-reference batch without tuning its floor, selecting its favorable
cases or constructing a post-result comeback boost. More injury penalty sweeps
and another generic tree library are not justified by this evidence.

The next substantive alternative should estimate a smooth, bounded workload
mean from career/role evidence rather than predict unconstrained adjustments
and rely on zero clipping. Compare it on the same full population with distinct
stage support, keeping learned transitions, prospect growth and exits together.
Use proper chronological fitting and actual player reviews; do not claim a
bounded mean alone supplies calibrated appearance or career-value uncertainty.
Joint delivered-value uncertainty and explicit unresolved-status scenarios
remain required before the complete hitter candidate is called finished.
