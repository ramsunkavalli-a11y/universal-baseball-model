# ADR 008: Use an exhaustive Performance taxonomy with a FaBIO-compatible core view

- Status: Accepted for foundation design
- Date: 2026-08-15

## Context

FaBIO is the strongest public precedent for the universal Performance/Profile layer because it reduces plate appearances to a small, interpretable set of fielding-independent/non-fielding-dependent event families and assigns league-context run values.

The familiar FaBIO shorthand is a 12-bin taxonomy:

1. BB + HBP
2. K
3. IFFB
4-6. Pull / Center / Opposite OFFB
7-9. Pull / Center / Opposite LD
10-12. Pull / Center / Opposite GB

However, Collier's earlier detailed methodology explicitly excluded plate appearances ending in a **bunt or foulout** from the batted-ball sample. That matters because the modern MLB Stats API/Gameday feed exposes explicit `bunt_grounder`, `bunt_popup`, and `bunt_line_drive` trajectory labels and because foul-territory airborne outs are not rare enough to ignore silently.

The universal model also has a stricter coverage requirement than the original exploratory work: every affiliated player and every usable true PA should remain accountable in the Performance layer, with explicit evidence quality rather than hidden denominator changes.

## Reuse and empirical evidence

The reusable source uses the official Gameday trajectory vocabulary:

- `ground_ball`
- `line_drive`
- `fly_ball`
- `popup`
- `bunt_grounder`
- `bunt_popup`
- `bunt_line_drive`

Trajectory coverage among physical in-play pitches was essentially complete in the audited 2005, 2015, 2024 Rookie/complex/DSL, and 2025 AAA slices.

### `popup` is a strong public-data proxy for IFFB

Across the four audited eras/levels, every `popup` with a known `hit_location` was first touched by positions 1-6 (pitcher/catcher/infield); **0% were first touched by an outfielder**. Narrative hit-like outcomes were roughly 0-0.5%.

That is substantially stronger evidence than simply assuming that the words “popup” and “infield fly ball” are synonyms. For the universal public-data taxonomy, Gameday `popup` is accepted as the IFFB family.

### `fly_ball` is a strong proxy for OFFB

- 2005 AAA: 100% of known-location `fly_ball` events were first touched by an outfielder.
- 2015 AAA: 100%.
- 2024 Rookie/complex/DSL: ~98.4%.
- 2025 AAA: ~98.6%.

Small modern deviations are expected because `hit_location` is the first fielder to touch the ball and defensive positioning is not the same concept as trajectory. The trajectory label itself remains the primary signal. Gameday `fly_ball` is accepted as the OFFB family.

### Bunts are a real special family

Bunt trajectories represented approximately:

- 2.6% of in-play balls in 2005 AAA;
- 2.8% in 2015 AAA;
- 0.7% in 2024 Rookie/complex/DSL;
- 1.3% in the audited 2025 AAA slice.

They are too common historically to disappear from Performance, but they are strategically selected contacts and were explicitly excluded from Collier's detailed FaBIO sample. They should not be silently relabeled as ordinary GB/LD/IFFB.

### Foul airborne outs cannot be recovered safely from spray-angle magnitude alone

Descriptions mentioning foul territory represented roughly 7-10% of `popup + fly_ball` in the tested slices, heavily concentrated in popups.

The public Petti/pybaseball spray transform places the foul lines at roughly ±45°, but the coordinate evidence is not precise enough to use that as a hard fair/foul classifier:

- most historical foul popups fall outside the approximate fair sector, but some remain inside it;
- many foul flyouts remain inside ±45°;
- some officially in-play ground balls fall outside ±45°, especially in older data.

Therefore **spray angle remains a direction measurement, not a fair/foul detector**. Foul-airborne status, when used, must come from a separately certified source flag/narrative rule rather than an angle cutoff.

## Decision

### 1. Performance accounting is exhaustive

Every true PA that passes basic source-quality requirements remains in the top-level Performance accounting. We do not reproduce the historical practice of making bunts/foulouts vanish from the denominator.

For each league/season/context normalization, special events can receive their own empirical average run value or be valued through the official structured PA outcome layer. The exact run-value implementation will be backtested later, but **coverage is not sacrificed to force 12 bins to be exhaustive**.

### 2. The FaBIO 12 bins become a core skill/profile view

The interpretable core taxonomy is retained for events where its assumptions fit:

- `popup` → IFFB
- `fly_ball` + certified direction → Pull / Center / Opposite OFFB
- `line_drive` + certified direction → Pull / Center / Opposite LD
- `ground_ball` + certified direction → Pull / Center / Opposite GB
- official structured BB/HBP → BB+HBP
- official structured K → K

Direction uses ADR 007's coordinate-derived field thirds.

This produces a **FaBIO-compatible core view**, not an assertion that the entire baseball universe naturally contains only 12 event types.

### 3. Bunts remain explicit special events

Preserve the source trajectory subtype:

- `bunt_grounder`
- `bunt_popup`
- `bunt_line_drive`

A later model may pool these hierarchically if sample sizes require it, but the canonical evidence layer does not erase the subtype.

Bunts are excluded from ordinary GB/LD/IFFB skill rates unless a later out-of-time validation demonstrates incremental predictive value from including them.

### 4. Foul-airborne status remains an explicit eligibility attribute

Do not infer foul/fair from spray angle.

The source descriptions make foul-territory airborne outs observable, and Collier's detailed methodology excluded them. Before a production model depends on the flag, the narrow narrative rule must be certified and versioned.

Until then:

- the raw airborne trajectory and geometric spray angle are preserved;
- Performance still accounts for the actual official PA outcome;
- the core FaBIO profile can expose `core_profile_eligible` separately from the underlying trajectory;
- sensitivity analysis can compare inclusion versus exclusion of flagged foul-air events rather than silently choosing one convention.

### 5. Unknowns remain unknown

If trajectory, direction, or another required piece of evidence is missing/conflicting, the event is not imputed into a favored bin. It remains explicitly unclassified for that subcomponent and reduces the effective evidence/sample size.

## Canonical conceptual fields

The eventual normalized BIP evidence should distinguish at least:

- `source_trajectory` — original Gameday label;
- `trajectory_family` — IFFB / OFFB / LD / GB / BUNT / UNKNOWN;
- `spray_angle` — continuous coordinate-derived angle when available;
- `direction` — Pull / Center / Opposite when applicable;
- `special_event` — e.g. bunt subtype or certified foul-air flag;
- `core_profile_eligible` — whether the event enters the FaBIO-compatible skill view;
- provenance / source-quality fields.

The exhaustive Performance event and the core Profile classification are related but are **not the same column**.

## Why this is preferable to cloning FaBIO literally

It preserves the strongest part of Collier's methodology—a compact, interpretable skill profile—without inheriting hidden sample exclusions as though they were universal truths. It also allows historical comparability: a FaBIO-compatible view can be produced for benchmarking, while the project's primary Performance layer can remain exhaustive and uncertainty-aware.

## Remaining gate

Before implementing the full PA event mapper:

1. certify the narrow foul-airborne description rule and quantify its sensitivity;
2. define the official structured non-BIP outcome mapping (BB, HBP, K, interference, sacrifices, etc.);
3. define the league/context run-value target and how special events enter Overall Performance;
4. backtest the 12-bin core versus expanded/exhaustive alternatives out-of-time rather than assuming the historical taxonomy is optimal.
