"""Reconstruct cutoff-only, prior-shrunk MLB batting summaries from actual counts."""
import numpy as np
from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.mlb_event_logit import VALUES

DETAIL = ['quality_0', 'quality_1', 'quality_2', 'pooled_mlb_quality']
RECENCY = np.array([1., .8, .6])


def reconstruct(player_id, origin, counts, environments):
    numerators = []; mass = []; seasons = []
    for lag in range(3):
        y = origin - lag
        if y not in environments:
            raise ValueError('Unknown MLB source-season coverage')
        c = np.asarray(counts.get((y, player_id), np.zeros(8)), float)
        ref = np.asarray(environments[y], float)
        if c.shape != (8,) or ref.shape != (8,) or not np.isfinite(c).all() or not np.isfinite(ref).all() or (c < 0).any() or (ref < 0).any() or not np.isclose(ref.sum(), 1):
            raise ValueError('Invalid MLB counts or reference')
        n = float(c.sum()); numerator = float((c @ VALUES - n * (ref @ VALUES)) * UNIT)
        mass.append(n); numerators.append(numerator)
        seasons.append(dict(season=y, actual_counts=c.tolist(), PA=n, source_reference=ref.tolist(), batting_wins_times_600=numerator,
                            unshrunk_batting_per600=numerator/n if n else None, shrunk_batting_per600=numerator/(n+1200), production_share=n/(n+1200)))
    pooled = float(RECENCY @ numerators / (RECENCY @ mass + 1200))
    return dict(zip(DETAIL, [r['shrunk_batting_per600'] for r in seasons] + [pooled], strict=True)), dict(seasons=seasons, pooled_weighted_PA=float(RECENCY @ mass), prior_PA=1200., pooled_mlb_quality=pooled, cutoff=origin)
