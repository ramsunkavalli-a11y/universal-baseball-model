# Hitter model stopping point and remaining work

2026-10-08. We have an evaluated next-season MLB batting forecast and useful,
separately tested nonbatting components. We do **not** yet have one validated
full hitter WAR model, a dependable defensive grade for every minor leaguer,
or six years of club-control value. Keep the frozen forecast unchanged.

The latest change is small: using the historical first-base average instead of
zero as the starting point lowers the main defensive-talent error by 2.35%.
It barely changes overall player-value accuracy, and several older years get
worse. This closes the agreed first-base test, not the broader defense problem.

## What actually drives the current forecast

The selected 4,030-player forecast estimates next calendar year's MLB hitting,
chance of appearing, and PA if the player appears. Expected PA is the chance
of appearing multiplied by conditional PA. Batting contribution then combines
that expected PA with the hitting rate and a fixed replacement allowance.
It contains **no added defense, position or baserunning runs**. The earlier
partial-WAR and multiyear explorers are different, provisional packages.

| Component | Current construction | Status and important limit |
| --- | --- | --- |
| Hitting before MLB debut | Regularized linear model using level history, translated events, age/profile and dated scouting; 220 inputs | In the frozen forecast; sparse profiles and translation remain qualified |
| Hitting after MLB debut | Regularized linear models with 262 inputs when MLB Statcast is available, 199 without it | In the frozen forecast; availability differs and minor tracking has not earned inclusion |
| MLB participation and PA | Separate histogram gradient-boosted tree models; 251 inputs each | In the frozen forecast; getting the right arrivals and their workload remains difficult |
| Future position | Observed position repertoire, total defensive exposure and transition research | Separate research; current assignment sources improved, but young position changes and allocation remain unresolved |
| MLB range | Recent native measurements with direct sample shrinkage; corrected OF reference; qualified first-base historical prior | Separate research; useful history, not a universal minor-talent grade |
| Catcher framing | Recent native runs divided by received pitches, heavily shrunk | Separate research; useful MLB signal, no supported general minor transfer or fixed long-run ABS value |
| Catcher throwing and blocking | Separate adjusted measurements and actual attempt/blocking denominators | Separate research; uncertain talent gains, missing measurements and young-player reversals remain |
| OF arm and first-base receiving | Recent adjusted runs per actual advancement/throw opportunities | Separate research; modest uncertain gains, particularly limited young-arm and receiving support |
| Running | Separate steal attempts, steal success and extra-base advancement, with opportunity-based shrinkage | Older Years 1–3 research supports useful MLB history; not incorporated in this frozen package or recertified for all levels/horizons |

[The selected-model audit](hitter-candidate-readiness-review.md) verifies the
ordered inputs and fitted-head construction. Its 199-input route has seven MLB
and 91 non-MLB pooled event-rate fields, not 105 minor-rate fields. The
[nonbatting review](nonbatting-hitter-component-review.md) reconciles older
winners and flawed failures without pretending the older assemblies are current.

## What the evidence says

The [completed 2026 evaluation](hitter-final-2026-result.md) used the exact
pre-outcome frozen forecast once. It expected 644.3 participants and 181,374 PA
in its fixed cohort; 655 participated for 182,453 PA. Close totals conceal
misses: never-debuted players delivered 46.24 batting-contribution wins against
27.33 forecast, while previously debuted players delivered 521.33 against
551.40. These are batting plus replacement units, not full WAR.

Among current-MLB players, PA error was 140.66 PA and batting-contribution error
1.0542 wins. Including thousands of non-arrivals lowers the all-player headline
to 64.34 PA and 0.4594 wins; it does not make regular-player error that small.
No matched preseason 2026 ZiPS/Steamer export is in that evaluation. The older
matched playing-time comparison was 138.33 PA error here versus 135.38 for
Steamer, while average absolute error was 106.41 versus 92.08. Those qualified
comparisons do not support a blanket claim that every part is 20% worse.

Three defensive findings are worth retaining without exaggerating them:

- [MLB channel histories](defense-value-v12-result.md) improved delivered
  defined-defense error about 13% against neutral defense in a separate custom
  value assembly. That assembly omits running and is not FanGraphs WAR.
- [Correcting the OF reference before shrinkage](defense-reference-history-v26-result.md)
  lowered measured later-MLB range error from 2.48650 to 2.28984 runs per 500
  innings, about 7.9%. Delivered-defense error improved about 1.6%; custom
  expanded-value improvement was only 0.17% and uncertain. This was an earlier
  result, not a new gain from today's handoff.
- [The locked first-base prior](defense-first-base-prior-v28-result.md) lowered
  main skill error from 1.90843 to 1.86361 runs per 500 innings on 47 measured
  people. Its paired interval excludes zero versus original history, but not
  versus saved age calibration. Older 2017, 2019 and 2021 origins worsen.
  Custom expanded-value error moves only 0.429686 to 0.429614 wins, about
  0.017%, with an interval including no gain. Keep it as qualified research.

These percentages are different comparisons, populations and targets. They
cannot be added together or transferred to the selected 2026 batting package.
All historical defensive comparisons are exposed development evidence.

## Baseball checks that change the interpretation

Toglia's small positive first-base sample projected +0.465 range runs per 500
innings. The new prior reduces that to +0.178 against later pooled −2.402:
better, but still badly wrong. O'Hearn moves from +0.297 to +0.024 against later
+2.226, so the same correction hurts a player who improves. Santana's strong
later range remains underrated; Guerrero's poor range remains understated.
Freeman's pooled-talent estimate improves while his following-season delivered
estimate worsens. The [44 focal and peer calculations](defense-first-base-prior-v28-player-review.md)
retain these distinctions, incomplete outcomes and exits.

Catcher errors also go both ways. Hedges and Bailey are underrated, while
Realmuto is overrated. [The source and opportunity diagnosis](defense-component-bias-v27-result.md)
shows that actual future opportunities do not remove the skill misses. A blanket
catcher penalty would damage genuine positive talent; it is not the first-base
reference correction applied to another position.

Wilson and minor comparison players without measured MLB range still have
unknown skill. A conservative numerical prior and near-zero expected MLB PA
are not proof that their talent estimate is right. Likewise, Lovich's inflated
conditional hitting grade from 26 Single-A PA remains an open batting-reliability
failure; the defense work has not fixed it.

## What is not settled

Minor defensive counts can reflect positioning, pitcher contact mix, scorer
choices and opportunities rather than transferable MLB ability. Recent DSL and
complex cohorts lack mature, comparable MLB-quality training at the available
cutoffs. Failed short-horizon transfer tests do not establish that defense is
unpredictable. [Older measured fielding](defense-older-quality-v24-result.md)
expands potential follow-up, but older conversion credit and modern native range
cannot be pooled as though their units were interchangeable.

[Framing](catcher-framing-talent-v4-result.md),
[throwing and blocking](catcher-throw-block-v5-result.md), and
[arm and receiving](arm-receiving-v6-result.md) have actual opportunity-based
baselines and separate later-quality tests. Most gains remain uncertain; learned
young-age adjustments failed or lacked support. Throwing conditional on attempts
does not establish deterrence. Full ABS removes framing credit in a scenario,
not the same thing as forecasting challenge rules or implementation dates.

Position is not defense quality. [Better repertoire mechanics](defense-repertoire-v9-result.md)
remove invented catcher/other-position time but still miss prospect switches.
[Current-assignment source repairs](defense-role-v16-result.md) improve inputs,
not yet accuracy. The [paired-position diagnostic](probability-and-position-diagnostics-2026-10-08-result.md)
does not justify replacing the positional constants. Position totals and
first-base/framing optimism remain open; forcing a league quota would not prove
the individual forecasts are sensible.

Park/opponent translation is not fully neutral in the selected hitting route.
Foreign entrants remain incompletely covered. Current hitting/value uncertainty
is not a validated joint distribution: multiplying separate means does not
establish dependencies or career upside. Six calendar years are not six service
years; contracts, future entrants and rights/costs are needed for club or trade
value. The old multiyear component gains remain qualified research, not a
replacement selected model.

## The next bounded milestone

Keep the current forecast as a fixed reference. Next resolve the compatibility
of older measured MLB fielding and modern native range before another
minor-to-MLB talent fit. Use overlapping measured people and positions to identify
what can share a scale and what must remain separate; audit mature training
support, including low-level non-arrivals, before fitting. Freeze that contract
before results, retain incompatible/unknown records explicitly, and walk gains,
harms and ordinary cases before deciding whether to keep a bridge. If overlap
is insufficient, preserve separate targets rather than invent a conversion.

This follows the defense plan instead of launching another learner or prior
search. The Lovich reliability defect remains a separate publication gate for
conditional hitting grades. Only after those claims are supportable should a
new full-value candidate assemble batting, workload, roles and nonbatting
components on identical historical players and targets. No automatic promotion,
repeated team-record test or second attempt to pass the opened 2026 season.

## Verified stopping point

The first-base contract, all scores/intervals, source histories and 44 player
records have an independent arithmetic replay. The preceding bias review includes
56 records and additive recovery of omitted channel metadata. Final receipts
link the reviewed narrative to unchanged machine outputs and protected hashes.
The [completion audit](../reports/model-evidence/hitter-stopping-point-2026-10-08/completion-audit.json.gz)
closes this bounded review and handoff only, not the remaining full-model work.
Archive paths remain accessible with D connected; the cleanup preserved all
data and the current forecast/explorer.
