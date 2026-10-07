# Catcher evidence: recover omitted samples and quarantine false zeros

2026-10-06. This source checkpoint fixes two concrete problems before another
catcher talent test. It does not claim an improvement in forecasts.

## Catchers were silently being filtered out

The older request used `min=1`, described as a permissive one-pitch cutoff.
The actual response metadata instead kept `minPitches="q"`, the qualified-catcher
filter. Setting **`minPitches=1`** explicitly recovers all available pitch samples:

| Season | Old qualified rows | Correct all-sample rows | Additional catchers with at least 1,000 pitches |
| --- | ---: | ---: | ---: |
| 2016 | 63 | 104 | 15, but modern framing runs unusable |
| 2019 | 64 | 112 | 19 |
| 2025 | 57 | 111 | 20 |

Common catchers have unchanged pitches/run values; the correction changes source
coverage, not their grades. Modern 2019/2025 framing runs agree with the separate
native fielding ledger within 2.5e-14. One extra 2019 native catcher row is Kyle
Schwarber's three defensive outs with zero framing runs and no available called-
pitch sample. No receiving ability is inferred from that zero contribution.

## Modern 2016–2017 framing zeros are not average talent

The current modern native ledger has 104 non-null framing values in 2016 and
113 in 2017, all exactly zero. The 2016 framing page repeats the zero values,
despite differing actual pitch/called-strike observations. These are unavailable
modern run measurements, not evidence that every catcher was an average framer.
The corrected pilot retains raw zeros for provenance but sets usable framing
runs/rates to unknown for that year. New component work must quarantine both
years, not count them as measured zero talent or mature training examples.

MLB's updated framing data begins in 2018; older seasons use a separate legacy
table. [MLB framing documentation](https://www.mlb.com/glossary/statcast/catcher-framing)

Do not silently splice the legacy definition into the newer model. Recover it
separately and establish measurement compatibility, or state that the modern
talent comparison has only 2018-onward support. General MLB range results are
unaffected: that comparison never uses catcher framing.

## Players show why coverage and sample size matter

Twenty-two fixed/input-selected source cases and three exposure-selected peers
per case are preserved with the full native observations and rates. No future
success selects the examples or comparisons.

- Gary Sánchez, 2025: the old export omitted him despite 1,633 actual pitches,
  above its purported 1,000-pitch local model threshold. Correct capture supplies
  −2.51 framing runs, or −1.53 per 1,000 pitches. This is usable evidence, not
  proof of a perfectly measured talent grade; eventual forecasts must shrink it.
- Luke Maile, 2025: 1,184 pitches/+2.06 runs were also omitted. His positive
  small sample must be retained with uncertainty, not mistaken for absent skill.
- Eric Haase, 2025: 1,507 pitches/−0.34 runs were omitted too. Correct collection
  is not a directionally favorable adjustment. His exposure-selected peers are
  Basallo, Sánchez and Pereda, all omitted by the qualified-source filter.
- Bailey, 2025: 8,913 pitches/+25.05 runs remain +2.81 per 1,000 under both
  settings. The source change does not boost an already included star.
- Hedges, 2019: 7,094 pitches/+22.62 runs remain +3.19 per 1,000. In 2025 his
  4,047 pitches/+10.62 supply +2.63 per 1,000. These are distinct dated evidence
  records, not a fitted future prediction.
- Realmuto, 2019: +4.92/10,095 pitches; 2025: −8.43/9,714. Receiving results
  change over time; an immutable career label would miss the later decline.
- Grandal, 2016: 8,282 observed pitches with modern run value zero are
  quarantined, not labeled average. His 2019 +16.03/9,798 is a genuine modern
  measurement. Gary Sánchez, Realmuto and Hedges have the same 2016 definition
  boundary, regardless of how much playing time they received.

## What this changes and what it does not

The new source route can represent backup/limited-sample catchers and separates
the numerator's measurement availability from pitch exposure. The old framing
confirmations were qualified-catcher comparisons; they do not establish broad
all-catcher coverage. Any legacy calculation treating modern 2016–2017 zeros
as observed framing needs a corrected sensitivity review before reuse.

Neither old sealed reports nor the production hitter forecast/explorer were
rewritten. No 2026 outcomes were queried. No new catcher learner was fitted.
Throwing and blocking opportunities remain separate; innings or batting PA
cannot substitute for actual called pitches/steal attempts.

Source/player review is complete. Extend the same certified capture to modern
2018–2025, preserve the old qualified anchors, then audit mature future quality
windows before a native-unit framing test. Lower-minors framing needs actual
pitch-location/call data; absence remains unknown, not inferred zero talent.

Evidence: [source review](../reports/model-evidence/catcher-native-opportunity-v3/source-review.json)
and [player source calculations](../reports/model-evidence/catcher-native-opportunity-v3/player-walkthrough.json).

## Same-method extension completed

After the pilot/source-player checkpoint, the verified all-pitch request was
extended to 2018–2025. It recovers **878 catcher-season rows across 252 people**,
with 43 additional fixed/minimum-exposure player traces and their peers. Every
common numerator agrees with its separately captured native framing run value.
Only two native catcher rows lack a pitch sample: Mauer's zero-out 2018 row and
Schwarber's three-out 2019 cameo. Neither becomes a measured zero-ability label.

The newly visible tiny samples require severe regression: Chad Wallach has
15 pitches/+0.30 runs in 2025, and Donny Sands has eight pitches/−0.13 in 2022.
Neither rate is a credible lasting talent grade. This is why the source keeps
exact exposure instead of equating a non-null number with reliable skill.

The modern source is now ready for a **separately contracted** future-MLB quality
baseline/support test in native runs per actual received pitch. It does not
create 2016–2017 modern measurements, lower-minors framing coordinates, catcher
throwing/blocking opportunities or ABS-era delivered value. The active defense
goal remains unfinished; no catcher fit or forecast was changed at this checkpoint.

Full-extension evidence: [modern source review](../reports/model-evidence/catcher-native-opportunity-v3/modern-source-review.json)
and [all source/player traces](../reports/model-evidence/catcher-native-opportunity-v3/modern-source-player-walkthrough.json).
