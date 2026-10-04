"""A dated affiliated-minor evidence clock, never an individual absence clock."""
import numpy as np
import polars as pl

from universal_baseball.hitter_numeric_history import BUCKETS
from universal_baseball.practical_hitter_v30 import EVENTS

AFFILIATED = [b for b in BUCKETS if b not in ['MLB', 'MEX']]
WEIGHTS = [1., .8, .6]


def seasons(origin, available):
    if not available:
        return [origin-k for k in range(3)]
    years = []
    year = origin
    while len(years) < 3:
        if year != 2020:
            years.append(year)
        year -= 1
    return years


def rebuild(source, counts, games, *, available):
    """Only declared history-derived fields change; preserve identity and labels."""
    keys = ['player_id', 'season', 'bucket']
    for table in [counts, games]:
        if table.unique(keys).height != len(table):
            raise ValueError('Duplicate season-level source')
    if not counts.filter((pl.col('season') == 2020)&pl.col('bucket').is_in(AFFILIATED)).is_empty():
        raise ValueError('Unexpected affiliated 2020 production')
    c = {(s['player_id'], s['season'], s['bucket']): s for s in counts.iter_rows(named=True)}
    g = {(s['player_id'], s['season'], s['bucket']): s for s in games.iter_rows(named=True)}
    # Every relevant season is source-covered before missing own-player rows
    # can mean zero. This helper is not a raw capture completeness certifier.
    covered = set(counts['season']) & set(games['season'])
    rows, provenance = [], []
    for o in source.select('row_id','origin_year','player_id','draft_rank').iter_rows(named=True):
        y, pid = o['origin_year'], o['player_id']
        clock = seasons(y, available)
        if not set(clock+[y-k for k in range(3)]) <= covered:
            raise ValueError('Uncovered source season')
        row = {'row_id': o['row_id']}
        provenance.append(dict(row_id=o['row_id'], origin_year=y,
            **{'affiliated_source_year_'+str(k): v for k,v in enumerate(clock)},
            **{'affiliated_calendar_gap_'+str(k): y-v for k,v in enumerate(clock)}))
        exposure = 0.
        minor_pa, minor_games = [0.]*3, [0.]*3
        for b in BUCKETS:
            years = clock if b in AFFILIATED else [y-k for k in range(3)]
            h = []
            for k, year in enumerate(years):
                s, game = c.get((pid,year,b)), g.get((pid,year,b))
                pa = float(s['plate_appearances']) if s else 0.
                gp = float(game['games_played']) if game else 0.
                if (s is None) != (game is None) or (s and pa != game['plate_appearances']):
                    raise ValueError('Counts and games disagree')
                h.append((pa,gp,s))
                exposure += pa
                if b != 'MLB':
                    minor_pa[k] += pa
                    minor_games[k] += gp
                if b in AFFILIATED:
                    row[f'{b}_{k}_pa'] = pa
                    row[f'{b}_{k}_present'] = float(pa > 0)
                    for event,(num,den,prior) in EVENTS.items():
                        row[f'{b}_{k}_{event}'] = ((s[num] if s else 0)+100*prior)/((s[den] if s else 0)+100)
            if b in AFFILIATED:
                row[f'pooled_{b}_pa'] = sum(w*s[0] for w,s in zip(WEIGHTS,h))
                for event,(num,den,prior) in EVENTS.items():
                    n = sum(w*s[2][num] for w,s in zip(WEIGHTS,h) if s[2])
                    d = sum(w*s[2][den] for w,s in zip(WEIGHTS,h) if s[2])
                    row[f'pooled_{b}_{event}'] = (n+100*prior)/(d+100)
                pa = sum(w*s[0] for w,s in zip(WEIGHTS,h))
                gp = sum(w*s[1] for w,s in zip(WEIGHTS,h))
                row[f'games_pool_{b}'] = gp
                row[f'role_pool_{b}'] = (pa+40)/(gp+10)
        for k in range(3):
            row[f'minor_pa_{k}'] = minor_pa[k]
            row[f'games_minor_{k}'] = minor_games[k]
            row[f'role_minor_{k}'] = (minor_pa[k]+40)/(minor_games[k]+10)
        row['draft_rank_low_exposure'] = o['draft_rank']*100/(100+exposure)
        rows.append(row)
    # Explicit Float64 avoids the legacy first-row integer schema failure.
    a = pl.DataFrame(rows, schema_overrides={n: pl.Float64 for n in rows[0] if n!='row_id'})
    names = [n for n in a.columns if n!='row_id']
    assert set(names) <= set(source.columns)
    out = source.drop(names).join(a,on='row_id',validate='1:1').select(source.columns)
    if available:
        # Arithmetic reconstruction can differ at floating roundoff. Where
        # the calendar clock did not change, preserve the actual saved input.
        mask = source['origin_year'].is_in([2020,2021,2022]).to_numpy()
        out = out.with_columns(pl.Series(n,np.where(mask,out[n].to_numpy(),source[n].to_numpy()),dtype=pl.Float64)
                               for n in names)
    preserved = [n for n in source.columns if n not in names]
    assert out.select(preserved).equals(source.select(preserved))
    assert np.isfinite(out.select(names).to_numpy()).all()
    return out, pl.DataFrame(provenance), names
