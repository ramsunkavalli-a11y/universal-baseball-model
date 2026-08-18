# Defense universal official-fielding source audit contract

Last updated: 2026-08-18

Status: **SOURCE INVENTORY ONLY — NO DEFENSIVE SKILL MODEL.**

## Question

Which non-tracking fielding statistics already present in the project's certified 2021–2024 official Stats API captures are broad and consistent enough across MLB and affiliated levels to deserve a later predictive-signal test for Defense v1's untracked evidence tier?

## Frozen input

Reuse the immutable artifact from historical position/role source certification:

- workflow run `32148467330`
- artifact `position-role-historical-source-2021-2024`
- seasons 2021–2024
- 16 actual leagues per season / 64 season × league pairs

Do not re-fetch or open 2025 for this audit.

## Audit grain

Read every retained official `fielding_offset_*.json` page and inspect each split's raw `stat` mapping.

For every raw stat key report:

- row count where the key exists;
- non-null/non-blank count;
- numeric-parseable count;
- season × league pair count in which the key appears;
- level groups in which it appears;
- positions in which it appears.

Also compute the same coverage restricted to catcher (`position.abbreviation == C`) rows.

## Candidate labels

These labels mean **source-feasible for later testing**, not useful defensive metrics.

A general-fielding key is `broad_universal_source_candidate = true` only if:

- it appears in all 64 season × league pairs; and
- at least 95% of rows on which it is defined are non-null/non-blank.

A catcher-only key is `broad_catcher_source_candidate = true` only if:

- it appears on catcher rows in all 64 season × league pairs containing catcher rows; and
- at least 95% of catcher rows on which it is defined are non-null/non-blank.

Do not choose a predictive formula or defensive weighting from this audit.

## Interpretation boundary

- Presence does not imply skill signal.
- Fielding percentage, errors, assists, putouts, chances, double plays, passed balls, caught stealing, or any other traditional statistic must pass a separate chronology-safe predictive test before entering Defense v1.
- Rate fields derived by the source from the same counts are not independent evidence.
- Park/team/opportunity/context confounding remains unresolved here.
- No neutral fallback is frozen by this audit.
- No WAR/value calculation is authorized.
