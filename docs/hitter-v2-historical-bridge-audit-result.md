# Hitter v2 historical bridge-support audit result

Date: 2026-08-26

Scientific result: the older data contain substantial same-player support, but
the missing 2020 MiLB season still prevents a clean adjacent-year bridge across
all affiliated levels. No model was fit or scored.

## 2019 MLB source certification

The 2019 MLB lane passed before entering the bridge. Its 49 schedule-bounded
Savant captures produced 186,517 plate appearances across 51,646 player-game
rows and 990 players. Outcome accounting reconciles exactly to official season
totals with zero mismatch rows. Four extra observed physical contacts remain a
declared diagnostic and do not change terminal-outcome or PA accounting.

The first run failed closed because current Savant displays 2019 Oakland as
`ATH`, while the season-specific official authority uses `OAK`. The correction
added only an explicit 2019 alias; unknown teams still fail closed. The failed
execution remains recorded in
`docs/hitter-v2-historical-mlb-2019-execution-incident.json`.

## Bridge support

The audit used integer player IDs only and retained each level stint. It found:

- 574 matched players from 2019 to 2020, with 256,740 origin PA and 65,816
  destination PA;
- 539 matched players from 2020 to 2021, covering 92.77% of the shortened-season
  2020 MLB population;
- 2,854 players reappearing from 2019 to 2021, with 747,171 origin PA and
  640,162 destination PA;
- 402 model-ready 2019 minor leaguers reaching MLB in 2020 and 608 reaching MLB
  in 2021; and
- 534 players present in all three observed seasons.

The 2019-to-2021 link is a two-year reappearance, not an adjacent-season pair.
It is permanently labeled as such and cannot be supplied to an adjacent-year
fitter. Multi-level player-seasons are labeled ambiguous rather than forced
into a favorable promotion or demotion category.

## What this establishes

The history is useful enough to justify a carefully preregistered experiment:
it adds real prior exposure and a meaningful set of MiLB-to-MLB transitions.
It does not solve everything. The only observed 2020 destination is MLB, so the
data cannot independently estimate every one-year MiLB level transition across
the pandemic gap. The shortened 2020 schedule also leaves 241 of 539 matched
2020 origins below 100 PA.

Accordingly, historical model use remains closed. A defensible next gate is
either more pre-2020 source history, which creates ordinary adjacent MiLB
seasons, or a frozen gap-aware integration experiment that treats 2020 MiLB as
missing, uses the two-year bridge only for explicitly declared purposes, and
defines the Marcel comparison before fitting.

## Provenance and exact stop

The generated 2019 MLB report SHA-256 is
`29ab0ad94330b89af769846ae31ae9601ed96b17a29e817986899ca264b80365`.
The generated bridge report SHA-256 is
`2768568fd9f50078cc8f31394b296230fb3d186348f992948345085cc433ceed`.

No offensive target was scored, no candidate was fit, no protected 2026
payload was opened, and no historical artifact is yet authorized as a model
predictor. Stop for review.

Canonical lint passed and all 1,021 repository tests passed. The first full
test invocation recorded 1,001 passes and 20 setup errors because pytest could
not read its default Windows temporary root; the identical suite passed after
its temporary directory was explicitly placed in the writable workspace.
