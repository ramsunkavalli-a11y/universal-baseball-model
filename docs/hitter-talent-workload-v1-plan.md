# Does explicitly projected talent improve prospect playing time?

2026-09-23. Fixed before fitting or scoring. Workload-only development test;
no protected 2026 outcomes, live forecasts, value components or explorer changes.

## Question and evidence audit

Compare against the newly selected detailed D workload head, not just older
baselines. D already sees age, level, performance, progression and year-end
40-man status. It does not explicitly see a predicted talent rate or Rule 4
pedigree. Earlier `draft-pedigree-source-and-decision.md` reports useful hitter
arrival/role evidence, but that is not a test of this new conditional-PA model.

The local official draft capture was located in the September 7 checkout at
`reports/generated/draft-history/draft-history.parquet`. It covers 2006 onward.
Use only year, identity, pick number and school class for eligible past drafts.
No signing bonuses, slot dollars, current scouting text, current public grades,
or draft records after a snapshot. The input hash preserves the capture identity;
archive the narrow <=2022 structured extract needed for this experiment.
No certified publication-dated public grade panel has been located here; do not
substitute current FV for historical grades. Absence of a draft match is unknown
entry history, not proof of international signing or low talent.

## Fixed models

Use the repaired 2009–2022 panel and the previous 12 Years 1–3 folds, exact same
training and forecast rows, PA targets and identity weights. Keep F annual
participation probabilities fixed. Only never-debuted minor leaguers change;
all other forecasts remain accepted B. Frozen D and stronger ensemble E are
mandatory references. Refit D once (2021 H1) to verify exact recipe reproduction.

- T: D inputs plus two explicit talent estimates: predicted MLB batting-plus-
  replacement wins per 600 PA in Year 1 and in Year 3, conditional on playing,
  and a support flag for each. These are batting-rate proxies, not full talent,
  future WAR totals, peak ability, scouting grades, or certainty of playing.
- P: D inputs plus matched Rule 4 record, within-draft log-pick quality, high-
  school class, known school class and years since that draft. Latest eligible
  draft per player only; unmatched numeric fields remain missing.
- TP: D plus both packages. **The only primary candidate.** T and P are fixed
  explanatory ablations and cannot be selected to rescue a failed TP.

For each historical snapshot year s, fit the talent heads using only outcomes
that had matured by s. Never fit one talent head at the outer cutoff and use
its in-sample fitted values as historical workload inputs. For a rate horizon k,
use positive PA and finite observed `600 * war_hk / pa_hk` targets, excluding
windows spanning 2020. Weight by observed PA times active-player identity weight;
the label is an observed rate, not predicted total value divided by expected PA.
Require at least 200 active rows and two distinct training origins; otherwise
save missing estimates with a zero support flag. Keep those early workload rows.

Use D's detailed feature package for talent; fixed balanced LightGBM regression,
seed 427, four threads, rate predictions clipped to the existing [-5,10] bound.
Talent excludes new pedigree so its contribution remains identifiable. Fit
workload with the unchanged balanced LightGBM/seed417 recipe and [1,750] PA bound.
No tuning, manual talent bonuses, monotonic constraints, blends or player patches.
Different batting and workload targets allow a compressed talent forecast to
help; because it is built from existing inputs, success is not proof of new data.

The rate head is trained among players with MLB opportunity and is not an
unbiased identification of every non-arriver's latent ability. It also omits
defense and running. Same-player earlier information is allowed chronologically;
these are not cold-player folds. Save nested fit years, label maturity and counts.

## Fixed evaluation and decision

Evaluate all starting prospects, including zero-PA outcomes, using equal-origin
RMSE/MSE, MAE, bias and total PA errors, annually and cumulatively over three
years. Reuse 2016/21/22 for complete cumulative windows. Report upper/lower minors,
under-23 upper minors, each origin, matched/unmatched draft evidence and talent
quintiles defined from cutoff predictions, never realized future talent.

Accept TP as a workload research candidate only if:

1. Cumulative MSE beats both D and E with whole-player paired 97.5% bootstrap
   intervals below zero (2,000 draws, seed417), and improves >=2/3 origins each.
2. It beats D and E on point-estimate MSE in each horizon.
3. Cumulative MAE and absolute cohort-total PA error do not worsen versus D.
4. No >5% MSE harm versus D in supported annual upper/lower/young-upper prospect
   groups or origin cohorts (>=200 rows, >=10 active players).
5. Among prospects with no PA in the complete three-year window, mean predicted
   cumulative PA does not rise by >5% versus D. This checks false optimism.
6. Non-prospect primary forecasts remain exactly unchanged.

Future regulars (>=450 PA in the relevant year), Pena/Duran and large misses are
diagnostics only, not reasons to waive gates. Report conditional errors among
participants separately. The explicit rate package does not predict a regular-
role probability. No participation-score claim follows from this fixed-p test.

Mutation checks: future draft records cannot alter prior features; changing
future rate/PA labels cannot change a nested talent forecast; changing all labels
unavailable at 2021 H3 cannot change nested inputs through 2021 or its TP workload
forecast. Also mutate the held snapshot's own rate labels in a representative
inner fold. Hash-lock code, inputs and plan before fitting. Preserve archive,
run focused tests and prior freeze verification, then commit the milestone.

Historical development exposure and shared season shocks limit inference even
with bootstrap intervals. Failure rejects this encoding/connector, not the
baseball proposition that better prospects tend to earn more opportunities.
