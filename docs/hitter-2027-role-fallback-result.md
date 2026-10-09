# Position workload: usable v1 mechanics, not perfect future assignments

2026-10-09. The single exposure-pooling repair retains larger old MLB histories
instead of letting a short minor stint replace them. On the same 12,432 forecasts,
fielding-position RMSE improves from 163.142 to 161.926 outs (0.75%); MAE from
25.167 to 25.063 (0.41%). DH-start RMSE improves 0.86% and position-run RMSE 0.48%.
Fielding-position RMSE improves in each of 2023, 2024 and 2025 and each stage.
These small development differences are not claims of a statistically proven
gain or better defensive talent. No resampling interval was computed.

Fielding outs total 3,090,302 against 3,095,594 actual (0.17% low); DH starts
13,975 against 14,510 (3.7% low). Position runs remain too favorable: -1,306
against -1,558, versus -1,117 from the older independent-budget model. Do not
choose the first candidate merely because its errors cancel into a nicer total.
The repaired model has sounder source weighting and better individual errors,
but position-mix bias is still an explicit integration risk.

## Players, including the harm

The same source-to-calculation review was repeated, with new objective extrema
and three origin-only peers for each case where present. The repaired fallback
is a sum of actual exposure times recency weights, then normalized once.

- Tatis's 2023 fallback now includes 1,420 MLB outs from 2020 at quarter weight,
  3,149 from 2021 at half weight, and 54 minor outs from 2022 at full weight.
  Its field/DH shares are 82.1% SS, 4.1% CF, 11.1% RF and 2.6% DH. The two-game
  minor record no longer erases his MLB repertoire. It still cannot discover
  his next RF assignment, nor repair this old test's 40-PA forecast. His current
  2027 forecast uses the separately refreshed model, not this stale PA cache.
- Bogaerts is the largest gain: two large older MLB SS seasons now survive a
  69-out minor stint. The 2025 SS forecast rises from 374 to 843 outs against
  3,250 actual. Still too much 2B is forecast from his current MLB role. Peers
  Polanco, McNeil and Lopez were chosen from current role/workload, not success.
- Story is the largest harm: old 2022 second-base work (2,441 outs at quarter
  weight) reenters behind his 106-PA current season. The model predicts 264 2B
  and 800 SS outs rather than 1,093 SS outs; actual is 4,114 SS and zero 2B.
  His forecast PA is only 173 versus 654. Pooling solves evidence erasure, not
  the distinction between a permanent assignment change and a temporary role.
  Allen, Wilson and Williams are retained as origin-selected peers.
- Ohtani retains his almost entirely DH role; there is no borrowed infield time.
  Eldridge retains 1B/DH, not arbitrary utility positions. Alvarez's 2023 excess
  projected DH time remains: minor DH rotation is a limitation, not proof of
  a poor catcher. Bailey's early workload misses also remain.
- Chourio, Holliday, Witt and Buxton retain the direction-changing limitations
  detailed in the preceding review. Do not describe their roles as certain.
- McLain is still the largest false high through zero actual participation.
  Tatis is the largest false low, mainly from stale PA. Connor Joe is the
  ordinary measured case: 480 projected versus 472 actual PA, but too much LF
  (1,203 versus 595 outs) and too little 1B/RF. Matching PA does not ensure
  correct positional value. Peers Grossman, Taylor and Peralta are retained.

Upper-minor DH starts remain high (1,291 versus 805); lower-minor DH has tiny
actual support (85 versus 19). Young-origin fielding totals remain 65% high,
driven partly by the fixed old opportunity model. No talent claim is made from
those delivered outcomes. All rows and unknown-role cases remain in scoring.

**Decision:** player review complete. Use this constrained, exposure-weighted
mechanism provisionally for the new 2027 component assembly, with visible
position uncertainty and no further weight tuning. It passes the predeclared
individual-error tolerance and removes the targeted source-erasure defect.
This is not unrestricted forecast release: inspect the current players and
full additive WAR, retain role/league-total warnings, and do not force league
totals or present multi-year role assignments as established facts.

Evidence: `reports/model-evidence/hitter-2027-v1/role-fallback-repair/` contains
the before-fit seal, support tables, complete group scores and the source-to-
player calculations, including gains, harm, false extremes and ordinary peers.
