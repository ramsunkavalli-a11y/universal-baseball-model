# Pitching v1 development contract

Last updated: 2026-08-20

Status: **PRE-OUTCOME CONTRACT — binding before candidate scoring**

## Objective

Select the simplest universal one-year pitcher rate projection that improves on
a neutral and recent-results baseline across MLB and affiliated levels while
keeping future workload and role outside the rate estimand.

## Population and grain

Development input grain:

`season + actual league_id + player_id`

Players may have multiple league rows in one season. Translation is applied at
the observed league row before evidence is combined on the MLB reporting scale.
Team rows within the same player/league/season are summed deterministically.

Required observed fields:

- `pitching_batters_faced`;
- `pitching_strike_outs`;
- `pitching_base_on_balls`;
- `pitching_intentional_walks`;
- `pitching_hit_batsmen`;
- `pitching_home_runs`;
- `pitching_games_played` and `pitching_games_started` for role context.

Every row must satisfy:

`UBB = BB - IBB >= 0`

`OTHER_BF = BF - K - UBB - HBP - HR >= 0`

`K + UBB + HBP + HR + OTHER_BF = BF`

Rows with non-integral, negative or non-reconciling counts fail closed.

## Chronology

Authorized folds mirror the established batting chronology:

| Snapshot cutoff | Future season | Role |
|---|---:|---|
| 2021-10-15 | 2022 | candidate selection |
| 2022-10-15 | 2023 | out-of-time validation 1 |
| 2023-10-15 | 2024 | out-of-time validation 2 |
| 2024-10-15 | 2025 | untouched confirmation only after freeze |

All predictor evidence must precede the snapshot cutoff. The 2025 target and
any downstream pitcher ranking remain quarantined until one candidate form and
all hyperparameters are frozen.

## Outcome profile

The ordered profile is:

`K, UBB, HBP, HR, OTHER_BF`

Future scoring uses all positive-BF player/league rows. Zero future opportunity
is missing rate evidence, not a bad outcome. Players lacking future BF remain in
workload diagnostics but not the conditional rate score.

## Fixed comparators and candidate family

### P0 — neutral environment prior

Leave-one-player-out age/level/role prior translated to the MLB reporting
environment. This is the no-player-specific-skill comparator.

### P1 — recent-season empirical Bayes

Most recent authorized season evidence, translated to MLB and shrunk toward P0.

### P2 — multiseason recency empirical Bayes

At most 1,095 days of authorized history with continuous exponential recency
weighting, translated to MLB and shrunk toward the identical P0 prior.

The candidate grid is intentionally small:

- half-life days: `180`, `365`, `730`;
- prior strength in effective BF: `100`, `250`, `500`;
- role prior form: pooled, or starter-share banded at `<0.25`, `0.25–0.75`,
  `>0.75` when every band meets the predeclared peer floor.

No other candidate or hyperparameter may be introduced after 2022 scores are
opened. If role bands lack support, the pooled prior is used; bands are not
merged reactively.

## Translation

The first translation candidate uses adjacent within-player level transitions
on the five-part CLR scale, fitted only from predictor-window evidence. The MLB
anchor is zero. Every reported level must connect to MLB through observed
eligible transitions or fall back through the frozen universal hierarchy.

The no-translation surface is retained as a diagnostic comparator. Translation
must not use the future target season being scored.

## Primary selection metric

Future-BF-weighted multinomial log loss over all five outcomes:

`loss = -sum(count[p,k] * log(pred[p,k])) / sum(BF[p])`

Probabilities are floored only at a fixed numerical epsilon of `1e-15` for log
evaluation and then renormalized. No result-dependent probability clipping is
allowed.

Selection on 2022:

1. P2 must beat P1 and P0 on aggregate primary loss.
2. It must not lose to P1 in both MLB and non-MLB strata.
3. No individual component may show a calibration slope outside `[0.5, 1.5]`
   when the diagnostic has adequate variation; unavailable slopes are reported,
   not repaired.
4. Ties within `1e-12` select the simpler/stronger-shrinkage form in this order:
   P1, then longer half-life, then larger prior strength, then pooled role prior.

The selected form is then refit using only chronologically available evidence
for 2023 and 2024 validation. It must beat P0 in both years and may not lose to
P1 in both years. Otherwise P1 becomes the Pitching v1 rate model.

## Secondary diagnostics

- unweighted player mean log loss;
- component Brier score and calibration by K/UBB/HBP/HR/OTHER_BF;
- MLB versus AAA/AA/High-A/Single-A/Rookie strata;
- starter-share bands;
- BF evidence deciles;
- age bands;
- translated versus native-MLB rows;
- common-MLB-environment run-value MAE after the rate decision.

None may rescue a primary-gate failure.

## Source and evidence boundaries

- Reuse exact frozen/certified source artifacts where available.
- Do not silently refresh mutable historical source bytes.
- Do not infer missing pitching sacrifice bunts.
- Do not use realized future level, role, BF, injury or roster membership as a
  rate predictor.
- Do not use future fielding, catcher, park or opponent outcomes to repair the
  pitcher profile.
- Keep intentional walks observable but neutral in v1 pitcher walk skill.
- Preserve source row counts, BF, role counts, fallback paths and translation
  provenance in every materialized surface.

## Gates after rate projection

Rate-model success does not authorize final pitcher WAR. The following require
separate frozen contracts:

1. future BF/outs and starter-share projection;
2. event run weights and pitcher-positive run conversion;
3. MLB fixed-reference centering;
4. park/opponent audit;
5. starter/reliever replacement allocation;
6. reliever leverage policy;
7. runs-to-wins method;
8. uncertainty and two-way-player aggregation.
