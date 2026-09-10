# Zero-mass WAR uncertainty diagnostic

Status: exact mixture promoted after rolling confirmation.

The current Phase 1 range is a bell curve around expected WAR. That is structurally
wrong for players with a meaningful chance of no MLB activity: the real forecast has
an exact mass at zero plus a separate active-player distribution.

A parameter-free hurdle challenger was built from the already frozen participation,
conditional workload and rate variance. It preserves every point estimate and total
variance. Only the shape of the P10–P90 range changes.

On the frozen March 27, 2025 forecast:

| Group | Range | Overall coverage | Mean interval score | Active-player coverage |
| --- | --- | ---: | ---: | ---: |
| Hitters | Moment-normal | 96.9% | 0.968 | 82.0% |
| Hitters | Zero-mass hurdle | 94.4% | 0.795 | 67.3% |
| Pitchers | Moment-normal | 95.9% | 0.635 | 73.7% |
| Pitchers | Zero-mass hurdle | 93.8% | 0.509 | 60.3% |

Lower interval score is better. The hurdle improves overall interval score by 17.8%
for hitters and 20.0% for pitchers, largely by giving likely inactive players an
honest zero-width interval at zero. It also exposes that the conditional active-player
distribution is too narrow, especially for pitchers.

Do not choose between these ranges from one disclosed season. The next candidate must
retain the exact zero mass, widen or reshape the active distribution separately, and
be selected and confirmed over rolling forecast origins. A global width multiplier
would mix two different problems and violate the model's skill/opportunity separation.

That next component test is now complete. Rolling prior-origin scaling supports a
1.207 hitter and 1.245 pitcher performance standard-deviation adjustment while leaving
participation and workload untouched. An exact simulation now combines the frozen
zero-truncated workload model with that scaled performance distribution. On 2025 it
improves the current moment-normal interval score to 0.789 for hitters and 0.512 for
pitchers, with no point-estimate change. See the
[rolling conditional result](rolling-conditional-war-uncertainty-result.md).

The rolling combined gate subsequently passed: interval score improved in every
2022–2025 origin for both components. The private playable build now uses the exact
zero mass and simulated positive distribution. Only the 22 two-way players retain an
independent-moments combination. Do not add a second workload width correction:
conditional workload already meets its coverage target. See the
[combined result](rolling-combined-war-uncertainty-result.md).

Reproduce with:

```powershell
.\.venv\Scripts\python.exe scripts\audit_historical_war_hurdle_uncertainty.py
```
