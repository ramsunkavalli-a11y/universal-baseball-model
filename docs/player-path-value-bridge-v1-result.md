# Player value: first joint-outcome test

2026-09-23. **The new path model is rejected; the valuation interface and audit
are delivered. Live forecasts and the explorer are unchanged.**

## What the project is now explicitly aiming to deliver

Our projection system should describe possible careers, including failure,
ordinary success and sustained high production. The valuation layer should price
the team's remaining rights in each career path, including costs, before averaging.
Market return is a separately estimated comparison, not a label copied into our
talent model. Mean production alone is insufficient for this purpose.

The new path-to-value interface separates those tasks. It requires whole-player
WAR, explicit annual rights and obligations, a complete liability/control tail,
and a stated marginal win-price schedule. Unknowns block value, rather than
silently becoming free control, zero salary or zero future production. Guarantees
can produce negative surplus when a player does not play. Failure probabilities
are not discounted a second time. Future club decisions cannot use future realized
performance. The interface supplies arithmetic, not fitted contracts or a validated
market curve; **no player dollar values are released**.

A unit test illustrates the distinction in arbitrary price units: a 50/50 chance
of 0 or 12 wins has the same six-win mean as a certain six wins. With a continuous
schedule pricing the first two wins at one unit each and later wins at two, the
uncertain outcome has expected value 11, versus 10 for the certain outcome. With
a linear price both are six. This is a mathematical example, not an empirical
claim that uncertain players always deserve a premium or that 12-WAR seasons
are realistic typical outcomes.

## What was tested

The [fixed plan](player-path-value-bridge-v1-plan.md) defines three candidates:
an age/stage matched historical-path baseline, a forest using age/level/workload,
and the same forest adding hitting history (all 77 existing features). Each draw
keeps a donor's complete annual PA and batting-value vector together. Forest
structure and donor outcomes use disjoint identities, and self-donors are excluded.
This is conditional historical resampling, not a revival of the old rejected
career simulator or a guarantee of complete lifetime/control coverage.

There are 33 method/fold runs, including three normal three-year test origins,
pandemic stress tests, a player-disjoint sensitivity and separate current research
distributions. No target past 2025 is used. Six-year validation remains limited:
all four six-year test windows cross 2020. The three- and six-year fits are separate
experiments and cannot be combined into one coherent annual probability curve.

The available long-history outcome is batting plus replacement, not full WAR.
“Sustained high batting” means at least two seasons with four batting/replacement
wins; it is not an All-Star label. Regular workload means at least two seasons
with 450 PA. Events overlap and are not mutually exclusive career categories.

## Results: more information helps, but this distribution is not good enough

| Normal three-year test | Age/stage paths | Basic forest | Hitting-history forest | Delivered mean model |
| --- | ---: | ---: | ---: | ---: |
| Distribution error, CRPS (lower better) | 0.3641 | 0.2968 | 0.2894 | Not a distribution |
| Mean-production RMSE | 1.644 | 1.366 | 1.333 | **1.214** |

Hitting history improves distribution error against the basic forest in all three
origins. The paired change is -0.00745, with a player-clustered 95% interval
[-0.01126, -0.00339]. Joint annual-path score also improves. Those results support
the information content of hitting history, not adoption of this whole model.

The candidate fails the predeclared delivered-mean retention gate and the regular
workload probability gate. Pooled sustained-high batting counts look reasonable
(76.9 predicted versus 76 observed), but that mostly reflects existing MLB players.
It does not establish prospect upside calibration. Across 9,845 never-debuted
minor-league player-origin rows, **28.7 regular-workload outcomes were predicted
versus 44 observed**. Only four sustained-high batting outcomes occurred in that
subset; apparent agreement there is insufficient evidence.

The six-year stress results also improve on both new distribution baselines, but
the candidate's mean RMSE is 2.289 versus 2.173 for the delivered reference. This
does not solve the longer-horizon problem. The reference uses the already-delivered
rookie repair for Years 1–3 and unchanged prior annual means for Years 4–6.

Aggregate central-80% coverage is about 89%, partly because many outcomes and
intervals are exactly zero. That number must not be interpreted as well-calibrated
uncertainty for valuable prospects. Bootstrap intervals are conditional on these
fixed historical comparisons and Monte Carlo draws, not independent confirmation.
The 2021/2022 outcome windows overlap; 2016/2021 are separately reported.

## A useful diagnosis for the Eldridge question

After scoring, we examined historical players aged 23 or younger with 1–99 MLB PA
at the cutoff. In 98 player-origin rows over the three normal tests:

| Following three years | Actual | New hitting-history path model |
| --- | ---: | ---: |
| No additional MLB PA | 10 | 46.8 expected |
| At least two 450-PA seasons | 16 | 6.75 expected |
| Mean batting/replacement wins | 1.508 | 0.705 |

The existing delivered mean was 1.095 for this subset: closer, but still below the
observed average. This small, post-score diagnostic is not proof of individual
mispricing and was not used to change any gate or player projection.

The new forest can borrow too broadly for rare young MLB profiles. The current
three-year donor library contains only 43 MLB-stage players aged 19–22; the
six-year library has 34. Eldridge's six-year sampled donors average age 24.6,
and 287 of 400 samples begin in the minors despite his MLB appearance. That is
evidence of weak local support. Whether this borrowing causes the forecast error
requires a new test; it is not permission to manually boost Eldridge.

The latest-snapshot-per-player sampling rule was meant to stop long careers
dominating the library, but it also discards earlier young-player snapshots.
That is a plausible contributor and should be audited against identity-balanced
sampling of all eligible snapshots. No post-score reweighting was attempted.

Current Eldridge and other player distributions are retained as **rejected research**
in the package, not displayed in the production explorer. In particular, their
failure/regular/high-production percentages are not credible new player forecasts.

## Next bounded milestone

1. Diagnose historical retention/advancement for young players with brief MLB
   exposure, preserving cutoff-known promotion timing and substantial minor-league
   evidence. Audit donor population construction before adding model complexity.
2. Predeclare one revised distribution model that preserves adequate young-player
   support and separates continuation/role from performance without drawing an
   eventual success tier using future information. Retain all current comparators
   and the prospect regular/success calibration checks, not just overall error.
3. Complete the whole-WAR target/accounting audit and validate joint service/control
   paths. Feed only supported paths and sourced costs into the new value interface.
4. Keep a separate future-entrant reserve for league/team forecasting. Future
   draftees are not assets already owned by today's clubs, and current players'
   values must not be raised simply to fill the future league's PA budget.

This closes the fixed experiment. It does not authorize an open-ended search for
parameters that make Eldridge, public FV lists or previously exposed results look
right. The objective remains independent model-derived player-rights value.

## Reproducibility

```text
.venv/Scripts/python.exe -X utf8 scripts/fit_player_path_value_bridge_v1.py
.venv/Scripts/python.exe -X utf8 scripts/score_player_path_value_bridge_v1.py
.venv/Scripts/python.exe -X utf8 scripts/report_player_path_value_bridge_v1.py
.venv/Scripts/python.exe -X utf8 scripts/verify_player_path_value_bridge_v1.py
.venv/Scripts/python.exe -X utf8 -m pytest tests/test_player_path_value.py -q -p no:cacheprovider
```

The durable package is `model_artifacts/player-path-value-bridge-v1-2026-09-23/`.
Source manifests, per-player scores and rejected current research summaries are
retained. The 121 MB of sampled-donor archives remain in the local fingerprinted
cache, with hashes and donor/query identity mappings; deterministic replay can
regenerate draw indices. No financial, service-day or public-grade data was used
to manufacture a value. The live explorer and all previously delivered packages
remain unchanged.
