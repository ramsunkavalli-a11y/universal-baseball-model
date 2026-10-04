"""Recover cached ordinary MLB contact detail; no new model or tracking features."""
import json
from pathlib import Path
import polars as pl
from universal_baseball.mlb_contact_history import (
    RAW_COLUMNS, KEY, CELLS, outcome_counts, contact_ledger, annual_cells, schedule_venues,
)
from universal_baseball.savant import project_savant_performance_rows
from universal_baseball.mlb_performance import assign_savant_actual_league
from universal_baseball.mlb_season_stats import MlbTeamLeague
from universal_baseball.current_talent_mlb_evidence import build_mlb_current_talent_player_game_evidence
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path('C:/Users/ramav/Documents/Codex/2026-08-20/i-ve-been-using-online-chatgpt/work/park-inputs')
OUT = ROOT/'reports/generated/hitter-own-mlb-contact-source'
CURRENT = ROOT/'reports/generated/hitter-preseason-readiness-v68'
CONTRACT = ROOT/'docs/hitter-own-mlb-contact-source-contract.md'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False, default=str)+'\n', encoding='utf8', newline='\n')


def checked(path, expected):
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f'Changed source capture {path}')
    return actual


def main():
    assert not (OUT/'source-report.json').exists(), 'Preserve completed source receipts'
    OUT.mkdir(parents=True, exist_ok=True)
    hashes = {str(p): sha256_file(p) for p in [CONTRACT, Path(__file__),
              ROOT/'src/universal_baseball/mlb_contact_history.py',
              ROOT/'src/universal_baseball/savant.py', ROOT/'src/universal_baseball/contact_profile.py',
              ROOT/'src/universal_baseball/current_talent_mlb_evidence.py',
              ROOT/'src/universal_baseball/mlb_performance.py', ROOT/'src/universal_baseball/batted_ball_direction.py',
              ROOT/'src/universal_baseball/mlb_performance_materialization.py',
              ROOT/'src/universal_baseball/current_talent_contact_value_source.py']}
    official_path = ROOT/'reports/generated/practical-hitter-v31/counts.parquet'
    official_hash = read(ROOT/'reports/generated/practical-hitter-v31/preflight.json')['input_hashes'][str(official_path)]
    hashes[str(official_path)] = checked(official_path, official_hash)
    official = pl.read_parquet(official_path).filter(pl.col('bucket') == 'MLB').with_columns(
        (pl.col('babip_hits')-pl.col('doubles')-pl.col('triples')).alias('singles'))
    reports = []; annual = []; exclusions = []
    for year in [2023, 2024]:
        base = CACHE/f'mlb-{year}'
        report_path = base/f'reports/generated/current-talent-historical-mlb-game-evidence/{year}/report.json'
        legacy = read(report_path); hashes[str(report_path)] = sha256_file(report_path)
        assert legacy['accepted'] and legacy['reconciliation']['exact_outcome_reconciliation']
        assert legacy['scope']['season'] == year
        team = legacy['source']['team_authority']; team_path = base/team['raw_path']
        hashes[str(team_path)] = checked(team_path, team['response_sha256'])
        teams = [MlbTeamLeague(team_id=t['id'], abbreviation=t['abbreviation'],
                              league_id=t['league']['id'], league_name=t['league']['name'])
                 for t in read(team_path)['teams'] if t['league']['id'] in [103, 104]]
        assert len(teams) == 30
        capture = legacy['schedule']; path = base/capture['raw_path']
        hashes[str(path)] = checked(path, capture['response_sha256'])
        venues = schedule_venues(read(path), year)
        frames = []
        for capture in legacy['source']['savant_captures']:
            path = base/capture['raw_path']
            hashes[str(path)] = checked(path, capture['response_sha256'])
            assert path.stat().st_size == capture['response_byte_count']
            raw = pl.read_csv(path, columns=RAW_COLUMNS,
                              schema_overrides={c: pl.String for c in RAW_COLUMNS},
                              null_values=['null', 'NaN', 'nan', ''])
            projected = project_savant_performance_rows(raw, regular_season_only=True)
            assert len(raw) == capture['raw_row_count'] and len(projected) == capture['projected_row_count']
            frames.append(projected)
        projected = assign_savant_actual_league(pl.concat(frames), teams)
        assert projected.unique(KEY).height == len(projected)
        assert set(projected['game_year']) == {year}
        summary, profile, note = build_mlb_current_talent_player_game_evidence(projected)
        for kind, actual in [('profile', profile), ('summary', summary)]:
            record = legacy['storage'][kind]; path = base/record['path']
            hashes[str(path)] = checked(path, record['file_sha256'])
            expected = pl.read_parquet(path)
            keys = ['season', 'game_pk', 'league_id', 'player_id'] + (['core_bin'] if kind == 'profile' else [])
            assert actual.select(expected.columns).sort(keys).equals(expected.sort(keys)), kind
        counts, substitutions = outcome_counts(projected)
        cols = ['plate_appearances', 'strike_outs', 'unintentional_walks', 'hit_by_pitch',
                'singles', 'doubles', 'triples', 'home_runs']
        positive = official.filter((pl.col('season') == year) & (pl.col('plate_appearances') > 0)).select('season', 'player_id', *cols)
        assert counts.select(positive.columns).sort('player_id').equals(positive.sort('player_id'))
        events = contact_ledger(projected, venues); cells = annual_cells(events)
        assert len(events) == legacy['evidence']['total_observed_contacts']
        assert len(projected.filter(pl.col('is_plate_appearance_terminal'))) == legacy['evidence']['true_pa_terminal_count']
        # The profile includes K/BB/HBP as well as geometry: compare geometry only.
        geometry = profile.filter(pl.col('core_bin').is_in([c.removeprefix('count_').split('___')[0] for c in CELLS]))['occurrence_count'].sum()
        assert cells['geometry_core_contacts'].sum() == geometry
        events.write_parquet(OUT/f'events-{year}.parquet')
        cells.write_parquet(OUT/f'cells-{year}.parquet'); annual.append(cells)
        counts.write_parquet(OUT/f'outcomes-{year}.parquet')
        substitutions.write_parquet(OUT/f'outcome-substitutions-{year}.parquet')
        excluded = events.group_by('season', 'contact_profile_status', 'cell_eligible', 'canonical_outcome').len().sort('contact_profile_status')
        exclusions += excluded.to_dicts()
        reports.append(dict(season=year, official_counts_exact=True, legacy_profiles_and_summaries_exact=True,
                            physical_contacts=len(events), geometry_core_contacts=int(geometry),
                            classified_contacts=int(cells['classified_contacts'].sum()),
                            physical_outcome_residual=int(legacy['evidence']['total_contact_count_residual']),
                            missing_venue_contacts=int(events['venue_missing'].sum()),
                            missing_batter_hand=int(events['batter_side'].is_null().sum()),
                            missing_pitcher_hand=int(events['pitcher_hand'].is_null().sum()),
                            contact_people=events['player_id'].n_unique(), contact_games=events['game_pk'].n_unique(),
                            outcome_substitutions=len(substitutions),
                            first_date=events['game_date'].min(), last_date=events['game_date'].max()))
        print(f'{year}: {len(counts)} people, {len(events)} physical contacts; accepted profiles and official counts reproduce.', flush=True)
    annual = pl.concat(annual).sort('season', 'player_id'); annual.write_parquet(OUT/'annual-cells.parquet')
    # This is a forecast-row feature-availability count, not a learned adjustment.
    source_path = CURRENT/'features.parquet'; anchor_path = CURRENT/'scored-predictions.parquet'
    hashes.update({str(p): sha256_file(p) for p in [source_path, anchor_path, CURRENT/'preflight.json']})
    features = pl.read_parquet(source_path)
    lookup = {(r['season'], r['player_id']): r['classified_contacts'] for r in annual.to_dicts()}
    coverage = features.select('row_id', 'origin_year', 'target_year', 'player_id', 'outer_fold', 'prior_debut', 'stage', 'next_pa').with_columns(
        pl.Series('own_mlb_classified_contact_history', [sum(lookup.get((r['origin_year']-lag, r['player_id']), 0)
                   for lag in range(3)) for r in features.iter_rows(named=True)]))
    coverage.write_parquet(OUT/'forecast-source-coverage.parquet')
    anchor = pl.read_parquet(anchor_path).sort('row_id'); cells = []
    for cell in read(CURRENT/'preflight.json')['cells']:
        train = coverage.filter(pl.col('row_id').is_in(cell['training_row_ids']))
        test = coverage.filter(pl.col('row_id').is_in(cell['test_row_ids']))
        assert train['target_year'].max() <= cell['year'] and not train['outer_fold'].eq(cell['fold']).any()
        assert not train['target_year'].eq(2020).any()
        active = train.filter((pl.col('next_pa') > 0) & (pl.col('own_mlb_classified_contact_history') > 0))
        cells.append(dict(year=cell['year'], fold=cell['fold'], training_rows=len(train),
                          active_contact_training_people=active['player_id'].n_unique(),
                          active_contact_training_rows=len(active),
                          test_rows=len(test), test_with_own_mlb_contact=int((test['own_mlb_classified_contact_history'] > 0).sum())))
    assert len(anchor) == 30506 and len(features) == 63282
    write(OUT/'source-report.json', dict(new_model_fits=0, source_walkthrough_status='pending',
          source_seasons=[2023, 2024], raw_columns=RAW_COLUMNS, tracking_predictors_used=False,
          forecasts_changed=False, protected_outcomes_used=False, deployment_approved=False,
          years=reports, exclusions=exclusions, actual_outer_cells=cells,
          limits=['Only two cached MLB seasons; earlier source gaps remain missing.',
                  'Raw observations, not park-neutral or opponent-neutral skill.',
                  'A source pass does not establish future MLB forecast improvement.'],
          input_hashes=hashes,
          output_hashes={str(p): sha256_file(p) for p in OUT.glob('*.parquet')}))


if __name__ == '__main__':
    main()
