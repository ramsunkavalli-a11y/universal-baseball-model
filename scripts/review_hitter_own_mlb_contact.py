"""Trace recovered source through actual players and unchanged saved forecasts."""
import json
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from universal_baseball.mlb_contact_history import CELLS
from prepare_practical_hitter_v33 import safe_matrix
import recover_hitter_own_mlb_contact as r

OUT = r.OUT
BASE = r.ROOT/'reports/generated/practical-hitter-numeric-repair-v53'
FIXED = [(592450, 2023, 'Aaron Judge'), (592450, 2024, 'Aaron Judge'),
         (665742, 2023, 'Juan Soto'), (474832, 2023, 'Brandon Belt'),
         (679529, 2023, 'Spencer Torkelson'), (680574, 2023, 'Matt McLain'),
         (701762, 2024, 'Nick Kurtz'), (821181, 2024, 'Juneiker Caceres')]


def peers(f, row):
    pool = f.filter((pl.col('origin_year') == row['origin_year']) &
                    (pl.col('stage') == row['stage']) &
                    (pl.col('prior_debut') == row['prior_debut']) &
                    (pl.col('player_id') != row['player_id']))
    same_position = pool.filter(pl.col('source_position') == row['source_position'])
    if len(same_position) >= 4:
        pool = same_position
    distance = sum(((pl.col(c)-row[c])/scale)**2 for c, scale in
                   [('age', 3), ('pa_0', 250), ('AAA_0_pa', 250), ('AA_0_pa', 250),
                    ('minor_pa_0', 400), ('quality_0', 1), ('scout_rank_score_0', .25)])
    return pool.with_columns(distance.alias('peer_distance')).sort('peer_distance', 'player_id').head(4)


def main():
    assert not (OUT/'cases.json').exists(), 'Preserve completed walkthrough evidence'
    report = r.read(OUT/'source-report.json')
    for mapping in ['input_hashes', 'output_hashes']:
        for path, digest in report[mapping].items():
            assert sha256_file(Path(path)) == digest, path
    f = pl.read_parquet(r.CURRENT/'features.parquet').sort('row_id')
    q = pl.read_parquet(r.CURRENT/'scored-predictions.parquet').sort('row_id')
    annual = pl.read_parquet(OUT/'annual-cells.parquet')
    oldcoverage = pl.read_parquet(OUT/'forecast-source-coverage.parquet').sort('row_id')
    assert oldcoverage['row_id'].equals(f['row_id']) and len(q) == 30506
    # Supplement, not replacement: a zero exposure alone cannot identify missing years.
    coverage = oldcoverage.with_columns(
        pl.Series('calendar_history_source_years_available', [sum(y-lag in [2023, 2024] for lag in range(3)) for y in f['origin_year']]),
        pl.Series('mlb_PA_in_available_source_years', [sum(row[f'pa_{lag}'] for lag in range(3)
                  if row['origin_year']-lag in [2023, 2024]) for row in f.iter_rows(named=True)]),
        pl.Series('mlb_PA_outside_available_source_years', [sum(row[f'pa_{lag}'] for lag in range(3)
                  if row['origin_year']-lag not in [2023, 2024]) for row in f.iter_rows(named=True)]))
    coverage.write_parquet(OUT/'forecast-source-missingness.parquet')
    stints_path = r.ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet'
    stints = pl.read_parquet(stints_path)
    selected = {(pid, year): ['fixed_source_case'] for pid, year, name in FIXED}
    for year in [2023, 2024]:
        pool = annual.filter(pl.col('season') == year).rename({'season': 'origin_year'}).join(
            f.select('origin_year', 'player_id', 'pa_0', 'player_name'), on=['origin_year', 'player_id'], how='inner', validate='1:1')
        pool = pool.filter(pl.col('pa_0') >= 200).with_columns(
            ((pl.col('physical_contacts')-pl.col('geometry_core_contacts'))/pl.col('physical_contacts')).alias('excluded_profile_fraction'))
        row = pool.sort('excluded_profile_fraction', 'player_id', descending=[True, False]).row(0, named=True)
        selected.setdefault((row['player_id'], year), []).append('largest_noncore_fraction_at_least_200_PA')
    for pid, year, name in FIXED:
        assert q.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == year))['player_name'].to_list() == [name]
    event_frames = {y: pl.read_parquet(OUT/f'events-{y}.parquet') for y in [2023, 2024]}
    names = r.read(BASE/'preflight.json')['rate_features']
    pa_names = r.read(r.CURRENT/'preflight.json')['pa_features']
    assert len(names) == 199 and len(pa_names) == 251
    assert not any('contact_' in name or 'core_bin' in name for name in names+pa_names)
    cases = []; head_hashes = {}; replayed = 0
    origin_keys = ['row_id', 'player_id', 'player_name', 'origin_year', 'target_year', 'outer_fold',
                   'age', 'source_position', 'stage', 'prior_debut', 'pa_0', 'minor_pa_0',
                   'preseason_raw_p', 'preseason_p', 'preseason_raw_conditional_pa', 'preseason_conditional_pa',
                   'preseason_pa', 'preseason_rate', 'preseason_value', 'origin_replacement_rate', 'next_pa', 'next_value']
    with threadpool_limits(limits=2):
        for (pid, year), reasons in selected.items():
            row = q.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == year)).row(0, named=True)
            te = f.filter(pl.col('row_id') == row['row_id']); k = row['outer_fold']
            source_row = te.row(0, named=True)
            history = stints.filter((pl.col('player_id') == pid) & pl.col('season').is_between(year-2, year)).sort('season', 'bucket', 'team_id')
            contact_history = annual.filter((pl.col('player_id') == pid) & pl.col('season').is_between(year-2, year))
            event_history = pl.concat([g.filter((pl.col('player_id') == pid) & pl.col('season').is_between(year-2, year)) for g in event_frames.values()])
            assert not len(event_history) or event_history['season'].max() <= year
            event_histories = []
            for (season,), part in event_history.group_by('season'):
                event_histories.append(dict(season=season,
                    exclusions=part.group_by('contact_profile_status', 'cell_eligible').len().sort('contact_profile_status').to_dicts(),
                    venues=part.group_by('venue_id', 'venue_name').len().sort('venue_id').to_dicts(),
                    matchup_hands=part.group_by('batter_side', 'pitcher_hand').len().sort('batter_side', 'pitcher_hand').to_dicts(),
                    core_homers=int(part.filter(pl.col('cell_eligible') & (pl.col('canonical_outcome') == 'HR')).height),
                    homers_without_geometry=part.filter((pl.col('canonical_outcome') == 'HR') & ~pl.col('cell_eligible')).select(*r.KEY, 'bb_type', 'hc_x', 'hc_y').to_dicts()))
            fit = r.read(BASE/f'fit-{year}-{k}.json')
            head = next(h for h in fit['heads'] if h['head'] == 'rate')
            assert sha256_file(Path(head['path'])) == head['sha256']; head_hashes[head['path']] = head['sha256']
            model = joblib.load(head['path']); x = safe_matrix(te, names)
            rate = float(model.predict(x)[0]); assert np.isclose(rate, row['preseason_rate'], atol=1e-10, rtol=0)
            terms = x[0]*model.coef_
            assert np.isclose(float(model.intercept_+terms.sum()), rate, atol=1e-10, rtol=0)
            trace = dict(intercept=float(model.intercept_), rate=rate,
                         signed_age_terms=float(sum(v for n, v in zip(names, terms) if n in ['age_centered', 'age_squared'])),
                         largest_terms=sorted([dict(feature=n, input=float(value), signed_term=float(term))
                                              for n, value, term in zip(names, x[0], terms)], key=lambda d: abs(d['signed_term']), reverse=True)[:12])
            replayed += 1
            for h in r.read(r.CURRENT/f'fit-{year}-{k}.json')['heads']:
                assert sha256_file(Path(h['path'])) == h['sha256']; head_hashes[h['path']] = h['sha256']
                model = joblib.load(h['path']); xp = te.select(pa_names).to_numpy()
                expected = 'preseason_raw_p' if h['head'] == 'participation' else 'preseason_raw_conditional_pa'
                prediction = float(model.predict_proba(xp)[0, 1]) if h['head'] == 'participation' else float(model.predict(xp)[0])
                assert np.isclose(prediction, row[expected], atol=1e-10, rtol=0); replayed += 1
            assert np.isclose(row['preseason_pa'], row['preseason_p']*row['preseason_conditional_pa'], atol=1e-10, rtol=0)
            assert np.isclose(row['preseason_value'], row['preseason_pa']*(rate/600+row['origin_replacement_rate']), atol=1e-10, rtol=0)
            peers_q = peers(f, source_row)
            peer_records = []
            for peer in peers_q.iter_rows(named=True):
                pred = q.filter(pl.col('row_id') == peer['row_id']).row(0, named=True)
                record = {n: pred[n] for n in origin_keys}
                record['peer_distance'] = peer['peer_distance']
                record['actual_target_relative_rate'] = peer['next_batting_rate'] if pred['next_pa'] else None
                record['contact_history'] = annual.filter((pl.col('player_id') == peer['player_id']) & pl.col('season').is_between(year-2, year)).select('season', 'physical_contacts', 'classified_contacts').to_dicts()
                peer_records.append(record)
            current_cells = [{n: value for n, value in r.items() if n not in CELLS} | dict(nonzero_cells={n: r[n] for n in CELLS if r[n]}) for r in contact_history.to_dicts()]
            cases.append(dict(origin={n: row[n] for n in origin_keys}, reasons=reasons,
                actual_target_relative_rate=source_row['next_batting_rate'] if row['next_pa'] else None,
                dated_stats=history.to_dicts(), own_mlb_contacts=current_cells,
                context_by_source_season=sorted(event_histories, key=lambda r:r['season']),
                coverage=coverage.filter(pl.col('row_id') == row['row_id']).row(0, named=True),
                unchanged_saved_rate_trace=trace,
                actual_rate_inputs={n: source_row[n] for n in names},
                actual_pa_inputs={n: source_row[n] for n in pa_names},
                peers=peer_records,
                source_only=True, hypothetical_contact_forecast=None))
    summary = coverage.join(q.select('row_id'), on='row_id', how='semi').group_by('origin_year').agg(
        pl.len().alias('forecast_rows'),
        (pl.col('own_mlb_classified_contact_history') > 0).sum().alias('with_own_mlb_contact'),
        pl.col('mlb_PA_outside_available_source_years').sum().alias('history_mlb_PA_without_source')).sort('origin_year').to_dicts()
    r.write(OUT/'cases.json', dict(selection_rules=['Eight fixed source cases', 'Largest noncore fraction per season at 200+ current MLB PA'],
          peer_rule='Same origin/stage/prior debut, position when four peers exist; distance uses only origin age, MLB/AAA/AA/minor PA, quality and current rank.',
          cases=cases, source_hashes=report['input_hashes'], saved_head_hashes=head_hashes,
          saved_heads_replayed=replayed, current_forecasts_unchanged=True))
    r.write(OUT/'review-receipt.json', dict(source_walkthrough_status='pending_readable_review',
          new_model_fits=0, saved_heads_replayed=replayed, reviewed_source_cases=len(cases),
          coverage=summary, source_only=True, forecast_changed=False,
          source_hashes={str(p):sha256_file(p) for p in [Path(__file__), OUT/'source-report.json',
              OUT/'cases.json', OUT/'forecast-source-missingness.parquet', stints_path]}))
    for c in cases:
        z = c['origin']; print(z['row_id'], z['player_name'], z['origin_year'],
               [(a['season'], a['physical_contacts'], a['classified_contacts']) for a in c['own_mlb_contacts']],
               'rate', z['preseason_rate'], 'PA', z['preseason_pa'], 'actual', z['next_pa'],
               'future rate', c['actual_target_relative_rate'], flush=True)
    print(summary, flush=True)


if __name__ == '__main__':
    main()
