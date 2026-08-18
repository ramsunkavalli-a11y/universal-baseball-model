# Defense v1 source / architecture checkpoint

Last updated: 2026-08-18

Status: **SOURCE ARCHITECTURE ESTABLISHED; DEFENSE v1 NOT YET FROZEN.**

## Downstream need

Defense must eventually provide a player × position defensive-quality forecast that can be combined with the already-frozen Position/Role and Playing Time channels. Position/Role answers *where* a player may play; Defense must answer *how much defensive value above/below an appropriate baseline* the player is expected to contribute there.

Do not collapse positional adjustment, defensive skill, opportunity, and team allocation into one model.

## Reuse result: range / OAA

Pinned public implementation: SportsDataverse `0.0.75`, upstream commit `1dafadb38c5240d8e29a0f818efbabe04cd6c417`.

### MLB

The frozen June-2024 reuse POC passed the upstream month-vs-season Savant oracle gate:

- 116,355 pitches;
- 20,623 balls in play;
- 18,820 usable OAA opportunities (`91.26%` of BIP);
- 263 fielders matched to the full-season 2024 Savant OAA leaderboard;
- Pearson correlation `0.3045` versus the frozen `>= 0.30` month-vs-season gate.

SportsDataverse's own full-season 2024 live test reports Pearson about `0.605` against Savant OAA, with a frozen floor of `0.55`.

**Decision:** reuse the public OAA implementation as the leading range-value Performance candidate rather than building a new catch-probability model from scratch.

### Tracked MiLB

SportsDataverse's default `mlb_statcast_search_minors()` parameters returned zero rows in the initial POC. This was a transport issue, not an OAA failure.

A follow-up diagnostic used the same SportsDataverse wrapper with the raw Savant `minors=true` parameter, then split the tracked pool client-side using official 2024 Triple-A team abbreviations.

Frozen 2024-06-10 through 2024-06-16 result:

- total tracked MiLB pool: 35,352 pitches;
- AAA: 27,749 pitches, 4,479 BIP, 3,986 usable OAA opportunities (`88.99%` of BIP);
- tracked non-AAA: 7,603 pitches, 1,196 BIP, 803 usable OAA opportunities (`67.14%` of BIP);
- required trajectory and responsible-fielder fields were present in both slices;
- both frozen execution/coverage gates passed.

Observed non-AAA home teams in the sample were Clearwater, Daytona, Dunedin, Fort Myers, and Jupiter, consistent with the public Florida State League tracking tier.

**Decision:** SportsDataverse OAA is technically reusable on the tested tracked MiLB data. This is **not** an accuracy validation because no proprietary MiLB OAA oracle is public.

## MiLB transport decision

Do not rely on `hfLevel` server-side filtering for the Savant minors CSV path.

For future source materialization:

1. retrieve tracked MiLB rows with `minors=true`;
2. use bounded date chunks / one-day fallback to avoid Savant's response cap;
3. classify level/league client-side from official team/league identity;
4. persist raw request parameters, row counts, and source hashes;
5. keep tracking coverage explicit rather than treating a missing row as neutral defense.

## Catcher components

Catcher defense must remain separate from generic range OAA.

### Framing

SportsDataverse `mlb_catcher_framing` uses a smooth called-strike probability model over public pitch location, scores only shadow-zone takes, and supports MiLB pitch frames technically.

Upstream validation:

- June-2024 vs full-season Savant oracle gate: Pearson `>= 0.50`, observed about `0.547`;
- full-season 2024 like-for-like: Pearson about `0.468`, frozen live floor `0.40`.

This is a credible reuse candidate, but MiLB execution/coverage and chronology still need our own gate.

### Blocking

SportsDataverse detects wild pitches / passed balls from `des` text because the public pitch `events` field does not expose them reliably. The implementation is reusable code, but the inspected offline oracle only establishes that the pipeline wires to the Savant leaderboard; it does not predeclare a strong correlation floor.

Treat blocking as **candidate / needs validation**, not accepted value.

### Throwing

SportsDataverse's full-season 2024 public-data throwing model reports only about `0.073` Pearson correlation with Savant. The upstream diagnosis is data coverage: only roughly 401 of ~1,773 real SB/CS attempts were recoverable from the public pitch descriptions.

Treat this as **weak evidence** unless our own source/validation work finds a better public attempt surface. Do not automatically add it to Defense v1 because code exists.

## Coverage tiers

Defense v1 should carry an explicit evidence tier rather than pretending every player has the same measurement quality.

Working tiers to test, not yet freeze:

- **Tier A — MLB tracked:** validated public range/OAA candidate + eligible catcher components.
- **Tier B — tracked MiLB:** range/OAA and potentially framing where fields/opportunity meet frozen coverage requirements; no proprietary oracle claim.
- **Tier C — untracked affiliated MiLB:** no tracked range evidence. Defensive quality remains unresolved rather than set to zero by assumption.

A neutral/shrunk fallback for Tier C is a possible baseline to test, not an accepted production rule.

## Minimum eventual output

Before WAR/value, Defense v1 should produce at minimum:

- player id;
- position;
- projected defensive runs above the chosen positional defensive baseline or an equivalent rate;
- opportunity/exposure basis;
- evidence tier;
- source coverage / uncertainty metadata;
- component provenance (range, framing, blocking, throwing where applicable).

Positional adjustment belongs to the later value layer, not inside the fielding-quality estimate.

## Next small batch

1. Run a frozen catcher feasibility POC on MLB and the already-proven tracked MiLB transport, prioritizing framing and treating blocking/throwing separately.
2. Inventory universal non-tracking defensive evidence already available from official fielding stats / mature public sources and test whether any plausible Tier-C signal deserves development before defaulting to a heavily shrunk or neutral fallback.
3. Only after those source gates, define chronology, multi-season shrinkage, aging/projection, and out-of-time validation for Defense v1.

## Binding boundaries

- No production Defense v1 model is frozen yet.
- No untracked-level defensive values are imputed yet.
- No catcher component is accepted into production yet.
- No WAR/value calculation is authorized by this checkpoint.
- Playing Time v1 and Position/Role v1 remain frozen and untouched.

## Evidence records

- `docs/defense-sportsdataverse-reuse-poc-contract.md`
- `docs/defense-sportsdataverse-reuse-poc-result.json`
- `docs/defense-milb-statcast-transport-diagnostic-contract.md`
- `docs/defense-milb-statcast-transport-diagnostic-result.json`
