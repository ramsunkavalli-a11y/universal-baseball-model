# Pitcher projection testing queue

Status: queued research; no production values change.

These tests follow the rejected eight-outcome contact expansion. Each candidate
must improve future-player forecasts rather than merely describe past results.

## Literature review scope

Before freezing additional candidates, review public pitcher-projection work that
can be reproduced at the granularity already available here: official season totals,
certified play-by-play where coverage permits it, and stable demographics. Tom
Tango's work on Marcel, component weighting, regression, aging, platoon effects, and
times through the order is the primary methodological reference. Use other public
work from the past two decades to find competing testable ideas—not to import a
published projection, player grade, or outside FV opinion.

The review should cover:

- how much history to weight and how strongly each component should regress;
- minor-league level and run-environment translation;
- starter/reliever workload, role transitions, and times-through-order evidence;
- platoon skill and the extra uncertainty in observed split statistics;
- batted-ball trajectory, direction, and contact-quality persistence;
- aging, injury/availability boundaries, and forecast uncertainty;
- proper chronological evaluation and survivor/selection-bias controls.

For each useful claim, record the required fields, available coverage, expected
direction, comparison baseline, and a frozen rejection rule. Literature proposes
hypotheses; our later-season data decides whether they enter this model.

## Priority 1: pooled extra-base hits

Test a seven-outcome profile using universally available official season totals:
SO, UBB, HBP, 1B, non-HR XBH (`2B + 3B`), HR, and other out. Pooling doubles and
triples reduces the rare-triple noise in the rejected eight-outcome model.

- Compare several heavier contact priors with the current five-part incumbent.
- Select only on chronological development data.
- Require lower component log loss and Brier on a later frozen period.
- Keep the 2026 regular season protected for final confirmation.

## Priority 2: lineup challenge and platoon balance

Apply the broader pitcher-projection review to times through the order, platoon
splits, and starter-role forecasting before freezing this test. Then source-gate two
simple event-level summaries:

1. results against lineup positions 1-6 versus 7-9;
2. results against same-side versus opposite-side batters.

Use lineup band as opponent context, not as a direct talent label. First estimate
the expected K, UBB, HBP, HR, and contact outcomes for the batters faced using only
pre-forecast information. Test whether a pitcher's regressed residual against the
top six is repeatable and adds future component or workload information beyond the
quality and handedness of his opponents.

Estimate platoon skill as separate, strongly regressed component differences. Test
whether effectiveness against opposite-side batters improves future starter share,
batters faced, or MLB component forecasts beyond throwing hand, age, level, prior
starts, and prior workload. Do not infer starter ability from merely having faced
more top-order or opposite-side batters.

Lineup positions 1-6 versus 7-9 are the only first-pass bands. Do not search all nine
slots or tune the dividing line after results are visible. If available universally,
times-through-order exposure is a separate context variable rather than a substitute
for lineup quality.

## Priority 3: pitcher contact trajectory and direction

First certify comparable event-level coverage by league and season. Season-total
`groundOuts` and `airOuts` are not valid event counts: double plays can record more
than one out. Unsupported rows must fall back to the incumbent rather than receive
imputed preferred contact.

Test additions in this order, stopping when an increment fails:

1. ground-ball versus airborne-contact share;
2. infield-fly share within airborne contact;
3. pulled airborne contact within airborne contact;
4. pulled ground balls within ground balls.

Direction is defined from the batter's perspective. Models must account for batter
side, pitcher hand, opponent mix, level, season, and park before treating a contact
shape as pitcher skill. Frequency and damage are separate questions: historical
pulled-air frequency may predict future HR/XBH risk, while historical pulled-ground
frequency may predict future contact suppression or double-play value.

## Guardrails

- Use only evidence available before the forecast date.
- Apply hierarchical, exposure-based shrinkage; rare IFFB evidence receives the
  strongest regression.
- Compare every increment with the same players, targets, and denominators.
- Score future outcomes with proper scores and report player-cluster uncertainty.
- Do not choose signs, cutoffs, or priors from player names, FV grades, prospect
  counts, contracts, or current 2026 results.
- Do not assume pulled air is a pitcher skill merely because it is damaging. It
  must be repeatable and improve later forecasts after opponent adjustment.
- An event-level candidate cannot become universal production logic unless its
  source coverage and measurement meaning pass the all-level source gate.
