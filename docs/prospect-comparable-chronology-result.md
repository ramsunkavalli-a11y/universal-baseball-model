# Prospect comparable chronology audit

**Decision:** `withhold_any_player_type_failing_a_fold`

Every reference outcome window ends before its validation snapshot. Non-arrivals are retained as zero.

| Type | Target | Reference origins | Total MAE vs baseline | Arrival Brier vs baseline | Supported conditional MAE vs baseline | Pass |
|---|---:|---|---:|---:|---:|---:|
| hitter | 2008 | 2003 | 0.187 vs 0.271 | 0.076 vs 0.089 | 0.709 vs 0.805 | True |
| hitter | 2013 | 2003,2008 | 0.201 vs 0.270 | 0.075 vs 0.097 | 0.762 vs 0.839 | True |
| hitter | 2018 | 2003,2008,2013 | 0.219 vs 0.294 | 0.082 vs 0.107 | 0.855 vs 0.946 | True |
| hitter | 2021 | 2003,2008,2013,2016 | 0.242 vs 0.307 | 0.083 vs 0.112 | 0.728 vs 0.813 | True |
| pitcher | 2008 | 2003 | 0.162 vs 0.215 | 0.085 vs 0.100 | 0.756 vs 0.755 | False |
| pitcher | 2013 | 2003,2008 | 0.179 vs 0.220 | 0.101 vs 0.120 | 0.834 vs 0.842 | True |
| pitcher | 2018 | 2003,2008,2013 | 0.180 vs 0.217 | 0.091 vs 0.117 | 0.933 vs 0.949 | True |
| pitcher | 2021 | 2003,2008,2013,2016 | 0.184 vs 0.210 | 0.089 vs 0.108 | 0.805 vs 0.791 | False |

## Frozen global/local blend

The local comparable rate was blended toward the historical arrival-population mean. The weight was selected on 2008, 2013 and 2018, then tested unchanged on 2021.

| Type | Selected local weight | 2021 MAE vs baseline | 2021 RMSE vs baseline | Pass |
|---|---:|---:|---:|---:|
| hitter | 1.0 | 0.728 vs 0.813 | 0.941 vs 1.038 | True |
| pitcher | 0.7 | 0.795 vs 0.791 | 1.066 vs 1.075 | False |

A player type may be displayed as validated conditional talent only if every frozen fold passes. Public FV and rankings are not used.
