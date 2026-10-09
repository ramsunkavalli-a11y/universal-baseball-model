# First base talent with a historical position prior

First-base range history is currently shrunk toward raw zero even though the
native source's observed first-base average is frequently negative. Test one
historical position prior in the same native units. Do not subtract a positional
value adjustment, force a future total, or change the target to make it easier.

This is a bounded correction to the skill baseline, not an attempt to explain
every first-base miss with a constant penalty. The previous bias diagnosis and
all 56 player records must be complete before execution.

## Fixed calculation

At each origin and player-ID-modulo-five held fold, pool qualified native
first-base observations in the latest three calendar seasons. Exclude all
players in that fold. Weight seasons 1, 0.5 and 0.25 and retain actual shortened
2020 exposure. Compute the historical first-base mean in runs per 1500 outs.
Report people, exposure, annual contributions, source cutoff and profile limits.
Require at least 20 distinct reference people and two measured seasons; if not
supported, retain the existing zero prior and mark the fallback.

For the individual player, retain the existing three-year weighted runs and outs
and the unchanged 3000-out prior size. Candidate rate is:

(1500 × individual weighted runs + 3000 × historical first-base mean)
divided by (individual weighted outs + 3000).

Zero history uses the prior estimate with an explicit unknown-talent flag. It
does not become measured first-base ability. No age, recency or prior-size
tuning, extra polynomial, source-type pooling or target centering is allowed.
Other positions and catcher components remain unchanged.

## Main talent comparison

Use the unchanged native-range quality ledger and its origin eligibility:
same-position later MLB range per 1500 outs over the next three calendar years,
at least 1500 outs in two measured seasons, complete follow-up and no missing
positive official same-position exposure. Restrict the focal comparison to first
base without dropping difficult eligible players. Non-arrivals and insufficient
future samples retain unknown quality and remain in the coverage ledger.

Primary origin is 2022 with 2023–2025 measured quality. Report the separate 2021
stress origin and earlier mature origins as development evidence, not additional
independent trials. Keep the zero, original shrunk-history and saved age-calibrated
anchors. Use person-weighted RMSE and MAE, bias, position-age/exposure groups,
origin totals and paired person bootstrap uncertainty with 2000 draws and seed
728028. Do not select another prior or change eligibility after seeing results.

All reference observations must have season at or before the forecast origin;
the held person's entire fold is excluded. This is a contemporaneous empirical
prior, not a fitted learner using earlier future-performance labels. Report that
distinction and preserve the old learner's profile/support flags.

## Separate contribution check

Apply only the first-base rate change to the unchanged outfield-corrected value
ledger. Keep opportunities, batting, position schedule, all other quality
components and native targets identical. Score first-base delivered runs on all
measured rows and actual defenders, then complete defined-defense and custom
expanded value by origin and stage. Keep partial outcomes unknown and all
forecasts present. Do not claim full WAR, six service years or trade value.

Retain the actual-opportunity decomposition to explain whether improved totals
come from a more sensible rate or simply compensating for exposure mistakes.
A league-total gain alone cannot justify adoption if individual quality worsens.

## Player review and disposition

Fixed diagnostic cases are Freeman, Olson, Goldschmidt and Guerrero at origin
2022, Santana at origin 2023, and Wilson at origin 2022. Retain their origin-only
comparison rule from the bias audit. Add the largest quality gain, deterioration,
false high, false low and median-error case when distinct and eligible. Preserve
annual source and label paths, prior arithmetic, support, opportunities and
contribution. Do not treat unmeasured minor comparisons as average talent.

Independently replay references, every changed rate, unchanged rows, label
membership, scores, intervals and named player arithmetic. Retain the candidate
only as a qualified research baseline if it improves measured talent without
serious age/exposure failures; otherwise keep the old anchors and explain the
failure. A small or uncertain gain is not deployment approval. Complete the
player review before another experiment.

No 2026 outcomes, frozen forecast changes or explorer promotion. After this
single comparison, return to compatibility of older measured MLB quality and
supported development/minor-to-MLB evidence. No prior-weight tournament.
