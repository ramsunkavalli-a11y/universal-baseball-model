# Separate outfield ability from positional value

The research assembly mixed two reference points: native range across outfielders
and a position schedule intended for position-relative fielding credit. This
matters for individuals even when opposite outfield offsets nearly cancel in
league totals. Keep intrinsic range for talent analysis, but use a compatible
position-relative definition before calling the assembly WAR-like value.

This is a definition repair, not an accuracy improvement. All nine existing
assemblies for 12,432 origins replay unchanged, as do their 149,184 component
rows. No new forecast, fit, score selection, 2026 evaluation or explorer change
occurred. The older-quality milestone is committed and pushed as `2a56a092`.
The documentation review keeps new source/accounting findings separate from
claims of predictive success.

## What the accounting changes

Qualified 2023 native range averages +2.002 runs per 500 CF innings, −1.381 in
LF and −0.795 in RF. Subtracting each measured position's exposure-weighted
average centers its fielding contribution. Infield and other channels are not
arbitrarily centered. These observed-season averages describe accounting, not
forecast inputs. The captured population excludes small missing measurements,
so this is a transparent research reference, not exact FanGraphs WAR.

[FanGraphs' fielding correction](https://blogs.fangraphs.com/a-fangraphs-war-fielding-update/)
explicitly makes outfield range position-relative before adding positional value.
Our old expanded common-win target was labeled custom, not published WAR. Its
matched quality comparison remains an internally defined comparison; it must
not be promoted as a certified WAR comparison with this reference unresolved.

Moving the range offset into the position column leaves total value exactly
unchanged. Removing it while retaining the original position schedule changes
the valuation definition. Neither operation identifies new player talent.
Within one position and season, a common reference shift leaves rankings intact;
mixed-position comparisons and position changes are affected.

The cutoff-only reference uses the already fixed three-season recency window,
with all modulo-five held-ID people excluded. Its 45 origin/fold/position
calculations replay independently. It cannot silently borrow the future
observed-season centers. [The fold amendment](defense-reference-v25-fold-amendment.md)
preserves the failed first assertion and distinguishes the assembly's different
player grouping. No saved fold or forecast was changed.

## Totals can conceal individual differences

The own-repertoire forecasts contain the following offsets. These are amounts
included by the raw reference, not forecast errors or gains from a new model.
The observed column uses realized seasonal references and native exposure on
the identical complete-defined target subset.

| Forecast origin | Complete forecast rows | Forecast offset in runs | Observed offset in runs |
| --- | ---: | ---: | ---: |
| 2022 | 4,139 | +13.336 | −5.918 |
| 2023 | 4,083 | +8.920 | +1.065 |
| 2024 | 3,892 | +17.959 | −10.677 |

In the first origin, projected CF offsets total +146.361 runs, versus −71.617
in LF and −61.408 in RF. Netting those into +13.336 hides the size and direction
of individual reallocation. The all-forecast offsets are +5.916, +6.999 and
+11.486 runs; they are different populations from the complete target subset.
There are 156 positive-exposure OF channel records with unknown measured range.
They remain unknown, not invented zero defense or omitted identities.

## The sparse prior is part of the problem

The existing history rule shrinks toward zero *raw* range. Raw zero is not average
at CF or at a corner. Merely subtracting the full position center afterward
can give a lightly observed corner fielder unwarranted positive position-relative
quality. Hernández's 24 weighted LF outs have less than 1% reliability, but that
naive conversion reads +0.914 runs per 500 innings. That is not a usable new grade.

For unknown-quality prospects, the adapter keeps talent null. A mean-zero
position-relative fallback corresponds to the position reference in raw units,
not an observed player grade. Rafaela and his peers make this concrete in the
[player review](defense-reference-v25-player-review.md). Implement centering
before shrinkage, with an explicitly compatible prior, rather than converting
the already shrunk raw forecast and calling it a finished solution.

## Decision and next work

Retain the separate intrinsic and position-relative accounting adapter and its
unknown-skill behavior. Do not deploy a naive subtraction forecast, overwrite
the old research results or call this a demonstrated prediction improvement.
Next contract one compatible history/prior baseline on the unchanged opportunity
forecast and position-relative target, with current MLB quality and delivered
value evaluated separately. Keep the existing intrinsic talent benchmark and
frozen forecasts unchanged. No recency/prior tournament or reopened DP/count
recipe follows. Older/native bridging and lower-minors evidence remain in scope
after this accounting repair. The broad defense goal remains active.

Independent checks replay 111,888 saved assemblies, 37,296 OF reference records,
30 annual centers, 45 cutoff centers, all eight peer groups, 32 player records
and 147 raw minor fielding splits. Thirteen unit checks cover reference arithmetic,
chronology, held IDs and sparse fallbacks. These establish accounting integrity,
not predictive validation or deployment approval. Bulk sources and diagnostic
ledgers remain private; small selected walks and audit summaries are public.
