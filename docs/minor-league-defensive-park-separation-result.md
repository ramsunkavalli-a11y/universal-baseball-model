# Minor-league defensive park separation result

## Decision

Use physical venue IDs and a **visitor-anchored park adjustment** as the next
infield defensive environment. For the player rating, use the chronology-selected
50/50 blend of visitor-anchored and crossed-model ratings with 1,200 opportunities
of regression. Keep the full crossed model as an environmental diagnostic.

The 50/50 weight was not assumed. Early folds selected the pure visitor rating;
using only those results, the 2022, 2023, and 2024 folds each selected the 50/50
blend and 1,200-opportunity regression from the predeclared grid.

This result is based on 1,299,756 minor-league ground-ball opportunities from
2016-2024, excluding the nonexistent 2020 MiLB season. The protected 2026 result
was not accessed.

## The baseball question

A difficult infield can make every fielder look slow. The old model estimated a
park's out rate from all plays there, which means the regular home defenders could
partly create their own park adjustment. The new visitor-anchored method estimates
park difficulty only from visiting defenses and then applies that adjustment to
both clubs. A surface, lights, sun, wind, geometry, maintenance, or scoring effect
can enter the park estimate only if it also affects visitors.

The crossed diagnostic goes farther by estimating park, defensive team, and
responsible fielder together. It is useful for describing the complete environment,
but its extra team correction did not produce the strongest future player signal.

## What changed

- Official venue IDs cover 99.8% of the 1,299,756 opportunities. The historical
  source contains 92,683 games and 287 physical venues, including former
  Short-Season A.
- Visiting defenses supplied 48.8% of all opportunities.
- There were 4,198 park/level/position groups with at least 25 home and 25 visiting
  opportunities.
- Raw home and visiting park residuals had a 0.1468 correlation. Park difficulty
  is real, but noisy and much smaller than a simple raw park average suggests.
- The old and crossed park estimates correlated 0.8292.
- Separating the defensive team changed a park-position out probability by 0.005779
  on average in absolute terms.

## Fair next-season comparison

Every method was evaluated against the same 650,355 later-season ground-ball
outcomes for returning player-position pairs. Regression and method choices used
only older folds. Positive values mean that adding the prior player rating improved
the neutral event probability.

| Method | Brier improvement | Log-loss improvement |
|---|---:|---:|
| Previous coordinate plus all-defense park adjustment | 0.00009449 | 0.00035643 |
| Visitor-anchored park/player method | 0.00010957 | 0.00037360 |
| Visitor context plus crossed-model player rating | 0.00011208 | 0.00038662 |
| Fixed 50/50 player blend in visitor context | 0.00011516 | 0.00039057 |
| Chronology-selected visitor family | **0.00011389** | **0.00038200** |
| Fully crossed park/team/player method | 0.00008136 | 0.00026261 |

Relative to the previous coordinate/park method, the fully nested visitor family
increased the player contribution to Brier improvement by 20.5% and to log-loss
improvement by 7.2%. Its player contribution was positive in every reported
chronological fold from 2018 through 2024. The 50/50 blend also beat both parent
ratings on both pooled scoring rules after physical venue IDs replaced the old
home-team proxy.

## What this does and does not establish

The result supports the concern that the old park correction hid a small amount of
repeatable player talent. It does not show that surface, lights, sun, or wind can yet
be identified separately. The current public data identifies only the net effect
that follows a park across visiting teams.

The remaining unmatched 0.2% falls back to the season/home-team identifier rather
than dropping plays. Weather and sun variables would require adding game time,
field orientation, surface, and location to the physical-venue registry.

## Production boundary

This remains a component-persistence result. Before it enters projected WAR it
still needs:

1. a rolling, prior-season park estimate that can be carried to the player's
   destination environment;
2. conversion of outs above expected to runs;
3. projected defensive opportunities without oracle playing time;
4. age, level, and position translation; and
5. chronological testing inside the hitter value stack.

The machine-readable evidence is in
`reports/generated/pbp-infield-park-defense-joint-v1/report.json`, with fold details
in `event_fold_metrics.parquet`.
