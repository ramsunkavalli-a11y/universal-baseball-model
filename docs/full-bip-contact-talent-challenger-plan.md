# Full BIP contact-talent challenger

**Status:** both production paths held back after complete rate gate
**Priority:** P0 hitter and pitcher talent

## Existing work reused

The ten-bin non-bunt BIP classifier, batter-relative direction, source checks,
chronology rules, and player-profile projection already exist. They are not being
rebuilt. The current active peak-talent path does not directly use that complete
profile; this challenger tests the missing bridge.

## Candidate

For hitters and pitchers separately:

1. take the cutoff-safe projected probabilities for all ten BIP bins;
2. assign each bin a context-neutral run value learned only from earlier seasons;
3. sum `projected probability × neutral value` across all ten bins;
4. compare that BIP contact estimate with the active results-based contact estimate;
5. fit one earlier-origin, contact-weighted blend constrained to `0..1`;
6. score the unchanged blend on later seasons.

The candidate changes contact quality only. Strikeouts, walks, HBP, playing time,
position, role, and contract value remain separate. Pitcher run value is expressed
as offense allowed and inverted only later in the pitching-value layer.

## Required evaluation

- Score hitters and pitchers separately.
- Primary: future neutral run value per contact, equal-player RMSE and MAE.
- Secondary: contact-weighted RMSE/MAE and future component errors.
- Report by level, evidence band, age band, and same-level versus promotion path.
- Include players who later disappear or lose playing time when a future contact
  target exists; do not condition talent scoring on future role size.
- Compare on identical players and contacts.
- Estimate BIP-profile reliability upstream from historical repeatability; do not
  tune profile shrinkage on the later score.

## Promotion rule

The BIP layer advances only if its positive weight is learned from earlier origins,
it improves both equal-player primary errors in later time periods, and no supported
level reverses on both errors. Otherwise the fitted production weight is zero.

Passing this component gate permits integration into the talent replay. It does not
directly change playing time, WAR, FV, or trade value.

## Scored result

- [Pitcher result](full-bip-pitcher-challenger-result.md): passed both periods and
  every supported level, including a stricter non-HR target compatible with the
  separate home-run model.
- [Hitter result](full-bip-hitter-challenger-result.md): improved both overall primary
  scores in confirmation, but a very small equal-player AA reversal failed the strict
  level guardrail. It remains research-only.

The [active-model comparison](full-bip-active-model-result.md) is complete on a shared
cutoff-safe MLB-neutral scale. Pitcher passed at every supported contact level, while
hitter reversed at AA and AAA. The subsequent
[complete pitcher-rate replay](full-bip-pitcher-rate-replay-result.md) reversed overall
and at A and Rookie. Both production weights remain zero. Further work belongs in a
new rolling-origin Phase 2 level-reliability test, not rescue tuning.

Phase 2 must also reconcile the BIP profile's 100-contact prior with the aggregate
pitcher model's 800-BF prior before fitting any combined weight. Estimate that bridge
from earlier repeatability and require both contact-component and complete-rate wins.

That [reliability bridge](full-bip-reliability-bridge-2024-result.md) is now scored on
newly built, previously untouched 2024 outcomes. It still fails overall RMSE and
reverses at A and Rookie, while improving every measure at High-A, AA, and AAA. The
global candidate is closed. A future level-specific challenger needs a new untouched
full-season confirmation; the currently available 2025 public archive ends in May.
