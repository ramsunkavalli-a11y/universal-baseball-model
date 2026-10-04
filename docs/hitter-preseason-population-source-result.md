# Preseason coverage is recovered but foreign talent still needs a model

2026-10-04. The historical player source now reaches the actual preseason
information dates for 2012–2025. It recovers several missing signed hitters,
including experienced NPB and KBO arrivals. This is a source repair, not an
improved forecast: all current predictions and protected 2026 files are unchanged.
The practical hitter goal remains active.

## What was collected and corrected

There are 420 team 40Man listings, fourteen MLB team listings and fourteen
offseason transaction windows, each independently matched against disjoint
monthly windows: 506 main requests. The special 2022 cutoff is March 18 after
the lockout. No 2026 outcome source was requested. Original probe responses
and failed code remain preserved.

The original Ohtani control incorrectly expected 40-man membership in January
2018. He was a non-roster invitee and his contract was selected March 27.
That was a test-expectation error, not evidence that the returned absence was
wrong. See the [dated correction](hitter-preseason-population-probe-amendment.md).

The transaction check also caught a real extraction-design error: one trade
ID can carry several people. The complete windows contain 126,077 raw records,
including 1,036 exact duplicate rows. Collapsing by ID alone would lose 6,879
additional distinct event legs, including cash legs. The repair keeps composite
player/event identities and compares complete content and multiplicity with
monthly windows. It does not reinterpret late effective or resolution dates
as cutoff-known. See the [extraction amendment](hitter-preseason-population-transaction-amendment.md).

The source ledger has 83,300 player origins, retaining all 63,282 original source
rows and their identifiers. The 20,018 additions are broad source candidates,
not 20,018 new hitters. Most are pitchers or unresolved roles. Before the
additive role review, just 237 added origins have both positive context and
a numeric hitter hint. This is not an approved inclusion threshold. Generic
OF/IF and two-way codes require explicit handling; missing roles remain visible.

No cross-team 40Man listing conflicts occurred; four duplicate groups have
status or parent-team differences. These remain diagnostics. Returned status
does not certify historical health, rights or a future job. FullRoster remains
excluded from new admission because the earlier Kim counterexample showed a
later signing in an earlier requested response; passing a few other controls
does not erase that failure.

## What the player walkthrough shows

The [fourteen complete source walks](../reports/model-evidence/hitter-preseason-population-source/player-walkthrough.md)
include actual dated domestic statistics, every relevant raw event, returned
listing or absence, role hints, original forecast intermediates where a row
exists, and origin-only comparisons. New forecasts are not invented. Following
year PA diagnoses coverage only after identities are sealed.

| Player and forecast season | Preseason evidence | Old forecast coverage | Following MLB PA |
| --- | --- | --- | ---: |
| Conforto 2023 | January 6 agreement and Giants listing | Missing | 470 |
| Alfaro 2025 | January 16 minor agreement; no reserve listing | Missing | 39 |
| Sanó 2024 | Reported agreement precedes cutoff; official record is later | Still not recovered by this source | 95 |
| Ohtani 2018 | December minor agreement and dated two-way role | Missing | 367 |
| Suzuki 2022 | March 18 agreement and Cubs listing | Missing | 446 |
| Yoshida 2023 | December agreement and Red Sox listing | Missing | 580 |
| Jung Hoo Lee 2024 | December agreement and Giants listing | Missing | 158 |
| Hyeseong Kim 2025 | January 3 agreement and Dodgers listing | Present, only 0.36 expected PA | 170 |

Conforto's last two played MLB seasons had 233 and 479 PA with nine and fourteen
HR. Their absence from his later row is a population-timing problem, not a zero
talent forecast. Alfaro has 274 and 52 recent MLB PA plus AAA evidence, but a
minor agreement still does not imply a large workload. Sanó retains a genuine
reported-versus-official timing gap; this collection must not fabricate a
January official signing to make the source appear complete.

Ohtani and the other foreign professionals have no domestic batting input in
these origin windows. That is missing league evidence, not an inexperienced
player profile. Suzuki's roster uses generic OF code O; the original numeric
hint missed it. The reviewed role overlay recognizes OF/IF and preserves
two-way evidence rather than silently assigning a specific fielding position.
Ohtani's dated two-way annotation does not give him an individual talent bonus.

Hyeseong Kim is a different failure: the old row already exists, with about
0.47% participation times 76.42 conditional PA. New source evidence does not
change that saved forecast. His Korean performance is missing, so a domestic
no-history fallback is not a satisfactory professional-player projection.
Comparable sets built on domestic exposure are weak for these profiles: Ohtani's
original source peers are pitchers, and three other foreign cases have no peers
under the declared narrow rule. The review does not certify those comparisons.

The opposite cases stay in view. Wright already has a retained row and positive
listing, yet only three following-year PA; roster evidence cannot guarantee
recovery. Belt has 404 PA and nineteen HR in his last played season, no new
agreement, and zero following PA; free agency is not a known zero hitting rate.
Pollock, Canha and Devers correctly appear with Seattle, Detroit and Boston,
not their later Giants affiliation. Solano is the lowest-ID listed regular
outside the fixed case set, selected without his future results: the old 138
expected PA remains against 179 actual, with his January Seattle agreement now
visible. There is no fitted improvement or deterioration category in this
source-only milestone.

## Verification and the next model decision

An independent reviewer reconstructs all fourteen origin identity unions,
returned memberships, eligible event counts and historical exposure totals.
Raw archived bytes match every source file. Future-stat removal and mutation
do not change new source membership. The original cohort itself retains its
previous retrospective-source qualifications; this repair does not recertify
old fullRoster-only origins. Focused tests and the protected-freeze check must
pass before the final review receipt is issued.

For the next fixed integration comparison, retain the original 30,506 forecast
rows, report additions separately and use this same dated-source treatment in
historical training. Preserve unknown role, unsigned, exit and non-arrival cases;
do not declare every transaction candidate a hitter. Do not substitute public
benchmark forecasts as independent talent inputs or fit to these few names.

Experienced foreign professionals need league-adjusted production, age and
professional experience, supported scouting and dated role/contract context.
National origin is not a translation. Until those inputs and mature historical
examples exist, the model needs an explicit qualified foreign branch, not the
domestic empty-history expectation or an unsupported Japanese-player boost.
This source milestone does not establish that branch, correct the existing
public playing-time error gap, certify full WAR or complete long-term value.

Evidence: [independent final review](../reports/model-evidence/hitter-preseason-population-source/final-review.json),
[source ledger](../reports/model-evidence/hitter-preseason-population-source/population.parquet),
[original and reviewed cases](../reports/model-evidence/hitter-preseason-population-source/reviewed-cases.json),
and [raw responses with request metadata](../reports/model-evidence/hitter-preseason-population-source/raw-captures.zip).
