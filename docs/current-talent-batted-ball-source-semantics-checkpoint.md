# Current Talent batted-ball source-semantics checkpoint

Last updated: 2026-08-17  
Status: **PROVISIONAL SOURCE-SEMANTICS CHECKPOINT. Corrected contract is predeclared before richer development scoring; deterministic repo tests and tracked-only live MiLB recheck still must pass before historical MiLB materialization.**

## Purpose

This checkpoint records the source-semantic correction discovered while preparing the first richer Current Talent challenger.

It is **not** a model-performance checkpoint:

- no richer residual coefficients were fit from these audits;
- no 2022 future outcomes were scored;
- no B2-vs-richer proper scores were calculated;
- no 2023 confirmation outcomes were inspected or used to select the candidate.

Governing challenger plan: `docs/current-talent-batted-ball-quality-challenger-plan.md`.

## Issue discovered

The first deterministic projection treated every Savant row with complete exit velocity + launch angle as a model batted-ball event and keyed it at player plate-appearance grain.

Inspection of the exact retained certified MLB Savant source cache showed that Savant also reports EV/LA on foul contacts. A plate appearance can therefore contain several complete launch-measurement contacts before the eventual in-play result.

That makes both assumptions wrong for the challenger:

1. complete EV+LA alone is not sufficient to define the model BBE;
2. `game_pk + batter + at_bat_number` is not a unique raw tracked-contact key.

Baseball Savant's standard BBE concept is a batted ball that produces a result. The corrected source contract now uses the result-producing pitch row and retains pitch identity explicitly.

Official glossary: `https://baseballsavant.mlb.com/csv-docs` / Statcast glossary definitions as linked from Baseball Savant.

## Corrected canonical model BBE

A richer-model BBE must have:

- valid game date / game PK / batter / plate appearance / pitch number;
- normalized Savant `type == X`;
- nonblank terminal `events`;
- observed `launch_speed`;
- observed `launch_angle`;
- no explicit `bunt` in the Savant play narrative.

Canonical key:

`game_pk + player_id + at_bat_number + pitch_number`

Fail closed if the corrected source contains:

- a duplicate result-producing pitch key; or
- multiple result-producing BBE for the same player/PA.

Bunts are excluded because the frozen 10-bin Current Talent contact target is non-bunt contact. This reuses the repository's existing explicit Savant bunt-narrative rule rather than creating a new classifier.

Broad source-capability diagnostics remain broader than model BBE and may include foul/contact rows. They operate at pitch grain and are explicitly called **observations**.

## Certified source artifacts used

### 2021 MLB

Workflow run: `31986504169`  
Artifact: `current-talent-historical-mlb-2021`  
Artifact digest: `sha256:8d1aae424cb287c0ae19ce8c6312fdf674ddd68d02d2192a2009941f3ac70363`

The artifact retains the exact raw Savant chunk cache used by the certified MLB Current Talent evidence workflow.

### 2022 MLB

Workflow run: `31988255280`  
Artifact: `current-talent-historical-mlb-2022`  
Artifact digest: `sha256:f376ca20ef40e9906a86118b87a4c6b3934bb6a963c28a226cb9b8b66663be8e`

The same retained-source audit was applied at the three predeclared 2022 development cutoffs. This inspects source/feature availability only; it does not evaluate future predictive performance.

## Source-only audit results

All rows below are strictly before the named cutoff and use the corrected result-producing, non-bunt, complete-EV+LA definition.

| cutoff | corrected BBE | players with BBE | players >=20 BBE | median raw BBE among eligible | median 180d-effective BBE | mean player weighted EV | mean player weighted sweet-spot | result bunts excluded | complete EV/LA foul contacts observed | duplicate pitch keys | multiple result BBE in PA |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2021-07-15 | 65,578 | 797 | 497 | 116 | 94.47 | 88.47 mph | 34.74% | 776 | 60,493 | 0 | 0 |
| 2022-07-15 | 67,923 | 593 | 491 | 130 | 110.04 | 88.28 mph | 34.97% | 544 | 61,267 | 0 | 0 |
| 2022-08-01 | 77,516 | 608 | 504 | 145 | 114.23 | 88.15 mph | 34.87% | 621 | 70,107 | 0 | 0 |
| 2022-09-01 | 98,823 | 643 | 542 | 164 | 127.57 | 88.09 mph | 34.75% | 829 | 89,600 | 0 | 0 |

Interpretation:

- the corrected BBE definition is source-feasible at MLB scale;
- the >=20 rule still retains roughly 500 MLB hitters at the relevant annual/development cutoffs;
- the very large number of complete EV/LA foul rows confirms why complete measurement alone cannot define BBE;
- zero duplicate corrected pitch keys / zero multiple-result PAs across the audited cutoffs support the fail-closed canonical grain;
- excluding explicit bunts is material enough to enforce but does not threaten sample viability.

Do **not** interpret the EV/sweet-spot summary values above as challenger performance or as evidence that these features will improve B2.

## Reproducible repo audit

Added:

- `scripts/audit_current_talent_batted_ball_source_semantics.py`
- `tests/test_current_talent_batted_ball_source_audit.py`

The script:

- reads retained Savant CSV bytes only;
- reports broad complete-contact/foul counts;
- calls the canonical `project_complete_tracked_bbe` implementation;
- applies the same 180-day / >=20 feature builder;
- reports source/feature availability only;
- explicitly records that no model scoring or residual fit was performed.

The manual Minor Savant source workflow now includes the audit unit test in its deterministic preflight test set.

## Verification boundary

This checkpoint remains **provisional** because the newest deterministic commits cannot currently be inspected through GitHub Actions from this session; the connector is denying Actions/check-run reads. The manual tracked-only Minor Savant probe also cannot be dispatched from the available connector.

Therefore:

1. do not call the corrected implementation CI-green yet;
2. do not call the tracked-only MiLB source recheck passed yet;
3. do not bulk-materialize historical MiLB tracking yet;
4. do not fit/score the real richer candidate yet.

## Next gate

1. Run/inspect current deterministic CI.
2. Manually rerun `.github/workflows/current-talent-savant-minors-probe.yml`.
3. Confirm the corrected result-producing/non-bunt projection works on the tiny historical MiLB raw responses and preserves the certified game/player identity/capability picture.
4. If and only if that passes, materialize the minimum 2021–2022 MiLB tracking needed for the fixed richer development protocol while reusing the certified MLB source caches.
