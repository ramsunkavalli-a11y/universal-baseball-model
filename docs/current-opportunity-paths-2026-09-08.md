# Current opportunity paths — 2026-09-08

**Status:** complete universal baseline for full 2027–2032 seasons

Official 2026 evidence through September 8 was used only as predictor evidence. It was
not used to select or evaluate the historical model. The output contains:

- 3,940 hitters and 23,640 hitter player-years;
- 5,276 pitchers and 31,656 pitcher player-years;
- six full future seasons, 2027–2032;
- 22 players with both legitimate hitter and pitcher components; and
- zero team-depth inputs and zero workload caps; and
- positive PA/BF variance retained from the same historical hierarchy for downstream
  uncertainty.

An initial run incorrectly gave pitcher paths to position players with incidental
mop-up appearances. Role identity now uses official position evidence. That correction
reduced pitcher coverage from 5,690 to 5,276 and two-component coverage from 436 to 22.
Incidental pitching statistics no longer create a second career path.

The historical selected Playing Time v1 coefficient artifacts are not present in this
checkout. Therefore all hitter rows use the disclosed historical age/level fallback;
no substitute coefficients were invented. Pitchers use historical age/level/recent-
role fallbacks. Every player still receives all six seasons.

Generated path hashes:

- hitter paths: `116de7404d5ec5f2c0ff2eadfcbdc13814b393e872c5cef7b6ec56bed60afee9`;
- pitcher paths: `d211fe2a07dde0cf08cc02c1b1259388ccfb018e00f24d0a570077a6f252f646`.

These are opportunity paths, not WAR or trade values. Their historical workload
spread now supports the separate multi-year uncertainty calculation. The current 2026 remainder is
deliberately absent because a full-season cohort forecast cannot be relabeled as a
rest-of-season forecast.
