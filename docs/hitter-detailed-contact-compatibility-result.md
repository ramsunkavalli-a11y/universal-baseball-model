# Detailed contact needs source repairs before a fair model comparison

2026-10-04. The older detailed-contact gain is not a result we can transfer
directly into the current hitter candidate. The audit found different populations,
validation, value references and contact coverage, plus confirmed participant
errors in the raw measurements. The right next action is to reconstruct reliable
contact inputs and run one matched comparison, not dismiss contact or start
another algorithm tournament. No model was fitted and no forecast changed.

## What the review established

The old ninety-cell block contains **minor-league contacts only**, not MLB
contacts. All 38,114 player-seasons through 2024 have zero MLB contact exposure.
It pools outcomes across levels, although separate level-exposure counts are
also supplied. The fixed formula `(cell count + .5)/(contacts + 45)` reconstructs
every nonnegative integer cell and its total exactly. These cells are not
park-adjusted. The separate learned park-residual block is a different input.

The old ablation compares 28,183 forecasts with one another fairly on its own
membership. Today's candidate has 30,506 forecasts; 24,029 identities match,
4,154 occur only in the old evaluation and 6,477 only in the current one.
Next-year PA labels agree exactly on all matched identities. Value labels differ
by up to .7423 custom wins because their reference constructions differ; the
older label uses target-season MLB averages and replacement, whereas current
uses its documented origin reference. Neither is full WAR. Therefore .4321 old
RMSE versus .4534 current RMSE is not an isolated test of contact quality.

All older training labels mature by their forecast cutoff. But 20,399 of 28,183
test identities also have earlier rows in training; current excludes the entire
held-player fold. This is a different validation task, **not automatic temporal
leakage**. An operational incumbent forecast can reasonably use earlier labeled
examples of that player. It cannot be renamed the current unseen-player test.
The old equal-weight ensemble also reflects choices made after development
comparisons. Its nominal uncertainty does not correct that research selection.

The park adjustment holds out each hitter within two event folds. That is useful
event evaluation, but does not demonstrate the outer forecast fold's exclusion
from every learned adjustment. Do not import those residuals into current
whole-player validation without a nested reconstruction. Raw cells with a fixed
prior do not have this particular learned-transform dependency.

## Source conflicts and the confirmed repair

There are 670 flagged player-seasons involving 631 people and 93,891 contacts:
missing official count coverage, contacts exceeding recorded PA, or measured HR
exceeding recorded HR. This is a **conflict inventory**, not an estimate of the
fraction of incorrect contacts. There are no duplicate terminal keys or exact
duplicate rows in the nine underlying annual contact files inspected.

The largest discrepancies involve Mexico. All 329 missing 2018 count matches
are labeled AAA in the old table. Sampled games resolve to Mexican League ID
125 in the newer terminals, while the older files retain synthetic league ID
-1. Examples include Elizalde with 275 contacts/14 measured HR against 77
recorded domestic PA/two HR, and Carbonell with 215 contacts/ten HR against
17 domestic PA/no HR. These combine different league coverage; they are not
proof that the players hit impossible numbers of home runs. Mexican League
identity and missing count coverage must remain explicit. Country alone is not
a league classifier: some Mexican League games take place in the United States.

Three selected 2024 players have a smaller, independently confirmed defect.
Official top-level matchup evidence for all ten measured HR in their source
profiles establishes three wrong participant assignments:

| Source assignment | Actual hitter | Game and sequence |
| --- | --- | --- |
| Adam Hall | Casey Martin | 750493 and 74 |
| Cristopher Navarro | Zach Kokoska | 750929 and 76 |
| Drew Maggi | Eddys Leonard | 752195 and 39 |

The named source player scored on the homer rather than hitting it. This matches
the previously documented mutable-batter/pinch-runner defect in
[the participant policy](adr/019-do-not-trust-mutable-source-batter-id-without-contact-reconciliation.md).
Stored newer terminal records agree with the old wrong IDs, so agreement between
those two derived tables was not independent certification.

The repair pilot overlays official matchup identity on **501 contacts in those
ten games**, changes exactly three participant IDs and preserves every physical
field and event result. Maggi's selected-game HR fall from six to five and
Navarro's from three to two; Hall loses the misassigned HR, and the true hitters
gain them. This is not a complete season repair. Ten outcome-selected disputed
HR are not a random sample from which to estimate the overall corruption rate.
The official feeds were captured now, not certified original game-day vintages.

The existing [sequence overlay policy](adr/021-overlay-contact-participant-identity-at-play-sequence-grain.md)
already supplies the correct repair architecture. It was not applied in this
contact branch. Season contacts below PA are too weak a check: Hall's 120
contacts fit inside 212 PA despite the wrong HR. The current raw-shape source
uses related uncorrected terminals, so earlier shape tests need this source
qualification too. The current count-based forecast does not use those shape
features; its forecast and official batting counts are unaffected by this pilot.

## Eleven player source and forecast walkthroughs

The six fixed cases precede inspection. Five additional cases follow the saved
rules: old contact's largest matched gain/harm, false high/low and an ordinary
active forecast. Exact separate-level histories, reconstructed cells, old lag
inputs and four origin-selected peers are saved in the case artifact. Values
below use each old model's own observed value reference; current PA components
are shown separately. These are source/output walkthroughs, not replayed old
model paths or causal explanations of fitted changes.

**Judge after 2024:** 704 MLB PA/58 HR, no minor contact in the three lag years.
Old detailed/stats-only value is 6.933/6.893 against 9.231 observed. Current
99.07% times 535.74 active PA gives 530.75 against 679 actual. The old contact
addition changes this player despite having no own contact evidence: refitting
on the broader population can change his forecast. Do not attribute the change
to measured Judge fly balls. Castellanos, Suarez, Diaz and Schwarber receive
589, 657, 651 and 724 PA; these are workload, not equivalent superstar controls.

**Soto after 2023:** 708 MLB PA/35 HR/121 unintentional walks, no minor contact
in the lag years. Old detailed value 5.775 is worse than stats-only 6.102 against
8.782 observed. Current 99.31% times 638.36 gives 633.93 versus 713 PA.
Detailed contact does not help every star, even when its pooled score improves.
Guerrero, Tatis, Kwan and Witt receive 697, 438, 540 and 709 PA.

**Reynolds after 2018:** 383 AA PA/seven HR, with 256 measured AA contacts;
earlier contact counts are 382 Aplus and 145 A/Aminus. Old detailed/stats-only
.055/.086 both miss actual 4.153; current 15.64% times 81.02 gives just 12.67
versus 546 PA. Available contact history does not rescue this readiness miss.
Navarreto, Woodrow, Hernandez and Nunez receive zero, zero, zero and 43 PA, but
are not fully matched talent comparisons and do not explain Reynolds away.

**Lugo after 2017:** 557 AA PA/13 HR/32 walks/72 K, with 431 AA contacts.
The two older values .225/.230 both have the wrong sign against -.164 actual.
Current 69.31% times 118.16 gives 81.90 versus 101 PA. His opportunity estimate
is much closer than his hitting-value estimate. Guillorme and Kiner-Falefa get
74/396 PA; VanMeter and Burks zero. No defense or position value is measured here.

**Kurtz after 2024:** 35 A plus 15 AA PA/four HR, only 27 measured contacts,
split 17/ten. Old detailed .019 versus stats-only .021 misses 5.721 observed;
current 6.06% times 168.16 gives 10.18 versus 489 PA. Fifty professional PA
cannot make a precise contact profile; this is not evidence to omit pedigree or
claim certainty about his eventual ceiling. Smith gets 493 PA; Barreat,
Alderman and Conticello zero, with unequal pedigree and readiness.

**Langford after 2023:** 200 professional PA/ten HR, including 54 AA/26 AAA PA.
The 126 contacts pool rookie/Aplus/AA/AAA measurements. Old detailed .099
worsens stats-only .169 against 2.250 observed. Current 59.91% times 358.74
gives 214.92 versus 557 PA. More pooled detail is not sufficient to solve fast
elite entry. Pichardo, Parada, Teel and Shaw all get zero PA, but these workload
neighbors do not establish comparable draft/scouting talent.

**Meadows after 2018, largest old gain:** 191 MLB PA/six HR plus 285 AAA PA/
twelve HR; 213 measured contacts are AAA. Detailed value 1.765 improves on
.995 against 4.770 observed. Current 95.22% times 260.50 gives 248.06 versus
591 PA. This is a useful measured young-entrant case, not an example of MLB
contact coverage. Laureano/McMahon/Fowler/O'Neill get 481/539/zero/151 PA.

**McNeil after 2018, largest old harm:** 248 MLB PA plus 241 AA/143 AAA PA,
with 19 minor HR and 293 AA/AAA contacts. Detailed 1.539 worsens stats-only
2.053 against 4.905 actual. Current 97.10% times 454.55 gives 441.37 versus
567 PA. Strong measured contact does not guarantee the fitted block helps.
O'Brien, Ward, Garcia and Austin get 47/48/46/179 PA and have differing ability.

**Tatis after 2021, false high:** 546 MLB PA/42 HR; only four 2019 minor
contacts enter the old window. Detailed/stats-only 3.490/3.613 both miss zero
next-year value. Current 98.98% times 558.65 gives 552.97 PA against zero.
The later absence cannot justify rewriting origin talent or calling four
contacts a health model. Carlson/Baddoo/Chisholm/Soto get 488/225/241/664 PA.

**Judge after 2023, false low:** 458 MLB PA/37 HR, no minor contacts in the
window. Detailed/stats-only 3.830/3.793 both miss 11.067 observed. Current
98.51% times 544.11 gives 536.00 versus 704 PA. Both hitting and workload
matter; direct contact attribution cannot explain these refitted changes.
Frazier/Flores/Pederson/Contreras get 294/242/449/358 PA, not equivalent talent.

**Pujols after 2017, ordinary old value:** age 37, 636 MLB PA/23 HR, no minor
contact. Detailed .981 is close to .932 observed; stats-only .861 is also close.
Current 90.61% times 512.95 gives 464.77 versus 498 PA. This confirms that a
well-predicted case is present; it does not prove contact caused that accuracy.
Cruz/Phillips/Bautista/Granderson get 591/27/399/403 PA, with different aging paths.

## Decision and the next comparison

Source review is complete. The older predictive result remains qualified
development evidence, not recertified by this inventory. No new predictive
benefit or blanket contact failure is established. Seven focused checks pass;
the early test fixture was corrected before the successful audit. A missing
Path conversion stopped the supplementary read before any output; fixing it
changed no preserved audit or forecast. The initial official request was blocked
by the network sandbox; the authorized read then completed all ten captures.
The completion check initially treated the suffix Jr. as Tatis's surname; its
name check was corrected before the completion receipt was written. No evidence
or case membership changed.

Next reconstruct ninety-cell information from league-preserving measurements,
using the existing player-game residual trigger and official sequence overlay.
Keep source IDs, corrected IDs, authority and unresolved conflicts. Audit sampled
unflagged games and do not use names or seasonal HR excess alone as a universal
repair. Reconcile Mexican League coverage separately, and do not mix it into
affiliated AAA or fill missing performance with zero. Include usable MLB
trajectory/result evidence where it exists without adding Statcast measurements.

Then run one predeclared information comparison on current matched targets and
whole-player chronological folds, with fixed opportunity and both current and
translated hitting anchors. Start with raw coherent cells; learned park/opponent
residuals require their own nested source proof. Do not add all of these changes
at once and call the result a pure contact effect. Every new fit still requires
actual saved-model player walks before disposition. Public workload MAE,
readiness, calibrated uncertainty and full player value remain unfinished.
Protected 2026, frozen files and deployed explorer are unchanged.

Evidence: [compatibility inventory](../reports/model-evidence/hitter-detailed-contact-compatibility/report.json),
[selected player sources and forecasts](../reports/model-evidence/hitter-detailed-contact-compatibility/cases.json),
[raw event provenance](../reports/model-evidence/hitter-detailed-contact-compatibility/event-provenance.json),
[official participant adjudication](../reports/model-evidence/hitter-detailed-contact-compatibility/official-adjudication.json),
[ten game repair pilot](../reports/model-evidence/hitter-detailed-contact-compatibility/repair-pilot.json).
