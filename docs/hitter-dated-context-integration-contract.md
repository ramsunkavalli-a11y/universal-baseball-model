# Test corrected preseason inputs before adding foreign performance

2026-10-04. The reviewed preseason ledger now covers every original feature
origin. Before changing talent and workload simultaneously, test its source
corrections in the existing opportunity model. This is the first controlled
step of the planned context-versus-foreign integration, not its completion.
The Japan/Korea performance translation and omitted-player forecasts remain
required next work. This is exposed historical development evidence.

## Fixed population and question

Use all 63,282 original source rows and exactly 30,506 original forecast rows,
the seven origins 2016–2018 and 2021–2024, and the existing five whole-player
folds. Targets are next-calendar-year MLB PA and appearance, including zero
PA exits/non-arrivals. Training labels must be mature at the outer origin and
must not come from target 2020. Keep every original row regardless of support.
The original source is broad; this test does not retroactively approve every
old role or certify a universal hitter population.

The anchor is the current saved preseason opportunity forecast. Corrected
context changes only the 251 existing opportunity inputs, without adding an
employment/retirement flag or reopening the closed team-record topic. Reuse
the exact two shallow histogram-boosting head settings, equal-origin weights,
conditional PA clipping to [1,800] and existing hard-unavailable/retirement
policy. Replay both old heads against their old inputs before accepting each
cell. Do not change or retune settings after looking at results.

## Allowed source corrections

Replace the old year-end requested-list indicator with the returned dated
preseason 40Man-list indicator. A negative returned listing remains a proxy,
not certified absence of reserve rights, retirement, health or employment.
Do not use the ledger's cumulative positive-context flag as current employment:
it can include an earlier event followed by an exit.

If the old domestic position is UNKNOWN, X, I or O, and the dated listing
contains exactly one explicit hitter position from 2 through 10 or Y, with no
pitcher code or source conflict, fill that broad input position and its complete
one-hot representation. Do not overwrite a known domestic position, guess a
specific position from a generic infielder/outfielder hint, or classify a mixed
pitcher/hitter listing as an exclusive hitter. This is an opportunity input,
not validated defensive value.

If and only if original age is imputed/unknown and the reviewed foreign ledger
has one exact birth date plus a hitter/two-way hint, fill age at origin December
31 and rebuild age_centered, age_squared and age_unknown. The existing head uses
origin-age features; January information-date age is recorded separately rather
than silently shifting the age convention of known players. No nationality
adjustment, current profile position or future result becomes an input.

All other inputs, ranking vintages, domestic production and hitting forecasts
remain identical. Every original source row must have an exact unique dated
context join. Future context rows must not alter an earlier origin's features.
Missing foreign history stays unknown and is not inserted as fabricated zero
talent. The foreign counts themselves are not used in this first fit.

## Before fits and scoring

Seal code, source, contracts, old heads and original membership. Reconstruct the
allowed changes, save all seventy participation/active-head preflights before
fitting, and count distinct training people in actual heads by prior debut,
stage, age, current MLB exposure and changed-context/foreign-history profiles.
Save missing/sparse profile and feature-range warnings, not an automatic claim
that a large generic training set supports incoming foreign professionals.

Primary is equal-origin expected-PA MSE over unchanged original membership.
Report RMSE, MAE, bias, totals, Brier and log loss, origins (especially 2021),
current MLB, upper/lower never-debut minors, absent prior-debut players and all
changed-context rows. Retain the exact 2,627 public matched rows and compare PA
to Steamer, with the original 10% RMSE/15% MAE engineering limits unchanged.
Use nominal paired whole-player bootstrap intervals, seed 83, 2,000 resamples.
Do not claim independent confirmation or multiplicity adjustment.

Hitting stays at combined_rate. Secondary delivered contribution is expected
PA times (fixed hitting/600 plus the original schedule-compatible replacement
reference). Score it against next_pa times (next_batting_rate/600 plus that same
replacement reference), the declared season-relative diagnostic. Preserve the
old common-reference next_value separately; do not tune or give forecasts the
realized target environment. This is batting plus replacement, not full WAR.
Show opportunity and hitting error terms and totals; close value can mask two
offsetting errors.

## Player review and disposition

Fixed cases: Hyeseong Kim 2024, Jung Hoo Lee 2024, Ha-Seong Kim 2022, Eric Thames
2016, Judge 2024, Kurtz 2024, Kwan 2021 and Caminero 2024. Include the largest PA
gain/harm, false high/low and an ordinary active forecast. Retain omitted Ohtani
2017, Suzuki 2021, Yoshida 2022 and Lee 2023 as explicit source-only gaps: do not
fabricate an old projection for them. Select four original-population peers by
origin-known age, stage, recent MLB/minor exposure and listing, never outcomes.
Walk actual dated statistics and old/new source inputs through head traces,
raw probability, conditional PA, policy, product and fixed-hitting value to
reality. Explain both beneficial and harmful changes; preserve sparse support.

No next modeling experiment before this walkthrough and separate execution,
support, predictive and baseball dispositions. Retain only a sensible material
gain without meaningful systematic harm; a small pooled win is not model
approval. A failed source-date test does not reject foreign production. The
complete context/foreign/additions comparison remains pending, as do the public
workload gap and the wider hitter objective. No protected 2026 outcome access,
frozen forecast/explorer changes, new college collection or algorithm tournament.
