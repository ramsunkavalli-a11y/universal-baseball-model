# Run-Value / Base-Out-State Reuse Audit

**Status:** Foundation design audit  
**Date:** 2026-08-15

## Question

Before assigning run values to the accepted FaBIO-compatible Performance event bins, determine what mature public work already solves for:

- start/end base occupancy;
- start/end outs;
- runs scored on an event;
- runner-only events occurring inside a plate appearance;
- run expectancy / RE24;
- event linear weights;
- league-season normalization.

The goal is to avoid writing a general baseball state machine from scratch if public work already captures the hard edge cases.

## Conclusion

**Do not derive Performance run values directly from the current armstjc pitch rows, and do not write an original RE24 methodology.**

Use a narrow hybrid:

1. retain armstjc as the historical physical-pitch / batted-ball bootstrap;
2. retain official Stats API `allPlays` as PA/result/matchup authority;
3. model the official state-transition layer after the already-solved Chadwick/baseballquery event semantics rather than inventing new rules;
4. use the standard RE24 formula and average event values by league-season FaBIO bin;
5. assign players the **league-typical value of their bin**, not their occurrence's actual contextual RE24.

This preserves the central FaBIO/tRA idea while keeping runner/score context out of the player's individual Performance score.

## Source audit

### 1. armstjc/milb-data-repository

**Role:** historical physical-pitch + Gameday batted-ball bootstrap.  
**Verdict for run-value state:** useful end-state evidence, **not sufficient as the canonical state-transition source**.

The released schema contains fields that look attractive for RE24:

- `outs_when_up`;
- `on_1b`, `on_2b`, `on_3b`;
- `pre_bat_score`, `post_bat_score`;
- `pre_fld_score`, `post_fld_score`.

But code review shows a material semantic mismatch between labels/documentation and parser behavior:

- the source documentation describes `on_1b/on_2b/on_3b` as runners on base at the start of the pitch;
- the parser actually fills those columns from `matchup.postOnFirst`, `postOnSecond`, and `postOnThird`, which are **post-play-sequence** runner states and are repeated on the exported physical-pitch rows;
- `outs_when_up` is copied from each playEvent's `count.outs`, so its exact before/after meaning at terminal contact must be certified rather than assumed;
- the pre/post score columns are PA/play-sequence level values repeated across pitch rows.

More fundamentally, this export intentionally skips non-pitch playEvents and can omit zero-pitch official sequences. Therefore it cannot be the complete ordered state-transition history needed to distinguish a terminal batter event from a stolen base, caught stealing, wild pitch, pickoff, or other runner event occurring inside the same PA.

**Reuse:** keep its post-state/score fields as reconciliation evidence. Do not promote the documented names to canonical start-state semantics.

### 2. Chadwick `cwevent`

**Role:** mature target event semantics and MLB historical validation.  
**Verdict:** strongest reference contract; use as an external validator, not copied production code.

Chadwick's documented event descriptor already exposes the exact concepts we need:

- `OUTS_CT`: outs at event start;
- `EVENT_OUTS_CT`: outs made on the event;
- `BASE1_RUN_ID/BASE2_RUN_ID/BASE3_RUN_ID`: runners at event start;
- `START_BASES_CD`: base state at event start;
- `END_BASES_CD`: base state at event end;
- `START_BAT_SCORE_CT` / `START_FLD_SCORE_CT`;
- `EVENT_RUNS_CT`: runs on the event;
- `FATE_RUNS_CT`: runs scored later in the half inning after the event;
- `PA_NEW_FL` / `PA_TRUNC_FL` for PA boundaries/truncation.

This is a much better conceptual contract than inventing baseball-state field definitions locally.

Chadwick is GPL software. We should use the CLI/output for validation and historical MLB comparison, not copy its C implementation into this project.

### 3. baseballquery (`jso8910/baseballquery`)

**Role:** existing Stats API -> Chadwick-style state reconstruction.  
**Verdict:** highest-value parser precedent for the specific hard problem.

baseballquery's live-season path reconstructs Stats API into Chadwick `cwevent`-like rows. Its `ParsePlateAppearance` logic explicitly:

- collects runner movements by `runners[*].details.playIndex`;
- identifies runner/action events occurring before the terminal PA result;
- recursively/iteratively emits those movements as separate events rather than folding them into the batter's terminal event;
- maintains a live runner state;
- emits `START_BASES_CD`, `END_BASES_CD`, `EVENT_RUNS_CT`, start scores, outs, and event outs;
- then emits the terminal PA/result event.

This directly addresses the contamination problem that a naive PA-start -> PA-end RE24 calculation would have: stolen bases, caught stealings, wild pitches, etc. can happen during a PA and should not automatically change the league run value assigned to K, BB/HBP, or a batted-ball bin.

The package is not a good production dependency for this project because it is intentionally coupled to MLB, Retrosheet IDs, full Chadwick-compatible output, SQLite, and its own stats/query framework. Its own documentation also calls out rare Stats API reconstruction ambiguities around ROE/FC, fielding credit, and responsibility.

However, its algorithm is a strong public implementation precedent. Package metadata declares an MIT license.

**Reuse:** adapt the minimal state-transition ideas and test fixtures/edge-case vocabulary, not the full package architecture.

### 4. baseballr

**Role:** public RE24 / linear-weight formula reference and secondary implementation cross-check.  
**Verdict:** reuse the methodology, not its state extraction as our universal canonical layer.

`run_expectancy_code()` implements the familiar 24-state process and computes:

`RE24 = runs_scored + RE_after - RE_before`

`linear_weights_savant()` then averages RE24 by event type to produce event linear weights.

That is exactly the class of transform needed after we have certified state transitions.

Its Savant implementation is intentionally much simpler than the state machine we need: it operates on Statcast rows, chooses final-pitch rows at PA level, uses `lead()` to form the next state, and derives runs scored from description text. That is useful as an independent numerical cross-check, but it should not define universal MiLB state semantics.

`mlb_pbp()` itself is also useful precedent because it preserves all Stats API `playEvents` rather than only physical pitches.

### 5. tRA / StatCorner and FaBIO

**Role:** methodological precedent for the Performance value layer.  
**Verdict:** directly supports league-average event run values.

The tRA construction is:

`play_run_value = runs_scored + (run_expectancy_after - run_expectancy_before)`

then average the value of each play type and charge a pitcher according to the frequency of those outcomes. StatCorner explicitly notes a small baserunning correction.

Matt Collier describes FaBIO as following the tERA/tRA philosophy: every PA is placed in one of the 12 bins and the pitcher is charged the **league-typical runs expectancy value per occurrence** for that bin.

This is important: the player should not receive the actual RE24 of his own occurrence. Actual RE24 is an ingredient for estimating the **league bin weight**. Once the bin weight is estimated, every occurrence in that league-season receives the same bin value. That removes the player's own starting baserunner context, runner quality, defense, and realized hit/out luck from the Performance score while preserving the league-typical consequence of the contact type/direction.

## Proposed state/value architecture

### A. Canonical state-transition grain

Add an official-derived `game_event` / `state_transition` grain below `play_sequence`:

`game -> play_sequence -> 1..N state transitions`

A transition may be:

- runner-only / baserunning event;
- pitch-related runner event;
- terminal PA result;
- official non-PA action that changes base/out/score state.

Each transition should minimally carry:

- game / sequence / ordered event index;
- whether it is the terminal PA result;
- structured official event type;
- start outs and end outs;
- start base-state code and end base-state code;
- runs scored on transition;
- batting-side score before/after;
- associated batter/pitcher where meaningful;
- source snapshot / normalization provenance;
- quality flags for ambiguous runner movements.

The target semantics should match Chadwick's `OUTS_CT`, `EVENT_OUTS_CT`, `START_BASES_CD`, `END_BASES_CD`, and `EVENT_RUNS_CT` closely enough that MLB games can be compared directly.

### B. Run-expectancy matrix

Estimate a 24-state matrix from state-transition history by competition/season where sample size supports it:

`RE(base_state, outs) = mean(runs remaining in half inning from that state)`

The inning-ending state has RE = 0.

Primary calibration should be **league/competition-season**, not one global MiLB table. PCL vs International League, ACL/FCL/DSL, and historical run environments can differ materially.

Small-sample competition-seasons should not get unstable independent matrices. The eventual production estimator should shrink/fallback hierarchically toward level-season and broader affiliated-season environments. The exact pooling rule is a later calibration decision, not an ingestion decision.

### C. Raw transition value

For each transition:

`transition_re24 = runs_on_event + RE(end_state) - RE(start_state)`

This is an empirical ingredient, not yet a player score.

### D. FaBIO bin weight

For each eligible terminal PA event, join its accepted Performance bin and estimate:

`bin_run_value = mean(transition_re24 | league-season, FaBIO bin)`

Potential batter-side splits can be tested later; do not fragment the first estimator unless out-of-time stability demonstrates value.

Bunts/foul-air/special events remain outside the 12-bin core and get explicit accounting rather than being forced into a bin.

### E. Player Performance value

Each player's occurrence receives the appropriate **league-season bin_run_value**, not its actual transition RE24.

For hitters, positive run value is favorable. For pitchers, signs can be inverted into runs avoided or an ERA-like expected-runs rate later. The underlying event-value table should remain offense-positive and role-neutral.

This separation is important:

- observed transition RE24 estimates what the bin is typically worth in that environment;
- the player score depends on the bin he produced/allowed, not the actual contextual outcome of his specific play.

## Why PA-start -> PA-end is not good enough

A runner can steal, be caught stealing, advance on a wild pitch/passed ball, or be picked off during a PA. If the entire PA is treated as one state transition, those independent runner events contaminate the value assigned to the terminal K, BB/HBP, or batted-ball bin.

The contamination is not necessarily random: longer PAs create more opportunities for runner events, so BB/K bins could be biased differently from contact bins.

The baseballquery implementation demonstrates that the Stats API contains enough `playIndex` information to split these movements before the terminal event. We should use that solved structure rather than accept the simpler PA-wide approximation.

## What not to reuse blindly

- **armstjc `on_1b/on_2b/on_3b` names:** parser code shows they are post-sequence state, not the documented pitch-start state.
- **armstjc `outs_when_up`:** certify exact terminal semantics before using it as start or end outs.
- **baseballr PA-level `lead()` state logic:** good numerical precedent, not sufficient for exact runner-event attribution.
- **actual player occurrence RE24 as Performance score:** too contextual and contrary to the FaBIO/tRA league-average-bin idea.
- **one global run-expectancy matrix:** obscures large league/era run-environment differences.

## Next certification gate

Before implementing a production state parser:

1. live-audit armstjc `on_*`, outs, and pre/post score fields against official Stats API states;
2. quantify how often a true PA has runner movements before the terminal event, proving the size of the PA-wide contamination problem;
3. build a very small Stats API state-transition POC modeled after baseballquery/Chadwick semantics;
4. on MLB games, compare that POC to Chadwick/Retrosheet start/end base state, outs, and event runs where feasible;
5. on representative MiLB games including DSL/complex, reconcile transition-level end states and inning runs back to the official feed;
6. only then freeze the canonical state-transition schema and first league-season RE24 estimator.

No production backfill or player run-value score should precede this gate.
