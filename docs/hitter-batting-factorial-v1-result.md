# Batting connection: the inherited baseline caused most of the apparent failure

2026-09-25. Executes the unchanged
[eight-cell diagnostic](hitter-value-factorial-v1-plan.md). No model refits or
automatic forecast replacement. W from the weighting experiment is NOT used.

## The answer in baseball terms

The earlier integration started with an old batting-value forecast and added
the estimated value of a change in PA. That carries forward an old discrepancy
between the baseline's batting value and the new rate/playing-time estimate.
The fair comparison holds the new PA and rate fixed and asks whether retaining
that discrepancy helps. Here it hurts, substantially, in every complete origin.

That is different from discovering that detailed hitting information or improved
playing-time estimates are useless. Most of the prior total gap was an assembly
problem, not evidence that the richer batting-rate block was inferior.

## Primary test: does improved playing time help at the strongest old connection?

Holding the independent anchor batting rate and product formula fixed, change
only E→H expected PA. Three-year batting-plus-replacement RMSE is **1.13984→1.13999**.
The MSE difference is **+0.000352**, paired player-history 95% interval
**[−0.007088, +0.007650]**, 4,000 draws, seed 1729. Essentially a tie, not evidence
of value improvement. Origin effects: 2016 +0.00852, 2021 −0.00890, 2022 +0.00143.

This target is our constructed batting-plus-replacement measure in WAR-equivalent
units, not independently validated full WAR, trade return, or dollar value.

## All eight fixed cells — no winner selected after looking

Three-year equal-origin batting-value RMSE, all matched players:

| Playing time | Batting-rate block | PA × rate | Old value + value of PA change |
|---|---|---:|---:|
| E: ensemble | Independent anchor | 1.13984 | 1.21130 |
| H: integrated workload | Independent anchor | 1.13999 | 1.21329 |
| E: ensemble | Horizon-specific | 1.13020 | 1.20918 |
| H: integrated workload | Horizon-specific | 1.12944 | 1.21044 |

At fixed H workload and horizon rates, changing only assembly improves
1.21044→1.12944. The extra baseline term increases MSE by 0.18951; it harms
2016, 2021 and 2022 separately (+0.30015, +0.15906, +0.10932). It is not solely a
2021 artifact. Much of the difference is among players with an earlier MLB debut:
their corresponding RMSE is 2.52582 versus 2.33024.

The identity is exact: marginal minus product = `B_value - B_PA * rate / 600`.
It does not depend on the new PA. The archived report separates its squared
magnitude from its cross-error term rather than calling every difference an
aging, workload or talent gain. Product accounting is not universally optimal;
these results concern these fixed baseline residuals and rate blocks.

Horizon-specific rates also beat the anchor under both formulas in this exposed
history. This is a secondary diagnostic, not an independent new rate selection.
The two rate fits differ in training eligibility and seed as well as horizon;
the result cannot be described as a clean test of aging.

## Important remaining weaknesses

With anchor/product, H improves upper-minors prospect RMSE 0.92644→0.91987 but
worsens lower-minors prospects 0.35703→0.36348. The complete prospect population
is essentially tied (0.56939→0.56986). No scope was selected from these results.

Fixed top-ten error-change lists show why PA gains are not automatically value
gains. In the 2016 cohort H reduces already-low batting projections for eventual
strong contributors Cody Bellinger and Ozzie Albies; in 2021 it improves Julio
Rodriguez and Steven Kwan but further underpredicts Corbin Carroll. In 2022 it
improves Michael Busch but increases overpredictions for Endy Rodriguez and
Dustin Harris. These descriptions concern archived predictions/labels, not
unmeasured causal explanations of their careers. No player overrides were made.

The expanded seven-component ledger tells a similar assembly story on its
separate 8,308 complete rows: H/horizon marginal 1.27023 versus product 1.20238.
It is secondary and cannot replace the batting primary test. Direct nonbatting
totals remain fixed; only documented component rate heads respond to PA.

## Component-error interactions: narrower conclusions

For every selected position, running, fielding and catcher component, the report
now decomposes its own error change, interaction with the rest of the forecast,
and combined error. It shows each origin/horizon and changed/unchanged rows.
Several components improve their own targets; throwing and blocking can still
worsen the whole forecast through cross-errors. These existing native-label
components are distinct from the broken all-level PBP catcher experiments.

The earlier OF bridge also required a correction in attribution. Comparing
the **replacement itself** with existing defense, not the whole retained arm
with zero defense, identifies 1,525 changed and 2,404 unchanged players. The
replacement slightly worsens its own component MSE (+0.00000273 on all rows)
and total MSE (+0.00006004). Thus the previous whole arm's component improvement
over neutral defense was not proof that the MiLB replacement helped. Keep that
replacement rejected; measurement work remains justified independently.

## Decision

The large prior batting-value loss is now largely explained by inherited
baseline accounting. Correct the research integration direction toward explicit
PA×rate batting, with independently valid component exposure. Do not call the
minimum-error cell a newly validated production winner, and do not overwrite the
2026 freeze. The primary workload-to-batting transfer remains unresolved.

One justified next integration step is to specify a release candidate with the
explicit product connector, fixed rate/workload choices, and component/label
gates—not another engine tournament or post-hoc horizon blend. Event-time
catcher attribution and fair range responsibility remain separate source work.
Stop this factorial after its report as its contract requires.

52,181 annual rows and 12,891 complete player-origin sums; all three archived
cells reproduced within 1e-12 before new scores. Archive hashes, rate cutoffs,
future-label-independent assembly, identities, and cumulative sums verify.
Artifact: `model_artifacts/hitter-batting-factorial-v1-2026-09-25/`.
