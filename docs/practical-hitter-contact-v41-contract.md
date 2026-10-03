# V41: direct future-MLB contact-shape transfer

2026-10-03. A bounded batting comparison, not another workload tournament.
V40 qualifies the older minor-target gradient result, not all later contact work.
The later neutralization-v2 work did use a future-MLB component-value target;
its small shape gain was uncertain. Its underlying terminal PBP supplies minor
contact back to 2016. Reuse raw measurements, not its saved model weights or
all-level pooled features.

## Source and experiment

- Reconstruct ten trajectory/direction bins from existing terminal PBP, source
  seasons 2016–19 and 2021–24. No 2020 MiLB invention. Preserve actual league:
  MEX, DSL and distinct rookie leagues remain separate. Add only MLB records
  from the separately hashed universal shape source (2021–24), avoiding duplicate
  minor measurements. No launch angle, exit velocity or new tracking inputs.
- Shape is raw descriptive evidence, not park-neutralized talent. In this batch
  do not inherit same-season learned contact residuals, park factors or sparse
  opponent effects. Their fold/source-independence needs a separate bridge.
- Pool own counts with 1/.8/.6 recency, separately in the existing 14 buckets.
  Supply ten (count+10)/(contacts+100) shares, log exposure, measured-contact /
  official PA fraction, and an availability flag per bucket (source amendment).
  Missing produces the fixed prior plus zero exposure, not observed poor contact.
  Counts/coverage distinguish a shape based on 27 contacts from one based on 400.
- Same V34 complete population, exact whole-player chronological folds and mature
  future MLB targets; batting rate trained only future-active, actual-PA weighted
  within equal-origin weights. Retain all evaluation non-arrivals for value.
- Two fixed comparisons: physically scaled ridge alpha 100 (existing strongest
  rate architecture plus shape) and histogram gradient boosting with the existing
  depth-3/250/leaf-30/.05/L2-10 settings. No tuning or validation selection.
  PA remains V34 bit-exact. If a row has no usable bucket evidence, or its measured
  buckets have no future-active training people, retain its V34 batting forecast.
  Earlier folds with no supported contact remain exact baselines, not fake fits.
- Score conditional MLB batting and delivered batting-plus-replacement value,
  whole population, public matches, current MLB, minors, brief debuts and origins.
  Report the narrower supported-contact comparison alongside the unchanged broad
  denominator. Do not call a contact experiment a decade-wide MLB-shape test.
- Before disposition, review actual stats, source exposure/bins, saved rate
  intermediates and contribution arithmetic for fixed Judge/Winn/Steer/Kurtz/Lux/
  Meidroth/Bellinger cases, largest gains/harms, false highs/lows and ordinary
  players. Include origin-selected unsuccessful peers. No scores-only promotion.

The protected 2026 forecast and outcomes remain unchanged. V33b stays working
unless the completed comparison justifies an integrated research candidate.
