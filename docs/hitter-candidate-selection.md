# Hitter candidate selection and closed comparisons

2026-10-04. Keep the current coherent research candidate and preserve the
already-tested linear prospect hitting alternative. Do not start another
workload or team-record sweep. The completed comparisons narrow our choices;
they do not establish a finished player-value model.

## What to carry forward

| Part | Current choice | Evidence and limitation |
| --- | --- | --- |
| Established MLB hitting | Existing full-history regularized linear head | Competitive matched public hitting scores, with environment and archive-date qualifications; breakouts and collapses still missed |
| MLB appearance and active workload | Existing shallow histogram heads | Deeper conditional heads now reviewed and worse overall; public PA absolute error and return/readiness gaps remain |
| Prospect hitting alternative | Existing linear rankings plus historical event translations | Debutant hitting RMSE 2.6144 to 2.5831 on the intended future-season-relative target; total-value gain uncertain; no promotion |
| Uncertainty | Existing coherent event-count research layer | Physically valid count draws, modest previously reviewed range gain; not an improved mean or validated career distribution |

The prospect alternative is a useful positive component result, not a new test
to repeat and not a whole-model winner to discard because its delivered-value
interval crosses zero. It changes hitting only for players who had not debuted
at the origin. Established forecasts and every playing-time forecast stay exact.
Its all-player tree sensitivity is not an approved replacement for the established
hitting head.

The [new compatibility receipt](../reports/model-evidence/hitter-candidate-selection/compatibility.json)
verifies 304 saved source/output/model hashes, replays all 35 translated linear
heads and confirms the same 30,506 forecast identities, current columns, fixed
opportunity, established hitting and contribution arithmetic. It independently
reconstructs the corrected rate response from actual event counts and the
target-season environment. There are no new fits, features, forecast changes,
selection tuning or new experimental results in this reconciliation. The earlier
sixteen player reviews remain authoritative.

## What the prospect alternative does for actual players

Hitting below is custom batting wins above MLB average per 600 PA, not full WAR.
The target is centered on the actual future-season average; delivered offense
keeps its separate common-origin reference. These numbers must not be mixed
with origin-centered observed rates from another report.

| Player and origin | Current hitting | Translated linear hitting | Actual future hitting | Expected and actual PA |
| --- | ---: | ---: | ---: | --- |
| Nick Kurtz 2024 | -.063 | +1.024 | +5.150 | 10 versus 489 |
| Wyatt Langford 2023 | +.688 | +1.439 | +.549 | 215 versus 557 |
| Pete Alonso 2018 | +.286 | +.592 | +3.283 | 215 versus 693 |
| Julio Rodríguez 2021 | +.754 | +1.216 | +2.683 | 254 versus 560 |
| Jackson Holliday 2023 | +.621 | +.826 | -2.838 | 351 versus 208 |
| Aaron Judge 2024 | +4.534 | +4.534 | +6.287 | 531 versus 679 |

Kurtz's fifty real A/AA PA and ranking now influence a more favorable hitting
estimate, rather than pretending he already has a large MLB sample. It still
does not identify the magnitude of his breakout or the speed of his arrival.
Alonso and Julio move toward reality, but remain conservative. Langford's rate
gets less accurate while his delivered offense gets closer because expected PA
is too low. Holliday gets worse, and stays in the evidence. Judge is deliberately
unchanged. These facts support retaining a component alternative, not assuming
that optimistic prospect forecasts are automatically better player valuations.

The graph uses historical movers and level differences; it still pools parks,
opponents and selection into promotion. Connected levels are not sufficient
active-profile support. Only 787 debutants supply the observed next-year MLB
rate score, and just eight thin-sample players do; ordinary DSL players have
almost no direct next-year MLB batting labels. A hypothetical DSL MLB hitting
rate cannot be validated by observing zero immediate playing time.

## Names and units that can mislead future work

The current forecast fields are `preseason_pa`, `preseason_rate` and
`preseason_value`. Inherited `baseline_pa` and `baseline_value` still refer to
the older opportunity model before fresher ranks were introduced. They are not
the current anchor. `baseline_rate` happens to remain equal because the ranking
update changed opportunity, not hitting. The reconciliation explicitly checks
this mapping rather than assuming every column called baseline is equivalent.

Rate labels also have two intentional centers. Training and the corrected
prospect talent test use future-season-relative batting rate. The delivered-value
test uses the origin's common event reference. Current public converted comparisons
retain that separate common-origin convention and their existing qualifications.
Event weights are converted using the saved wOBA scale and runs-to-wins divisor;
simply multiplying weighted events by 600 does not produce batting wins/600.

## Coherent next work

The new user direction permits Statcast where available. The
[integration plan](hitter-statcast-integration-plan.md) defines the material
extension: direct future MLB hitting using measured power and usable contact
quality, not a rerun of the two closed Current Talent contact residuals. The
[ordinary MLB source](hitter-own-mlb-contact-source-result.md) and
[launch source review](hitter-statcast-history-result.md) recover cached 2023 and
2024 evidence without changing any forecast. Earlier MLB measurement history,
covered minor sources, clean league/park/opponent handling and actual fold support
are required before the bounded hitting comparison. Untracked players retain
the current forecast; source availability itself is not a talent bonus.

The lower-level follow-up and shared-development-rate comparisons are already
completed in `hitter-followup-support-result.md` and
`hitter-shared-development-result.md`. Do not put those same experiments back in
the queue. Their mature-follow-up and target limitations remain unresolved model
questions, not authorization to repeat the identical comparison.

Close the generic opportunity/head-capacity queue and carry the translated linear
prospect branch as an evaluated alternative. Before any new fit, identify a
substantive representation or coverage change that the completed talent work has
not already tested. A new library name, another rank feature or a tiny favorable
group is not a sufficient reason to rerun the same idea.

The remaining material questions are whether actual lower-level production and
pedigree can forecast later MLB talent with appropriately mature follow-up, and
whether advancement/return opportunity is supported for the profiles we forecast.
Separate that longer development question from next-year contribution: a teenage
prospect can be valuable while having almost no immediate MLB PA. No extra college
collection, invented career outcome for censored players, blanket youth boost,
retirement hindsight rule or team-record variant is permitted.

The current public PA MAE is still 15.56% above Steamer; the existing team-filtered
historical explorer is a research view, not a finished full hitter model. Fielding,
running, catching/position, supported annual paths and actual control/market value
remain separate unfinished parts. Protected 2026 outcomes, the frozen forecast
and both research/deployed explorers are unchanged. The full goal remains active.

Source results: [prospect hitting](hitter-talent-bridge-v74-result.md),
[rate support and age audit](hitter-rate-support-audit-result.md),
[workload comparison](hitter-positive-workload-capacity-result.md),
[current candidate model card](hitter-research-candidate-model-card.md).
