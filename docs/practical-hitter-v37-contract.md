# Empirical MLB event anchor with learned adjustments

2026-10-02. Before fitting. V36's 13 completed player reviews show its naked
logit suppresses established power and learns harmful correlated cross-effects.
This is a bounded structural repair, not changing the penalty until it wins.

## Exact change and target

Use exactly V36's 144 inputs, fixed multinomial likelihood, penalty 0.001,
optimizer settings, training memberships and expected V34 PA. Replace the
league-only logit offset with an own-player empirical MLB event profile:

    anchor = (three-year 1/.8/.6 event counts + 100 * origin league rates)
             / (three-year weighted actual MLB PA + 100)

Eight mutually exclusive event counts include other and reconstruct total PA.
Use actual shortened-season evidence, not schedule-inflated sample size. Missing
MLB competition gives the origin league prior, not invented observations or
an assertion that every prospect is average. Minor history/draft/age remain
available to learned adjustments; their ability to distinguish prospects must
be tested rather than assumed. The 100 prior stays fixed from prior input
stabilization, not tuned against Judge's outcome. Report the anchor-only forecast
as a deterministic reference as well as the fitted correction.

For mature training labels transport the origin anchor's relative odds to the
observed target league environment: normalize(anchor * target league rates /
origin league rates). This distinguishes ball/environment from player effects.
At prediction use the origin anchor, never the future league environment.
Convert all predicted probabilities against the actual completed-origin league
reference, exactly as V36. Known target environment is only a mature training
label offset and scoring reference, not a forecast-time feature.

This repairs the starting estimate, not the missing future health/job information,
park/opponent normalization, international pedigree or calibrated prospect paths.
Expected value remains fixed PA times conditional batting plus replacement;
not full WAR or validated joint uncertainty. No 2026 outcomes/frozen changes.

## Checks and comparison

Same 30,506 test rows and 35 chronological whole-player cells as V34/V36;
target-2020 excluded. Verify eight-event counts, positive/summing-to-one anchors,
zero-effect recovery of the empirical anchor, environment transport identity,
same 144 features and actual prior MLB exposure before fits. Support and target
checks remain; no future outcome drops or outcome-total scaling.

Score conditional rate and delivered value against V34, V33b, V36 and deterministic
anchor-only reference on identical populations. Report each origin/stage,
brief-debut/thin-entry/absence/regular groups and public timing/environment caveats.
PA forecasts are unchanged and cannot satisfy the unresolved PA MAE goal here.
Proper event loss is supplementary, not a replacement for batting-value accuracy.
Persist paired nominal player-cluster intervals and cohort/value totals.

Fixed diagnostics McNeil 2018, Steer 2022, Winn 2023, Kurtz 2024, Judge 2016/2024,
Olson 2022, Lux 2023, McLain 2024, Tatis 2022 and Davis 2017. Add largest gains/
harms, false highs/lows and an ordinary example. Show actual source counts and
exposure, anchor/reliability, learned odds terms, event probabilities, runs
conversion, fixed PA, actual outcomes and origin-only peers. No adoption or
next-model choice until that review is complete. A better component remains
development evidence, not automatic frozen/research explorer promotion.
