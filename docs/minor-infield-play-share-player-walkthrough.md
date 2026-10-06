# Infield play-share: players behind the result

2026-10-05. [Contract](minor-infield-play-share-contract.md),
[scores](minor-infield-play-share-result.md), and
[full source/input/peer/replay traces](../reports/model-evidence/minor-infield-play-share/player-traces.json).
All 13 player-origins were inspected before disposition. Eight were named before
fitting; five additional origins follow the locked error-selection rules, with
one case covering both largest gain and false low. No favorites were forced into
eligibility. All 150 saved models reproduce their complete query populations.

## Reading the numbers

Origin means statistics available through that season; prediction is next year.
Minor ground-ball exposure is shared team exposure while at that position, not
balls the player alone should have caught. Past years count half/quarter, so
counts can be fractional. Expected plays come from OTHER defensive teams in the
same season/league, with handedness/park cells shrunk toward their league.
An excess divided by exposure + 600 is a coarse signal, not true individual range.

Quality below means native MLB range runs per 1,500 defensive outs; roughly
500 innings. It is not WAR, Gold Glove voting or overall defensive runs. Observed
quality requires substantial MLB infield time. No MLB defense means zero
delivered range runs but UNKNOWN quality. The simple benchmark is this experiment's
fixed age/level/history model, not a replay of the current full hitter model.

| Player / origin | Benchmark quality | Complete-exposure quality | Observed next-year quality | What the comparison shows |
| --- | ---: | ---: | ---: | --- |
| Witt / 2021 | -1.82 | -3.33 | -3.41 | Better rookie-rate estimate; not proof of his later ceiling |
| Volpe / 2022 | -0.25 | -0.55 | +0.34 | Small harm; selected proxy's positive signal does not survive the broader denominator |
| Peña / 2021 | -1.52 | -1.93 | +1.99 | Misses a good MLB defender despite slightly positive minor SS evidence |
| Abrams / 2021 | -2.77 | -3.12 | -4.85 | Correct direction, still too mild; sparse young-AA support |
| Lawlar / 2022 | -2.73 | -2.77 | +8.76 | Sparse support and noisy 231-out MLB sample; not a reliable elite grade |
| Mayer / 2024 | -1.27 | -1.34 | +3.91 | Wrong direction on his first MLB fielding season |
| Downs / 2018 | -1.41 | -3.67 | unknown | No next-year MLB defense; no truth label for the poor quality forecast |
| Mateo / 2018 | +0.35 | +0.13 | unknown | No next-year MLB defense; cannot reject his eventual fielding ability |
| Rafaela / 2024 | -0.84 | -0.36 | outside IF-quality target | Main delivered gain is predominantly outfield defense |
| Edwards / 2023 | -1.11 | +0.05 | -6.51 | Positive multi-position minor evidence makes a major miss worse |
| Abrams / 2023 | -0.52 | -0.34 | -5.81 | Existing negative MLB evidence is compressed too aggressively in this simple model |
| Peguero / 2024 | -0.57 | -1.02 | -1.20 | Coherent modest improvement, with useful MLB history |
| Linares / 2024 | +6.48 | +6.71 | unknown | Catcher with a tiny 2B cameo; unsupported conditional extrapolation, not evidence of elite IF talent |

## Source → adjustment → forecast → reality

**Witt, 2021.** His ledger includes 317 rookie SS ground balls in 2019 and
2021 AA/AAA SS exposures of 490/522, plus 138 at 3B. There is no invented 2020
performance. Weighted SS credits are 205 versus 222.93 expected on 1,091.25
shared ground balls: (205 - 222.93)/(1,091.25 + 600) = -0.01060.
The selected-touch rate is only -0.00049. Same-fit removal of the new signals
raises quality from -3.33 to -2.35; the observed 2022 rate is -3.41.
Delivered runs barely move -0.017 → -0.082 versus -8.65 actual. Thus quality can
improve without fixing opportunity or the tail of delivered value. Young AAA
quality-profile support is 16 distinct training people, not 54 (the delivered
head's count). Origin-known peers Arias, Peraza and Gorman have very different
realized fielding rates; none is excluded for disappointing results.

**Volpe, 2022.** 2022 AA/AAA SS exposures are 1,013/205; the pool also includes
half-weight 2021 A/A+ evidence and brief other positions. SS credits 337.5 versus
342.09 expected on 1,631.5 exposures produce -0.00206, while the selected-touch
rate is +0.01634. New signals mechanically lower the same fitted quality mean
0.118 runs; the benchmark/candidate difference is larger because coefficients
were refitted as declared. Actual MLB range is +0.90 runs over 4,040 outs.
Peers Dale, Rocchio and Tena include a non-arrival and two negative measured rates.
Neither appealing rankings nor this case justify assigning a favorite a bonus.

**Peña, 2021.** His latest AAA SS slice has 61 credits on 242 ground balls,
versus 54.6 expected; older A/A+ evidence is worse. The three-year pool has
103.5 versus 102.08 credits on 469.5 SS exposures: +0.00133 after shrinkage.
The new signals add only +0.038 quality runs in the same fit, but the overall
refitted prediction is -1.93 rather than -1.52. Actual 2022 range is +4.65 runs
over 3,495 outs. This is weak representation/transport, not a proved scorer bug.
His age/exposure-nearest AAA-labeled peers Encarnacion, Rey and Gozzo do not
field in MLB next year; a highest-observed batting level is not readiness proof.
Quality support is only 16 people. This head does not contain scouting/pedigree.

**Abrams, 2021.** Current AA SS exposure is 340 ground balls/68 credits against
73.3 expected, with a smaller 2B slice and quarter-weight rookie history.
Pooled SS residual is -2.44 credits on 425 exposures. Quality moves -2.77 →
-3.12 against -4.85 actual; delivered -0.081 → -0.098 against -6.75.
Young-AA quality support is three people. Nearest peers Castillo, Barreto and
Garcia all have no next-year MLB defense. Getting the sign right does not
validate a precise value projection or justify an across-the-board young boost.

**Lawlar, 2022.** SS credits across A/A+/AA/rookie contexts total 177 versus
174.99 expected on 868.5 weighted exposures. His selected-touch signal is
-0.01841, whereas complete-exposure is +0.00137: assigning blame through the
first-handler filter really changes the input. Nevertheless delivered runs
barely change -0.148 → -0.142 versus +1.35 actual. His +8.76 quality rate comes
from only 231 MLB outs and is not a ceiling estimate. Quality support is four
people. Mayo, De Los Santos and Del Rosario are the origin-known peers; all
are next-year non-arrivals. Peer selection is not evidence that those prospects
had identical talent, positions or organizations.

**Mayer, 2024.** His 2024 AA SS record contributes 108 credits versus 115.7
expected on 608 ground balls. The full pool has 209.75 versus 218.78 on 1,133.25.
Small 3B evidence is positive but heavily shrunk. Same-fit signal contribution
is -0.078 quality runs; final -1.34 misses +3.91 over 926 MLB outs. Delivered
0.025 → 0.023 misses +2.41. Quality support 19 remains sparse. Garcia,
Fernandez and Lee have no next-year MLB defense; the good Mayer outcome does
not license awarding all similarly aged minor players the same expectation.

**Downs and Mateo, 2018.** Downs has 842 current 2B ground balls and 447 SS,
plus 2017 SS exposure. His SS residual is -30.11 on 745 weighted ground balls;
complete signal predicts -3.67 quality and -0.136 delivered runs. All of Downs,
Vilade, Rondon and Taylor have zero MLB defense in 2019. Quality support is
ZERO, so do not call the poor rate projection verified. Mateo has 1,434 current
AAA SS ground balls and older A+/AA history; SS pool is 451.5 versus 444.8
expected on 2,098.25. Small negative 2B evidence partly offsets positive SS.
Both delivered forecasts remain small positives (+0.215/+0.201) before zero
2019 defense. Peers Edman, Neuse and Lopez actually arrive and supply positive
range. This horizon says nothing decisive about Mateo's later career.

**Rafaela, 2024: largest gain AND largest false low.** His minor SS pool is
35.5 credits versus 28.53 expected on just 140.25 exposures. Recent MLB role
shares are approximately 48% SS/49% CF. The candidate adds 0.050 delivered runs
(0.346 → 0.396), against +19.42 actual. Next year's official IF outs are only
495 of 3,997. This is a minuscule correction on an enormous miss, and most
target value is outside the infield. It is not evidence the minor SS proxy
identified an elite MLB center fielder. Peers Neto, Noel and Harris show mixed
position trajectories and actual range; all remain in the trace.

**Edwards, 2023: largest harm.** His minor histories span 2B, 3B and SS, with
particularly positive 3B credit residual (+15.54 on 268.25 weighted exposures).
Known MLB range input is already negative (-1.35 per 1,500 outs after shrinkage).
The proxy's same-fit quality contribution is +1.318; quality goes -1.11 → +0.05
before -6.51 actual. Delivered -0.474 → -0.338 likewise worsens against -7.79.
Future defense is at IF positions, but this player-aggregate target does not
isolate transport of his strongest minor position. Quality support is 18.
Vargas, Gelof and Garcia peers have mixed future quality. Ball difficulty,
pitcher contact mix, positioning and future role remain unresolved, not excuses
to tune a penalty to Edwards.

**Abrams, 2023: largest false high.** His minor evidence has become a fading
264-ground-ball SS pool with only +3.23 excess credits. Current role is SS.
Known MLB input is -2.69 after shrinkage, yet the coarse quality benchmark is
only -0.52 and complete proxy -0.34, versus -5.81 actual. Delivered -0.946 →
-0.938 versus -13.61 is essentially unchanged. This failure is mostly the
simple benchmark's compression/role-exposure representation, not the new proxy
creating a large boost (same-fit delivered contribution +0.013). Neto, Witt
and Rafaela peers have contrasting outcomes. No injury or motivation explanation
is inferred from later box-score results.

**Peguero, 2024: ordinary useful case.** The pool includes 2024 AAA 2B/SS
exposures of 431/786 and prior AA/AAA. Weighted residuals are -5.51 at 2B and
-8.96 at SS; known MLB history is -1.48 after shrinkage. Complete quality -1.02
is nearer -1.20 actual than benchmark -0.57. Delivered -0.446 → -0.476 against
-0.480. Same-fit delivered signal is -0.029 and quality signal -0.346. Quality
support is 71. Jung, Sweeney and Tena peers include both positive and negative
future outcomes. This is a sensible small gain, not enough to overturn the cohort.

**Linares, 2024: unsupported non-arrival.** His latest infield evidence is
51 ground balls at 2B in 2023, half-weighted to 25.5 with six credits versus
4.58 expected. His observed role is 88.5% catcher. Complete quality +6.71 is
mostly the existing coarse benchmark (+6.48), not these few excess plays;
the same-fit contribution is +0.096. Quality-profile support is ZERO. He and
peers St. Laurent, Hadeen and Diaz have no 2025 MLB defensive outs, so quality
truth remains unknown, not zero. Delivered forecast is only +0.008 versus
zero. This numerical conditional forecast must not become a published general
defensive grade. Tiny cameos do not establish future positional talent.

## Judgment

The corrected denominator changes measurements substantially for some players,
but most changes wash out at delivered value. Simple benchmark compression,
future position mix and sparse conditional support are genuine limits. No
identified outcome requires a personal override; no source bug is inferred from
disagreeing with a player's reputation. Lower-level zero participation cannot
validate or reject his eventual talent. The candidate is not promoted; neither
this test nor the older denominator-flawed tests close minor-league defense.

Walkthrough complete means these limits were reviewed, not that the model passed.
