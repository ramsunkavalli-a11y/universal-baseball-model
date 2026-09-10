# Pitcher pooled-XBH result

Status: rejected in development; later period not scored.

The seven-part version pooled doubles and triples into one non-HR extra-base-hit
outcome. On the 2024 development cohort of 173 pitchers and 23,129 target MLB BF, the
expanded five-part incumbent scored 1.477310 log loss and 0.705645 Brier.

| Regression prior | Log loss | Brier |
| ---: | ---: | ---: |
| 800 BF | 1.477754 | 0.705773 |
| 1,600 BF | 1.478206 | 0.706019 |
| 2,400 BF | 1.478625 | 0.706188 |
| 4,000 BF | 1.479137 | 0.706378 |

Every candidate was worse on both proper scores. The runner therefore did not
calculate a 2025 result. No production or private-preview player value changed.

Together with the rejected separate single/double/triple test, this says the saved
season-total contact splits have not added stable future MLB pitcher information to
the current strikeout, walk, HBP, home-run, and broad-contact profile. More granular
contact work must first pass event-level coverage and opponent-context gates.

Machine-readable evidence: `docs/pitcher-pooled-xbh-result.json`.
Frozen protocol: `docs/pitcher-pooled-xbh-plan.md`.
