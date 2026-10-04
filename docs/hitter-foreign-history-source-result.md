# International professional batting: sources found, NPB history collected

2026-10-04. This is a source-readiness milestone, not a new projection or an
accuracy improvement. The controlling [practical hitter plan](practical-hitter-model-v30-plan.md)
and protected 2026 forecast remain unchanged.

## The accessible sources

The easiest common interface is FanGraphs: [KBO from 2002 onward](https://blogs.fangraphs.com/introducing-kbo-stats-on-fangraphs/)
and [NPB from 2018 onward](https://blogs.fangraphs.com/weve-added-npb-data-to-the-site/).
Its member export is currently signed out in the task browser. Historical
controls must actually show the requested years before downloading: a proposed
old-year URL did not change the new international page's current-season defaults.
No current-season table was accepted as a historical export.

For Japan, [official NPB season tables](https://npb.jp/bis/2005/stats/)
and [year/team player listings](https://npb.jp/bis/players/all/index.html)
are publicly accessible without a member login and cover earlier seasons. We
collected 2005–2024, rather than starting after Ohtani's move. Official KBO also
has [historical season controls](https://www.koreabaseball.com/Record/Player/HitterBasic/Basic1.aspx),
but neither a complete KBO export nor an official historical KBO collection is
qualified yet. KBO IDs and MLB links require their own review; do not assume the
NPB crosswalk solves them. Other international leagues are not certified here.

## What is now available locally

- Twenty seasons, all twelve first-team clubs each season: 240 batting tables.
- 13,154 player-team-season rows and 1,287,308 PA, including 3,859 zero-PA rows.
- Nineteen counting fields: games, PA, AB, runs, hits, doubles, triples, HR,
  total bases, RBI, SB, CS, sacrifices, sacrifice flies, BB, IBB, HBP, K and GDP.
- Exact archived bytes and request receipts for 502 collection sources, with
  separate English review captures. Raw HTML, register archive and bulk
  normalized data stay in ignored private directories, not in the public repo.
- Origin-bounded foreign batting history attached to 693 existing source
  player-origins involving 241 identities. These are not 241 newly approved
  hitters: the source contains pitchers' batting too. The original 83,300-origin
  source ledger and all original forecast rows are unchanged.

The pinned [Chadwick register](https://github.com/chadwickbureau/register)
supplies NPB/MLBAM links and DOB. It is identity infrastructure, not a predictor
of future MLB arrival. Collection retains NPB players without MLBAM IDs.
After exact same-year/team matching plus a narrowly reviewed published-initial
rule, 215 rows still lack an NPB identity. Another 642 identified rows lack a
Chadwick record. These gaps are visible, not filled with guessed names.

## What the checks found

All 240 archived Japanese tables were reconstructed separately, including
249,926 count-field checks. Total bases, PA accounting and rounded batting rates
also passed the collector's checks. There are 67 PA not enumerated by the
displayed count columns; they remain explicit and are not silently called outs.
Later-season deletion and an adversarial future-season mutation leave every
joined cutoff history unchanged. Thirteen focused tests pass; all 31 protected
forecast/input files pass their existing hash checks.

Nine fixed/ordinary player histories were walked through. Twenty-four recent
player-team-season lines match all nineteen counts in the official English
rendering. Three earlier Fukudome renderings return 404; their Japanese raw rows
are verified, but dual-language validation is incomplete. This is a second
rendering of the same official records, not an independent statistical provider.

Two source-design issues were repaired explicitly, not passed off as missing
talent: old indexes have relative links, and foreign names often omit an initial
in the batting table. The latter recovers 1,242 identities without changing any
counts. Brandon Laird is the real positive control: the 2017 table's `レアード`
matches the same-team listing's `Ｂ．レアード`, NPB 23525130/MLBAM 477186, with
571 PA, 32 HR and 125 K. Conflicting surnames remain unresolved. A transient
network timeout stopped collection; the same qualified collector resumed from
verified cached sources only after its process had exited. No completed receipt
or model result was overwritten.

## What the players tell us

These examples show why foreign professionals must not get an empty-history
fallback, and why a blanket Japanese-player bonus would also be wrong:

- Ohtani before 2018: five observed NPB batting seasons, 1,170 PA. His last
  three years contain 35 HR in 732 PA, but also a 27.9% K rate and .391 BABIP.
  That is meaningful power evidence with uncertainty, not proof that the old
  model would have identified a future superstar. His pitching role comes from
  separate dated evidence, not these batting counts.
- Suzuki before 2022: 3,539 observed NPB PA; last-three-year HR rate 5.49% and
  K rate 14.59%. Tsutsugo before 2020 has a nearly identical HR rate, 5.47%,
  but a higher K rate, 20.89%. A single power or league indicator would erase
  an important difference that separate component translation can preserve.
- Yoshida before 2023: 3,189 observed PA and a 6.60% recent K rate. Contact,
  walks and power need separate treatment; NPB contact alone does not certify
  his MLB rate, health, defense or playing time.
- Kensuke Tanaka before 2013: substantial NPB experience at age 31, but only
  a 0.65% recent HR rate. Experience is not the same as high MLB offensive upside.
- The rule-selected ordinary case, Yohei Ohshima, has no MLBAM link. His 7,844
  observed NPB PA remain in the foreign source, while they do not manufacture
  an MLB job or model eligibility. This guards against collecting only movers
  or retrospectively successful names.

The existing candidate has no saved forecast at the reviewed pre-arrival origins
for these eight movers. Recovering the source evidence does not itself create
their forecasts. [Full source walkthrough](../reports/model-evidence/npb-hitting-history/player-walkthrough.md)
and [aggregate review](../reports/model-evidence/npb-hitting-history/review.json)
are saved with exact source and code hashes.

## The next step within the existing plan

Finish KBO access/identity qualification, then use one predeclared foreign-history
and preseason-population integration comparison. Separate translated hitting
talent from dated MLB employment/role evidence and playing-time opportunity.
Keep original forecast rows fixed for comparison, report added players separately,
and preserve signed failures, unsigned players and non-arrivals. The translation
must use earlier mover outcomes with mature training/player separation; a small,
selected mover sample cannot certify every foreign prospect.

Use league-season context and defensible park adjustments, not an unfiltered NPB
average containing pitcher batting. Japan's 2020 season occurred with fewer games;
do not copy the canceled MiLB-season assumption onto these actual observations.
Keep pre-2005 experience left-truncated and historical publication vintages
qualified. No broad algorithm sweep, closed team-record retest or automatic
forecast promotion is justified by this source milestone. The public playing-time
accuracy gap and the practical hitter goal remain open.
