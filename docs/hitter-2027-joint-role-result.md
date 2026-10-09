# Joint workload helps accounting, but the fallback rule needs repair

2026-10-09. This fixed comparison covers 12,432 unchanged player forecasts for
2023–25, with identical old batting/PA and corrected pitcher/DH records in both
arms. It tests positions/opportunities, not talent or full WAR.

Fielding-position RMSE is 163.142 outs under the existing repertoire method and
162.819 under the joint budget (0.20% better); absolute error improves 0.46%.
DH-start RMSE worsens 0.91%, from 5.513 to 5.563. Position-run RMSE barely changes,
0.9529 to 0.9523. These are effectively similar individual forecasts, not a
meaningful new accuracy breakthrough.

Accounting changes more: all three seasons' positional runs total -1,117 under
the old method, -1,540 under the joint budget, against -1,558 observed. The old
method's excess credit is largely removed without forcing any league totals.
Fielding outs are now 2% below observed. DH starts overshoot by 10.6%, including
1,327 versus 805 for upper-minor origins. Better aggregate positional accounting
does not validate those individual role assignments.

## Source-to-player checks and decision

The saved walkthrough has 28 focal player/origins and three origin-only peers
where available. All joint budgets and both sets of position outputs are replayed.
The histories include the observed following season for comparison, explicitly
separated from inputs dated at the origin.

- Ohtani's 2023 forecast previously retained about 130 irrelevant OF outs from
  old tiny fielding appearances. A joint field/DH vector reduces that to three;
  2024 has zero. His 2024 DH forecast rises from 124 to 129 starts against 159.
  The remaining workload miss is not evidence that he should play the field.
- Alvarez's 2023 input contains 39 MLB catching outs and one DH start, plus
  2,038 minor catching outs and 33 DH starts. At 14/(14+100) MLB reliability,
  the joint model assigns 68.6% of job time to catcher: 1,737 catching outs and
  30 DH starts, versus 2,621 and three observed. The older method's 2,282 catching
  outs was better. Minor-league DH rotation need not transfer directly to MLB.
  Origin peers Pineda, Lavastida and Okey are retained, not selected for success.
- Bailey's 2023 forecast has only 2.8 expected PA versus 353 observed. No position
  allocation can repair that old opportunity forecast. In 2025 it supplies
  2,049 catching outs versus 3,089, again with only 345 versus 452 forecast PA.
  The new 2027 batting/PA generation is separate from this fixed historical test.
- Witt's 2024 third-base residue is only 64 outs, not a borrowed role, but it
  comes from an older minor season despite his 2023 all-SS fielding. By 2025
  both methods are entirely SS apart from small DH exposure.
- Eldridge's 2025 forecast retains only his actual 1B/DH repertoire, with 373
  first-base outs versus 102 observed. His zero MLB outcome in 2024 stays in
  the score. No invented 2B/3B/catcher assignments are permitted.
- Chourio's 2024 projection remains mostly CF instead of LF/RF; Holliday remains
  mostly SS instead of 2B. They are genuine future-role failures, not bad glove
  estimates. Buxton's 2024 return from DH to CF also remains missed.
- Arcia is the largest deterioration: his 234-PA current MLB season is mostly
  2B, while the fallback uses only 36 minor SS outs and two DH starts. Normalizing
  that tiny fallback makes it 60% DH. The candidate forecasts 242 SS outs against
  3,630 actual; peers Madrigal, Chisholm and Villar are preserved. The short minor
  stint should not erase his larger older MLB repertoire.
- Tatis's 2023 fallback similarly uses only 54 minor SS outs and one DH start,
  discarding his older MLB history. The old upstream PA forecast is just 40
  versus 635 actual, and the future RF assignment is also missed. His known
  suspension/return issue was repaired elsewhere; this stale PA cache is not
  a fresh availability model and must not be promoted wholesale.
- Franco is the largest apparent gain because fewer forecast SS outs reduce
  error against zero actual play. That is an old availability miss, not a new
  discovery about defense. McLain is the largest false high because actual
  participation is zero. Westburg is the ordinary measured case: plausible
  2B/3B history, but too little 3B and too much SS in both methods.

No stage has worse fielding-position RMSE; young-origin totals are still high
(12,983 outs versus 7,855) and young DH exposure is 81 versus 20 starts. Tiny
delivered totals cannot establish young-player defensive talent. All unsupported
and nonarrival rows remain included. No uncertainty interval was computed, so
the tiny error difference is not claimed to be statistically established.

**Disposition:** retain joint-budget mechanics for one fallback repair, not
general deployment. The named-player review is complete and identifies a
specific source-selection defect: latest minor evidence outranks all older MLB
evidence regardless of its size. Replace that priority with exposure-weighted
recent fallback evidence, then rerun this same fixed comparison. Do not tune
weights or select players out of the score. Native opportunities, full-WAR tests
and final current-role warnings remain required.
