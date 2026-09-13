# Strict six-year prospect comparable result

**Decision:** `withhold_six_year_partial_outcomes`

Every reference outcome ends before its target snapshot, and target players are removed from their own reference pool.

| Type | Target | References | WAR RMSE vs baseline | Arrival Brier vs baseline | Conditional RMSE vs baseline | Pass |
|---|---:|---|---:|---:|---:|---:|
| hitter | 2013 | 2003 | 1.589 vs 1.660 | 0.100 vs 0.119 | 1.029 vs 1.179 | True |
| hitter | 2016 | 2003,2008 | 1.660 vs 1.717 | 0.095 vs 0.118 | 1.174 vs 1.318 | False |
| hitter | 2018 | 2003,2008 | 1.610 vs 1.678 | 0.101 vs 0.125 | 1.070 vs 1.241 | False |
| hitter | 2019 | 2003,2008 | 1.257 vs 1.314 | 0.091 vs 0.116 | 0.944 vs 1.113 | True |
| pitcher | 2013 | 2003 | 1.094 vs 1.121 | 0.123 vs 0.138 | 1.117 vs 1.155 | True |
| pitcher | 2016 | 2003,2008 | 1.036 vs 1.065 | 0.116 vs 0.138 | 1.283 vs 1.326 | True |
| pitcher | 2018 | 2003,2008 | 0.897 vs 0.925 | 0.113 vs 0.136 | 1.237 vs 1.270 | True |
| pitcher | 2019 | 2003,2008 | 0.810 vs 0.841 | 0.103 vs 0.126 | 1.172 vs 1.205 | True |

MAE remains reported in the JSON but does not veto a mean expected-WAR forecast. This is still partial WAR, not full controlled value or FV.
