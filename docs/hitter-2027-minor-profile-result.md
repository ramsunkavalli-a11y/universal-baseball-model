# A modest minor-defense prior, with the correct comparison

2026-10-09. The saved age/position/level/innings model is broadly comparable to
the current position-average fallback; its advantage is much smaller than the
old comparison with raw zero suggested. No coefficients were fitted or tuned.
All 13,133 saved predictions replay exactly from their original held-player fits.

| Origin | Measured people / positions | Position-reference RMSE | Profile RMSE | Reference / profile MAE |
| --- | --- | --- | --- | --- |
| 2022 primary | 62 / 71 | 2.772 | 2.732 | 2.231 / 2.211 |
| 2021 stress | 83 / 94 | 2.877 | 3.012 | 2.286 / 2.362 |

Units are native range runs per 500 innings. Primary RMSE improves 1.43%; stress
RMSE worsens 4.67%. Both are within the predeclared practical 5% tolerance, not
evidence of a statistically secure advantage. Nonarrivals remain unknown skill,
not zeros. Position references exclude the same player group and use only
origin-known measurements. For later value assembly subtract the OF reference
once, after estimating native quality; do not count CF difficulty twice.

## Baseball checks

The 25 selected position cases and origin-only peers retain source age, level,
innings, every coefficient contribution, reference calculations and subsequent
native range records. Their earlier count-model walks remain supplemental;
the present comparison is the unchanged profile against a compatible prior.

- **Rafaela, largest harm/false low:** age 21, AA, 777 CF innings. Reference
  +1.807, profile +1.259, actual pooled +6.657. CF itself contributes +1.187;
  age contributes -0.145 and innings -0.117 relative to training averages.
  This ordinary profile cannot recognize his exceptional glove. Barrosa, Mears
  and Doston are preserved as input-selected comparisons with unknown/limited
  MLB outcomes, not assumed successes.
- **Young:** 2022 CF reference +1.704, profile +2.272, actual +6.952. The profile
  moves correctly but still misses his standout ability. In 2021 it moved the
  wrong way (+0.444 versus a +1.764 reference and +6.857 later quality).
- **Lukes, largest gain:** age 27, AAA, 199 RF innings. Reference -0.760, profile
  +1.196, actual +3.503. Age contributes +1.231 and AAA-related terms help.
  This is a conditional profile among players reaching measured MLB defense;
  it is NOT evidence that getting older improves a player's glove. Do not use
  its age coefficient as an aging curve. Peers Kohlwey, Dawson and Snyder remain.
- **Edwards, false high:** age 22, AAA, 178 SS innings. Profile +0.122 versus
  zero reference and -6.840 later range. None of these coarse inputs identifies
  the severe weakness. Young, Turang and Hernandez are origin-only peers.
- **Westburg, ordinary case:** age 23, AAA, 319 3B innings. Profile +0.814 versus
  zero and +2.888 actual. Position and AAA terms explain the modest positive
  estimate; it still underestimates him. Pérez, Loftin and Fermín are retained.
- **Volpe, Neto, Witt and Peña:** the profile is not consistently better than
  the position prior. Volpe 2022 is -0.615 versus +0.772 later; Neto +0.288
  versus -1.438; Witt 2021 -0.200 versus +2.033; Peña +0.437 versus +0.533.
  Individual misses remain even when pooled tolerance passes.

**Decision:** review complete; reuse as a qualified conditional range prior for
unmeasured minor defenders with compatible current-season inputs and training
range support. Do not use the failed count candidate, turn tiny grade differences
into scouting certainty, or override measured MLB history with this profile.
Missing/out-of-range/unsupported DSL and complex inputs retain disclosed
comparable-position priors, not fabricated precise grades. Current adaptation
must log that fallback and independently replay its players. This is neither
general lower-minor talent validation nor a full-player-value accuracy claim.
