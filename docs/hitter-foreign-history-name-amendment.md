# Resolve published NPB initial and surname abbreviations separately

2026-10-04. The successful source probe retains 34 unresolved identities in
335 rows. The 2017 Nippon-Ham batting table, for example, prints `レアード`
while its historical identity listing prints `Ｂ．レアード`. Its exact full-name
rule therefore misses a real published abbreviation. This matters for league
translation: omitting foreign returners would leave a distorted mover sample.

Preserve the qualified exact-only collector and its original outputs. After
complete capture, create an additive reviewed identity overlay. Permit one
additional rule: remove exactly one published Latin initial followed by a dot
from an identity-list name, then require exact surname equality within the same
season/team. Support the ASCII/fullwidth initial and dot representations. No
transliteration, substring match, learned alias or fuzzy search is allowed.
If more than one identity satisfies this rule, retain ambiguity and do not join.
The current/old-player label and debut note remain excluded from model features.

The overlay must preserve source row count and every statistic, leave previous
exact identities unchanged, identify the applied rule and publish aggregate
remaining gaps. Reconstruct these matches against raw archived listings and
include Laird plus an ambiguous synthetic surname in review/tests. No forecast
or predicted MLB gain is inferred from recovering an identity.
