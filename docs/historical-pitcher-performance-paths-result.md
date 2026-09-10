# Historical pitcher performance paths

Status: source ready; no player value changed.

The career-path source now keeps pitcher component performance beside the already
retained workload and role sequence. It contains 1,798 pitchers, 10,788 annual rows
and 6,372 active pitcher-seasons from 2009-2025. The calculation uses the same
five-part K, unintentional-walk, HBP, HR and other-contact run conversion as the
current pitcher model, with each season's MLB environment and the shortened 2020
workload handled explicitly.

| Career tier | Pitchers | Mean six-year BF | Mean component WAR | Median component WAR |
|---|---:|---:|---:|---:|
| Fringe | 881 | 130 | 0.01 | -0.01 |
| Meaningful only | 213 | 508 | 0.78 | 0.67 |
| Established | 704 | 1,626 | 4.28 | 3.33 |

This is the missing source for a more coherent pitcher simulation. The challenger
should sample annual workload, role and performance from the same historical pitcher
instead of applying one prospect rate to every simulated season. A historical replay
must restrict the path library to careers observable at the forecast cutoff. Current
individual prospect rates remain excluded from promotion because they did not beat a
population mean for later MLB quality. The new path source is not itself evidence that
the challenger will improve forecasts.
