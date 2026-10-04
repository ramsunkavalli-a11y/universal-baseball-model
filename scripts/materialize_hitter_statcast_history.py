"""Recover cached launch measurements with explicit support; no model fits."""
import json
from pathlib import Path
import polars as pl
from universal_baseball.hitter_statcast_history import project_launch_history, annual_launch_features, KEY
from universal_baseball.mlb_contact_history import RAW_COLUMNS
from universal_baseball.storage import sha256_file
import recover_hitter_own_mlb_contact as ordinary

ROOT = ordinary.ROOT
OUT = ROOT/'reports/generated/hitter-statcast-history'
PLAN = ROOT/'docs/hitter-statcast-integration-plan.md'


def main():
    assert not (OUT/'source-report.json').exists(), 'Preserve sealed source outputs'
    OUT.mkdir(parents=True, exist_ok=True)
    prior_path = ordinary.OUT/'source-report.json'
    prior = ordinary.read(prior_path)
    review_path = ordinary.OUT/'review-receipt.json'
    review = ordinary.read(review_path)
    # Own-source integrity and player replay receipts are prerequisites, not model validation.
    for group in [prior['input_hashes'], prior['output_hashes'], review['source_hashes']]:
        for path, digest in group.items():
            ordinary.checked(Path(path), digest)
    hashes = {str(p): sha256_file(p) for p in [PLAN, Path(__file__), prior_path, review_path,
        ROOT/'src/universal_baseball/hitter_statcast_history.py',
        ROOT/'src/universal_baseball/current_talent_batted_ball_quality.py',
        ordinary.OUT/'cases.json']}
    sources = []; annual = []; cases = ordinary.read(ordinary.OUT/'cases.json')
    projected_years = {}
    allowed = RAW_COLUMNS+['launch_speed', 'launch_angle']
    for year in [2023, 2024]:
        base = ordinary.CACHE/f'mlb-{year}'
        receipt_path = base/f'reports/generated/current-talent-historical-mlb-game-evidence/{year}/report.json'
        receipt = ordinary.read(receipt_path)
        hashes[str(receipt_path)] = sha256_file(receipt_path)
        frames = []
        for capture in receipt['source']['savant_captures']:
            path = base/capture['raw_path']
            hashes[str(path)] = ordinary.checked(path, capture['response_sha256'])
            assert path.stat().st_size == capture['response_byte_count']
            raw = pl.read_csv(path, columns=allowed, schema_overrides={c: pl.String for c in allowed},
                              null_values=['null', 'NaN', 'nan', ''])
            assert len(raw) == capture['raw_row_count']
            frames.append(project_launch_history(raw, year))
        q = pl.concat(frames).sort(KEY)
        assert q.unique(KEY).height == len(q) and q.unique(KEY[:-1]).height == len(q)
        source = pl.read_parquet(ordinary.OUT/f'events-{year}.parquet').rename(
            {'at_bat_index': 'source_at_bat_index'}).with_columns(
                (pl.col('source_at_bat_index')+1).alias('at_bat_number'))
        context = source.select(*KEY, 'core_bin', 'canonical_outcome', 'cell_eligible',
            'contact_profile_status', 'venue_id', 'venue_name', 'batter_side', 'pitcher_hand', 'league_id')
        q = q.join(context, on=KEY, how='left', validate='1:1')
        # A source-only audit must explain unmatched records before downstream use.
        unmatched = q.filter(pl.col('league_id').is_null())
        if len(unmatched):
            raise ValueError(f'{year}: {len(unmatched)} terminal launch contacts lack ordinary identity/context')
        assert q['venue_id'].null_count() == 0
        assert q['invalid_ev'].sum() == 0 and q['invalid_la'].sum() == 0, 'Inspect invalid provider readings before acceptance'
        features = annual_launch_features(q)
        q.write_parquet(OUT/f'launch-events-{year}.parquet')
        features.write_parquet(OUT/f'annual-{year}.parquet')
        annual.append(features); projected_years[year] = q
        sources.append(dict(season=year, raw_chunks=len(frames), terminal_nonbunt_contacts=len(q),
            measured_ev=int(q['valid_ev'].sum()), measured_la=int(q['valid_la'].sum()),
            complete_pairs=int(q['complete_pair'].sum()), missing_pairs=int((~q['complete_pair']).sum()),
            people=q['player_id'].n_unique(), games=q['game_pk'].n_unique(),
            launch_pairs_without_geometry=int(q.filter(pl.col('complete_pair') & pl.col('core_bin').is_null()).height),
            homers_without_geometry=int(q.filter((pl.col('events')=='home_run') & pl.col('core_bin').is_null()).height),
            measured_homers_without_geometry=int(q.filter((pl.col('events')=='home_run') &
                pl.col('complete_pair') & pl.col('core_bin').is_null()).height),
            missing_pair_outcomes=q.filter(~pl.col('complete_pair')).group_by('events').len().sort('events').to_dicts(),
            first_date=q['game_date'].min(), last_date=q['game_date'].max()))
        print(f'{year}: {len(q)} terminal non-bunt contacts, {q["complete_pair"].sum()} complete launch pairs.', flush=True)
    annual = pl.concat(annual).sort('season', 'player_id')
    annual.write_parquet(OUT/'annual-launch-features.parquet')
    fpath = ordinary.CURRENT/'features.parquet'
    hashes[str(fpath)] = sha256_file(fpath)
    f = pl.read_parquet(fpath)
    lookup = {(r['season'], r['player_id']): r['measured_pair_contacts'] for r in annual.to_dicts()}
    coverage = f.select('row_id', 'origin_year', 'target_year', 'player_id', 'outer_fold', 'prior_debut', 'stage', 'next_pa').with_columns(
        pl.Series('own_mlb_launch_pairs', [sum(lookup.get((r['origin_year']-lag, r['player_id']), 0)
            for lag in range(3)) for r in f.iter_rows(named=True)]),
        pl.Series('available_source_years', [sum(y <= r['origin_year'] and y >= r['origin_year']-2 for y in projected_years)
            for r in f.iter_rows(named=True)]))
    coverage.write_parquet(OUT/'forecast-source-coverage.parquet')
    preflight = ordinary.read(ordinary.CURRENT/'preflight.json')
    cells = []
    for c in preflight['cells']:
        tr = coverage.filter(pl.col('row_id').is_in(c['training_row_ids']))
        te = coverage.filter(pl.col('row_id').is_in(c['test_row_ids']))
        assert tr['target_year'].max() <= c['year'] and not tr['outer_fold'].eq(c['fold']).any()
        cells.append(dict(origin_year=c['year'], outer_fold=c['fold'],
            active_training_people_with_launch=tr.filter((pl.col('next_pa')>0) &
                (pl.col('own_mlb_launch_pairs')>0))['player_id'].n_unique(),
            test_people_with_launch=te.filter(pl.col('own_mlb_launch_pairs')>0)['player_id'].n_unique(),
            tracked_training_origins=sorted(tr.filter(pl.col('own_mlb_launch_pairs')>0)['origin_year'].unique().to_list())))
    reviewed = []
    for case in cases['cases']:
        r = case['origin']; year = r['origin_year']; pid = r['player_id']
        history = annual.filter((pl.col('player_id')==pid) & pl.col('season').is_between(year-2, year))
        details = []
        for y, q in projected_years.items():
            if not year-2 <= y <= year:
                continue
            part = q.filter(pl.col('player_id')==pid)
            details.append(dict(season=y, terminal_contacts=len(part),
                measured_pair_count=int(part['complete_pair'].sum()),
                measured_missing_geometry=part.filter(pl.col('complete_pair') & pl.col('core_bin').is_null())
                    .select(*KEY, 'events', 'launch_speed', 'launch_angle', 'contact_profile_status').to_dicts(),
                missing_measurements=part.filter(~pl.col('complete_pair')).select(*KEY, 'events', 'launch_speed', 'launch_angle').to_dicts(),
                venue_counts=part.group_by('venue_id', 'venue_name').len().sort('venue_id').to_dicts()))
        reviewed.append(dict(origin=r, reasons=case['reasons'], dated_stats=case['dated_stats'],
            annual_launch_history=history.to_dicts(), source_details=details,
            actual_target_relative_rate=case['actual_target_relative_rate'],
            current_rate_inputs=case['actual_rate_inputs'], current_rate_trace=case['unchanged_saved_rate_trace'],
            peers=case['peers'], tracking_candidate_forecast=None, forecasts_changed=False))
    ordinary.write(OUT/'cases.json', dict(source_only=True, selection_rules=cases['selection_rules'],
        peer_rule=cases['peer_rule'], cases=reviewed))
    outputs = {str(p): sha256_file(p) for p in sorted(OUT.glob('*')) if p.is_file()}
    ordinary.write(OUT/'source-report.json', dict(source_only=True, new_model_fits=0, forecasts_changed=False,
        protected_outcomes_used=False, deployment_approved=False, source_walkthrough_status='pending_readable_review',
        raw_columns=allowed, source_years=[2023, 2024], years=sources, actual_fold_support=cells,
        source_hashes=hashes, output_hashes=outputs, quantile_method='linear, p=.95',
        provider_estimation_vintage_known=False, raw_metrics_not_park_or_opponent_adjusted=True))


if __name__ == '__main__':
    main()
