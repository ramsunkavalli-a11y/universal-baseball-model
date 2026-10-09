"""Cutoff-explicit tracking inputs, separate from sealed historical builders."""
import math
import polars as pl
from universal_baseball.hitter_statcast_history import KEY
from universal_baseball.hitter_statcast_measurement import interference_award

METRICS = {'mean_ev': (90., 10.), 'ev95': (105., 10.), 'hard_hit_fraction': (0., 1.),
           'mean_la': (0., 20.), 'la_sd': (0., 20.), 'sweet_spot_fraction': (0., 1.),
           'hard_air_fraction': (0., 1.)}


def project_measurements(raw, season, *, source_cutoff):
    if not 2015 <= season <= source_cutoff <= 2026:
        raise ValueError('Only explicit completed source seasons through 2026 permitted')
    required = {'game_date', 'game_year', 'game_type', 'game_pk', 'batter', 'pitcher', 'stand',
                'p_throws', 'at_bat_number', 'pitch_number', 'type', 'events', 'des',
                'launch_speed', 'launch_angle'}
    if required - set(raw.columns):
        raise ValueError('Missing measurement columns')
    if len(raw) and (set(raw['game_year'].cast(pl.Int64).unique()) != {season}
                    or set(raw['game_type'].unique()) != {'R'}):
        raise ValueError('Source outside declared season or regular play')
    if raw.unique(['game_pk', 'batter', 'at_bat_number']).height != len(raw):
        raise ValueError('Duplicate terminal PA')
    reason = pl.when((pl.col('type') != 'X') | pl.col('events').fill_null('').str.strip_chars().eq(''))
    reason = reason.then(pl.lit('not_terminal_inplay')).when(interference_award()).then(pl.lit('interference_award'))
    reason = reason.when(pl.col('des').fill_null('').str.to_lowercase().str.contains(r'\bbunt\b')).then(pl.lit('bunt'))
    marked = raw.with_columns(reason.otherwise(None).alias('measurement_exclusion'))
    excluded = marked.filter(pl.col('measurement_exclusion').is_not_null())
    q = marked.filter(pl.col('measurement_exclusion').is_null()).select(
        pl.col('game_date').str.to_date(strict=True), pl.lit(season).alias('season'),
        *[pl.col(c).cast(pl.Int64) for c in ['game_pk', 'at_bat_number', 'pitch_number']],
        pl.col('batter').cast(pl.Int64).alias('player_id'), pl.col('pitcher').cast(pl.Int64).alias('pitcher_id'),
        pl.col('stand').alias('batter_side'), pl.col('p_throws').alias('pitcher_hand'), 'events',
        pl.col('launch_speed').cast(pl.Float64, strict=True), pl.col('launch_angle').cast(pl.Float64, strict=True))
    if q.select(pl.any_horizontal(pl.col(*KEY).is_null()).any()).item():
        raise ValueError('Missing identity')
    if len(q) and set(q['game_date'].dt.year().unique()) != {season}:
        raise ValueError('Cross-season date')
    q = q.with_columns(
        (pl.col('launch_speed').is_not_null() & (~pl.col('launch_speed').is_finite() |
            ~pl.col('launch_speed').is_between(0, 130))).fill_null(False).alias('invalid_ev'),
        (pl.col('launch_angle').is_not_null() & (~pl.col('launch_angle').is_finite() |
            ~pl.col('launch_angle').is_between(-90, 90))).fill_null(False).alias('invalid_la'))
    q = q.with_columns((pl.col('launch_speed').is_not_null() & ~pl.col('invalid_ev')).alias('valid_ev'),
                      (pl.col('launch_angle').is_not_null() & ~pl.col('invalid_la')).alias('valid_la'))
    return q.with_columns((pl.col('valid_ev') & pl.col('valid_la')).alias('complete_pair')).sort(KEY), excluded


def materialize_tracking(frame, annual, *, source_cutoff):
    if not 2015 <= source_cutoff <= 2026:
        raise ValueError('Tracking cutoff must be 2015–2026')
    if frame['origin_year'].max() > source_cutoff or annual['season'].max() > source_cutoff:
        raise ValueError('Future origin or measurement source')
    if frame.unique('row_id').height != len(frame) or annual.unique(['player_id', 'season']).height != len(annual):
        raise ValueError('Duplicate tracking join identities')
    lookup = {(r['player_id'], r['season']): r for r in annual.iter_rows(named=True)}
    controls, measures = [], []
    for lag in range(3):
        controls += [f'sc_{lag}_{s}' for s in ['ev_sample', 'la_sample', 'pair_sample', 'pair_coverage', 'source_year_available']]
        controls += [f'sc_{lag}_{m}_known' for m in METRICS]
        measures += [f'sc_{lag}_{m}' for m in METRICS] + [f'sc_{lag}_ev95_sample', f'sc_{lag}_hard_air_sample']
    rows = []
    for o in frame.iter_rows(named=True):
        pid, year = o['player_id'], o['origin_year']
        r = dict(row_id=o['row_id']); ev_total = 0; pair_total = 0
        for lag in range(3):
            y = year - lag; a = lookup.get((pid, y)); prefix = f'sc_{lag}_'
            if a and (a['last_date'].year != y or a['last_date'].year > year):
                raise ValueError('Measurement date outside source season')
            r[prefix+'source_year_available'] = float(2015 <= y <= source_cutoff)
            for kind in ['ev', 'la', 'pair']:
                n = int(a[f'measured_{kind}_contacts']) if a else 0
                if n < 0:
                    raise ValueError('Negative measurement sample')
                r[prefix+kind+'_n'] = n
                r[prefix+kind+'_sample'] = float(math.log1p(n)/math.log(601))
            ev_total += r[prefix+'ev_n']; pair_total += r[prefix+'pair_n']
            r[prefix+'pair_coverage'] = a['pair_coverage'] if a else 0.
            for m, (center, scale) in METRICS.items():
                v = a[m] if a else None
                r[prefix+m+'_known'] = float(v is not None)
                r[prefix+m] = float((v-center)/scale) if v is not None else 0.
            r[prefix+'ev95_sample'] = r[prefix+'ev95']*r[prefix+'ev_sample']
            r[prefix+'hard_air_sample'] = r[prefix+'hard_air_fraction']*r[prefix+'pair_sample']
        r['sc_own_ev_n'] = ev_total; r['sc_own_pair_n'] = pair_total; r['sc_tracked'] = ev_total > 0
        rows.append(r)
    overlay = pl.DataFrame(rows, schema_overrides={c: pl.Float64 for c in controls+measures})
    if (set(overlay.columns) - {'row_id'}) & set(frame.columns):
        raise ValueError('Tracking overlay would replace existing fields')
    return frame.join(overlay, on='row_id', validate='1:1'), controls, measures
