# Player Value v1 WAR literature review

Last updated: 2026-08-19

## Purpose

Record the public-methodology review performed before final Player Value v1 WAR aggregation and preserve the resulting architecture corrections.

This memo is intentionally upstream of final rankings. Its purpose is to prevent convention choices from being selected because they produce preferred player ordering.

## Primary methodology reviewed

### FanGraphs

- Position Player WAR: https://library.fangraphs.com/war/war-position-players/
- Replacement Level: https://library.fangraphs.com/misc/war/replacement-level/
- Positional Adjustment: https://library.fangraphs.com/misc/war/positional-adjustment/
- Complete position-player example: https://library.fangraphs.com/calculating-position-player-war-a-complete-example/

FanGraphs' published position-player framework is:

`WAR = (Batting + Base Running + Fielding + Position + League Adjustment + Replacement) / Runs Per Win`

Its replacement formula allocates 57% of the roughly 1,000 league WAR to position players:

`Replacement Runs = (570 * MLB_games / 2430) * (RunsPerWin / lgPA) * player_PA`

FanGraphs also applies a league adjustment so the above-average run components reconcile to the intended league-average baseline rather than assuming their raw sums are exactly zero.

### Baseball-Reference

- WAR overview: https://www.baseball-reference.com/about/war_explained.shtml
- Position-player details: https://www.baseball-reference.com/about/war_explained_position.shtml
- Runs to wins: https://www.baseball-reference.com/about/war_explained_runs_to_wins.shtml
- WAR glossary: https://www.baseball-reference.com/about/war_explained_glossary.shtml

Baseball-Reference position-player WAR includes:

- batting runs;
- baserunning runs;
- GIDP runs;
- fielding runs;
- positional adjustment;
- replacement runs.

Its overall replacement baseline is also about a .294 winning percentage / 1,000 league WAR, but it currently assigns 59% to position players and 41% to pitchers. The commonly cited 20.5 replacement runs per 600 PA is a modern 162-game position-player multiplier, not a complete statement of final replacement accounting: Baseball-Reference subsequently fine-tunes/re-centers replacement runs to the desired league WAR total.

Baseball-Reference converts runs to wins using player-aware PythagenPat. Player Value v1 retains this as methodology context/sensitivity rather than the binding conversion because the frozen common league-wide RPW preserves a simple additive projected-run decomposition.

### MLB Statcast / Baseball Savant

- Baserunning Run Value: https://baseballsavant.mlb.com/leaderboard/baserunning-run-value

Statcast's public Baserunning Run Value combines stolen-base value and non-steal advancement value. This makes modern MLB baserunning a directly available public run-valued component rather than something that must be inferred only from SB/CS.

## Findings that change Player Value v1

### 1. Replacement level must be reopened

The prior fixed `20.5 runs / 600 projected MLB PA` freeze was too literal a representation of Baseball-Reference methodology.

Decision:

- supersede the fixed 20.5/600 convention for final WAR;
- predeclare the FanGraphs 570-position-player-WAR allocation as the binding candidate;
- use completed certified MLB games, PA, and the frozen league-wide RPW to derive the replacement run rate;
- retain the Baseball-Reference 590-WAR allocation and prior 20.5/600 calculation as sensitivities.

The old implementation/verification remains in the repository for provenance and must not be deleted.

### 2. Baserunning is a missing WAR component

Both major public WAR systems explicitly include baserunning. Omitting it would make the final statistic knowingly incomplete, especially for high-impact runners.

Decision:

Open a baserunning gate before WAR aggregation. Preferred evidence hierarchy to investigate:

1. eligible MLB Statcast Baserunning Run Value / underlying public opportunity data;
2. affiliated MiLB baserunning evidence where comparable advancement data exist;
3. if rich MiLB advancement data are unavailable, SB/CS-based run value as a lower-information fallback;
4. neutral fallback where evidence is insufficient.

GIDP avoidance must be audited in this gate. It may be modeled separately if public opportunity data support a clean implementation; it must not be silently double-counted with batting or baserunning.

### 3. Explicit MLB-reference centering is required

Above-average component systems require a coherent average baseline. FanGraphs explicitly uses a league adjustment; Baseball-Reference likewise centers its average-relative framework.

This project cannot assume its independently constructed batting, Defense, positional, and future baserunning components sum exactly to zero in aggregate.

The universal-DH era makes this particularly important because the fixed FanGraphs positional schedule is not automatically zero-sum when DH exposure is added to the eight fielding positions.

Decision:

After the component definitions are frozen, calculate an **MLB-reference centering adjustment** from a fixed certified MLB reference population, scaled by projected MLB PA. Do **not** center against the loaded universal player/prospect ranking population.

Candidate form:

`Ravg_raw_ref = aggregate(Rbat + Rbr + Rdef + Rpos [+ Rdp if separate])`

`centering_runs_per_pa = -Ravg_raw_ref / aggregate_reference_MLB_PA`

`Rlg_i = projected_expected_mlb_pa_i * centering_runs_per_pa`

The exact component population/exposure semantics must be predeclared before this gate freezes.

### 4. Park adjustment needs an audit, not an automatic extra term

Traditional WAR batting is park-adjusted because observed offensive outcomes inherit park context.

Player Value v1 differs: the batting projection produces a common core-event composition and values it in one pooled MLB RE24 environment. This may already remove much of the park context that conventional wRAA/wRC-based WAR must correct.

Decision:

Before adding any park factor, test whether the frozen batting/current-talent outputs retain systematic park/team residuals. Add a park correction only if a concrete residual-context problem is demonstrated. Avoid double-adjusting a projection that is already effectively park-neutral.

### 5. Runs per win survives the literature review

The frozen FanGraphs/Tango league-wide position-player RPW method remains appropriate:

`RPW = 1.5 * MLB_runs_per_9_innings + 3`

Why retain it:

- public and transparent;
- adapts to the run environment;
- one common conversion preserves additive projected runs;
- avoids making each player's own projected quality alter the divisor.

Baseball-Reference's PythagenPat conversion remains a sensitivity/interpretive comparison.

### 6. Uncertainty should be preserved, but need not block v1 point WAR

WAR is an estimate, and the uncertainty is especially material in a universal MLB+MiLB/prospect ranking model.

Decision for v1:

- preserve component evidence counts, fallback flags, and provenance in final outputs;
- do not over-interpret small WAR differences;
- build formal uncertainty intervals after the point-estimate pipeline is mechanically complete unless an implementation need makes them necessary earlier.

## Revised gate order

Before final WAR aggregation:

1. **Replacement level revision/refreeze** — ACTIVE.
2. **Baserunning / GIDP audit and model** — REQUIRED.
3. **MLB-reference centering** — REQUIRED.
4. **Park-neutrality audit** — REQUIRED; correction only if evidence supports one.
5. Required sensitivities:
   - Baseball-Reference positional schedule;
   - alternate recent certified MLB batting reference when available;
   - replacement 570 vs 590 allocation and legacy 20.5/600 comparison;
   - player-specific/PythagenPat runs-to-wins comparison if practical.
6. WAR aggregation and QA.
7. Formal uncertainty layer after point-estimate v1, unless promoted earlier by evidence.

## Architecture principle

Final position-player Player Value should remain decomposable:

`RAR = Rbat + Rbr + Rdp(if separate) + Rdef + Rpos + Rlg + Rrep`

`WAR = RAR / RPW`

Every term must remain separately persisted. No centering, replacement, or park adjustment may be hidden inside the frozen batting or Defense skill layers.
