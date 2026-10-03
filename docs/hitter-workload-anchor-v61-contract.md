# Compare demonstrated workload with direct playing time prediction

2026-10-03, before fitting. Test whether keeping demonstrated MLB workload
explicit helps a shallow model avoid pooling healthy regulars, brief debuts and
temporarily absent players into an overly generic playing-time mean.
This is a hypothesis, not a claim that past playing time guarantees a future job.

## Target and fixed population

Predict expected next-calendar-year MLB PA for all 30,506 historical hitter
forecasts. Preserve the 63,282 corrected source rows and 35 chronological,
whole-player cells from V53, including reconstructed origin 2020 but excluding
target 2020. Training outcomes must mature by each cutoff. Retain every exit,
minor leaguer, zero outcome and sparse profile. No protected 2026 data.

Batting talent, replacement accounting and definitive availability policies
are fixed to corrected V53. Delivered offense is the new PA multiplied by that
same hitting-plus-replacement rate; this remains a product approximation, not
full WAR or a joint uncertainty model. Exact public archive dates remain unknown.

## One bounded architecture contrast

For each origin, define an **observed workload reference** as the greatest
MLB PA in its three history years, annualized by 162 divided by that historical
season's completed league-average team games, capped at 800 and floored at 100.
The floor also applies to players with fewer than 100 demonstrated PA. This separates
the short 2020 schedule from low player use. Raw actual counts and cancellation
flags stay unchanged; annualization is a workload reference, not added talent
evidence. Histories with no MLB use receive a numeric reference of 100 PA so
the model can learn adjustment down toward non-arrival or up toward entry.
That 100 is not a prospect forecast or known job, and is fixed without tuning.

Two arms receive exactly the same corrected V53 opportunity inputs, observed
reference and reviewed availability-source fields:

1. Direct control learns next-year PA, the already tried architecture, now
   providing a matched same-information control rather than a new discovery.
2. Anchored challenger learns next-year PA minus the observed reference and
   adds that reference back at prediction. Targets stay in PA units; weights
   and regularization are unchanged. This keeps a player-specific linear
   starting reference outside the trees. The learned correction can remove
   it entirely; a formerly regular player is not forced to remain one.

Both use the same existing histogram regression settings: 250 iterations,
depth three, minimum 30 rows per leaf, learning rate .05, L2 10, no early
stopping, random seed 31, equal-origin weights. No tuning, selected blend,
new learner tournament or manual star adjustments. Bound PA to [0,800] and
report both ends of clipping. Existing permanent/retirement policies remain
identical; unresolved restrictions remain flagged, not backdated permanent bans.

## Corrected information and support

Use the completed V60 observation-state source, not the flawed V59 medical
duration. Add medical coverage, recorded unresolved observation, log possible
absence upper bound, observed PA-window closures, plain roster-return closures,
and captured unresolved nonmedical restriction. Duration is explicitly an upper
bound, not measured missed days or clinical recovery. Unknown medical fields
are neutral-filled only with their coverage flag retained. Offseason return
does not certify a starting job. The original roster input remains a qualified
captured listing, not a guaranteed current contract or organizational right.

For each actual head, save preflight and distinct exposed-player counts BEFORE
fitting. Disable a sparse added status input with fewer than 20 exposed training
people, retaining coverage/reference controls. Report actual training support
by stage, prior debut, age, current workload, demonstrated workload and a
full-current-year absence after prior regular use. Keep unsupported rows scored.
No future outcomes may affect the reference, eligibility or support.

## Evaluation and required reviews

Compare both arms with V53 and each other on equal-year PA squared error,
MAE/bias, delivered offense, public matches, stage/origin totals and major
workload groups. Use the identical 2,627 common current-MLB Steamer/ZiPS rows;
never exclude the public one-PA forecasts to manufacture a win. Nominal
player-cluster paired uncertainty is development evidence, not a fresh holdout.
The declared practical benchmark goals and baseball checks are unchanged.

Fixed diagnostic cases: established Judge 2022, debut Judge 2016, Tatis 2022,
McLain 2024, Lux 2023, Franco 2023, Langford 2023 and Yordan 2022. Add the
largest delivered gain/harm, false high/low and ordinary case for EACH arm
versus V53. Show actual counts, annualization arithmetic, source flags, actual
saved-tree terms, raw/bounded PA, fixed hitting/value and outcomes. Pick peers
from origin-known stage, age, prior/current MLB use and workload reference,
not from subsequent success. No next experiment or disposition before review.

Reject an apparent public gain if it materially breaks prospect/exit allocation
or comes mainly from offsetting errors or excessive clipping. A tiny pooled
gain does not justify an upgrade. If this coherent architecture does not help,
close it; do not retune its floor or peak definition to the reviewed names.
No frozen forecast or deployed explorer promotion is authorized.
