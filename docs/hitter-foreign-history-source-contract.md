# Collect foreign professional hitting history before translating it

2026-10-04. The preseason audit found signed NPB and KBO hitters missing from
the old forecast, and an already included Hyeseong Kim with almost no projected
playing time. This source milestone supplies real professional history where
possible. It does not fit a translation, change any forecast, or certify the
practical hitter model. The controlling practical hitter plan remains in force.

## Sources and scope

Collect official NPB first-team, regular-season batting tables for every team
in 2005–2024, including low and zero PA rows. Enumerate tables from each official
season index, not a list of MLB successes. Get historical team/player identity
listings from NPB's all-player index. The tables do not expose structured player
IDs: attach the NPB ID only when the same season/team listing has one exact
Japanese name after removing whitespace. Preserve unresolved or ambiguous names
without guessing. Historical listings may reflect later name changes; returned
current/old-player presentation and debut notes are not modeling features.

Use a pinned Chadwick register with its NPB and MLBAM IDs and exact birth date.
Identity/DOB lookup is retrospective infrastructure, not evidence of a future
MLB career: never use the register's last-played fields, future MLB debut,
current status, or eventual ID coverage to select the NPB population. Preserve
every NPB row whether or not it has an MLBAM cross-reference. A conflict in a
structured identity fails the join rather than merging histories.

The 2005 start supplies earlier inputs and movers than FanGraphs NPB's 2018
start, but is left-truncated for players with earlier experience. No inferred
career-total experience from this window. Farm-only players, NPB defense,
contracts, scouting and pitch-level data are not certified by this collection.
KBO remains a separate pending source: FanGraphs supplies 2002 onward and member
exports, while official KBO has historical season controls. Record actual
download/identity coverage before declaring KBO imported. Do not replace missing
KBO inputs with NPB factors or a nationality bonus.

References: [official NPB season tables](https://npb.jp/bis/eng/2017/stats/),
[historical player listings](https://npb.jp/bis/players/all/index.html),
[Chadwick identifiers](https://github.com/chadwickbureau/register),
[FanGraphs NPB coverage](https://blogs.fangraphs.com/weve-added-npb-data-to-the-site/),
and [FanGraphs KBO coverage](https://blogs.fangraphs.com/introducing-kbo-stats-on-fangraphs/).

## Collection and qualification

Save exact HTML/ZIP bytes, URLs, capture times, hashes, code and contract hashes.
Keep raw and bulk normalized data in ignored private directories; permission
for public redistribution has not been established. Commit code, synthetic
tests, aggregate coverage and a small attributed player review, not raw tables.
Never silently overwrite a capture. A current historical page is retrospective
season evidence, not proof of its publication vintage at a preseason cutoff.

First qualify 2005 and 2017 Nippon-Ham, 2021 Hiroshima and 2022 Orix tables and
their identity listings. Check Ohtani in 2017 and Suzuki in 2021; verify they are
absent from the respective following-year NPB team batting tables. Preserve any
failure before broad collection. Every requested table must advertise the exact
season, team and first-team batting scope. No default current-season tables.

Validate headers, nonnegative counts, unique source row keys, total bases from
hit types, PA accounting and rounded AVG/SLG/OBP. Allow a nonnegative PA residual
for opportunities not enumerated in the batting columns; do not silently count
it as an out. A zero denominator means an undefined calculated rate, not zero
talent. Report every residual, missing identity and crosswalk conflict. Do not
infer first-team absence as a missed season without complete season coverage.

Reconstruct all normalized rows independently from archived HTML. Verify
English tables for the fixed review cases, with named raw counts and translated
input status. Mutating later seasons must not change a cutoff history. Do not
retrieve protected 2026 outcomes or touch existing forecasts/explorers.

## Player review and next integration

Fixed cases before collection: Ohtani at the 2017 origin, Suzuki 2021, Yoshida
2022, Aoki 2011, Fukudome 2007, Tsutsugo 2019, Akiyama 2019 and Kensuke Tanaka
2012. Add an ordinary 2024 NPB batter using the lowest NPB ID with at least
100 PA outside those names, without considering MLB outcomes. For each show
source seasons/counts, ID/DOB joins, recent component rates, missingness,
left-truncated experience, what the old domestic input lacked and the unchanged
forecast or absence of a row. Select three NPB peers from cutoff-known age,
recent PA and production where identity/age support permits, preserving peers
without MLB history. Empty support stays explicit. Gains/harms are not model
categories in this source-only milestone; never fabricate candidate forecasts.

After source review, a separate fixed integration contract must distinguish
coverage, employment context and translated talent. Fit separate components
using earlier league movers, with age/season/park context and player separation.
NPB/KBO relative production is not MLB-relative production. Movers are selected
players, so a translation estimated on them cannot certify all foreign prospects.
Retain original evaluation rows, score additions separately, keep foreign-source
gaps visible and inspect actual training maturity. Public forecasts are benchmarks,
not independent talent inputs. No extra algorithm sweep or closed team-record test.
