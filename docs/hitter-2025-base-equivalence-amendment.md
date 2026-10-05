# Correct the initial base adapter before production

2026-10-05. The first source-only build reproduced the original V31 base: 58,746
rows and 437 fields. That is a valid raw-source reproduction, but not equivalence
to the selected model's corrected production inputs. Its receipt and builder
remain unchanged and are not permission to fit.

The corrected historical frame has 63,282 rows. Its 4,536 additional identities
are all origin 2020, reconstructed after the original build. Together with the
original 597 rows, the special 2020 cohort has 5,133 identities. Those origin
rows remain explicitly excluded from the selected training procedure; their
observed MLB history still enters later origins. Do not recreate their custom
age, membership and last-observed stage with a normal-season adapter.

V31 also had a documented prefit correction: cumulative MLB PA must sum every
MLB record through the player's own origin, including split MLB/minor seasons.
The first new adapter reproduced the uncorrected primary-stint version. Use a
separate tested-base wrapper with the existing correction, without changing the
sealed initial build. Prove equality to modern base fields on all 58,149
non-2020 identities, account separately for every excluded origin-2020 identity,
and reproduce the selected model's actual feature lists. No changed model
settings, new development test or new predictive-improvement claim is involved.

Save an additive review and corrected source-only 2025 inputs. Walk the fixed
players and peers against actual count sources and report corrected exposure,
unknown age, inactive eligibility and remaining feature families. No 2026
outcomes or fits may enter this source gate.
