# Full BIP pitcher contact-talent result

**Status:** contact signal confirmed; full-rate promotion rejected
**Model effect:** none

## Source

The certified public MiLB PBP reducer was extended to retain the same screened ten
BIP bins used for hitters plus supported terminal outcomes. Raw downloads were
streamed and removed after compact reduction.

| Season | Classified BIP | Pitchers |
|---|---:|---:|
| 2021 | 421,766 | 4,580 |
| 2022 | 479,253 | 4,743 |
| 2023 | 475,974 | 4,721 |

In 2021, 421,085 classified BIP (99.84%) also had a supported contact outcome after
one non-contact HBP label was excluded. Learned neutral wOBA values ranged from
`0.037` for popups to `0.834` for pulled line drives. Pulled outfield flies were
`0.762`; pulled, center, and opposite grounders were `0.203`, `0.235`, and `0.281`.
These are descriptive values learned from outcomes, not assigned bonuses.

## Forecast test

Both estimates used the same 100-contact population regression. The candidate used
the complete projected BIP mix and earlier-season neutral bin values. Development
fit one bounded blend weight on 2021 predicting 2022. That frozen weight was then
used with 2022 inputs predicting 2023.

| Test | Players | Baseline MAE | BIP blend MAE | Baseline RMSE | BIP blend RMSE |
|---|---:|---:|---:|---:|---:|
| 2021 → 2022 development | 2,548 | 0.05064 | 0.04624 | 0.06524 | 0.05963 |
| 2022 → 2023 confirmation | 2,512 | 0.04948 | 0.04605 | 0.06334 | 0.05881 |

Contact-weighted errors also improved in both periods. The development blend weight
was `0.9607` and was not changed for confirmation. Every supported origin level—A,
High-A, AA, AAA, and Rookie—improved on both equal-player MAE and RMSE in both
periods. There was no supported level reversal.

## HR-separated compatibility check

The active pitcher model already forecasts home runs separately. A stricter rerun
therefore gave home runs zero value inside the BIP contact target rather than counting
them twice. The weight was fit on 2021 predicting 2022 and frozen at `0.7611`.

| Test | Players | Baseline MAE | BIP blend MAE | Baseline RMSE | BIP blend RMSE |
|---|---:|---:|---:|---:|---:|
| 2021 → 2022 development | 2,548 | 0.04048 | 0.03763 | 0.05144 | 0.04849 |
| 2022 → 2023 confirmation | 2,512 | 0.04080 | 0.03788 | 0.05231 | 0.04942 |

Contact-weighted errors and every supported level improved too. This confirms that
the full BIP profile adds non-home-run contact information without taking credit for
the separate home-run component.

## Interpretation and boundary

The broad BIP profile carries repeatable future pitcher contact-quality information.
This succeeds where individual ground/popup/pull increments failed because it values
the coherent distribution rather than asking one isolated rate to move a broad
outcome model.

The later [active-model comparison](full-bip-active-model-result.md) also passed after
the active prediction, BIP estimate and future target were all put on one cutoff-safe
MLB-neutral scale. The frozen weight was `0.7883`; every supported confirmation level
improved.

The [complete pitcher-rate replay](full-bip-pitcher-rate-replay-result.md) is now
finished and reverses on confirmation overall, at A, and at Rookie. The production
decision is zero weight. No current pitcher talent, WAR, FV, or value changes.
