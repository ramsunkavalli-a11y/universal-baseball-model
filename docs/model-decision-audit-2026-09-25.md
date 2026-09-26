# Model audit: what exists, what the evidence says, and what happens next

2026-09-25. **Accounting/decision audit.** The later
[deep review](baseball-methodology-deep-review-2026-09-25.md) adds source and
estimand findings; its [repair program](methodology-repair-program-2026-09-25.md)
now controls the immediate sequence. This audit supersedes older immediate
experiment priorities in the roadmap and older logs, not their historical
results or the locked 2026 contract. No models were fitted, forecasts replaced,
2026 outcomes opened, or dollar values released.

The objective remains independent player projections followed by the value of
acquiring a player's rights. Better prediction of one component is useful, but
does not by itself establish better full-player or trade value.

## The substantive corrections

1. **The new playing-time combination has useful evidence.** Three-year PA RMSE
   is 190.97 versus 193.22 for the existing ensemble, with a favorable paired
   interval. It should not be dismissed because one arbitrary guard failed.
   It is also not ready to deploy: important calibration and joint-distribution
   questions remain.
2. **The value connection is genuinely weaker than an existing reference.**
   Three-year batting/replacement RMSE is 1.210 versus 1.140. The old comparison
   changed both the rate estimate and the accounting formula. It identified a
   weak batting-construction block, not which part caused the weakness.
3. **The lower-minors finding needs context.** Next-year PA RMSE is 9.25 versus
   9.01 across 12,098 player snapshots, with only 45 actual participants. The
   paired MSE difference is +4.465, interval [+0.092, +8.680]. Outside 2021 it is
   +0.098, interval [-3.496, +3.675]. Excluding 2021 is a sensitivity check, not
   permission to drop a difficult season or proclaim success. Years 2 and 3
   have slightly better point errors. This is not universal lower-minors harm.
4. **Better totals can conceal worse allocation.** The older prospect update
   misses about 49,366 prospect PA in the 2021 three-year cohort while assigning
   about 34,193 too many to prior MLB players. Those errors cancel. The new
   combination reduces the MLB over-allocation but still misses prospect
   opportunity. Its total shortfall is 72,770 PA, about 13.5% of that cohort's
   actual PA: a real issue, unlike treating its approximately 392-PA increase
   in average absolute total error versus the ensemble as decisive by itself.
5. **The explorer and the latest research model are different.** The safe
   component connector is in a rejected research package, not the displayed
   six-year forecast. The display still scales every component for 1,093
   repaired rookie-ball players, including selected direct-total position
   forecasts in Year 1 and direct-total running forecasts in Year 3. That
   treats totals as rates without establishing that they are rates. Ratios
   mostly shrink these totals; this is not evidence of widespread explosions.
   The largest individual component change is 0.447 runs in Year 1 and 0.399
   runs in Year 3; summed absolute changes are 114.2 and 120.4 runs. These are
   scaling amounts, not estimated forecast errors or proof that unscaled totals
   are better. The forecast is preserved, and this limitation is now explicit.
6. **Six calendar years are not six years of team control.** The current display
   has no full-control value for any of its 3,907 players. A prospect arriving
   late needs a later tail; existing contracts, service, costs and choices
   require separate paths. The old economics interface is not a validated
   dollar model.

## Exact output map

| Version / output | What is actually calculated | Status and scope |
|---|---|---|
| Original frozen 2026 hitter package | Equal mean of five batting/replacement formulations on supported rows: direct LightGBM; three-part LightGBM; two-part XGBoost, EBM and ridge. Population fallback for 187 players. Separate opportunity output; position, running and catcher additions; general defense neutral. | Locked 3,907-player one-year forecast, 3,720 with the five-member batting stack. Later development did not replace it. |
| Six-year base, September 22 | Existing Year-1 batting ensemble, direct horizon-specific ridge Years 2–3, direct richer ridge Years 4–6; separately fitted opportunity. | 2026–2031 calendar production. Years 5–6 lack pandemic-free complete-path outer tests. |
| Latest delivered package, September 23; explorer 8777 | For never-debuted RK players only, Years 1–3: expected PA = participation probability × conditional PA; batting = expected PA × PA-weighted rate / 600. All seven inherited component totals scaled by new/old PA. Other players and Years 4–6 preserved. | Provisional display; not current F/D/H research. Sources: `report_hitter_arrival_coherence_v1.py::assemble` and its immutable forecast package. |
| Research H, September 25 | F participation × D conditional workload for prospects; E workload for prior MLB players; B elsewhere. Batting = B batting + (H PA − B PA) × horizon-specific rate / 600. | Individual opportunity improves; whole assembly not selected for delivery. |
| Research E vs N | Identical E PA and nonbatting rules. E uses the marginal formula; N uses E PA × independently archived H1 rate / 600. | N is a mandatory stronger batting benchmark, not a promoted full model. |
| Research safe nonbatting connector | Benchmark rate × new PA / 600; selected direct total unchanged; selected neutral stays zero. Expanded value = batting + seven component runs / 10. | Prevents ratio amplification. Does not establish that fixed direct totals and opportunity are jointly coherent. |
| Pitcher development | Separate next-year zero-inclusive defense-independent component value; role-enhanced existing ensemble, opportunity forecast, and explicit unsupported-contact fallbacks. | Not a tested six-year pitcher career/value system. No pitcher changes in this audit. |
| Full-control / economic value | Current display `full_control_value` is null throughout; path/rights interface exists separately. | Unavailable, not zero. No credible dollar ranking inferred from the displayed calendar sum. |

Annual labels measure actual future **MLB** production, not performance at the
player's current minor-league level. Non-arrivals stay in the denominator with
zero MLB outcomes. Players can move levels without being excluded. This is
not proof that transitions are forecast well; transition/cohort tests are needed.

### What the batting target means

`hitter_value_panel.py::build_neutral_mlb_value_targets` uses fixed event weights
for unintentional walks, HBP, singles, doubles, triples and HR. It subtracts the
same season's league weighted rate, converts to batting runs using the fixed
scale, and adds a PA-proportional replacement allocation. At 10 runs per win:

`batting target = (weighted event rate − league rate) × PA / scale / 10
                  + 570 × schedule fraction × PA / league PA`.

`multiyear_hitter_value.py::calendar_targets` adjusts only replacement for
shortened schedules, preserving actual batting production. These are fixed-weight
MLB outcome labels, **not exact published fWAR and not a direct measurement of
park-neutral latent talent**. Context-adjusted predictors do not make these
realized labels context-free. Expanded labels add position, steals, advancement,
general defense, framing, throwing and blocking; first-base receiving and a
separate GIDP-avoidance residual remain outside the ledger.

The full realized batting target sums to its constructed 570-win budget in a
full schedule because batting runs are centered. This is an accounting property,
not independent evidence that predictions are good. Predicted totals need not
equal 570, and expanded totals are not normalized full WAR. Later-year totals
cover today's players, not unobserved future entrants. Organization filters
mean dated affiliation, not future rosters or ownership rights.

### Multiplication: the assumption we should actually test

For active players let W be PA and R the realized rate. Expected production is
`P(active) × E[W R | active] / 600`. Define a PA-weighted rate as
`r_w = E[W R | active] / E[W | active]`. Then multiplying activity probability,
conditional mean PA and this rate is an exact population identity. **It does
not require W and R to be independent.** PA-weighted squared-error rate fitting
targets this ratio when conditioned on the same information.

Actual fitted models can still disagree because their inputs, support,
regularization and clipping differ. The archived two rates in the next test use
PA weights, but the original frozen three-part member uses square-root PA
weights; do not transfer the identity indiscriminately to every member. A rate
learned among MLB participants also does not identify the counterfactual MLB
ability of every player who never arrives. Joint paths are important for
uncertainty and rights decisions, not automatically necessary to improve a mean.

There is a distinct probability/workload consistency problem: E averages a
direct PA member with hurdle members, but reports a separately averaged activity
probability. In 285 historical E records, PA exceeds 750 times that probability
(two retained by H). Under the model's own 750-PA bound these cannot describe one
joint distribution. This does not disprove E's PA point accuracy, but dividing
its mean PA by that probability cannot manufacture a valid conditional career
distribution. This limitation is not the same as the weighted-rate identity.

## Followable research sequence

1. Use the [evidence ledger](model-evidence-ledger-2026-09-25.md) to avoid
   rediscovering winners or rejecting a broad idea from a narrow test.
2. Apply the [decision standard](model-decision-standard.md): identify the
   quantity, fair comparator and inference before interpreting a score.
3. Run only the [fixed batting-connection diagnostic](hitter-value-factorial-v1-plan.md)
   next. Its primary comparison asks whether improved workload helps when
   connected to the strongest archived batting-rate reference. Other fixed
   contrasts locate the source of the previous gap. No new fit is required.
4. After that result, decide whether a rate refit, direct-total reconciliation,
   or participation/workload distribution is the actual bottleneck. Do not
   launch all three or revive the engine tournament by default.
5. Only an adequately validated mean/uncertainty system can underpin longer
   pitcher/hitter paths, service/contract choices and economic valuation.

The display's component scaling needs a separately versioned correction with
historical comparisons, not a silent overwrite of frozen files. Correcting
documentation here is not certifying either the display or the research assembly.

## Reproducible evidence and boundaries

Run `scripts/audit_model_decisions_v1.py` from the repository root. It reads only
archived historical scores/predictions and current forecasts, verifies accounting
identities and input hashes, and writes
`model_artifacts/model-decision-audit-v1-2026-09-25/audit-evidence.json`.
It does not compute the new eight-cell experiment. The JSON includes source
hashes, cohort splits, uncertainty, example players, display rescaling magnitude,
and nested-prediction availability. Tests in `test_model_decision_audit.py`
check the accounting identities and why mean and median scores can disagree.

The match covers 52,181 annual rows. Three-year batting support has 12,891
player-origin rows from 2016/2021/2022; complete expanded support has only 8,308
rows from 2021/2022. Many observations do not substitute for independent seasons.
Older snapshots exist from 2012, but the same E/F/D prediction recipes do not.
They cannot be relabeled as earlier nested forecasts for a new hybrid calibrator.

Existing verifiers check the original frozen package, latest delivered package
and research integration separately. Passing them establishes reproducibility,
scope and accounting checks—not that the model makes sound baseball decisions.

Verification for this milestone: 28 focused tests pass (seven new audit cases).
The frozen forecast's 31 files verify, including the original forecast hash
`d1953a28d35d87d141ecc65ec4b107906edad877982e79c0d3a216245b9e4708`.
The delivered six-year and research integration packages verify unchanged.
