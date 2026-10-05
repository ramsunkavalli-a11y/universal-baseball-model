"""Prove historical base equivalence, then assemble source-only forecast inputs."""
from pathlib import Path
import json
import numpy as np
import polars as pl
from universal_baseball.hitter_forecast_base import base_inputs, population
from universal_baseball.hitter_forecast_inputs import pooled_inputs
from universal_baseball.hitter_forecast_tracking import materialize_tracking
from universal_baseball.historical_prospect_rank import features as rank_features
from universal_baseball.storage import sha256_file
from prepare_hitter_games_v38 import features as game_features

ROOT = Path(__file__).resolve().parents[1]
OLD = Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated')
OUT = ROOT/'reports/generated/hitter-base-inputs-2025'
CONTRACT = ROOT/'docs/hitter-2025-population-and-base-input-contract.md'


def read(p):
    return json.loads(p.read_text(encoding='utf8'))


def write(p, obj):
    assert not p.exists(), f'Preserve {p}'
    p.write_text(json.dumps(obj, indent=2, allow_nan=False, default=str)+'\n', encoding='utf8', newline='\n')


def historical_snapshots(historical, exits, saved):
    frames = [pl.read_parquet(ROOT/f'model_artifacts/advanced-rookie-repair-v3/{y}/hitter_snapshots.parquet')
              for y in range(2011, 2020)]
    frames.append(saved.filter(pl.col('snapshot_year').is_between(2021, 2024)))
    snaps = pl.concat(frames).rename({'snapshot_year': 'origin_year', 'age_years': 'age', 'as_of_level_group': 'snapshot_level'})
    extra = exits.filter(pl.col('window_complete')).select('origin_year', 'player_id', 'age').join(
        snaps.select('origin_year', 'player_id'), on=['origin_year', 'player_id'], how='anti').with_columns(
        pl.lit('INACTIVE').alias('snapshot_level'))
    snaps = pl.concat([snaps, extra.select(snaps.columns)], how='vertical_relaxed')
    snaps = snaps.join(historical.select('origin_year', 'player_id', 'row_id'), on=['origin_year', 'player_id'], validate='1:1')
    assert len(snaps) == len(historical), 'Historical population mismatch'
    return snaps.sort('row_id')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT/'assembly-review.json').exists(), 'Preserve completed assembly'
    p_stints = ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet'
    p_counts = ROOT/'reports/generated/practical-hitter-v31/counts.parquet'
    p_values = ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet'
    p_debuts = ROOT/'reports/generated/hitter-arrival-source-repair-v1/debut-dates.parquet'
    p_roster = ROOT/'reports/generated/hitter-arrival-source-repair-v1/year-end-rosters.parquet'
    p_snapshots = OLD/'opportunity-history-sources-v2/tables/hitter_snapshots.parquet'
    p_exits = ROOT/'model_artifacts/post-arrival-support-v17/panel.parquet'
    p_hist = ROOT/'reports/generated/practical-hitter-v31/features.parquet'
    stints, counts, values, debuts, rosters, saved, exits, historical = [pl.read_parquet(p) for p in
        [p_stints, p_counts, p_values, p_debuts, p_roster, p_snapshots, p_exits, p_hist]]
    snapshots = historical_snapshots(historical, exits, saved)
    rebuilt = base_inputs(snapshots, stints.filter(pl.col('season') <= 2024), counts.filter(pl.col('season') <= 2024),
        values.filter(pl.col('season') <= 2024), debuts, rosters, source_cutoff=2024).sort('row_id')
    original = historical.sort('row_id'); compared = 0
    for c in rebuilt.columns:
        a, b = rebuilt[c], original[c]
        if a.dtype in [pl.Float64, pl.Float32]:
            assert np.allclose(a.to_numpy(), b.to_numpy(), rtol=0, atol=1e-12, equal_nan=True), c
        else:
            assert a.equals(b, check_dtypes=False), c
        compared += len(original)
    current = population(saved, exits, source_cutoff=2025)
    roster_review = read(ROOT/'reports/generated/hitter-rosters-2025-source/review.json')
    assert roster_review['approved_for_membership_feature']
    new_roster_path = ROOT/'reports/generated/hitter-rosters-2025-source/year-end-2025.parquet'
    assert sha256_file(new_roster_path) == roster_review['roster_sha256']
    full_roster = pl.concat([rosters, pl.read_parquet(new_roster_path)], how='vertical_relaxed')
    current_base = base_inputs(current, stints, counts, values, debuts, full_roster, source_cutoff=2025)
    for c in ['next_pa', 'next_value', 'next_state', 'next_batting_rate', 'next_active']:
        assert c not in current_base.columns
    draft_path = OLD/'draft-history/draft-history.parquet'
    draft = pl.read_parquet(draft_path).filter(pl.col('draft_year') <= 2025)
    overlay = pooled_inputs(current_base, counts, draft, source_cutoff=2025)
    out = current_base.join(overlay, on='row_id', validate='1:1')
    game_path = ROOT/'reports/generated/practical-hitter-v38/game-counts.parquet'
    games = pl.read_parquet(game_path)
    assert games['season'].max() == 2025 and games['season'].min() == 2008
    g = counts.select('season', 'player_id', 'bucket', 'plate_appearances').join(
        games.rename({'plate_appearances': 'games_source_pa'}), on=['season', 'player_id', 'bucket'], how='full', coalesce=True, validate='1:1')
    assert not g['plate_appearances'].null_count() and not g['games_source_pa'].null_count()
    assert g['plate_appearances'].equals(g['games_source_pa'])
    assert g['games_played'].null_count() == 0
    out, game_columns = game_features(out, games)
    rank_path = ROOT/'reports/generated/hitter-preseason-2026-archive-probe/preseason-2026-ranks.parquet'
    rank_review = read(rank_path.parent/'transport-and-player-review.json'); assert rank_review['rank_source_approved']
    assert sha256_file(rank_path) == rank_review['source_hashes'][str(rank_path)]
    ranks = pl.concat([pl.read_parquet(ROOT/'reports/generated/hitter-preseason-readiness-v67/ranks.parquet'), pl.read_parquet(rank_path)])
    lookup = {(r['season'], r['player_id']): r['rank'] for r in ranks.iter_rows(named=True)}
    capacities = {r['season']: r['list_capacity'] for r in ranks.iter_rows(named=True)}
    rank_overlay = pl.DataFrame([dict(row_id=r['row_id'], **rank_features(r['player_id'], 2026, lookup, capacities))
                                 for r in out.iter_rows(named=True)])
    out = out.join(rank_overlay, on='row_id', validate='1:1')
    annual_path = ROOT/'reports/generated/hitter-tracking-2025-audit/annual-launch-features-through-2025.parquet'
    tracking_review = read(annual_path.parent/'final-source-review.json')
    assert tracking_review['source_approved_for_existing_tracking_inputs']
    assert sha256_file(annual_path) == tracking_review['output_hashes'][str(annual_path)]
    out, controls, measures = materialize_tracking(out, pl.read_parquet(annual_path), source_cutoff=2025)
    current.write_parquet(OUT/'membership.parquet'); current_base.write_parquet(OUT/'base-inputs.parquet')
    out.write_parquet(OUT/'assembled-before-translation.parquet')
    # Source-only population audit; no batting names or ranks become role authority.
    batting = stints.filter(pl.col('season') == 2025).group_by('player_id').agg(
        pl.col('player_name').first(), pl.col('plate_appearances').sum(), pl.col('position').unique().sort().alias('positions'))
    outside = batting.join(current.select('player_id'), on='player_id', how='anti')
    assert outside['positions'].to_list() == [['1']]*len(outside), 'Non-pitcher source identity omitted'
    outside.write_parquet(OUT/'batting-identities-outside.parquet')
    fixed = [592450, 701762, 670541, 808982, 691406, 656555, 815908, 815888]
    exit_ids = current.filter(pl.col('membership_source') == 'continued_recent_debut_exit')['player_id'].head(2).to_list()
    no_current = out.filter((pl.col('pa_0') == 0) & (pl.col('minor_pa_0') == 0)).sort('player_id')['player_id'].head(2).to_list()
    cases = []
    for pid in dict.fromkeys(fixed+exit_ids+no_current):
        o = out.filter(pl.col('player_id') == pid).to_dicts()[0]
        peers = out.filter((pl.col('player_id') != pid) & (pl.col('stage') == o['stage']) & (pl.col('prior_debut') == o['prior_debut']))
        distance = sum(((pl.col(c)-o[c])/scale)**2 for c, scale in [('age', 5), ('pa_0', 200), ('minor_pa_0', 300), ('draft_rank', .25)])
        peers = peers.with_columns(distance.alias('distance')).sort('distance', 'player_id').head(3)
        source_ids = [pid, *peers['player_id'].to_list()]
        cases.append(dict(player_id=pid, actual_inputs=o, membership=current.filter(pl.col('player_id') == pid).to_dicts()[0],
            source_history=stints.filter(pl.col('player_id').is_in(source_ids) & pl.col('season').is_between(2023, 2025)).to_dicts(),
            peers=peers.select('player_id', 'player_name', 'age', 'stage', 'pa_0', 'minor_pa_0', 'draft_rank', 'distance').to_dicts()))
    write(OUT/'source-player-cases.json', dict(cases=cases, source_only=True, protected_outcomes_used=False, player_walkthrough_status='pending'))
    paths = [CONTRACT, Path(__file__), ROOT/'src/universal_baseball/hitter_forecast_base.py', p_stints, p_counts, p_values,
        p_debuts, p_roster, p_snapshots, p_exits, p_hist, draft_path, game_path, rank_path, annual_path,
        new_roster_path, rank_path.parent/'transport-and-player-review.json', annual_path.parent/'final-source-review.json',
        ROOT/'src/universal_baseball/hitter_forecast_inputs.py', ROOT/'src/universal_baseball/hitter_forecast_tracking.py']
    write(OUT/'assembly-review.json', dict(historical_rows=len(original), historical_base_fields=len(rebuilt.columns),
        historical_fields_compared=compared, historical_equivalence=True, population=len(out),
        membership_groups=current.group_by('membership_source').len().to_dicts(),
        stage_groups=out.group_by('stage').len().to_dicts(), unknown_ages=int(out['age_unknown'].sum()),
        pitcher_only_batting_outside=len(outside), pitcher_only_PA_outside=int(outside['plate_appearances'].sum()),
        no_current_batting=len(out.filter((pl.col('pa_0') == 0) & (pl.col('minor_pa_0') == 0))),
        game_source_PA_matches=True, game_features=len(game_columns), tracking_features=len(controls+measures),
        input_hashes={str(p): sha256_file(p) for p in paths},
        output_hashes={str(p): sha256_file(p) for p in sorted(OUT.glob('*.parquet'))},
        feature_families_pending=['held-player own-origin translation', 'availability evidence', 'qualified foreign/new entrant coverage'],
        candidate_ready_to_fit=False, candidate_frozen=False, new_model_fits=0, protected_outcomes_used=False,
        source_player_walkthrough_status='pending'))
    print(f'{len(original)} historical rows x {len(rebuilt.columns)} base fields reproduce; {len(out)} source-only forecast inputs', flush=True)
    print('Translation, availability and population qualification remain before fitting', flush=True)


if __name__ == '__main__':
    main()
