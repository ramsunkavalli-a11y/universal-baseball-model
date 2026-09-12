# Age-to-peak talent result

Last updated: 2026-09-12  
Status: **RATE MODELS PASS; PRECISE PITCHER ORDERING REMAINS PROVISIONAL**

## Question and target

The test predicts a player's translated component rates across reported ages 24–26
from evidence recorded before age 24. The target is the aggregate across at least two
ages and 150 PA/BF. It is not the noisiest best season. Players without later evidence
are unobserved rather than labeled untalented; arrival and playing time remain separate.

Inputs are age, age relative to level, level, evidence amount, and the current translated
and regressed strikeout/walk/contact/power profile. Public ranks, FV, organization,
contracts and future workload are not inputs.

## Method correction

The first version weighted evaluation and fitting by future PA/BF. That rewarded future
opportunity and answered the wrong question. The corrected peak fit gives every player
equal weight. Exposure-weighted event scores remain secondary calibration guardrails.
Historical examples are split by the year in which the age-24-to-26 window ended; the
missing 2020 minors window is excluded.

## Result

| Model | Player log-loss wins | Player Brier wins | Player uncertainty | Event log-loss wins | Event Brier wins | Decision |
|---|---:|---:|---:|---:|---:|---|
| Hitters | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | Pass |
| Pitchers | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | Pass |

The selected form uses age/level/evidence plus current component shape. The hitter
ridge is 1,000 and pitcher ridge is 100. The initial hitter target had combined
strikeouts with other outs and needed an under-20 guardrail. Separating strikeouts from
balls-in-play outs removes that defect: unguarded under-20 hitters improve log loss in
every supported cohort and Brier in 3/4, satisfying the 80% breadth rule. No age
guardrail is now used.

## Current inspection board

The board compares only ranked, non-MLB players with known age 23 or younger. Hitters
and pitchers are ranked separately. This removes the earlier invalid comparison between
a prospect-only public list and all MLB players, as well as inactive MLB players and
older AAA veterans. Players age 24+ belong in a separate MLB-readiness/rate view because
they are outside the model's pre-peak input population.

Current hitter leaders include Rainiel Rodriguez, Caleb Bonemer, Theo Gillen, Leo De
Vries, Eli Willits, Sebastian Walcott, Alfredo Duno and Jesús Made. The explicit
strikeout channel materially changes the ordering and moves Made from roughly 400th
under the flawed structure to 10th after the correct age-supported comparison universe
is applied. It also allows every hitter disagreement to distinguish contact risk from
ordinary balls-in-play outs.

Prominent young pitchers remain the larger gap. For example, Seth Hernandez has only
144 effective BF, a present translated 9.4% walk rate, and a modeled peak 12.2% walk
rate. The aggregate-results model therefore ranks him low despite his strong public
standing. The likely missing evidence is pitch quality/velocity and starter traits;
public opinion itself may not fill the gap.

The separate ranking audit found that correct average probabilities were not enough
to justify precise pitcher ordering. After using the correct fixed MLB run-value
reference, no component/age-level blend passed 2023–2025 confirmation. The component
mean remains an inspection order only. See
`docs/peak-talent-ranking-audit-result.md`.

Generated inspection files:

- `reports/generated/current-peak-talent/2026-09-08/tables/current_peak_hitters_top100.csv`
- `reports/generated/current-peak-talent/2026-09-08/tables/current_peak_pitchers_top100.csv`
- full hitter and pitcher CSV/Parquet tables in the same directory.

## Next talent work

1. Add player-level peak uncertainty/upper-tail fields without changing the mean rank.
2. Continue the model top 25 and external top 50 player case audit while treating
   exact pitcher ranks as provisional.
3. Determine whether official minor-league game feeds provide usable pitch velocity and
   pitch characteristics at scale; test them only as a new pitcher evidence family.
4. Keep position, defense and catching separate until their existing model interfaces
   are joined.

Do not reconnect these rates to FV until the player audit is complete.

## First comparison audit

The union of the model top 25 and external top 50 now has 21 broad hitter agreements
and 9 broad pitcher agreements. Each side has only three supported external-high /
model-low cases after separating promoted MLB players and insufficient evidence.
Model-high / external-low remains larger—12 hitters and 21 pitchers—and is the active
manual audit set. The pitcher model-high set now consists only of supported-age players;
role and within-role rank are included so relief-rate advantages remain visible.
