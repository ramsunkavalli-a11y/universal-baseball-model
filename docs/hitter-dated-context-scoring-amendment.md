# Correct the context test value reference and player identification

2026-10-04. The first review replayed every saved head and wrote aggregate
scores, but stopped when the fixed Hyeseong Kim case had a null display name.
It also used a legacy response field with the wrong value reference. This
amendment repairs the review, not the fitted models or forecast population.

## Preserve the initial evidence

Keep the initial reviewer and its scores.json, intervals.json and
public-benchmark.json unchanged. Their playing-time and appearance metrics are
valid. Their value metrics describe the common origin-season reference, despite
being labeled relative. They must not be cited as same-season relative value.
The original contract's secondary-label formula is superseded here; its primary
PA target, membership, cases, comparison and tuning restrictions are unchanged.

The new reviewer writes scores-relative.json, intervals-relative.json and
public-benchmark-relative-review.json. It verifies the initial PA/probability
metrics agree and independently reconstructs MLB event counts and league-season
environments from the existing dated stint source. Observed hitting is the
player's event-weighted production minus the target season's league reference,
in custom batting wins per 600 PA. Delivered value is observed PA times that
relative hitting rate divided by 600 plus the original replacement reference.
The reconstruction must agree with actual_future_relative_rate and
relative_value_label. The familiar next_batting_rate field is not this target.
Realized target environments are labels only; no forecast receives them.

## Keep fixed player cases

Resolve the already declared fixed names by exact MLBAM IDs and origin, verifying
their dated source names. Hyeseong Kim is 808975, Jung Hoo Lee 808982, Ha-Seong Kim
673490, Eric Thames 519346, Aaron Judge 592450, Nick Kurtz 701762, Steven Kwan
680757 and Junior Caminero 691406. Use a dated source name for readable review
when the saved forecast name is null, while preserving the original null field.
This changes neither case selection nor the model's inputs.

Complete the player mechanics and manual baseball review before disposition or
another modeling experiment. Preserve omitted foreign entrants as pending
forecasts, not successful zeros. No fits are repeated, protected 2026 remains
closed, and no forecast or explorer is promoted by this amendment.
