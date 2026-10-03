# Dated status did not earn a playing-time upgrade

2026-10-03. Corrected V53 remains the historical research baseline. The hitter
goal remains active. No protected 2026 outcome, frozen forecast or deployed
explorer was changed.

## What was actually compared

The [pre-fit contract](practical-hitter-opportunity-status-v59-contract.md)
kept batting talent, chronology, player folds and all 30,506 evaluation rows
fixed. Ten captured, cutoff-known transaction/availability inputs were added
to the existing appearance and conditional-PA models. All 70 fitted heads
were saved and replayed. Rare inputs needed 20 exposed training people in
the actual head; that rule left the full-medical-absence input disabled.
Coverage controls distinguish unavailable observations from a clean record.

| Identical population | Corrected baseline | Status addition | Meaning |
| --- | ---: | ---: | --- |
| All hitters, PA RMSE | 60.686 | 60.595 | Tiny change; mostly non-arrivals |
| Public matches, PA RMSE | 138.488 | 138.375 | Essentially unchanged |
| Public matches, PA MAE | 106.871 | 106.911 | Slightly worse; Steamer is 92.083 |
| Public matches, offense-value RMSE | 1.06136 | 1.06185 | Slightly worse |
| Absent former regulars, PA RMSE | 168.029 | 166.110 | Modest slice improvement, not a whole-model win |

Public matches are the same 2,627 rows with current MLB PA and both public
systems present. Public snapshot dates remain qualified. Offense value means
batting plus replacement, not full WAR. Nominal whole-player paired intervals
include zero for the all-hitter and public PA changes; historical development
exposure prevents treating them as a fresh confirmatory test.

Cohort errors persist: the 2021-origin forecast supplies about 167,422 PA versus
181,583 actual, while 2023-origin supplies 187,849 versus 182,194. Better pooled
RMSE does not settle those opposite errors.

## The source check changed the interpretation

The saved medical ledger marks 81 source player-years as an open injury spell.
For 47, a certified MLB PA window **entirely after the entry** contains actual
appearances. Among the 72 evaluation player-years with an open spell, 44 meet
that contradiction rule. These are repeated player-years, not 44 independent
people. Some supposed spells persist across later seasons.

Yordan Alvarez's July 2022 placement stays open despite a July 21 reserve-list
activation and 100 September/October PA. Castellanos and Maikel Franco have
later MLB appearances without a recognized return transaction. Merely expanding
the activation text parser would therefore not fix the source completely.

This does **not** prove full clinical recovery. It disproves uninterrupted IL
roster absence. Jarrett Parker's entry is after the PA window, and Garlick's
entry falls inside it: aggregate late PA must not automatically clear either
later injury. Canha has no late PA; absence of appearances does not certify
continued injury. Duration, observed return and medical recovery must be separate.

The candidate is withheld. Its near-null result is not clean evidence that
health information is useless. Both the stale flags and sparse comeback support
limit that interpretation. Mechanical cutoff/replay checks passed; source
meaning did not.

## What the actual player reviews show

Twelve complete forecast reviews and six additional source-to-head reviews
are archived, with actual counts, dated records, intermediate outputs and
origin-known comparison players.

- Tatis: fixed hitting talent is close to his following-year rate, but expected
  PA only moves 35 to 42 versus 635. A temporary interruption is not a permanent
  disappearance; the generic training profile is not comparable suspension support.
- McLain: expected PA moves 174 to 176 versus 577. The full-absence comeback
  feature has no relevant profile support and is disabled. A close offense
  total partly reflects overestimated hitting offsetting underestimated PA.
- Lux: 217 to 224 versus 487. Captured activation helps little; generic inactive
  peers are not a matched surgical-comeback population.
- Franco: 543 to 548 versus zero. An unresolved restriction is not learned as
  a normal active role, but it is also not legitimate to backdate a later ban.
- Langford: 43 to 45 versus 557. His direct status inputs are neutral; this
  small refit change is not newly learned trade, health or prospect evidence.
- Yordan: PA gets closer to reality, while offense gets worse because batting
  talent remains underestimated. The stale open-spell input reduces conditional
  PA by about twenty. A lucky improvement cannot validate a bad source.
- Chris Davis: projected PA near 504 versus 522 is reasonable; the much larger
  error is missing his hitting collapse. Availability cannot solve every miss.
- Waters: projected offense nearly equals actual through offsetting hitting and
  playing-time errors, not through two correct components.

Other reviews include Judge at two cutoffs, Ford and Encarnacion-Strand. Read
[the forecast walkthrough](../reports/model-evidence/practical-hitter-opportunity-status-v59/player-walkthrough.md)
and [the source walkthrough](../reports/model-evidence/practical-hitter-opportunity-status-v59/open-spell-walkthrough.md).

## Next coherent milestone

Repair observation state using dated MLB appearances or explicit bounded-return
evidence; do not label a missing activation as continuing injury, invent an exact
recovery date, or erase all prior absence days. Preserve late-injury controls,
restrictions and unknown coverage. Then compare substantive workload outcomes
(no MLB use, brief/part-time use, regular use), with conditional workload support
and transition uncertainty, rather than another injury-feature penalty sweep.
Batting stays fixed until opportunity makes a material, baseball-plausible gain.

The existing baseline is competitive on qualified matched hitting rates, but
public PA MAE is still about 16% above Steamer and the stated practical target
is not waived. Prospect fast entry, returns and cohort totals remain real gaps.

## Evidence and reproducibility limits

Lean scores, intervals, review records and hashes are in
`reports/model-evidence/practical-hitter-opportunity-status-v59/`.
Large source tables and saved models remain in the generated local evidence.
The experiment reuses local V29/V29b availability runners and their historical
capture dependencies; some pre-existing dependency files are not tracked.
This milestone does not claim that these new files alone reproduce the entire
experiment from a fresh clone. Preserve the executed source hashes and completed
fits; a later source adapter must pass parity checks rather than silently rewrite
this completed experiment.
