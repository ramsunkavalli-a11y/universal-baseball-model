# Refreshed defensive skill layer: reuse, not another tournament

2026-10-08. Twelve reviewed channels now have 2027-oriented skill estimates for
4,694 provisional hitter identities. They combine historical measurements with
the reconciled 2026 sources using the existing recipes. This is a reusable
component layer, not a full-WAR forecast or a new accuracy gain.

The seven range positions retain three years weighted 1, 0.5, 0.25 and a
3,000-out prior; outfield observations are centered before shrinkage and first
base uses the previously tested historical prior. Framing retains 6,000 received
pitches of prior exposure, catcher throwing 100 attempts, blocking 3,000 chances,
outfield arms 300 runner opportunities and first-base receiving 600 throws.
The same source player's held group is excluded from empirical position references.
No prior search, age fit or new future-outcome selection was performed.

## Baseball interpretation of the actual estimates

| Player | Refreshed skill estimate | What to take from it |
| --- | --- | --- |
| Bailey | +1.154 framing runs/1,000 received pitches; +3.695 throwing runs/100 attempts; -0.146 blocking runs/1,000 chances | Different skills can point in different directions; his strong older framing still matters. |
| Lindor | +0.769 SS range runs/500 innings | His mildly negative 2026 range does not erase multiple years of stronger evidence. |
| Olson | +1.633 range runs/500 innings; +0.209 receiving runs/100 throws | Range and receiving independently contribute, with substantial history for both. |
| Trevino | +0.375 framing; -0.315 throwing; +0.164 blocking, in the same units as Bailey | Positive 2026 throwing alone does not erase prior weakness. Pitching innings never enter the catcher estimate. |
| Judge | +0.408 RF and -0.887 CF range runs/500 innings; +0.377 arm runs/100 opportunities | His forecast must depend on where he plays. Do not add RF and CF rates as though he plays a full season at both. |
| Eldridge | -0.365 range runs/500 innings; +0.184 receiving runs/100 throws | Positive but limited observed range moves him above the -0.602 first-base prior, not automatically above average. His receiving evidence is separately positive. |
| Ohtani | No observed position-defense skill in this three-year input window | With a DH role, applicable position-defense exposure is zero. This is not an assertion that his pitching has no value. |
| Lovich | No observed MLB defensive skill | Comparable/profile estimates remain uncertain. A number cannot stand in for evidence of MLB defense. |

These are rates, not seasonal runs. All projected-opportunity and awarded-run
fields are intentionally empty until the role/exposure layer is connected.
For example, a catcher has a hypothetical first-base fallback in the rate grid,
but it awards nothing without first-base exposure. The explorer must show the
applicable positions, not sum the grid or rank unmeasured prior grades as facts.

The eight cases have source histories and 24 exposure-selected peers. Bailey's
peers include Raleigh, Stephenson and Dingler; Olson's include Alonso, Busch and
Walker. Peers for an entirely unmeasured player are merely zero-exposure source
comparisons, not evidence of similarity in future talent. Names absent from
2026 batting remain keyed by ID until the biography/membership refresh.

The existing official-position arm rule is retained: eight 2026 players have
small non-OF stints missing from native splits, so their all-position runner
denominators cannot certify an isolated OF rate. Their published arm runs are
retained; they are not turned into measured zero skill. This conservative rule
loses some useful mixed-position evidence and remains a visible v1 limitation.

## Still required before release

Position/exposure, baserunning, DP, non-OF arms and ABS decisions remain separate
integration work. The failed individual DP history test is not promoted simply
to fill a cell. Unmeasured minor defenders still need a supported profile model
or an explicitly uncertain comparable estimate. Then test the complete additive
forecast on matched historical players and walk its gains and misses.

Five adapter checks pass, in addition to 43 intake/accounting/reliability checks.
They cover future/duplicate inputs, position centering, independent catcher
denominators, recency, mixed-arm eligibility and missing-evidence disclosure.
They establish correct reuse, not improved prediction. See
[assembly evidence](../reports/model-evidence/hitter-2027-v1/defense-rates-assembly.json).
