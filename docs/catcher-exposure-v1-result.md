# Catcher opportunities: the new source test passes, with clear limits

2026-09-26. [Predeclared source contract](catcher-exposure-v1-contract.md).
No skill model was fitted and no forecast changed.

## What is now possible

We can reconstruct recorded pitches and the runners/outs/count BEFORE each
event, with the catcher and pitcher who were actually present. That supplies
usable non-event observations: a pitch with a runner aboard on which nothing
happened is retained, not just a pitch mentioned in a passed-ball narrative.

This moves blocking and conditional steal-outcome work past an important source
obstacle on the tested games. It does not yet establish predictive catcher skill,
population-wide historical coverage or a complete deterrence denominator.

## Frozen validation: all 128 new games pass

The first 256 previously examined games were development data. Before fetching
another feed we selected metadata-hash ranks 5–6 in the same 64 year/level/league
strata. All 128 were disjoint from earlier samples and absent from this cache.
Code/tests were frozen before fetching/scoring them. No failing game was replaced.

| Validation check | Result |
|---|---:|
| Recorded pitch events | 32,864 |
| Official pitcher pitch-count comparisons | 934 / 934 match |
| End-of-PA runner states and outs | 9,534 / 9,534 match |
| C/P scoring credits / final pitcher matchups | 2,827 / 2,827; 9,528 / 9,528 match |
| Player event totals / team event totals | 3,627 / 3,627; 1,024 / 1,024 match |
| Ordinary SB / CS / pickoff-CS | 273 / 87 / 16 |
| WP / PB | 207 / 41 |
| WP/PB linked to an exact pitch | 248 / 248 |
| Attempt runner starting-base checks | 376 / 376 match |

The independent verifier also checks every raw pitch key, nonduplicate pitch
IDs, valid pre-pitch counts, 2,064 half-inning transitions and contiguous PA
indices. The extra six state checks without a final pitch matchup matter: the
source is not limited to PAs ending with another delivered pitch.

The sample includes rookie, short-season, A, A+, AA and AAA filename levels in
2016/2018/2021/2024. All 22 present year/level combinations have positive pitch
exposure; the tracked verification report includes exact counts and positive
player-event checks. These are related official scoring representations, not
independent human rescoring. Equal stratum sampling is not a league-rate estimate,
and validation conditional on archived games does not certify missing games.

## Three baseball distinctions that change the test

### 1. Blocking can matter with empty bases

Of the 248 WP/PB events, **nine occurred on pitches beginning with empty bases**:
eight WP and one PB. All began with two strikes. A runners-aboard-only rule would
miss them. MLB's [WP definition](https://www.mlb.com/glossary/standard-stats/wild-pitch)
includes batter advances on uncaught third strikes.

The source now retains all 32,864 pitches and identifies **20,196 pre-pitch
risk opportunities**: a runner aboard, OR two strikes with the batter eligible
to reach on an uncaught third strike. All 248 scored failures fall in that set.
The flag uses only the pre-pitch situation, not whether this pitch eventually
went into the dirt, became strike three, or caused an advance.

This estimates the chance of a SCORED advancement failure, not every physically
unblocked ball. A pitch with no scored advance is not proof the catcher blocked
it cleanly. WP/PB should initially be evaluated jointly with pitcher context,
not as if every WP were entirely the pitcher's fault and every PB a pure measure
of catcher talent. The all-pitch and at-risk denominators remain distinct.

### 2. A steal opportunity is not identical to a pitch

There are **21,474 runner-pitch exposures**, of which 5,030 have the next base
occupied. We retain these because coordinated steals can occur; an open-base
filter would remove part of that situation before learning anything about it.

Of 360 ordinary SB/CS attempts, **14 have no unique pitch link** (eight SB, six
CS). Two explicitly link to pickoff events; the other 12 remain nonpitch-or-
missing-link cases. Do NOT call all 14 proven between-pitch attempts. Another
12 pickoff-CS events are explicitly anchored to nonpitch pickoffs. All these
events remain in the numerator ledger with their runner state; none becomes a
fabricated zero or an invented preceding-pitch label.

Therefore the full event list is suitable for defining a conditional **battery**
steal-outcome test, with pickoff-CS kept separate. It is not a pure catcher-arm
rating. Some ordinary CS involve the pitcher; pitcher, runner, destination base
and catcher context need to be separated without selecting only successful
catcher-credited plays. That would create another outcome-conditioned sample.

For deterrence, **do not divide all attempts by pitch exposures and declare it
complete**. A future contract must cover both pitch and nonpitch opportunities,
for example explicitly defined runner-PA/risk spells. Administrative actions
are not extra opportunities, and realized total PA length is not a pre-PA feature.

### 3. Missing an unrelated fielder need not erase known battery data

The new C/P-only timeline retains the earlier 2024 game with a delayed LF
substitution. It does not move that substitution backward or certify LF. It
checks the known C/P, their scoring credits, event totals and pitch counts.
The earlier full-nine-fielder result stays 127/128 under its original contract;
this new, narrower certification is separately versioned, not a rewritten score.

## Development failures remain visible

All 256 development games reconcile recorded pitch counts and battery events.
Runner states pass in **252/256**, leaving 1,173 pitches and 23 scored events
outside the full runner-state-certified slice. Four feeds have contradictory
runner records: one runner on two bases, a retired batter still listed on base,
or incompatible safe/out movements. We do not fix these by copying later state
backward. They remain in `development-report.json` with exact game/PA reasons.

One additional game (551162, PA 49) has a WP action without a pitch ID link.
It follows a `no_pitch`-style placeholder in a walk sequence. Box pitch counts
still agree with the feed, illustrating that same-source agreement cannot prove
every real physical delivery was recorded correctly. The game is excluded from
the fully linked blocking-model slice, not merely stripped of its unlinked WP.
Thus development blocking-source eligibility is **251/256**, not 256/256.

Two general source semantics were repaired before freezing validation:

- On a third-out force, the feed may omit irrelevant safe advances. Verify all
  recorded starts/outs, then end the inning; do not invent live post-inning bases.
- A scorer can record advance/return/advance legs for one runner in an event.
  Require a complete consistent path through all recorded legs. Do not pick the
  last row merely because it matches the desired result.

Seventeen new synthetic tests cover these, simultaneous advances, double steals,
safe-on-error movements, substitutions, unknown batteries, no-pitch inning ends,
empty-base blocking risk and exact-link failures. Development outcomes were
inspected to debug source rules, not presented as untouched validation.

## Decision and next execution boundary

**Ready on covered games:** recorded pitch exposure, pre-event runner state,
exact WP/PB labels, and the complete conditional SB/CS event ledger. This is
sufficient to design a fair blocking/battery-throwing experiment without Statcast.
It is not sufficient to fit a useful multi-season projection from 128 games.

**Next:** scale the frozen extraction to a predeclared historical population and
audit coverage before looking at predictive scores. Preserve failed games and
compare included/excluded mass by year, league/level, park and event family.
Keep the pitch/state/link checks, PA continuity and half-inning checks in the
batch gate. An extraction improvement must be versioned rather than silently
editing this frozen validation. Final-PA handedness must not be copied across
mid-PA pitching changes; model context must follow the event-time identity.

Then predeclare ONE chronological blocking/conditional-outcome test using the
repaired inputs, pitcher/runner/catcher separation, park/level/era context and
strong neutral/legacy benchmarks on identical games. Test subsequent-season
prediction, not how convincing in-sample catcher rankings appear. Preserve 2021;
add mover/returner and coverage sensitivity. Do not retune the earlier dirt-PA
extractor or jump directly from this source success to catcher WAR. Deterrence
still requires its own all-attempt risk-window definition.

## Reproduction

`scripts/audit_catcher_exposure_v1.py` selects, develops, freezes, fetches and
validates. `scripts/verify_catcher_exposure_v1.py` independently checks manifests,
raw pitch keys, risk membership, event links and movement starting bases.
Tracked manifests/reports: `model_artifacts/catcher-exposure-v1-2026-09-26/`.
Hashed detailed Parquet ledgers: local ignored `reports/generated/catcher-exposure-v1/`.
Full historical feeds remain in local quarantine. No new 2026 performance was
opened; no pitcher/hitter/catcher forecast or explorer changed.

Verification: **76 focused regression tests pass**, including the 17 new exposure
tests. The independent exposure/source verifiers pass. Both the original
31-file/3,907-player forecast freeze and the 43-fit/188,080-row arrival-coherence
delivery verify unchanged. Existing range and batting diagnostic artifacts were
also rechecked; their prior conclusions were not rewritten.
