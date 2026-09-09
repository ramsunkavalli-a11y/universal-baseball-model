# Modern pitcher component aging result — 2026-09-08

Status: **challenger rejected; retain Tango's regressed curve for Phase 1**

## Method

The challenger used retained official MLB data from 2015–2025. Each pitcher-season's
K, unintentional walk, HBP, HR and other-BF profile was regressed by 200 BF toward its
season's MLB population before adjacent-season differences were measured. This follows
the key warning in Tom Tango's adjacent-pitching work: raw survivor deltas exaggerate
aging because noisy performances and selective return are not handled.

The model fit smooth quadratic age effects on coherent log component ratios. Player
weights used capped harmonic-mean BF, and a zero-effect ridge prior prevented sparse
ages from producing extreme curves. The estimand is rate change conditional on a
pitcher appearing in MLB in both adjacent seasons. Disappearance remains in the
separate participation/workload model.

Parameters were fit only through the 2021 target season, then tested on 2022–2025.
The 2026 partial season was not used.

## Result

The later-period test contains 2,442 adjacent pitcher pairs, 1,069 pitchers and
618,983 target BF.

| Method | BF-weighted component log loss |
|---|---:|
| Tango regressed curve | 0.9650473 |
| No aging | 0.9651145 |
| Modern fitted challenger | 0.9654387 |

Lower is better. Tango beat no aging overall and in three of four test seasons. The
modern challenger beat no aging only in 2023 and lost overall to both comparisons.

## Decision

Keep Tango's more-regressed adjacent-pitching curve as the simple Phase 1 sensitivity.
Do not tune the rejected challenger after seeing these results. A Phase 2 revisit may
use more recent training years, role-specific curves, injury evidence or a joint
participation/rate model, but it must use a new predeclared test.
