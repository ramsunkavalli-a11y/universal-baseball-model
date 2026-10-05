"""Reconcile 2025 tracking sources and prove the historical input definition."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import polars as pl
import requests
import numpy as np
from universal_baseball.hitter_forecast_tracking import project_measurements, materialize_tracking
from universal_baseball.hitter_statcast_measurement import project_measurements as historical, interference_award
from universal_baseball.hitter_statcast_history import annual_launch_features, KEY
from universal_baseball.storage import sha256_file
from prepare_hitter_statcast_next_year import materialize as old_materialize
import capture_hitter_tracking_2025 as source

ROOT = source.ROOT; OUT = ROOT/'reports/generated/hitter-tracking-2025-audit'
CONTRACT = source.CONTRACT


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def write(path, obj):
    assert not path.exists(), f'Preserve {path}'
    path.write_text(json.dumps(obj, indent=2, allow_nan=False, default=str)+'\n', encoding='utf8', newline='\n')


def capture(name, url, params):
    expected = requests.Request('GET', url, params=params).prepare().url
    path = OUT/'captures'/f'{name}.json'; receipt = path.with_suffix('.receipt.json')
    if receipt.exists():
        r = read(receipt); assert r['requested_url'] == expected
        assert r['response_sha256'] == sha256_file(path)
        assert r['contract_sha256'] == sha256_file(CONTRACT)
        return read(path)
    assert not path.exists(), f'Unreceipted capture {path}'
    response = requests.get(url, params=params, timeout=(20, 60)); response.raise_for_status()
    obj = response.json(); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)
    write(receipt, dict(requested_url=expected, returned_url=response.url,
        response_sha256=hashlib.sha256(response.content).hexdigest(), captured_at=datetime.now(timezone.utc),
        collector_sha256=sha256_file(Path(__file__)), contract_sha256=sha256_file(CONTRACT),
        protected_outcomes_used=False))
    return obj


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT/'initial-audit.json').exists(), 'Preserve completed initial audit'
    for month in range(3, 11):
        source.capture(month)  # Verifies receipt and exact source bytes, does not refetch.
    raw = pl.concat([pl.read_parquet(source.OUT/f'2025-{m:02}.parquet') for m in range(3, 11)])
    q, excluded = project_measurements(raw, 2025, source_cutoff=2025)
    dated_path = ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet'
    dated = pl.read_parquet(dated_path).filter((pl.col('season') == 2025) & (pl.col('bucket') == 'MLB'))
    official = dated.group_by('player_id').agg(pl.col('player_name').first(),
        (pl.col('at_bats')-pl.col('strike_outs')+pl.col('sac_flies')+pl.col('sac_bunts')).sum().alias('official_contacts'),
        *[pl.col(c).sum() for c in ['singles', 'doubles', 'triples', 'home_runs', 'plate_appearances']])
    normal = raw.filter((pl.col('type') == 'X') & pl.col('events').fill_null('').str.strip_chars().ne('') & ~interference_award())
    measured = normal.group_by(pl.col('batter').cast(pl.Int64).alias('player_id')).agg(
        pl.len().alias('source_contacts'), *[(pl.col('events') == e).sum().alias(c+'_source')
        for e, c in [('single', 'singles'), ('double', 'doubles'), ('triple', 'triples'), ('home_run', 'home_runs')]])
    joined = official.join(measured, on='player_id', how='full', coalesce=True).with_columns(
        pl.exclude('player_id', 'player_name').fill_null(0))
    joined = joined.with_columns((pl.col('source_contacts')-pl.col('official_contacts')).alias('contact_residual'))
    residuals = joined.filter((pl.col('contact_residual') != 0) | pl.any_horizontal([
        pl.col(c) != pl.col(c+'_source') for c in ['singles', 'doubles', 'triples', 'home_runs']]))
    residuals.write_parquet(OUT/'reconciliation-residuals.parquet')
    joined.write_parquet(OUT/'player-reconciliation.parquet')
    # Compare the full preserved 2022 raw source, not only toy examples.
    old_raw = pl.concat([pl.read_parquet(ROOT/f'reports/generated/hitter-statcast-historical-capture/2022-{m:02}.parquet')
                         for m in range(3, 11)])
    new_q, new_ex = project_measurements(old_raw, 2022, source_cutoff=2024)
    old_q, old_ex = historical(old_raw, 2022)
    assert new_q.equals(old_q) and new_ex.equals(old_ex)
    annual_old = pl.read_parquet(ROOT/'reports/generated/hitter-statcast-full-history/annual-launch-features.parquet')
    f = pl.read_parquet(ROOT/'reports/generated/hitter-overseas-integration/features.parquet').filter(pl.col('row_id') < 63282)
    # Historical source frame contains tracking already; compare overlays without replacing fields.
    f = f.drop([c for c in f.columns if c.startswith('sc_')])
    old_f, old_control, old_measure = old_materialize(f, annual_old)
    new_f, control, measure = materialize_tracking(f, annual_old, source_cutoff=2024)
    assert old_control == control and old_measure == measure
    added = [c for c in new_f.columns if c not in f.columns]
    for c in added:
        if new_f[c].dtype == pl.Float64:
            assert np.allclose(new_f[c].to_numpy(), old_f[c].to_numpy(), rtol=0, atol=1e-12), c
        else:
            assert new_f[c].equals(old_f[c]), c
    api = 'https://statsapi.mlb.com/api/v1'
    schedule = capture('schedule-2025', api+'/schedule', dict(sportId=1, season=2025, gameType='R', hydrate='venue'))
    games = [g for d in schedule['dates'] for g in d['games']]
    assert all(str(g['season']) == '2025' and g['gameType'] == 'R' for g in games)
    completed = [g for g in games if g['status']['detailedState'].split(':')[0] in {'Final', 'Completed Early'}]
    by_game = {}
    for g in completed:
        by_game.setdefault(g['gamePk'], []).append(g)
    conflicts = [dict(game_pk=pk, segments=gs) for pk, gs in by_game.items()
                 if len({g['venue']['id'] for g in gs}) > 1]
    # Preserve unresolved split venues rather than assigning the final park blindly.
    venues = pl.DataFrame([dict(game_pk=pk, venue_id=gs[-1]['venue']['id'], venue_name=gs[-1]['venue']['name'])
                          for pk, gs in by_game.items() if pk not in {c['game_pk'] for c in conflicts}])
    q = q.join(venues, on='game_pk', how='left', validate='m:1')
    teams = capture('teams-2025', api+'/teams', dict(sportId=1, season=2025))['teams']
    authority = {t['abbreviation']: t['league']['id'] for t in teams}
    identity = raw.select(pl.col('game_pk').cast(pl.Int64), pl.col('batter').cast(pl.Int64).alias('player_id'),
        pl.col('at_bat_number').cast(pl.Int64), pl.col('pitch_number').cast(pl.Int64),
        pl.when(pl.col('inning_topbot') == 'Top').then(pl.col('away_team')).otherwise(pl.col('home_team')).alias('batting_team'))
    identity = identity.with_columns(pl.col('batting_team').replace_strict(authority, default=None).alias('league_id'))
    q = q.join(identity.select(*KEY, 'league_id'), on=KEY, how='left', validate='1:1')
    assert q['league_id'].null_count() == 0
    annual = annual_launch_features(q)
    annual.write_parquet(OUT/'annual-launch-features-2025.parquet')
    q.write_parquet(OUT/'launch-events-2025.parquet'); excluded.write_parquet(OUT/'excluded-2025.parquet')
    combined = pl.concat([annual_old, annual], how='vertical_relaxed').sort('season', 'player_id')
    combined.write_parquet(OUT/'annual-launch-features-through-2025.parquet')
    pids = [592450, 701762, 670541, 808982, 691406, 656555]
    cases = pl.DataFrame(dict(row_id=pids, player_id=pids, origin_year=[2025]*len(pids)))
    inputs, _, _ = materialize_tracking(cases, combined, source_cutoff=2025)
    inputs.write_parquet(OUT/'fixed-case-tracking-inputs.parquet')
    walks = []
    for pid in pids:
        walks.append(dict(player_id=pid, official_2025=official.filter(pl.col('player_id') == pid).to_dicts(),
            raw_contact_rows=raw.filter(pl.col('batter') == str(pid)).height,
            exclusions=excluded.filter(pl.col('batter') == str(pid)).group_by('measurement_exclusion').len().to_dicts(),
            measured_annual=combined.filter((pl.col('player_id') == pid) & pl.col('season').is_between(2023, 2025)).to_dicts(),
            input_row=inputs.filter(pl.col('player_id') == pid).to_dicts()[0],
            venues=q.filter(pl.col('player_id') == pid).group_by('venue_id', 'venue_name').len().to_dicts()))
    write(OUT/'fixed-player-walks.json', dict(cases=walks, source_only=True, forecast_fits=0, protected_outcomes_used=False))
    hashes = {str(p): sha256_file(p) for p in [CONTRACT, Path(__file__), dated_path,
        ROOT/'src/universal_baseball/hitter_forecast_tracking.py',
        ROOT/'reports/generated/hitter-statcast-full-history/annual-launch-features.parquet']}
    hashes.update({str(p): sha256_file(p) for p in sorted(source.OUT.glob('*.json'))})
    write(OUT/'initial-audit.json', dict(raw_rows=len(raw), nonbunt_contacts=len(q), people=len(annual),
        complete_pairs=int(q['complete_pair'].sum()), invalid_ev=int(q['invalid_ev'].sum()), invalid_la=int(q['invalid_la'].sum()),
        missing_venue_rows=q['venue_id'].null_count(), venue_conflicts=conflicts,
        residual_players=len(residuals), residuals=residuals.to_dicts(),
        historical_projection_rows=len(old_raw), historical_projection_exact=True,
        historical_feature_rows=len(f), historical_feature_fields=len(added),
        historical_fields_compared=len(f)*len(added), historical_feature_equivalence=True,
        source_player_walkthrough_status='pending', source_approved=False, input_hashes=hashes,
        original_publication_vintage_verified=False, protected_outcomes_used=False, model_fits=0))
    print(f'2025 source: {len(raw)} rows, {len(q)} nonbunts; {len(residuals)} residual players, {len(conflicts)} split venues', flush=True)
    print(f'Historical equivalence: {len(f)} rows x {len(added)} fields; source review pending', flush=True)


if __name__ == '__main__':
    main()
