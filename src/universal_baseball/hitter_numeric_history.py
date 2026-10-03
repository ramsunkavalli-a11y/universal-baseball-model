"""Rebuild fractional pooled evidence without dataframe schema inference."""
import numpy as np
import polars as pl
from universal_baseball.practical_hitter_v30 import EVENTS

BUCKETS = ['MLB', 'AAA', 'AA', 'Aplus', 'A', 'Aminus', 'DSL', 'RK120',
           'RK121', 'RK124', 'RK128', 'RK134', 'RKother', 'MEX']


def repair(source, counts):
    """Only use each row's dated origin/earlier counts; leave labels untouched."""
    required = ['row_id', 'player_id', 'origin_year', 'draft_known', 'draft_year']
    if any(c not in source.columns for c in required):
        raise ValueError('Missing dated identity or draft fields')
    if counts.unique(['player_id', 'season', 'bucket']).height != len(counts):
        raise ValueError('Duplicate season-level count records')
    lookup = {(o['player_id'], o['season'], o['bucket']): o
              for o in counts.iter_rows(named=True)}
    origins = source.select(required).to_dicts()
    columns = {}
    for bucket in BUCKETS:
        a = np.zeros((len(source), 1+2*len(EVENTS)), dtype=float)
        for i, o in enumerate(origins):
            for lag, w in enumerate([1., .8, .6]):
                row = lookup.get((o['player_id'], o['origin_year']-lag, bucket))
                if row is None:
                    continue
                a[i, 0] += w*row['plate_appearances']
                for j, (_, (num, den, _)) in enumerate(EVENTS.items()):
                    a[i, 1+2*j] += w*row[num]
                    a[i, 2+2*j] += w*row[den]
        columns[f'pooled_{bucket}_pa'] = a[:, 0]
        for j, (event, (_, _, prior)) in enumerate(EVENTS.items()):
            columns[f'pooled_{bucket}_{event}'] = (
                a[:, 1+2*j]+100*prior)/(a[:, 2+2*j]+100)
    elapsed = []
    for o in origins:
        if o['draft_known'] and (o['draft_year'] is None or o['draft_year'] > o['origin_year']):
            raise ValueError('Missing or future draft evidence')
        elapsed.append((o['origin_year']-o['draft_year'])/10 if o['draft_known'] else 0.)
    columns['draft_elapsed'] = np.asarray(elapsed, dtype=float)
    result = source.with_columns(pl.Series(c, a, dtype=pl.Float64) for c, a in columns.items())
    changes = []
    for c in columns:
        old, new = source[c].to_numpy(), result[c].to_numpy()
        different = ~np.isclose(old, new, atol=1e-12, rtol=0)
        if different.any():
            changes.append(dict(feature=c, old_dtype=str(source.schema[c]),
                                corrected_dtype='Float64', changed_rows=int(different.sum()),
                                maximum_absolute_difference=float(np.max(abs(new-old)))))
    unchanged = [c for c in source.columns if c not in columns]
    if not source.select(unchanged).equals(result.select(unchanged)):
        raise AssertionError('Unrelated features or labels changed')
    return result, changes
