# Phase 1 sequential replay contract

**Status:** frozen implementation gate  
**Date:** 2026-09-09

## Purpose

Prove that the existing player-universe, projection, control and contract-economics
pieces can produce a complete sequence of dated player-value records without hindsight,
dropped players or unexplained value changes. This is the remaining Phase 1 integration
gate. It is not a new component-model search.

## First build

Begin with a small set of completed-season checkpoints. Each checkpoint must contain
every player in its separately frozen rights universe, including review, unknown-rights
and no-incumbent-rights rows. It must persist:

- the as-of date and evidence cutoff;
- replay mode;
- player and dated rights owner;
- last completed game represented;
- model and evidence-bundle versions;
- expected remaining WAR and its bounds;
- expected remaining cost;
- discounted transferable-rights value and its bounds;
- coverage and calculation status.

The replay compares adjacent checkpoints and assigns value movement to observable
categories: new or departed universe member, games added, rights-owner change, contract
evidence change, projection evidence change, model revision, or passage of time. A
material unexplained change fails.

## Temporal boundary

Two modes from the canonical data contract remain distinct:

1. `retrospective_event_cutoff`: current corrected history may be used, but no baseball
   event after the cutoff may enter. This is the practical first build.
2. `vintage_information_set`: every source must also have a defensible public knowledge
   time no later than the cutoff. Null or later knowledge times fail.

The replay must never rename the first mode as a true vintage test. A last-game date or
source maximum event date after the evidence cutoff fails in both modes.

## Mechanical gates

Each checkpoint fails when:

1. its dates, mode, model or evidence-bundle identity are inconsistent;
2. player IDs or player-rights rows are duplicated;
3. its player/owner set differs from the frozen checkpoint universe;
4. a completed-game or source event crosses the evidence cutoff;
5. vintage mode uses missing or future knowledge time;
6. an available row lacks finite WAR, cost or value estimates;
7. lower/upper bounds do not contain the point estimate;
8. a player with no incumbent rights reports transferable value other than zero; or
9. adjacent checkpoints contain a material value change with no classified reason.

Review rows remain present and do not become zero-valued available rows. Small numerical
changes use a declared tolerance and do not require a reason.

## Phase 1 outputs

- validated checkpoint value records;
- an adjacent-checkpoint player delta ledger;
- coverage and review counts by checkpoint;
- league totals for expected remaining WAR, cost and value;
- explicit replay mode and source timing diagnostics.

Forecast accuracy, participation calibration and interval coverage are reported against
later outcomes after the mechanical path passes. Trade prices remain a separate noisy
market comparison, not the definition of correct player value.

## Deferred to Phase 2

- full daily scheduling and publication;
- true vintage claims where no contemporaneous archive exists;
- granular injury, pitch-quality, scouting and buyer-context attribution;
- rescue tuning of component models based on replay outliers.
