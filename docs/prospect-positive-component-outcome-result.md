# Prospect positive-component outcome result

**Run date:** 2026-09-09  
**Decision:** reject for player value; retain the hurdle design

This audit separates two questions:

1. Will a prospect receive meaningful MLB opportunity?
2. Given at least 200 PA or BF in a season, will his core components be at least MLB
   average for that season?

The two probabilities would be multiplied only after each part passes. This avoids
letting thousands of non-arrivals dominate the quality score and follows the existing
hurdle-model treatment of playing time.

Hitter quality uses neutral wOBA event weights. Pitcher quality uses the standard
fielding-independent `13 HR + 3 (UBB + HBP) - 2 K` numerator per BF. The target
excludes defense, baserunning, catcher framing, and contact management and is not
whole-player WAR.

The certified outcome source now includes completed 2025 while excluding 2026. The
2020 workload gate is scaled to a 162-game equivalent; event rates are not scaled.

## Conditional outer result

| Population | Players | Positive rate | Core log loss | Candidate | Core Brier | Candidate |
|---|---:|---:|---:|---:|---:|---:|
| Hitters | 63 | 38.1% | .6743 | .6885 | .2411 | .2478 |
| Pitchers | 76 | 57.9% | .6945 | .6937 | .2501 | .2504 |

Earlier-fold selection chose origin plus 50 PA of production-rate regression for
hitters. It became worse on both outer scores. Pitcher selection chose draft pedigree
plus 50 BF of regression; its changes were effectively zero and both uncertainty
intervals were centered on no gain.

This is a useful rejection. Current inputs predict promotion better than MLB quality,
and origin must not be used as a quality shortcut. Draft evidence also does not earn a
WAR bonus or FV floor. The hurdle structure remains the right framework, but the
quality side needs richer process evidence, longer complete history, or both.
