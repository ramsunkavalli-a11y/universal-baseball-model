# History continuity and prospect probability calibration

2026-09-23. Development experiment specified after the miss diagnostic but before
these fits. Historical results are exposed; this is not an untouched confirmation.
No 2026 outcomes, live forecasts, public prospect grades or player-specific boosts.

## Question

Do missing-season-aware summaries or past-only probability calibration improve
the rich hitter arrival challenger? Keep rankings distinct from probability levels.
The diagnosis suggests 2021 disruption and young advancing/short-history players;
it does not establish causality or justify increasing everybody's probability.

## Fixed comparison

Two feature arms, same LightGBM settings, population, targets and identity weights
as hitter-detail-arrival-v1:

- R: the existing 886-feature rich challenger, unchanged.
- H: R plus compact observed-history summaries. For each snapshot, look back at
  most three calendar years, use only seasons with actual positive recorded PA,
  and retain the elapsed time. Add prior exposure/observed-season count, time
  since the last observed season, PA-weighted batting rates for the prior window
  and current-plus-prior window, and exposure-weighted level history. Calendar
  recency weight is fixed at 0.7^years elapsed, not tuned. Also add continuous
  advancement x age and advancement x current log-PA interactions. No synthetic
  2020 stats; all existing exact-calendar lags and missingness indicators remain.
  These are summaries, not injury diagnoses or minor-to-major rate translations.

For each, report raw and calibrated probabilities (R, RC, H, HC). HC is the primary
candidate; the other arms are mechanism checks, not a menu for post-hoc deployment.
Calibration is a monotone logistic intercept/slope transform of raw log odds,
penalized toward the identity transform with fixed penalty 10. Fit only to
never-debuted prospects' out-of-time predictions whose complete target windows
have matured by the current cutoff. Use the latest five eligible origins,
equal-origin weights scaled to mean row weight one, at least three origins and
20 positive/20 negative outcomes. Otherwise retain raw probabilities and record
the fallback. No calibration on the current cohort's totals or outcomes. Other
cohorts retain raw probabilities. Calibration can repair confidence but not the
within-year prospect ordering. Logit slope constrained to [0.05, 5].

## Chronology and outcomes

Main next-year tests: 2017, 2018, 2021–2024. Three-year tests: 2021/2022.
Targets: any MLB PA next year; any MLB PA in three years; >=450 PA in at least
two of three years. Preserve all zeros and exclude incomplete targets.
Generate auxiliary raw out-of-time forecasts from 2013 onward to supply earlier
calibration observations; train each using only labels mature at that origin.
Exclude windows crossing 2020 from training/calibration. Report 2019 three-year
forecasts separately as pandemic stress, never pool into the main score.
The 2021/2022 three-year calibrators have no post-pandemic mature outcomes; an
era shock cannot be learned from unavailable examples. Prior feature recipes and
auxiliary materializations remain inherited development limitations.

## Scoring and decision

Primary: never-debuted prospects, equal-origin Brier and log loss, pooled event
counts, annual scores, calibration bins, within-origin top-5% and top-10% recall.
Paired 2,000 player-cluster bootstrap intervals (seed 417); these do not capture
all season-level dependence. Always report 2021 separately and all other years
combined. Audit age<=23 advancing players, current PA<400, first season at level,
substantial repeats, partial-promotion returns, and upper/lower prospects with
full group denominators. Groups overlap and are descriptive, not extra winners.

Compare HC against R, B2 tree/logistic and the stronger existing probability
ensemble on exactly shared keys. For a supported next-year improvement require
both proper scores to improve against R with upper paired 95% differences <0,
a majority of origins improving, expected/observed in [0.75,1.25], no >10% harm
in supported upper/lower groups (>=200 rows and 30 events), and both scores better
than B2 tree and the ensemble on matched available rows. Otherwise no upgrade.
Three-year evidence remains exploratory (<3 ordinary origins, only 31 regular
events); no probability-only result authorizes a delivered-value or WAR claim.

Freeze plan/code/input hashes before fitting. Unit-test exact prior-only history,
gaps, unavailable vs zero data, calibration maturity/support, monotonicity and
future-label invariance. Refit 2022 regular H after mutating unavailable future
labels/predictors; require identical raw and calibrated predictions. Verify the
original frozen forecast seal. Save forecasts, calibration coefficients/support,
metrics and a concise result note. Do not retune after seeing this run.
