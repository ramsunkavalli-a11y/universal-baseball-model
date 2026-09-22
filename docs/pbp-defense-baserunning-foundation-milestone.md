# Historical PBP defense and baserunning foundation milestone

## Outcome

The project now has a shared 2016-2024 minor-league play-by-play foundation for
defense and baserunning. It covers every available playing-season partition at
AAA, AA, High-A, Single-A, Rookie/complex, and the former Short-Season A level.
The missing 2020 minor-league season remains an explicit gap. No 2026 result was
read or used.

This is materially different from the earlier general-defense challenger. The
earlier test used fielding percentage, range factor, errors, and related box
statistics. The new foundation reconstructs the actual ball-in-play, fielder,
runner, park, level, handedness, and base/out opportunity before crediting a
player with a residual.

## Materialized evidence

- Public source assets inventoried: 244
- Nonempty source assets accepted: 238
- Empty boundary placeholders: 6
- Games: 93,249
- First-touch fielding opportunities: 4,219,232
- Non-steal runner opportunities: 912,587
- Physical pitches preserved for catcher work: 23,993,223
- Conservative dirt-ball/block opportunities: 218,316

The materializer streams one source file at a time and keeps compact Parquet
partitions rather than retaining an additional 18 GB raw copy.

## What the chronological tests say

Each test projects a later season from strictly earlier player evidence. Model
form and regression are selected using only older folds. The benchmark is a
neutral projection that treats the returning player as average.

### Infield range

The first model covers ground balls assigned to second base, third base, or
shortstop. Expected out probability adjusts for level, position, batter side,
pitcher hand, park, batter, and coordinate bin before assigning the residual to
the fielder.

- Opportunities: 1,299,756
- Later-season player-position tests: 7,796
- Candidate RMSE: 0.052425 outs per opportunity
- Neutral RMSE: 0.053286
- Improvement: 0.000861
- Prediction/actual correlation: 0.1723

The coordinate model was selected in every reported fold. The model required
heavy regression: approximately 1,200-2,000 recency-weighted opportunities.
This is useful signal, but it is not a license to publish unshrunk one-year
minor-league defensive ratings.

A subsequent park-separation test mapped 99.8% of opportunities to official
physical venue IDs and estimated park difficulty from visiting defenses. Across
650,355 later-season events, the chronology-selected visitor family raised Brier
improvement from 0.00009449 to 0.00011389 and log-loss improvement from 0.00035643
to 0.00038200. Earlier folds chose the pure visitor rating; the 2022-2024 folds each
selected a 50/50 visitor/crossed player-rating blend with 1,200-opportunity
regression using only older results. This is the selected park-adjustment
challenger; the full crossed park/team/player model remains a diagnostic
environmental model. See `docs/minor-league-defensive-park-separation-result.md`.

### Non-steal runner advancement

The runner model compares first-to-third, first-to-home, second-to-home, tag-up,
and ground-ball advancement outcomes with similar opportunities after level,
park, hit type/location, outs, and handedness adjustment. Runner and outfielder
effects are separated in a crossed shrinkage model.

- Opportunities: 890,022
- Joint runner/outfielder opportunities: 651,514
- Later-season runner tests: 13,857
- Runner RMSE improvement: 0.006796 ordinal bases per opportunity
- Runner prediction/actual correlation: 0.4332

This is the strongest result in the milestone. It supplies the missing
minor-league non-steal advancement evidence that the current selected
baserunning component does not have.

### Outfield arm

- Later-season outfielder tests: 6,128
- RMSE improvement: 0.000097
- Prediction/actual correlation: 0.1061

The full history moved the arm result from slightly negative to barely positive.
It remains much less reliable than runner skill and should stay a separate,
heavily regressed component.

### Catcher throwing

The first catcher model separates catcher and pitcher contributions to the
result after a steal attempt. Pickoff/rundown plays are excluded.

- Attempts: 39,189
- Observed caught-stealing share: 67.5%
- Later-season catcher tests: 2,241
- RMSE improvement: 0.000080
- Prediction/actual correlation: 0.0471

This is only a small positive result. It does not yet capture deterrence—the
catcher's effect on whether runners attempt—and it cannot identify the runner
from every compound English narrative. It should not replace the current model.

### Catcher blocking

The conservative first test uses PAs with one dirt-ball code, a runner aboard,
continuous reconstructed state, a known catcher/pitcher, and an unambiguous
passed-ball/wild-pitch narrative.

- Clean opportunities: 217,733
- Recorded failures: 911
- Later-season catcher tests: 1,988
- RMSE change: **+0.000071** (worse than neutral)
- Prediction/actual correlation: 0.0117

The current blocking formulation fails. It should remain neutral. This does not
show that blocking skill is nonexistent; it shows that the conservative
one-dirt-ball narrative target does not project well enough in its current form.

## Important boundaries

- These are component-persistence tests, not WAR-stack promotion tests.
- Runner advancement currently uses a transparent ordinal extra-base target;
  it still needs conversion to RE24 runs.
- Park is modeled as a season/home-team outcome environment. A production
  projection must carry a rolling park effect into the destination environment.
- The infield test currently covers only ground balls at 2B/3B/SS.
- Position translation, defensive exposure, age effects, and changes in level
  are not yet integrated into projected WAR.
- 2026 remains the protected final test.

## Decision

Promote the shared PBP foundation as development infrastructure. Advance
minor-league runner advancement and infield range to the next integration stage.
Keep outfield arm as a low-weight experimental component. Keep catcher throwing
experimental until deterrence is added. Withdraw the present blocking
formulation.

The next model milestone is to convert the successful residuals to runs, project
their future opportunities without oracle playing time, and test whether they
improve the existing hitter value model on chronological pre-2026 folds.
