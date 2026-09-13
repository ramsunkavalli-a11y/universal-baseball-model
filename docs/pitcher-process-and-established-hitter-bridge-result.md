# Pitcher process and established-hitter bridge result

**Status:** active in the private preview  
**As of:** 2026-09-08

## What changed

The validated high-minors pitch-process model now feeds the next-year pitcher
component projection, then frozen Tango aging, WAR, Model FV, and contract value. It
applies only when the production talent path is based on affiliated evidence. A
current minor-league stint cannot overwrite a pitcher's established MLB history.
Missing pitch-process evidence leaves the prior rate unchanged.

For hitters with at least one 200-PA MLB season in the prior two years, active
probability now uses current MLB PA, each of the prior two MLB seasons, age, and a
1,200-PA-regressed batting-quality measure. The 200-PA boundary matches the existing
meaningful-role definition and prevents a recent debut from being treated as an
established veteran. Public grades, ranks, contracts, teams, and future information
are not inputs. Only active probability changed; validated conditional workload and
talent rates remain separate.

## Historical checks

Across 7,706 later-period player-horizon rows that satisfy the established-player
boundary, the established-hitter challenger improved Brier score from 0.1523 to
0.1435 and log loss from 0.4645 to 0.4376. Both proper scores improved separately at
horizons one through six. Projected-PA MAE also improved from 156.8 to 145.5, but the
new conditional-count estimate was not promoted. A separate three-year workload
anchor barely changed overall error and materially worsened the established-player
tail, so the validated conditional workload remains in place.

The pitcher process model passed its prior three-origin confirmation and paired
uncertainty gates. In the current build it changes 1,994 affiliated-evidence pitchers
and zero MLB-history or population-prior pitchers.

## Player traces

- Keyner Martinez: 2027 conditional talent improved from 0.42 to 1.44 WAR per 800
  batters faced. His final nested-career Model FV is 22.4, displayed as 20. The
  remaining constraint is very low modeled MLB opportunity, not translated talent.
- Aaron Judge: the old model ignored his 679 and 704 PA in the prior two seasons and
  assigned only 486 expected PA in 2027-2031. The corrected active probabilities raise
  that to about 739 PA and rest-of-contract WAR from 4.07 to 6.10. The 2027-2031 mean
  is 5.93 WAR, with 0.17 remaining in 2026. The result remains conservative because
  2026 is injury-shortened and age-related exit risk is retained.

## Required build order

1. Run `audit_pitcher_process_challenger.py` and
   `audit_established_hitter_opportunity.py` to produce promoted artifacts.
2. Build the Phase 2 workload and conditional-rate baselines.
3. Run `materialize_pitcher_process_war_bridge.py`, then
   `materialize_established_hitter_opportunity_bridge.py`.
4. Materialize WAR uncertainty with `phase2-conditional-war-paths` as its input and
   `phase2-war-uncertainty` as its output.
5. Rebuild Model FV, nested career FV, current value, and the results explorer.

Do not use the older generic conditional-path directory for the private preview. The
bridge scripts explicitly reconnect current Phase 2 opportunity rows to prevent that
stale-lineage failure from recurring.
