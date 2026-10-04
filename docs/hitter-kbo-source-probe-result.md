# Korean first team batting can be collected without a member login

2026-10-04. The official public KBO form is usable when live form state is kept
within its session. Five source seasons are collected and independently reviewed:
2005, 2015, 2020, 2023 and 2024. This is source readiness, not improved projections.

The two official stat groups return matching player-ID membership when sorted
by PA and BB rather than average. Their 1,777 rows include 408 zero-PA rows and
225 with one to ten PA. Total exposure is 265,857 PA. All sixteen summable count
fields agree with separate official team tables in every season. Player games
are deliberately not equated to team games. Seven PA remain unenumerated by the
displayed columns; they are not relabeled as outs. Undefined rates remain missing.

Every normalized count row was reconstructed from archived HTML, totaling 30,209
field checks. Six player cases were walked through, with 78 matching count fields
in the official English origin-season rendering. Five fixed cases have matching
English names and birth dates against a static-fields-only MLB identity response.
The ordinary case has no fabricated MLBAM join. This does not qualify a full
league-wide crosswalk. Ten focused tests pass, including three new regression
tests after the initial independent review, and all 31 frozen files are unchanged.

## What went wrong and how it was corrected

The average leaderboard is not complete league coverage: sorting a counting
statistic opens all published participant pages. Current and retired player
links have different paths; both supply a stable KBO ID, while the retrospective
retirement label must not become a historical availability feature. A sort POST
made from cached form state in a new session returned HTTP 200 but redirected
to an error page. A fresh live-session attempt succeeded. That supports a live
session requirement; it does not establish the exact server-side cause.

The English reviewer initially missed YEAR because it is a row-heading `th`,
not a statistical `td`. A strict missing-year failure caught this before any
completed player review. The correction includes both cell types in order and
has a regression test showing unrelated future-season mutations do not affect
the origin check. Original error responses and failed code hashes are preserved
in the separate corrections. No completed source/forecast result was overwritten.

## What the players reveal

Hyeseong Kim's 2024 source line contains 567 PA, 11 HR, 62 K and 45 unintentional
walks. The unchanged saved candidate still has only 0.3409 expected MLB PA,
from participation probability 0.004499 and 75.764 conditional PA. Source-only
qualification has not repaired that forecast; it establishes the missing
professional evidence and exposes the need to integrate dated signing/role
context with translated talent. Do not simply multiply raw KBO rates into MLB PA.

Jung Hoo Lee's 2023 line contains 387 PA and 23 K: a shortened sample, not an
unobserved player or proof that he cannot play regularly. Ha-Seong Kim's 2020
line contains 622 PA, 30 HR and 68 K, a different offensive profile. Byung-Ho
Park and Eric Thames both have substantial 2015 power, but their K rates are
25.88% and 15.29%. These differences should survive component-wise translation;
a single Korean-professional or home-run-rate indicator would erase them.

The rule-selected ordinary player, Choi Kyung Hwan in 2005, remains in the source
at age 33 with 379 PA and three HR. No MLB job or participation is inferred.
Peers use origin-year exposure/K/HR only; their age and role are not certified
by this count-only comparison. No new forecast or future MLB label was invented
to turn these cases into accuracy evidence. The raw line is not park-adjusted,
and a displayed club is not verified stint-level exposure.

[Player walkthrough](../reports/model-evidence/kbo-hitting-source-probe/player-walkthrough.md)
and [aggregate review](../reports/model-evidence/kbo-hitting-source-probe/review.json)
contain the fixed selections, actual counts, intermediate saved forecast and
source/code hashes. Primary sources are the
[KBO historical forms](https://www.koreabaseball.com/Record/Player/HitterBasic/Basic1.aspx),
[official team counts](https://www.koreabaseball.com/Record/Team/Hitter/Basic1.aspx)
and [official English profiles](https://eng.koreabaseball.com/Teams/PlayerInfoHitter/Summary.aspx?pcode=67304).
English/Korean tables are renderings of the same official data, not independent
providers. Raw and bulk data remain private.

## Next within the existing plan

Collect the remaining 2005–2024 first-team seasons under the fixed collection
contract, reusing these qualified seasons unchanged. Bulk SB/CS, historical
position, DOB, MLBAM coverage, publication vintage and league-strength/park
translation remain unqualified. This source capability does not justify another
algorithm tournament, a team-record retest, protected forecast promotion or
declaring the hitter model finished.
