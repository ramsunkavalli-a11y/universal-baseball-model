# The current hitter model, plainly

2026-10-03. This is a useful historical research baseline, not a finished front-
office valuation system. The goal remains incomplete. Do not replace the frozen 2026
forecast or imply protected-season validation from these development results.

## What it predicts

The next calendar season's expected MLB plate appearances, batting performance
if the player participates, and batting-plus-replacement contribution. Minor
leaguers, established hitters, brief debuts and exits remain in the population.
It does not yet provide reliable present-day MLB-equivalent prospect grades,
full WAR, six club-controlled seasons, contracts or risk-adjusted trade value.

## What the working forecast is built on

Three years of official batting counts, pooled with recent years weighted more
heavily, separately for 14 league buckets. Strikeouts, walks, HBP, home runs,
doubles, triples and BABIP opportunities have exposure-based stabilization.
Age, observed career/debut history, listed position, dated draft evidence and
the imperfect year-end roster listing provide context. Older MLB batting value
is expressed relative to its own season's run environment. No major/minor
competition equivalence or complete historical injury/contract coverage is
claimed.

A shallow boosted-tree model predicts expected PA directly. A regularized linear
model predicts batting rate. Multiplying those estimates gives expected batting-
plus-replacement value; this is an approximation, not a coherent joint career
distribution. The stronger working assembly is V33b. V34 carries a completed
2020 source extension; V38 adds games/PA-per-game to that extension. These are
separate reviewed comparisons, not silently mixed winning pieces.

The working research assembly now includes the V44 reported-retirement policy:
eligible recorded retirement sets next-year delivered PA/value to zero without
changing hitting ability. Dated return evidence clears it. This is reversible,
not permanent ineligibility or a calibrated zero comeback probability. Public
matched scores below do not change. The earlier separate explorer is preserved
and does not silently become this updated assembly.

## How good is it?

The reviewed V49 research alternative separates MLB appearance probability from
PA conditional on appearing and adds historical prospect rankings. Its matched
public PA RMSE/MAE are 142.11/110.09, versus Steamer 135.02/92.40. This improves
the point scores modestly and repairs some lower-minor immediate-readiness
excess, but underpredicts upper-minor arrivals and fast new draftees. It does not
change hitting ability or replace the working forecast. The [31 actual player
reviews and result](practical-hitter-readiness-v49-result.md) are complete; the
goal remains active and talent work is next.

| Same 1,789 public-matched forecasts | PA RMSE | Average absolute PA error |
|---|---:|---:|
| Working count/draft baseline | 143.96 | 110.56 |
| Games/involvement research candidate | 143.19 | 111.32 |
| Steamer archive | 135.02 | 92.40 |

The baseline's large-error measure is about 7% worse than Steamer; its average
absolute miss is about 20% worse. That is a meaningful remaining opportunity
gap, not an assertion we are competitive in every respect. Our declared 15%
absolute-error tolerance still fails. Public snapshots may have later roster/
injury information than the December cutoff. Converted public contribution has
a run-environment mismatch, so its score cannot prove better batting talent.

The newer verified late-season-PA research candidate reaches public PA RMSE
142.82, versus 143.96 working and 135.02 Steamer, but PA MAE 111.05 is slightly
worse than working 110.56. Its small incremental gain versus games is uncertain;
2021-origin and never-debut upper-minor errors worsen. It remains a separate
reviewed research choice, not the working default or a finished model. A new
local explorer shows this comparison and the reversible retirement policy
without changing frozen/deployed forecasts. See
[the timing result](practical-hitter-late-role-v46-result.md).

The [local research explorer](http://127.0.0.1:8785/) has team and stage filters,
actual historical outcomes, raw player histories and reviewed forecast cases.
An information year of 2024 means a forecast for 2025. Organization membership
is historical, not a projection of future team rosters. This display is batting
plus replacement, not full WAR or the protected 2026 forecast.

The 2024-origin whole cohort predicts 179,762 PA versus 182,880 actual and 556.7
batting-plus-replacement wins versus 570.2 actual. Those sensible aggregate totals
do not prove accurate individual forecasts or resolve other origins. The games
extension improves upper-minor allocation but increases 2023 excess. We inspect
both totals and actual players instead of enforcing a convenient universal sum.

## What actually improved in this program

Complete-team stint accounting and corrected career exposure; removal of
incomplete canceled-season training; a real 2020 hitter cohort extension;
exposure-based pooled production and dated draft inputs; complete-population
chronological/player-held-out checks; and a useful games/involvement challenger.
These changes and their scores are recorded separately. A source repair can be
valuable without its newly fitted forecast being a statistically proven upgrade.

Raw contact now has a source-reviewed 2016+ minor/2021+ MLB assembly. Ambiguous
plays and uncorroborated player/league joins are quarantined, not passed off as
talent. No forecast upgrade was claimed from that preparation alone.

A retrospective full-roster request can return membership from after its
requested date. Hyeseong Kim's Dodgers entry is a confirmed counterexample.
All original forecasts remain scored, but 218 roster-only rows now carry an
unverified-origin qualification. Foreign production and new international
player eligibility remain incomplete; zero forecasts are not reliable talent
grades for these players.

## What did not work

Shared cross-level exposure encoding, the first coherent event model, its
empirical-anchor repair, a dedicated current-MLB workload head, and the new
contact-rate challengers did not beat the strongest coherent forecast. Some
fixed individual mistakes improved, but other consequential players worsened.
We did not keep adding complexity to salvage the appearance of a win.

The player reviews show persistent weaknesses: fast entrants such as Kurtz,
brief-debut stars such as Judge/Steer/Winn, some missed-year returns, and future
availability losses. Tree batting models repeatedly compress exceptional hitters.
Matching delivered value can hide a wrong PA estimate offsetting a wrong rate;
Langeliers and Rivera are explicit examples. Every completed comparison has
source-to-forecast walks, including unsuccessful origin-selected peers.

## The coherent next work

Close the count/contact/library sweep. Concentrate on fast-entry/temporary-return
opportunity and the conditional prospect talent target, with the full population
retained and high-pedigree limited samples treated explicitly. Test a small
coherent repair against the current baseline and the same public matches; do not
retroactively turn known breakouts into eligibility rules or assign every absent
player a full healthy season. A credible uncertainty/arrival layer and complete
value components come after that, not a renamed annual point forecast.

The separate [local reviewed explorer](http://127.0.0.1:8784/) has a historical
team filter, batting-only rate, PA, actual results, reviewed alternatives and
selected manual explanations. It forecasts 2017–25, not new 2026 results.

[Controlling plan](practical-hitter-model-v30-plan.md) ·
[Working baseline result](practical-hitter-v33b-result.md) ·
[Games comparison](practical-hitter-v38-result.md) ·
[Direct contact comparison](practical-hitter-contact-v41-result.md).
