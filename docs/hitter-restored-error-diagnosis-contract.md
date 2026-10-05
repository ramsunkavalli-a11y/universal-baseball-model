# Diagnose the remaining hitting and delivered value gap

2026-10-05. Prospective specification for a diagnosis of saved forecasts only.
No model will be fitted, no forecast changed and no 2026 outcome opened.

The seven restored MLB event inputs improved the otherwise identical model,
but delivered batting value still narrowly loses to the incumbent. This check
asks where that remaining difference comes from, rather than assuming the older
count-model diagnosis still applies. Delivered value here means next-calendar-year
MLB batting plus replacement in win units, not fielding, full WAR, club control
or trade value. Observed hitting is defined only for players with MLB PA.

## Fixed evidence and population

Use the sealed seven-input comparison: all 30,506 original forecasts at origins
2016, 2017, 2018 and 2021 through 2024. Keep every non-arrival. Report the thirteen
source additions separately because they lack an incumbent forecast. Target
seasons end in 2025; canceled 2020 is absent. The completed one-time 2026 evaluation
and explorer remain unchanged. Verify the completed source, model, prediction,
walkthrough and public-report hashes before using them. Independently reconstruct
MLB target PA, batting labels and forecast-value equations from the dated stints.

Primary contrast is seven-input `components` versus unchanged `current`.
Secondary contrast is `components` versus matched four-summary `restored`.
All arms use exactly the same expected PA. Do not choose whichever arm wins in
a subgroup, combine forecasts, remove an outlier or search new priors/features.

## Origin known profiles and exact attribution

Reconstruct recent MLB exposure from source counts at origin, origin minus one
and origin minus two, with fixed weights 1, 0.8 and 0.6. Cross three groups
(no MLB PA, positive but below 600 weighted PA, at least 600) with presence or
absence of observed recent NPB/KBO PA. These six cells partition the original
population; empty cells remain explicit. Verify source season coverage and
compare reconstructed memberships against the earlier saved source-only diagnosis.
Do not infer source membership from future outcomes. A source absence is not
proof that all international history is available.

Each original row retains its global delivered-score weight
`1 / (7 * number of original rows at its origin)`. Each active row retains its
global hitting-score weight `actual PA / (7 * actual PA at its origin)`.
Group contributions must sum back to the same headline MSE difference. Do not
add independently reweighted subgroup scores, or add different overlapping
partitions to one another. Also partition by origin and active versus non-arrival.
Include raw PA and value totals, distinct players and active distinct players.

For an active player, write the delivered error as two exact terms:

- Hitting error at expected PA: `T = expected PA * (predicted rate - actual rate) / 600`.
- Opportunity error at observed hitting: `O = (expected PA - actual PA) * (actual rate / 600 + replacement)`.

Thus `error = T + O`. With PA unchanged, the squared-error difference is
`new T squared - old T squared + 2 * O * (new T - old T)`.
For a non-arrival, compare squared predicted value directly; do not invent an
observed hitting rate. Recompute these equations independently of the existing
geometry helper and check every row and partition. Opportunity error is common
to the arms, but its interaction with changed hitting can improve or worsen the
delivered score. These terms are an accounting identity, not causal attribution
or independent measures of model quality.

## Player review and decision limits

Retain all seventeen sealed source-to-model walkthroughs, including gains,
harms, false highs/lows, prospects, exits and the ordinary cancellation case.
Reference their immutable actual source counts, adjustments, fitted terms,
probes, joint support and origin-selected comparison players. For every case
show all three forecasts and exact hitting/opportunity error terms, plus both
contrast decompositions. No newly selected individual is used to justify a
modeling decision without an equally complete source-to-model walk.

Complete a readable result and player review before selecting the next fit.
Use the six exhaustive cells to locate the gap, not to create favorable-cohort
deployment rules. Previously saved paired intervals remain nominal development
evidence; this diagnostic supplies no new independent confirmation or proof of
significance. Keep source integrity, profile support, prediction, reasonability
and deployment separate. A very small near-tie need not warrant another model.
Choose one next investigation only if the source and player evidence supports
it, and state the hypothesis rather than claiming the arithmetic proved a cause.
