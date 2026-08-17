# Current Talent Challenger 2 terminal-source checkpoint

Date: 2026-08-17

This checkpoint records the source-only decision for `baseline2_plus_ev_sweet_spot_contact_value_residual_v1`. It does not contain a 2022 model score and does not authorize 2023 evidence.

## Historical reusable source findings

The 2021-22 armstjc MiLB PBP release is usable for terminal contact outcomes after the repo's existing exact-duplicate resolver and source-authority controls.

- The release `events` pitch field is not a reliable PA-result field and must not be used for this target.
- The PA result narrative (`des` / `description`) is repeated on pitch rows and is usable only from the terminal pitch of each PA.
- Duplicate physical pitch keys observed in the historical releases were exact duplicate snapshots under the existing resolver; the dedicated duplicate-resolution audit found zero variant duplicate keys, field conflicts, contact-status conflicts, or result-description conflicts.
- Terminal descriptions classify essentially all ordinary supported contact outcomes. Unsupported/special outcomes remain fail-closed.

## Official terminal-semantics reconciliation

GitHub Actions run `32066089450` sampled 360 terminal PAs across 2021-22 AAA, AA, High-A, Single-A, and Rookie/complex releases and joined them by `game_pk + atBatIndex` to the repo's existing MLB Stats API true-PA adapter.

Source-only results:

- model scoring: **false**;
- 2023 accessed: **false**;
- official PA matches: **360 / 360 (100%)**;
- `force out` narrative phrase -> official `force_out`: **200 / 200**;
- plain fielder's-choice reach -> official `fielders_choice`: **46** sampled PAs;
- fielder's-choice-out reach -> official `fielders_choice_out`: **34** sampled PAs;
- ordinary field-out control -> official `field_out`: **80 / 80**.

The audit's original aggregate gate reported false because its pre-reconciliation narrative fallback treated all explicit fielder's-choice reaches as one frozen group. That is a source-contract bug, not a model-performance result. The corrected frozen source mapping is:

- `force_out` -> `OUT`;
- `fielders_choice_out` -> `OUT`;
- `fielders_choice` -> `FC_REACH`.

The production narrative fallback mirrors those distinctions and remains subordinate to structured official `event_type` whenever official evidence is supplied.

## Accepted source contract

For historical MiLB Challenger-2 contact targets:

1. Resolve overlapping reusable PBP through the existing natural physical-pitch key consensus resolver.
2. Use only regular-season rows and actual league identity from the existing same-game league authority path.
3. Apply the existing participant-identity authority policy before player attribution.
4. Project one terminal pitch per `game_pk + at_bat_index`; earlier fouls/contact pitches may never inherit the PA result.
5. Classify the terminal PA result into the frozen nine groups using the source-reconciled narrative fallback. Unsupported/bunt/special/ambiguous outcomes remain outside the target.
6. Join the terminal outcome only to the exact terminal physical-contact pitch and the existing frozen core contact-bin classifier.
7. Preserve event date, actual league, level group, player identity, participant authority, contact bin, terminal outcome group, and source status in the materialized target table.

No filename-level league substitution, outcome guessing, 2023 evidence, or player/model performance feedback is allowed in this source layer.

## Next gate

The next safe step is deterministic 2021/2022 source materialization using `current_talent_contact_value_materialization.py`, followed by coverage/accounting inspection. Only after that source table is validated may the frozen additive `contact_bin + level_group` comparator and two-feature residual be wired into the 2022 development evaluator. The challenger remains unscored until that explicit development run.
