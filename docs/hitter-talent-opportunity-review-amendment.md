# Correcting the player identity in the opportunity review

2026-10-03. The original scorer used MLBAM 665742 for the intended Jeremy
Peña 2021 case. That ID belongs to Juan Soto. The original contract's named
case is Peña; his correct source identity is 665161, row 43288. Preserve the
scorer, its original cases, scores and verification. Add a separate trace for
Peña and review Soto too. This correction changes no training, forecast,
evaluation membership or score. It is a review-selection implementation error,
not evidence that the model confused the two players.

Also trace the highest projected hitting rate among never-debut lower-minors
players under age 20 at origin 2024, selected without the subsequent outcome.
This supplies a lower-level contrast to the upper-minors and current MLB cases;
it cannot establish long-term prospect validity from next-year non-arrival.
Resolve ties by player ID. Do not tune or fit another model from these cases.

The supplementary receipt records the identities, actual inputs, saved fitting
provenance and paths, dated level counts, support and four origin-selected
comparisons. Final disposition remains pending until all original and added
cases have actual written reviews.
