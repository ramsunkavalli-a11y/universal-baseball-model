# Prospect top-50 ranking audit checkpoint

**Status:** first comparison and source-wiring repair complete; ranking gate remains open
**As of:** 2026-09-08 model and FanGraphs snapshots

## What the first comparison says

The comparison product now shows both directions: every FanGraphs top-50 player
through the model and every model top-50 player through the FanGraphs snapshot. Each
modeled row exposes age, level, arrival probability, meaningful-role probability,
conditional WAR rate, expected career workload, expected WAR, value and the component
runs behind the skill rate.

- FanGraphs rows: 50.
- Players who had already reached MLB by the model checkpoint: 8. These are
  eligibility differences, not missing prospects.
- FanGraphs top-50 players still pre-MLB: 42.
- Unresolved identities among those 42: 0.
- Players in both eligible lists: 10.
- Model top 50: 49 hitters and 1 pitcher.
- FanGraphs still-pre-MLB top-50 group: 30 hitters and 12 pitchers.

The low overlap does not itself fail the model. The 49-to-1 model split is a material
warning because it accompanies an already known compression of translated pitcher
skill. It must be explained and tested independently of the public ranks.

## Structural findings

### Fixed: dated-source identity

The original identity rule required the ranking's organization to equal the current
organization. Trades made eight unique players look unmatched. The source resolver
now falls back to an exact normalized name only when that name identifies exactly one
player in the full control universe. MLBAM matches improve from 91 of 100 to 99 of
100. The remaining Luis Hernandez row is ambiguous and correctly stays unmatched.

### Fixed: comparison eligibility

Eight FanGraphs top-50 players had debuted before September 8. They now appear as
`graduated_to_mlb`, not as model omissions. The audit no longer mixes an earlier
prospect-list definition with the current pre-MLB model pool.

### Open P0: pitcher conditional skill scale

The pitcher shortage occurs before dollars or FV labels. Several highly ranked
outside pitchers have high modeled arrival and role chances but very low conditional
WAR rates. Examples:

- Gage Wood: 97% arrival and 71% meaningful-role chances, but -0.41 expected WAR.
  The translated line projects a 22.4% strikeout rate and 4.8% home-run rate, producing
  about 22 pitching runs below average per 800 BF.
- Christian Zazueta: 97% arrival and 72% meaningful-role chances, but -0.16 expected
  WAR for the same reason: strong opportunity combined with a deeply negative
  translated run rate.
- Thomas White: 93% arrival and 67% meaningful-role chances, but only 1.34 expected
  WAR because his conditional rate is about 0.98 WAR per 800 BF.

These are understandable calculations, but the translation and regression must prove
that they treat strikeouts, walks and home runs correctly for high-performing minor-
league pitchers. Public rank cannot decide that test.

### Open P0: low-level hitter evidence

The model strongly favors demonstrated AA/AAA performance and proximity. That gives a
clear reason for many model-only names. It also drives several young A-ball or newly
drafted players extremely low because current production and level evidence are thin.
Official draft pick and signing-bonus evidence already exists and showed useful
out-of-time arrival information, especially for hitters, but it is not in the current
production arrival model because subgroup and quality gates were mixed. The next
candidate should use pedigree only for arrival/role probability, retain strong
pooling, and never make it a WAR bonus or FV floor.

The audit also found two source-wiring defects in this group. The current scorer used
a blanket age-24 fallback before checking available birth dates, and it did not pass
the already captured Rule 4 draft table into the current predictor builder. Birth-date
age is now recovered for 822 modeled pre-MLB player/type rows; only one current hitter
still needs the explicit age-24 fallback. Official draft fields are now materialized
for explanation and future testing, but they do not affect the current production
formula.

The rebuild uses snapshot age for 6,165 player/type rows and birth-date age for the
remaining 822. One hitter has neither and retains the explicit age-24 fallback. Rule 4
history is attached to 1,029 hitters and 1,600 pitchers. Corrected ages flow through
arrival and value; draft fields remain explanation-only and therefore do not change a
projection.

### Open P1: proximity versus upside

Most model-only top-50 hitters are at AA or AAA with high arrival odds. This is valid
baseball logic, but the audit must determine whether proximity, positional runs and
career workload together crowd out younger high-upside players more than historical
outcomes support. The test must use historical cohorts, not public rank agreement.

## Product files

Running `scripts/audit_prospect_top50_rankings.py` creates a local HTML comparison,
two CSV files, two canonical Parquet tables and a JSON report under
`reports/generated/prospect-top50-ranking-audit/<date>/`.

Playable values were rebuilt only because the age-source defect was repaired. No
formula, public-rank input, draft bonus, FV floor or named-player override was added.
