# Ground-ball repair: complete accounting, not invented individual range

2026-09-26. [Frozen contract](ground-ball-ledger-v2-contract.md).

## The usable change

The new ledger retains **2,026,088 distinct ground-ball game/PA keys** from all
244 existing terminal partitions in 2016–2019 and 2021–2024. It preserves hits,
outs, errors, FC, unknowns and every defensive position, including pitcher/1B.
The old 2B/3B/SS first-touch construction selected 1,299,756 of those balls.
That is not itself its failure rate: the difference also includes legitimate
pitcher/1B chances and ambiguous records. The actual flaw is conditioning the
range opportunity on which player eventually touched the ball.

Each ball has three distinct views: complete ball/lineup accounting, exact
legacy-selection membership, and a named **post-outcome allocation benchmark**.
No ball gets nine independent successes/failures merely because nine fielders
were present. No player rating or model was fitted.

## Denominators that matter

| Recorded outcome | Complete GB keys | Selected by old 2B/3B/SS filter | OF first touch |
|---|---:|---:|---:|
| Single | 464,868 | 133,190 | 299,621 |
| Double | 40,924 | 1,568 | 38,256 |
| Triple | 3,930 | 16 | 3,889 |
| Reached on error | 85,461 | 71,214 | 80 |
| Ordinary out | 1,294,805 | 987,604 | 259 |
| Multiple-out play | 120,029 | 106,163 | 11 |
| FC reach | 14,971 | 0 | 8 |
| Unknown outcome | 1,093 | 0 | 35 |

Five source-labeled ground-ball HRs and two SFs also remain as anomalous records,
not automatically reclassified. The previous deep-review totals differ because
it discarded conflicts in a smaller set of diagnostic fields. V2 retains all
keys and exposes uncertainty rather than choosing whichever denominator looks best.

There are **2,574 source-conflicted keys**. Most involve park/team text (2,428
each), not conflicting ball outcomes; 975 also involve narratives and three
handedness. These categories overlap. The conservative benchmark leaves all such
records unassigned. It does not claim all 2,574 ball identities are wrong.
Null plus a known value is retained as non-null consensus rather than taking a
null from the first copy. Conflicting non-GB versions of a GB key are not dropped
before the conflict check. Eight synthetic tests cover these rules/allocation.

## What the allocation benchmark does—and does not know

| Allocation basis | Balls |
|---|---:|
| Observed pitcher/catcher/infield touch | 1,665,082 |
| Through single, equal split between adjacent IF positions | 299,238 |
| Through double/triple to LF/RF, corresponding corner IF | 39,633 |
| Explicitly unassigned | 22,135 |

All shares sum to one, including unassigned mass. Six otherwise allocated balls
have an unknown named fielder; their positional shares remain but no player ID
is invented. The all-inferred-shares-unassigned sensitivity leaves **361,006**
balls without individual responsibility. This is an accounting sensitivity,
not an uncertainty interval or a fitted alternative chosen for better RMSE.

Sean Smith's [Total Zone description](https://www.baseball-reference.com/about/total_zone.shtml)
distinguishes singles reaching neighboring fielding areas from ground-ball
extra-base hits assigned to corner infielders. V2 follows that distinction,
unlike our first sample candidate. The exact equal shares are OUR benchmark,
not a claimed replication of published numerical weights. CF extra-base hits,
OF-retrieved errors and FC remain unresolved. An outfield recovery cannot erase
an infield exposure, but it also cannot prove which infielder made a mistake.

Lichtman's [UZR primer](https://blogs.fangraphs.com/the-fangraphs-uzr-primer/) makes
comparable ball opportunity central to range measurement. Our coordinate copies
have been checked; comparable interception difficulty on hits and outs has not.
We cannot use first-touch position as both an outcome-dependent assignment and
an allegedly pre-play difficulty feature without acknowledging that limitation.

## Source comparison: 256 previously selected games

Both the archive and official full feeds contain exactly **5,742 ground-ball
keys** in these games: no missing or extra keys. There are **5,739 comparable
outcome matches and no mismatches**. The three unscored comparisons are:

- Two batter-interference groundouts correctly left unsupported by the narrative
  classifier. They are not ordinary successful range plays.
- One PA containing two in-play events in the full feed. This diagnostic refuses
  to arbitrarily choose an event, although the final outcome agrees on a single.

First-touch comparisons: **5,736 matches, five unscored, one disagreement**.
The discrepancy is game 772588/PA 46 (2024 rookie): archived first touch 2B,
official feed SS on a double play. This is a real source-version difference;
the benchmark is not retrospectively corrected for this one observed case.
The report stores every comparison, year/level breakdown and outcome confusion.

These games were chosen without outcomes, but have now been examined for source
development. They are not untouched predictive validation data. Exact agreement
between representations of the same official feed is not independent scoring.

## Scope limits and source decision

**Ball accounting passes within the archive; individual range certification does
not.** The outcome-dependent omission is repaired, but resolving a through hit
to a particular fielder still depends on assumptions. This is an explicit bounded
measurement blocker, not a negative result for the existence/predictability of
minor-league defensive talent.

The source has a separate `bunt_grounder` category. Those rows remain in the
original foundation and are inventoried in `verification.json`; they are NOT
included in the 2,026,088 `ground_ball` count. The 33 narrative-bunt records that
do carry a `ground_ball` label are preserved and unassigned. Do not describe this
artifact as every ground-contact type, every batted ball, or all scheduled games.
Terminal lineups outside the sampled games are not independently event-certified.

The defensible next choices are narrow:

1. For catcher work, finish the pitch/runner exposure source gate before fitting
   throwing, deterrence or blocking. The event-time source decision is
   [separate](defensive-timeline-v1-result.md).
2. For range, retain this benchmark and complete ledger; first define a testable
   proxy with explicit allocation sensitivity or obtain comparable ball-direction/
   difficulty evidence. Predicting a later version of the same biased first-touch
   statistic would not certify true range. Precise tracking is not required to
   test a coarse proxy, but the narrower claim must be stated up front.
3. Only after that source decision, lock persistence/transport comparisons on
   identical games, park/level movers versus returners, and full-population
   coverage sensitivity. No new range learner or validation-driven share tuning
   is authorized by this accounting run itself.

Artifacts and hashes: `model_artifacts/ground-ball-ledger-v2-2026-09-26/`.
Full yearly ledgers: local ignored `reports/generated/ground-ball-ledger-v2/`.
Reproduce with `build_ground_ball_ledger_v2.py build`; verify independently with
`verify_defensive_ledger_repairs_v1.py`. The frozen contract/code/source manifests
are checked before processing. No production prediction or protected outcome
was changed/used.
