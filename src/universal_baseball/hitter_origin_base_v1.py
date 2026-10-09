"""2027-origin extension of the reviewed base arithmetic; sealed builders unchanged."""
import math
import polars as pl
from universal_baseball.hitter_numeric_history import BUCKETS
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.practical_hitter_v30 import EVENTS

POSITIONS = [str(i) for i in range(1, 11)] + ['Y', 'UNKNOWN']


def _base_inputs(snapshots, stints, counts, values, debuts, roster, *, source_cutoff):
    if not isinstance(source_cutoff, int) or not 2011 <= source_cutoff <= 2026:
        raise ValueError('Only declared predictor origins through 2026')
    if snapshots['origin_year'].max() > source_cutoff or snapshots['origin_year'].min() < 2011:
        raise ValueError('Unsupported origin')
    for f in [stints, counts, values, roster]:
        if f['season'].max() > source_cutoff:
            raise ValueError('Future predictor source')
    for f, key in [(snapshots, ['origin_year', 'player_id']), (counts, ['season', 'player_id', 'bucket']),
                   (values, ['season', 'player_id']), (debuts, ['player_id']), (roster, ['season', 'player_id'])]:
        if f.unique(key).height != len(f):
            raise ValueError('Duplicate source identity')
    if snapshots['row_id'].n_unique() != len(snapshots):
        raise ValueError('Duplicate row identity')
    mlb = counts.filter(pl.col('bucket') == 'MLB').select('season', 'player_id', 'plate_appearances')
    check = values.join(mlb, on=['season', 'player_id'], how='left', validate='1:1')
    if check['plate_appearances'].null_count() or (check['mlb_pa'] != check['plate_appearances']).any():
        raise ValueError('Certified origin value/PA mismatch')
    needed = {y-k for y in snapshots['origin_year'].unique() for k in range(3)}
    if not needed <= set(values['season'].unique()):
        raise ValueError('Uncertified origin quality seasons')
    environments = values.group_by('season').agg(pl.col('schedule_fraction').n_unique().alias('fractions'),
        pl.col('league_pa').n_unique().alias('totals'))
    if environments.filter((pl.col('fractions') != 1) | (pl.col('totals') != 1)).height:
        raise ValueError('Conflicting origin environments')
    env = {r['season']: (r['schedule_fraction'], 570*r['schedule_fraction']/r['league_pa'])
           for r in values.unique('season').iter_rows(named=True)}
    val = {(r['season'], r['player_id']): r for r in values.iter_rows(named=True)}
    lut = {(r['season'], r['player_id'], r['bucket']): r for r in counts.iter_rows(named=True)}
    annual_age = stints.filter(pl.col('plate_appearances') > 0).group_by('season', 'player_id').agg(
        pl.col('reported_age').drop_nulls().median().alias('reported_age_annual'))
    primary = stints.filter(pl.col('plate_appearances') > 0).sort(
        ['season', 'player_id', 'plate_appearances', 'team_id'], descending=[False, False, True, False]).unique(
        ['season', 'player_id'], keep='first')
    metadata = primary.join(annual_age, on=['season', 'player_id'], validate='1:1').sort('season')
    histories = {}
    for r in metadata.iter_rows(named=True):
        histories.setdefault(r['player_id'], []).append(r)
    debut = {r['player_id']: r['mlb_debut_date'].year for r in debuts.iter_rows(named=True)}
    listing = {(r['season'], r['player_id']): r['team_id'] for r in roster.iter_rows(named=True)}
    rows = []
    for s in snapshots.iter_rows(named=True):
        y, pid = s['origin_year'], s['player_id']
        past = [r for r in histories.get(pid, []) if r['season'] <= y]; last = past[-1] if past else None
        age = s['age']; unknown = False
        if age is None and last and last['reported_age_annual'] is not None:
            age = last['reported_age_annual']+y-last['season']
        if age is None:
            age = 27.; unknown = True
        if not math.isfinite(age):
            raise ValueError('Invalid age')
        d = debut.get(pid); elapsed = y-d if d is not None and d <= y else -1
        row = dict(row_id=s['row_id'], origin_year=y, target_year=y+1, horizon=1, player_id=pid,
            outer_fold=player_fold(pid), age=float(age), age_unknown=int(unknown), age_centered=(age-27)/5,
            age_squared=((age-27)/5)**2, elapsed=elapsed, elapsed_scaled=max(-1, elapsed)/10,
            prior_debut=int(elapsed >= 0), window_complete=True, player_name=last['player_name'] if last else None,
            team_id=listing.get((y, pid), last['team_id'] if last else None), on_40man=int((y, pid) in listing),
            reorganized=int(y >= 2021), last_stat_gap=min(5, y-last['season']) if last else 5,
            source_position=last['position'] if last else 'UNKNOWN', snapshot_level=s['snapshot_level'])
        for pos in POSITIONS:
            row['position_'+pos] = int(row['source_position'] == pos)
        regular = 0; absence = 0
        for lag in range(3):
            year = y-lag; row[f'milb_canceled_{lag}'] = int(year == 2020); allpa = 0; mpa = 0
            for bucket in BUCKETS:
                c = lut.get((year, pid, bucket)); pa = c['plate_appearances'] if c else 0; allpa += pa
                prefix = f'{bucket}_{lag}_'; row[prefix+'pa'] = float(pa); row[prefix+'present'] = int(pa > 0)
                for ev, (num, den, prior) in EVENTS.items():
                    row[prefix+ev] = ((c[num] if c else 0)+100*prior)/((c[den] if c else 0)+100)
                if bucket == 'MLB':
                    mpa = pa
            row[f'pa_{lag}'] = mpa; row[f'work_{lag}'] = mpa/env[year][0]; row[f'minor_pa_{lag}'] = allpa-mpa
            v = val.get((year, pid))
            if mpa > 0 and v is None:
                raise ValueError('Observed MLB production without certified origin value')
            contribution = v['component_war'] if v else 0
            row[f'quality_{lag}'] = 600*(contribution-env[year][1]*mpa)/(mpa+1200)
            row[f'quality_present_{lag}'] = int(mpa > 0)
            regular += row[f'work_{lag}'] >= 400; absence += mpa == 0
        row['regular_window'] = int(regular); row['regular_window_scaled'] = regular/3; row['absence_window_scaled'] = absence/3
        row['current_state'] = 0 if row['pa_0'] == 0 else 1 if row['pa_0'] < 200 else 2 if row['pa_0'] < 400 else 3
        row['stage'] = ('Current MLB' if row['pa_0'] > 0 else 'Upper minors' if row['AAA_0_pa']+row['AA_0_pa'] > 0
                        else 'Lower minors' if row['minor_pa_0'] > 0 else 'Inactive / unknown')
        row['origin_replacement_rate'] = env[y][1]/env[y][0]
        row['career_mlb_observed_pa'] = sum(r['plate_appearances'] for r in past if r['sport_id'] == 1)
        row['career_mlb_left_truncated'] = int(d is not None and d < 2008)
        rows.append(row)
    return pl.DataFrame(rows, schema_overrides={'team_id': pl.Int64, 'player_name': pl.String,
                                               **{f'{b}_{k}_pa': pl.Float64 for b in BUCKETS for k in range(3)}})

def base_inputs(snapshots, stints, counts, values, debuts, roster, *, source_cutoff):
    """Retain the tested full-career MLB PA correction, including traded players."""
    if (snapshots['origin_year'] == 2020).any():
        raise ValueError('Canceled-origin rows require their separate builder')
    if debuts['mlb_debut_date'].max().year > source_cutoff:
        raise ValueError('Future debut census')
    if counts['plate_appearances'].null_count() or (counts['plate_appearances'] < 0).any():
        raise ValueError('Invalid source PA')
    result = _base_inputs(snapshots, stints, counts, values, debuts, roster, source_cutoff=source_cutoff)
    mlb = counts.filter(pl.col('bucket') == 'MLB')
    frames = []
    for year in sorted(result['origin_year'].unique()):
        career = mlb.filter(pl.col('season') <= year).group_by('player_id').agg(
            pl.col('plate_appearances').sum().alias('_complete_career_pa'))
        frames.append(result.filter(pl.col('origin_year') == year).join(career, on='player_id', how='left', validate='1:1')
            .with_columns(pl.col('_complete_career_pa').fill_null(0).alias('career_mlb_observed_pa'))
            .drop('_complete_career_pa'))
    return pl.concat(frames).sort('row_id')
