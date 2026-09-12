# Direct two-year talent development result

Last updated: 2026-09-12  
Status: **SUPPORTED NEAR-TERM RATE MODEL; NOT A PROSPECT CEILING**

The one-year development adjustment was not repeated twice. The same historical
framework was fit directly against translated component quality two seasons later.
Training, model selection, level translation, minimum future evidence and missing-
season rules remain the same. Every path touching the nonexistent 2020 minor-league
season is excluded.

## Result versus unchanged talent

The final research form beat carry-forward on both proper scores in all three later
two-year replays. This is the richer form for hitters and the simpler form for pitchers.

| Target | Hitter log-loss change | Hitter Brier change | Pitcher log-loss change | Pitcher Brier change |
|---|---:|---:|---:|---:|
| 2023 | -0.01397 | -0.00597 | -0.03156 | -0.00802 |
| 2024 | -0.01768 | -0.00686 | -0.02857 | -0.00706 |
| 2025 | -0.01697 | -0.00542 | -0.02913 | -0.00793 |

## Complexity decision

- Hitters: explicit strikeouts improve the overall two-year component candidate, but
  its extra interactions do not beat age/level alone on both scores in 3/3. Prefer the
  simpler age/level form.
- Pitchers: the richer form beats age/level alone on Brier in 3/3, but log loss in only
  2/3. Prefer the simpler age/level two-year pitcher form under the fixed 80% breadth
  rule.

The final decision model—not merely the richer candidate—now controls uncertainty and
subgroup reporting. Both chosen forms beat carry-forward on both scores in 3/3 replays,
and their paired-player 95% upper bounds remain below zero in 3/3. The chosen simpler
pitcher form has only one supported crossed subgroup reversal: MLB ages 23–25 in 2025,
and the loss is small.

This gives the development layer a logical shape instead of one universal adjustment:

- one-year hitters and pitchers can use current component shape after heavy shrinkage;
- two-year hitters and pitchers use the simpler age/level path;
- two-year pitchers use the simpler age/level path until richer detail proves broader.

Both horizons remain rate-only and conditional on a later observed season. Playing
time, position, arrival, contracts, public rank and public FV are absent.

## Current application check

The fits were trained through completed 2025 and applied to the current rate table. The
result correctly describes **two-year MLB-equivalent rate**, but it fails as a universal
prospect ordering. Typical 18-year-old Rookie/complex hitters receive roughly a
70-runs-per-600 decline and Single-A hitters roughly a 49-run decline in a historical
2023-origin diagnostic. That can describe how far a teenager remains from MLB quality
at age 20; it cannot describe eventual ceiling.

Keep this output as a near-term diagnostic. Do not connect its rank to FV or trade value.
The next talent target is translated age-24-to-26 skill, evaluated directly from
historical paths. Public ranks remain a post-model error audit only.
