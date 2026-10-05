# Six player checks of the new overseas batting source

2026-10-05. These are source walks, not new MLB projections. The same fixed
selection rule chooses the largest positive-PA row, the smallest positive-PA
row and the first zero-PA row in each league, using stable source-key and club
order for ties. The cases were not selected by future MLB success. All selected
controls are retained, including the unresolved Japanese identity.

The comparison people are selected without future outcomes by the captured
exposure and birth-year distance where both dates are known, otherwise exposure
alone. The original preparation mixed the focal three-year exposure with peer
snapshot-only exposure. The [window correction](hitter-international-2026-peer-window-amendment.md)
preserves those records and supplies comparisons using the same 2024 through
captured 2026 window on both sides. All totals below use the corrected window.
These are source exposure controls, not evidence of equal talent or role. No
peer supports a league translation or MLB job estimate.

## The six count changes

| Source control | Qualified source key | PA through 2025 in the 2024 onward window | Added 2026 snapshot PA | PA through the snapshot |
|---|---|---:|---:|---:|
| 栗原　陵矢 | NPB 01705130 | 930 | 628 | 1,558 |
| 石黒　佑弥 | NPB 01105159 | 0 observed | 1 | 1 |
| 尾形　崇斗 | Unknown | No qualified join | 0 in selected table row | No qualified join, stored subtotal 0 |
| 최원준 | KBO 66606 | 957 | 653 | 1,610 |
| 김시앙 | KBO 51303 | 7 | 1 | 8 |
| 최준용 | KBO 50556 | No earlier first-team row | 0 | 0 observed |

PA means plate appearances. Rates below are unadjusted counts divided by PA;
they are not MLB-equivalent talent. Unintentional walks exclude intentional
walks. No denominator means an unobserved rate, not a zero rate.

## Kurihara adds substantial observed hitting evidence

栗原　陵矢 has 598 PA and 20 HR in 2024, 332 PA and eight HR in 2025, and
628 PA and 40 HR in the 2026 snapshot. The combined source subtotal therefore
changes from 930 PA and 28 HR to 1558 PA and 68 HR. The raw HR rate rises
from 3.01% to 4.36%; strikeouts move from 17.85% to 18.10%, and unintentional
walks from 9.35% to 10.33%. This is real additional source exposure, not a
forecasted breakout or proof that the NPB power rate transfers unchanged.

His NPB key joins all three years even though the pinned crosswalk has no MLB
key. The aligned controls are 辰己　涼介 (11015138, 1587 window PA),
周東　佑京 (21925136, 1457) and 中野　拓夢 (41445153, 1835), with captured
birth dates in 1996. Their selection reflects age and exposure, not equivalent
power, defense or likelihood of moving to MLB. No hitting or workload head
received these new counts.

## Ishiguro demonstrates why games and an MLB key are insufficient

石黒　佑弥 has three games and zero PA in 2024, eight games and zero PA in
2025, and thirteen games with one PA in the snapshot. NPB key 01105159 joins
the records; MLBAM key 831630 is an identity link, not evidence of MLB experience
or hitter eligibility. Before the snapshot his rates are unobserved. After it,
the one PA falls in the residual other-event category and cannot support a
meaningful hitting estimate.

The source controls 西舘　昂汰 (11615159), 石原　勇輝 (41145159) and
庄司　陽斗 (81985159) also have one snapshot PA and recorded 2001 birth
dates. This illustrates the pitching and tiny-denominator rows in a batting
table; they must not be counted as established hitter forecasts. Current roster
sections were used only to exclude staff, not to backfill historical roles.

## Ogata remains an unresolved identity rather than a zero career

尾形　崇斗 is the fixed zero-PA control. His selected table row has zero PA,
but neither a qualified NPB key nor an MLB key is present. The before and after
subtotals are stored as 0 with `key_qualified=False` and no joined rows.
That combination means the history join is unknown, not that his earlier
professional career contained zero PA or that his talent is zero. Every rate
is unobserved, and no prior-name guess supplies a key.

The zero-PA controls 池田　隆英 (01105134), 泉　圭輔 (01105138) and
飯田　琉斗 (01105152) do have source keys. Their existence does not repair
Ogata's join. The selected case remains in the review to expose that limitation
rather than being replaced by an easier player.

## Choi Won-joon retains his history without an MLB key

최원준 has 508 PA and nine HR in 2024, 449 PA and six HR in 2025, and 653
PA and nine HR in the snapshot. KBO key 66606 produces 957 PA and fifteen HR
before, then 1610 PA and twenty-four HR after. Raw strikeouts fall from 14.32%
to 13.85%, unintentional walks rise from 7.63% to 9.07%, and HR move from
1.57% to 1.49%. A missing MLB key does not erase these Korean counts.

His captured birth date is unavailable, so the aligned controls are exposure-only:
문보경 (69102, 1616 window PA), 최형우 (72443, 1594) and 박해민
(62415, 1665). Known ages for some controls cannot create a missing focal age.
No promotion probability, contract assumption or MLB translation is inferred
from being a regular player in Korea.

## Kim Si-ang still has almost no observed hitting denominator

김시앙 has seven first-team PA in 2024, no collected first-team row in 2025,
and one PA across two games in the snapshot. KBO key 51303 produces seven PA
before and 8 after, with one single and one strikeout across the selected
window. Each raw single and strikeout rate changes from one-seventh to
one-eighth, or 14.29% to 12.50%. This arithmetic is not evidence of improved
contact talent. The absent 2025 first-team row does not certify absence from
farm teams or all professional baseball.

Aligned exposure-only controls 조민영 (55534, 8 window PA), 안인산
(50901, 9) and 강민균 (53103, 7) have no captured birth date. Even when an
exact source key works, eight PA are not a satisfactory independent talent sample.
MLB identity and historical role remain unknown here.

## Choi Jun-yong has games but no hitting rate

최준용 has KBO key 50556 and four games with zero PA in the snapshot. No
2024 or 2025 first-team row joins in the selected window. The before and after
observed batting subtotal is 0; rates are unobserved. Four games do not mean
four batting appearances, a healthy hitter role or zero professional talent.

정해영 (50662), 박시후 (50812) and 김동주 (51230) are the fixed
exposure-only zero-PA controls. Source keys allow records to be retained and
audited, but they do not establish that any of these people belong in the
future hitter forecast population.

## What these checks establish

For every control, replacing future snapshot PA with 999,999 leaves the 2025
subtotal unchanged. Independent reconstruction verifies the archived count
cells before these subtotals. All six cases have null MLB talent forecasts,
opportunity forecasts and predictive outcomes in the review receipt: none were
estimated, and no new 2026 MLB outcome was retrieved or scored.

The source walkthrough is complete within this dated snapshot scope. Unknown
identity, absent other-league history, tiny denominators, limited peer matching,
park exposure, historical roles and overseas completion remain limitations.
The disposition is to retain source evidence, not approve a model change.
