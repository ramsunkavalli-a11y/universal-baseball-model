# Outcome-complete ground-ball ledger v2: source contract

2026-09-26. Accounting repair only; no player-skill fits or forecast updates.
Freeze this specification before the full ledger and source comparisons run.

## Population and source handling

Read the 244 existing terminal partitions for 2016–2019 and 2021–2024 only.
The population is archived regular-season PBP, NOT all scheduled games. Retain
every game/PA key with a ground-ball label in ANY overlapping source. Keep all
versions of those keys when checking conflicts. Null plus one known value is
non-null consensus; two different known values are a conflict, not permission
to choose the first. Preserve conflicts, bunts, FC, errors, pitcher/1B touches,
and unknown outcomes as rows. Do not treat missing outcomes as outs or hits.
Retain source paths/hashes and per-field conflict names. Team/level/park/handedness
are context, not adjustments already applied. Lineups are archived terminal
identities, not individually event-time-certified for every historical game.

## Three deliberately different views

1. A ball ledger contains one ball, its outcome and all nine fielders. This is
   shared lineup exposure, not nine independent chances or nine copies of credit.
2. Reproduce the old first-touch selection on the same union of source keys.
   Count through hits, pitcher chances, FC and unknowns that it could not measure.
   Preserve its exact original behavior, including first-copy conflict handling,
   in a separately named legacy column; never silently repair its denominator.
3. A fixed Total-Zone-inspired accounting benchmark allocates a known IF touch to
   that position; through singles to adjacent pairs (LF=3B/SS, CF=SS/2B,
   RF=2B/1B); through doubles/triples to the corresponding corner IF for LF/RF.
   CF extra-base hits remain unassigned. Through errors remain unassigned because
   a recovery location does not identify the charged error or range responsibility.
   Bunts, FC, source conflicts and unsupported combinations remain unassigned.
   Include pitcher and catcher touches. Equal splitting of singles is OUR explicit
   benchmark assumption, not a published numerical estimate. Keep the entire
   inferred share as an unassigned sensitivity; no fitted transport weights yet.

Every benchmark row sums to one INCLUDING unassigned mass. Store unresolved
player IDs separately from unresolved position. A first touch is an observed
handler, not proof of pre-play responsibility. Coordinates are retained but must
not be called interception locations, ball difficulty or a certified range target.

Sean Smith's [primary Total Zone description](https://www.baseball-reference.com/about/total_zone.shtml)
distinguishes adjacent infield shares for singles from corner responsibility for
ground-ball extra-base hits. Our earlier sample candidate treated both alike;
v2 corrects that benchmark distinction and explicitly leaves uncertain cases open.
Lichtman's [UZR primer](https://blogs.fangraphs.com/the-fangraphs-uzr-primer/) bases
range on comparable ball opportunities, not merely the identity of the eventual
handler. Neither source certifies our recording precision or allocation weights.

## Checks and decision, not a new modeling contest

- All union keys survive exactly once; conservation and unknowns are checked.
- Compare structured final in-play events in the already selected 256 historical
  feeds: GB key coverage, outcome confusion (including unknowns), recorded
  first-touch positions. Report absent/extra keys and all disagreements, by era
  and level. These are source diagnostics, not new independent predictive tests.
- Report old/new denominators by outcome, year, level and attribution basis;
  do not report aggregate agreement alone.
- Keep the frozen timeline validation result (127/128 reconstructed games) intact.
  A delayed substitution in the remaining game is not retrospectively repaired.
- Outcome completeness within the archive may pass while named range measurement
  remains unsupported. In that case close the accounting repair with the exact
  blocker; do not claim the defensive skill failed or launch an unjustified refit.
- Source decision precedes any persistence/transport preregistration. Those tests
  must distinguish park/level movers from returners, use identical covered games
  for old/new contrasts and include a population-coverage sensitivity. No automatic
  fitting here. Runner-at-risk/pitch exposure still needs its own catcher gate.
