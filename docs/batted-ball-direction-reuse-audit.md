# Batted-Ball Direction Reuse Audit

Date: 2026-08-15

## Why this audit exists

The proposed FaBIO-like Performance layer needs batted-ball direction categories (Pull / Center / Opposite) crossed with batted-ball type. This is exactly the kind of small-but-easy-to-get-wrong transformation the project should **reuse and certify**, not casually reinvent.

This note evaluates available public precedents before production code is allowed to depend on a direction transform.

## FaBIO / public direction precedent

Matt Collier's public FaBIO descriptions divide batted-ball direction into **thirds of the field** based on batter handedness. This is the same broad Pull / Center / Opposite framing used by common public batted-ball direction statistics.

FanGraphs' public batted-ball direction definition also describes three equal field sections: **30 degrees each** across the approximately 90-degree fair field. That gives a natural geometric candidate for a continuous spray-angle transform:

- left-field third: field angle below -15°;
- center third: -15° through +15°;
- right-field third: field angle above +15°.

Handedness then determines whether the left/right third is Pull or Opposite.

These boundaries are a methodological precedent, not yet a certified universal source transform.

## Public Statcast coordinate transform already exists

### pybaseball

`pybaseball.datahelpers.statcast_utils.add_spray_angle()` already implements the widely reused Statcast `hc_x` / `hc_y` conversion:

`atan((hc_x - 125.42) / (198.27 - hc_y)) * 180/pi * 0.75`

Its optional adjusted form mirrors left-handed batters.

This is a mature public implementation and is preferable to deriving unexplained constants ourselves. The project does not need to add pandas/pybaseball as a runtime dependency merely for this one equation; the tiny transform can be ported exactly into a Polars expression with attribution and unit tests.

### Bill Petti / Zimmerman precedent

Bill Petti's published Statcast database code uses the same `125.42`, `198.27`, and `0.75` transform and notes that the underlying calculation was originally produced by Jeff and Darrell Zimmerman. In that field-coordinate convention, approximately -45° is the left-field line and +45° is the right-field line.

This is the reference implementation the project should match.

### SportsDataverse caution

SportsDataverse currently contains a Polars `spray_angle()` helper that cites Bill Petti's public formula, but its implementation uses:

`atan2(hc_x - 125.42, 198.27 - hc_y) * 180/pi`

without the `0.75` factor. Its docstring also says positive values represent the pull side, while the actual handedness transform leaves a right-handed left-field ball negative and flips left-handed values, which makes pull negative for both sides.

That discrepancy does **not** make SportsDataverse broadly unsuitable; it remains a strong candidate for later Minor Statcast retrieval. It does mean we should not import or copy this particular helper without independent calibration.

## Candidate transform for this project

To avoid adjusted-sign ambiguity, keep the first canonical variable as a **field-relative angle**:

- negative = left field;
- zero = straightaway center;
- positive = right field.

Use the Petti/pybaseball calibration exactly:

`field_spray_angle = atan2(hc_x - 125.42, 198.27 - hc_y) * 180/pi * 0.75`

Then classify by batter hand:

| Batter hand | Pull | Center | Opposite |
|---|---|---|---|
| R | angle < -15° | -15° to +15° | angle > +15° |
| L | angle > +15° | -15° to +15° | angle < -15° |

A switch hitter uses the per-event batting side (`stand`), not a career-level handedness label.

Boundary convention should be deterministic: exactly ±15° belongs to Center unless later validation demonstrates a reason to do otherwise.

## Why coordinates should not automatically become the universal direction source

The formula only helps when `hc_x` and `hc_y` exist. The universal model cannot silently drop lower-level batted balls whose coordinate coverage is structurally absent.

The reusable source also carries non-sensor `hitData` fields such as `hit_location` and `bb_type`. Those may provide much broader stringer coverage than launch-speed/launch-angle tracking. Before choosing the universal direction evidence hierarchy we need to measure:

1. `hc_x + hc_y` coverage among in-play pitches by level/league/season;
2. `hit_location` coverage over the same denominator;
3. agreement between coordinate-derived thirds and a coarse handedness-adjusted field-location mapping when both exist;
4. whether either signal exhibits park/stringer-specific anomalies, following the Ben-Porat measurement-first lesson.

A likely eventual hierarchy is coordinate-derived direction when certified coordinates exist, then a separately validated stringer-location direction fallback, then `unknown` rather than imputation. That is only a hypothesis until the coverage audit is run.

## Promotion gate

Do not make Pull / Center / Opposite a production Performance feature until all of the following hold:

- the Polars implementation matches the public Petti/pybaseball reference on deterministic fixtures;
- ±15° field-third classification is explicitly tested by batter hand;
- coordinate and stringer-location coverage are measured across AAA, AA, High-A, Single-A, ACL/FCL/DSL and older history;
- disagreement rates are inspected rather than silently reconciled;
- the chosen fallback hierarchy emits an explicit direction-evidence source and `unknown` state.

This is a small transformation, but it directly controls 9 of the 12 FaBIO event bins. It deserves source-level certification before modeling.
