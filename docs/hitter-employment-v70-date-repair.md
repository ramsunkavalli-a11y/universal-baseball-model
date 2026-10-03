# Employment source date repair before fitting

2026-10-03. The first source audit is preserved in `hitter-employment-v70/`;
it is provisional, and no model used those new state labels. Source review
found eight roster/state conflicts. Do not fit the first adapter or treat its
free-agent groups as certified current employment.

Bour's signing record says December 15, 2018, but its effectiveDate is May 15,
2019. Aoki's December 3, 2015 signing has a June 24, 2016 effectiveDate. Both
were publicly known in December: [Angels announcement](https://www.mlb.com/press-release/angels-agree-to-terms-with-justin-bour-301891352)
and [Mariners announcement](https://www.mlb.com/mariners/news/mariners-sign-free-agent-nori-aoki/c-158523864).
Using the latest of those fields hides a known signing. These are source
counterexamples, not evidence that all effective dates are wrong.

The repaired source-only adapter uses the record's date for explicit employment
announcements and preserves the other dates as audit fields. Historical
publication vintages remain uncertified; a reconstructed record date is not
proof of its first publication. A plain activation onto a recorded MLB team
can end recorded free agency without asserting a particular contract or medical
recovery. Older unresolved free-agency records become unknown in a later origin,
not permanent unsigned status. Roster contradictions remain flagged.

V70b uses the same raw files, forecasts, cohorts and nine fixed reviews; changes
only those employment-state definitions. Save both source outputs. No new fit,
roster overwrite, prospect exclusion or future signing is allowed. Check future
record exclusion and the two cross-year counterexamples, then review all sources,
existing model paths, outcomes and failed peers before deciding on a single
future employment representation test. Do not silently rewrite older medical
or availability models using this employment-specific date rule.
