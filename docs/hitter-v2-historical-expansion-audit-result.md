# Hitter v2 historical expansion audit result

Date: 2026-08-25

Scientific result: representative MiLB compatibility passed; full historical
materialization and model use remain unauthorized

## Outcome

The existing Hitter v2 cleanup and fail-closed accounting architecture works on
the bounded historical sample. All nine regular-season PBP/player-game pairs
from 2017-2019 passed the compatibility audit. The sample contained 292,669 PBP
rows, 91,680 terminal PAs, and 91,274 official PA. Every regular-season PBP game
had unique same-game league authority.

This result does **not** show that older history improves projections. No model
was fit or scored, no full season was materialized, and no protected 2026
outcome or participant payload was opened.

## What the source audit found

- **2019 is the best first expansion season.** PBP and player-game periods align
  at AAA, AA, High-A, A, and rookie. All five representative level pairs passed.
- **2017 is also structurally promising.** All five levels have period parity;
  the AAA and rookie boundary samples passed.
- **2018 needs a split policy.** AAA and AA have full paired periods and their
  samples passed. High-A and A have only one paired period out of six, and
  rookie has one out of four, so those lower-level cells are not acceptable for
  a full initial backfill.
- **2020 has two different meanings.** MLB played a shortened season that needs
  its own source certification. MiLB had no affiliated season, so the universal
  history must preserve a gap rather than create zero rows or zero talent.

## Cleanup lessons confirmed

The older PBP has the same 103-column shape seen in the newer audit and required
18 declared misspelling-alias actions across nine files. The natural pitch key
contained 2,737 repeated rows and the terminal projection found 1,051 repeated
terminal snapshots; the existing logic collapsed these without inventing extra
events. No terminal description was missing in the selected samples.

The player-game authority resolved 78,672 rows by consensus and 19 by the
predeclared component-wise dominance rule. One 2019 rookie row had conflicting
positive-PA team identity and remained failed closed. That is the desired
behavior: preserve the conflict instead of choosing a convenient team.

The smallest 2019 metadata files also exposed an important selection trap. AAA
March was exhibition-only, while AAA October and rookie September were
postseason-only. Filename period and level therefore cannot imply regular-season
scope; `game_type` must remain an explicit gate.

## What is and is not ready

Ready for review:

- the historical source contract;
- a repeatable bounded compatibility auditor;
- a defensible expansion order of 2019, then 2017, with 2018 AAA/AA conditional;
- a separate 2020 MLB certification lane.

Not ready or authorized:

- full-season historical materialization;
- historical translations, aging estimates, or component priors;
- any new candidate fit or comparison with Marcel;
- protected 2026 access, tracking fusion, Stage 3, or WAR.

## Exact next gate

After review, the next statistically sensible gate is a separate authorization
to materialize and reconcile full 2019 MiLB history and independently certify
the 2020 MLB source. It should remain source-only. Model use should be frozen in
a later contract only after coverage, exception rates, chronology, and hashes
for those full artifacts are known.

Generated evidence is intentionally ignored by git and pinned in the companion
JSON record:

- inventory report SHA-256:
  `91e6cc5f7ff777eb574f0bbdcefe714fc5aab01b7852826e8386fff51f23c492`;
- representative audit report SHA-256:
  `f576586d0404328e3774eaf294c7b853a7703441dbe14e4e3d3e3c7fb2b5e731`.

Canonical lint passed and the full repository suite passed all 1,007 tests.
