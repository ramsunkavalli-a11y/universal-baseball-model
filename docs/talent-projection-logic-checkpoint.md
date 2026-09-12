# Talent projection logic checkpoint

Last updated: 2026-09-12  
Status: **NEAR-TERM RATE SEPARATED FROM PEAK TALENT**

## What is now solid

- Present talent is translated to an MLB environment and heavily regressed for sparse
  evidence.
- Strikeout, walk, contact and power remain separate components.
- One- and two-year component changes beat unchanged talent in every later replay, with
  paired-player uncertainty support.
- The two-year pitcher model correctly falls back to the simpler age/level form when
  richer component interactions do not win broadly.
- MLB hitter development is disabled because it loses both scores in every replay.
- Playing time, organization, contract and public FV are absent from talent fitting.

## What the current inspection caught

The first current application ranked near-term translated rate. It therefore placed
many legitimate teenage prospects near the bottom: even an excellent 18-year-old may
still be far below MLB quality at age 20. This was not a useful universal talent rank.
The generated output is retained as a diagnostic, but it is not promoted or connected
to player value.

## Binding talent structure

1. **Present rate:** what the player appears capable of now, translated and regressed.
2. **Near-term rate:** direct one- and two-year skill change, with validated subgroup
   guardrails.
3. **Peak talent:** translated age-24-to-26 component quality from historical paths.
4. **Confidence:** evidence amount and historical forecast spread, shown separately.
5. **Missing dimensions:** defense, position/catching, physical tools and scouting-only
   information must remain explicit omissions until supported data exist.

Peak talent—not two-year rate—will drive the next prospect comparison. FanGraphs/MLB
Pipeline can reveal suspicious agreements and disagreements after scoring, but no
outside FV or rank may enter the model.

The first age-to-peak test is now complete. Its crucial corrections are equal-player
fitting/scoring so future workload cannot dominate talent, and a separate hitter
strikeout outcome so contact skill is not buried among other outs. Hitters and pitchers
both pass every later player, uncertainty, and event gate. Under-20 hitters meet the
fixed subgroup breadth rule without a guardrail.
See [the result](age-to-peak-talent-result.md).
