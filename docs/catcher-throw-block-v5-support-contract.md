# Count usable future MLB throwing and blocking evidence

2026-10-06, before prediction scoring. The source extension reconciles 1,018
throwing and 870 blocking records with native contributions. Eight early throwing
records have inconsistent opportunity identities and remain unknown talent;
five missing blocking records remain coverage gaps. Keep them, not invented zeros.

The component question is later MLB skill given actual tracked opportunities.
For each origin from its source start through 2024, except the separate 2020
origin, retain anyone with a channel record in the previous three calendar years,
including quarantined histories. Use only valid source rows for inputs. Keep
older incomplete histories flagged. No-history players need an uncertain prior,
not a measured average grade; minor-league-only transfer is not established here.

Define outcomes over the next three calendar years, complete by 2025, with at
least two measured seasons. Throwing needs at least 100 actual tracked attempts;
blocking needs at least 3,000 source blocking chances. Any positive native catcher
exposure with a missing or invalid channel measurement makes quality unknown.
Non-arrivals, exits and insufficient samples stay in coverage, not zero-quality
training. Do not select a player's best later year. Short 2020 MLB exposure
enters at its actual count; no cancelled MiLB season is synthesized.

Throwing units are native runs per 100 tracked attempts; blocking units are
native runs per 1,000 blocking chances. Context is already adjusted in the
source numerator. These different exposures must later be forecast separately;
they cannot be replaced by batting PA, innings or framing pitches.

Count distinct people, complete windows and training origins for each actual
origin and player-ID-modulo-five fold. Training labels must finish by the origin,
and the held player's entire history is excluded from learned support. Count
age groups at most 24, 25–29, 30+, unknown; weighted exposure below 10/10–49/50+
for throwing and below 500/500–2,999/3,000+ for blocking, jointly. Flag fewer than
20 matching people, extrapolation and source boundary loss. Recover unknown age
only using the already tested consistent cutoff-known dated-snapshot procedure.

Trace fixed source catchers and the two smallest valid origin samples, using
three peers selected by age, exposure and ID without outcomes. Later quality
availability must not change origin membership or input/support profiles. After
this audit, lock the exact neutral versus shrunk-history comparison; no learners,
hyperparameter sweeps, source repairs based on a desirable score or 2026 use.
