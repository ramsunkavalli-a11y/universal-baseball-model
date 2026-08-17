# Current Talent contact-value scale checkpoint

Status: **PASSED — AUTHORITATIVE SOURCE/VALUE-SCALE GATE**  
Date: 2026-08-17

This checkpoint closes the source/value-scale feasibility gate for richer Current Talent challenger 2, `baseline2_plus_ev_sweet_spot_contact_value_residual_v1`.

It does **not** mean challenger 2 has passed development. No 2022 challenger-2 model score and no 2023 richer confirmation score was produced by this gate.

## Authoritative execution

- workflow: `Current Talent contact-value scale audit`
- workflow run: `32056682313`
- accepted attempt: **5**
- artifact: `current-talent-contact-value-scale`
- artifact ID: `9297361481`
- artifact digest: `sha256:4acb317160c506c33311f94956efd8694663c54a05607a7dc54d2f85cb2a3d01`
- Retrosheet 2021 parsed-play archive SHA-256: `6c1503885a22f4fdd4f2195e78905839883406bf7bff5a7e1c11069a6bbde765`
- cutoff: event date strictly before `2021-07-15`
- development/confirmation data used: **false**
- player/model scoring performed: **false**

Machine-readable accepted result:

`docs/current-talent-contact-value-scale-result.json`

## Accepted source checks

- games: **1,348**
- state transitions: **103,534**
- observed base-out states: **24 / 24**
- frozen contact targets: **65,572**
- unsupported target contacts: **0**
- target contacts missing RE24: **0**

The target universe follows the frozen result-producing non-bunt contact semantics. Retrosheet's traditional `bip` flag excludes most over-the-fence home runs, so the accepted adapter defines result-producing contact for this narrow scale as `pa AND (bip OR hr)`, still excluding bunts and sacrifice bunts. This correction was made and regression-tested before accepting the artifact.

## Frozen terminal-outcome values

These values are fixed for the entire challenger-2 2022 development gate. They are event-weighted mean contextual RE24 within each frozen terminal group, using only the pre-2021-07-15 MLB run-expectancy matrix.

| Group | Value | Events |
|---|---:|---:|
| `1B` | 0.4651970407443663 | 13,526 |
| `2B` | 0.7665843002990237 | 4,208 |
| `3B` | 1.0004100521698496 | 352 |
| `HR` | 1.3834396983847337 | 3,193 |
| `ROE` | 0.43273757678346964 | 732 |
| `FC_REACH` | 0.1558534038205505 | 357 |
| `SF` | -0.06260868067734615 | 610 |
| `MULTI_OUT` | -0.8151401718384932 | 2,043 |
| `OUT` | -0.24975231369042597 | 40,551 |

Actual per-event RE24 remains contextual and is **not** a player-talent target. Challenger 2 may use only the frozen group means above as its context-neutral terminal-value scale.

## Superseded attempts

Attempts 1–3 never completed a valid source/value-scale artifact and are not evidence about challenger 2.

Attempt 4 completed but is **rejected** as an authoritative artifact because it used Retrosheet `bip` alone for the target universe and therefore retained only four HR. Artifact inspection caught that mismatch before acceptance.

Attempt 5 corrected the target to include result-producing HR even when `bip=0`, added a regression test, and produced the accepted 3,193-HR / 65,572-contact scale above.

## Next gate

Before any 2022 challenger-2 scoring, deterministic tests must establish:

1. fixed terminal-value assignment and fail-closed unsupported handling;
2. cutoff-safe additive OLS `terminal_value ~ contact_bin + level_group`, with reference `IFFB` / `MLB`;
3. deterministic two-feature no-intercept WLS for the richer player residual;
4. exact richer eligibility/fallback and identical comparator/richer event coverage;
5. no 2023 input in the development evaluator.

Only after those contracts pass should the offline 2022 evaluator be built and run.
