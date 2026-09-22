# Universal pitch sequence and game-feed hitter test

Status: **component completed; infrastructure retained; no change to the current hitter base**

## Plain-language result

We successfully combined nearly every affiliated pitch from 2016–2024 with the
official game conditions. The useful baseball information is the hitter's rate
of swinging, making contact, fouling pitches off, reaching two strikes, handling
the first pitch, and performing against left- and right-handed pitchers.

Those rates contain some future signal. They made the single LightGBM model a
little better overall and were especially promising for low-workload and
advancing players. But the gain was small, uncertain, and did not survive every
model family. The current five-model hitter ensemble already predicts MLB
arrival better than a chronology-safe stack that adds these rates. Therefore,
the rates do not replace or modify the current hitter model yet.

The negative results are also useful:

- Raw pitch and plate-appearance volume made the model worse. The existing
  workload features already contain that information.
- Directly feeding a player's weather and park exposure into the projection did
  not help. Game environment belongs in the event-level context adjustment, not
  as a shortcut that labels a player by where he happened to play.
- The first opponent/umpire residual construction helped arrival scoring in
  some tree models but hurt expected-value accuracy. It is not retained.

## Data now available

The official schedule feed is retrieved in 54 bulk season/level requests. It
now preserves:

- physical venue, city, state/country, surface, roof, capacity, and dimensions;
- scheduled and actual first-pitch time, day/night, game duration, and delays;
- temperature, condition, wind speed, and field-relative wind direction;
- attendance and all available umpire identities.

Across 91,568 completed regular-season games, weather, wind, day/night, surface,
roof, attendance, duration, and actual first pitch are effectively complete.
Home-plate umpire is 99.98% complete and field dimensions are 82.5% complete.
The pitch PBP matches an official context record for 98.59% of games.

The PBP feature layer contains:

- 23,993,223 physical pitches;
- 6,998,146 plate appearances;
- 34,590 hitter-seasons;
- all affiliated levels in 2016–2019 and 2021–2024;
- an explicit 2020 missing-season boundary;
- 77 annual pitch/game features carried through lag 0, lag 1, and lag 2.

Only universally available evidence is used: pitch result, count, batter side,
pitcher side, batter, pitcher, level, and game identity. Pitch location, pitch
type, velocity, and Statcast contact measurements remain outside this universal
base because their historical minor-league coverage is incomplete.

Official game weather is a game-baseline snapshot. It is not represented as the
weather at every pitch. Exact time-varying weather would require an external
hourly source joined to pitch timestamps and is not silently imputed here.

## Chronological hitter test

All comparisons use the existing next-season zero-inclusive MLB component-WAR
target and the same expanding folds with test origins 2017, 2018, 2021, 2022,
2023, and 2024. No 2026 outcome was read.

The fixed LightGBM comparison produced:

| Added block | Expected-WAR RMSE | Change from old base | Reading |
|---|---:|---:|---|
| Old base | 0.439518 | — | Required comparator |
| Pitch rates only | **0.438988** | **-0.000530** | Best clean version |
| All sequence fields | 0.439363 | -0.000155 | Counts dilute rates |
| Raw sequence volume only | 0.441135 | +0.001617 | Harmful |
| Game environment only | 0.439526 | +0.000009 | Neutral |
| Opponent/umpire residuals only | 0.439811 | +0.000293 | Harmful for value |
| Pitch rates plus environment | 0.439221 | -0.000297 | Worse than rates alone |
| Every new field | 0.439015 | -0.000503 | No better than rates alone |

For pitch rates alone, the player-clustered 95% interval for the RMSE change is
**-0.001923 to +0.000856 WAR**. The point estimate is favorable, but the interval
does not establish a reliable win.

The same rate block changed the LightGBM arrival scores by:

- Brier: **-0.000091** (better);
- log loss: **-0.000493** (better).

It also reduced conditional-value RMSE by 0.000498 in that model. However,
expected-WAR RMSE worsened by 0.000189 in XGBoost and by 0.002329 in ridge.
XGBoost still improved Brier and log loss, while ridge did not.

The LightGBM WAR change was better in the 2021–2024 folds and worse or flat in
2017–2018. Among rows with current-season pitch data, expected-WAR RMSE was
essentially flat (+0.000268). The pooled gain partly comes from how earlier
history and missing-current-season cases are routed, which is another reason not
to call this a settled talent improvement.

## Final arrival-only check

Because the tree models showed the most consistent benefit in MLB-arrival
probability, a regularized logistic stack combined:

1. the current five-model ensemble probability;
2. the LightGBM base-plus-pitch-rate probability; and
3. the XGBoost base-plus-pitch-rate probability.

Every fold was fitted only on earlier out-of-fold seasons. It failed against the
current ensemble:

| Arrival model | Brier | Log loss |
|---|---:|---:|
| Current ensemble | **0.049975** | **0.165267** |
| Chronological pitch-rate stack | 0.050601 | 0.166554 |

The worsening is statistically clear in the player-cluster bootstrap. The stack
therefore is not retained, even for arrival probability.

## Decision

1. Keep the official game-environment table and the universal pitch-rate
   materializer as reusable research infrastructure.
2. Do not add raw pitch volume, environment exposure, or the current
   opponent/umpire residuals to the hitter projection.
3. Do not change the current five-model MLB-arrival probability.
4. Preserve the pitch-rate-only challenger for the protected 2026 confirmation.
5. Use weather, wind, surface, dimensions, timing, and umpire/scorer-type effects
   inside event-level contact, defense, baserunning, and called-strike models—then
   aggregate context-neutral player talent. Do not treat a player's historical
   environment as if it were a repeatable skill.

This puts the question to bed for the current development sample: the universal
pitch sequence is real information, but it has not yet earned a place in the
production hitter value model.
