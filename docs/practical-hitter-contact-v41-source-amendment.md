# Four ambiguous 2023 terminal keys quarantined before fitting

The initial V41 source check stopped before writing a preflight or fitting a
model: four 2023 season/game/PA keys occur with both L and R batter sides. Two
are for batter 801740 in game 729987; two for 814188 in game 740946. The other
shape measurements agree. A duplicate's side would turn the same contact from
pull to opposite, so neither version is selected by assumption.

Quarantine all versions of these ambiguous keys from this raw contact assembly,
preserving them in `ambiguous-terminals-2023.parquet`. Exact copies of otherwise
identical source rows are counted once. The preparation records both numbers,
and stops for further review if conflicts become material. This does not repair
or replace the old PBP foundation, official batting counts, player eligibility
or any forecast. Review any additional quarantines before fitting.

## Official-count bridge, reviewed before fitting

The first complete source preflight found large contact/official-BIP ratios,
especially in rookie/DSL/MEX records. Some player/league/seasons have PBP evidence
but no matching official count row. Treat that as an unverified source bridge,
not fabricated zero batting or proof that either original source is correct.
Preserve initial preflight/features. Save every unmatched, zero-official-PA or
contact-count-exceeds-official-PA bucket in `unreconciled-player-leagues.parquet`
and exclude those buckets from this contact predictor only. Eligibility, official
counts, targets and baseline forecasts remain unchanged. This is not a claim
that the broader historical source mismatch has been repaired.

Use measured contacts/official PA rather than contacts/BABIP opportunities as the
measurement fraction. Sacrifice bunts and contact-versus-BABIP definitions can
make the latter exceed one even for legitimate tiny samples. The PA fraction
also reflects strikeouts/walks, already separately supplied in the model; it is
not a pure missing-contact percentage. Exposure and availability remain separate.
The prepared source review must inspect the excluded magnitude before any fit.
