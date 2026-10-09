# Additive 2027 value: player review

2026-10-09. This closes the accounting walkthrough, not the historical accuracy
or release gate. The sealed assembly receipt and its original pending status
remain unchanged; this dated review supplies the interpretation. All 38 saved
walks replay rate × opportunity / unit and sum to their reported WAR. They
include eight fixed cases, their origin-selected peers, and three high/low
forecast extremes. There are no observed 2027 outcomes, hence no claims of
predictive gains, harms or calibrated upside from this assembly.

## What the numbers mean

The old batting rate is converted back to runs using its original 10 runs/win;
the sum of all runs uses the common 9.8218146 runs/win environment. Replacement
is awarded once. Every position uses projected exposure, not a primary-position
label applied to all PA. Full details, inputs and exposures are in
`reports/model-evidence/hitter-2027-v1/full-value-player-walks.json.gz`; dated
source histories are in the preceding production, role and defensive reviews.

| Player | PA | Full-component WAR | Main explanation |
|---|---:|---:|---|
| Bryce Eldridge | 528 | 2.059 | Batting +1.704 and replacement +1.639, but 476 projected 1B innings and 68 DH starts cost 1.164 positional WAR. Running costs 0.271; range −0.035 and receiving +0.041 nearly cancel. The old 3.312 batting-plus-replacement number was not full WAR. |
| Aaron Judge | 462 | 3.359 | Batting +2.311, replacement +1.434, position −0.561; 716 RF innings, 54 CF innings and 18 DH starts. Defense adds about 0.131 and running costs 0.082. This is an expected-workload projection, not a claim that his healthy full-season ceiling is 3 WAR. |
| Francisco Lindor | 567 | 3.191 | Batting +0.492, replacement +1.757, position +0.553, range +0.173. His shortstop value is explicit and separate from his hitting. |
| Fernando Tatis Jr. | 579 | 4.144 | Batting +2.011, range +0.292, arm +0.074, running +0.205. The 814 RF/300 2B innings follow the captured 2026 usage, not a hindsight player-specific role override. |
| Shohei Ohtani | 585 | 4.003 | Batting +3.259 and replacement +1.814, offset by −1.407 at DH. All fielding channels are zero because projected fielding exposure is zero. This is hitter-only value and cannot support net dollars against his entire two-way contract. |
| Patrick Bailey | 288 | 1.582 | Batting −0.680, replacement +0.891, position +0.590, framing +0.683, throwing +0.200 and blocking −0.045. This is not a generic catcher bonus: position and measured receiving skills are separate. |
| Jackson Lovich | 1.0 | 0.002 | Supported minor-position estimates receive only his tiny expected MLB exposure. The old 26-PA batting distortion no longer places him among established stars. This does not estimate his eventual ceiling. |
| Carlos Concepcion | 0.05 | approximately 0 | No unsupported precise ACL glove grade is invented. The negligible delivered value reflects next-year MLB opportunity, not a declaration of no long-run talent. |

All rows also include the common league reference of +1.612836 runs/600 PA.
It is not a player-specific adjustment. Bailey under the same-reference full-ABS
sensitivity loses his 0.683 framing WAR, not his throwing/blocking/position
value. This sensitivity is not an ABS adoption probability or a full future
league revaluation.

## Extremes and ordinary comparisons

Bobby Witt Jr. leads these checked extremes at 6.825 WAR: 2.446 batting,
1.976 replacement, 1.150 range, 0.613 position and 0.466 running, plus 0.174
league adjustment. Pete Crow-Armstrong's 6.042 similarly includes 0.976 range,
0.229 arm and 0.503 running rather than treating all his value as batting.
Elly De La Cruz is 5.403, with smaller range credit (0.236), not the same glove
grade given to every shortstop. These large forecasts still require historical
whole-value scrutiny; plausible arithmetic is not accuracy evidence.

Negative values are retained: Frazier −0.192, Farmer −0.188 and Wagaman −0.168.
Their weak projected batting exceeds the replacement credit. We do not floor
them at zero or infer that their contracts disappear. Ordinary peers include
Seager 2.055 and Chapman 1.868; Chapman's +0.232 fielding does not erase his
near-neutral batting projection. Wells 2.093 has +0.541 framing but −0.075
throwing, unlike Bailey. These comparisons expose component differences instead
of awarding undifferentiated positional value.

## Totals, restrictions and disposition

4,851 players sum to 569.221 development WAR on 191,261.7 expected PA. The fixed
662-person 2026 MLB reference has 178,696 projected PA. Three pitchers with one
2026 PA each are explicitly outside the hitter forecast (IDs 571945, 681190,
682989), not silently dropped from reference membership. The reference balances
by construction; the entire forecast population is not scaled to 570 WAR.

68 generic/unknown role records, totaling 22.6 expected PA, remain incomplete.
Their numerical subtotals must not be ranked as fully supported complete value.
DP, GIDP, non-OF throwing and ABS challenge skill have explicit population
estimates, not measured player-specific grades. A zero running estimate is not
itself evidence of no history: the explorer must use the underlying
`baserunning_evidence_tier`, not infer coverage from the sign/nonzero value.

Batting is still league-relative observed-context production, not certified
park-neutral talent. Additional park credit is zero to avoid an unjustified
second correction. This qualification is material for portability and comparison
to FanGraphs WAR. The full-WAR historical comparison, annual paths, current
rights/contracts and explorer are not finished. Proceed to those gates; retain
this assembly as development, with **player walkthrough complete** but **release
not approved**. No new fitting or improvement claim is made here.
