"""Source walks and origin-blind peers; no invented double-play forecasts."""
import math
from pathlib import Path

import polars as pl
from universal_baseball.storage import sha256_file
from verify_double_play_support_v22 import ROOT, PUBLIC, read, write


def identity(r):
    return r['population'], r['origin_year'], r['player_id'], r['position']


def main():
    assert read(PUBLIC/'independent-review.json.gz')['status'] == 'pass'
    labels = read(PUBLIC/'labels.json.gz')
    native_path = ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet'
    counts_path = ROOT/'reports/generated/defense-minor-counts-v18/counts.parquet'
    official_path = ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet'
    native = pl.read_parquet(native_path).to_dicts()
    cases = [(543760, 'MLB_history'), (665926, 'MLB_history'), (596019, 'MLB_history'),
             (571448, 'MLB_history'), (502671, 'MLB_history'), (677951, 'MLB_history'), (687518, 'minor_prospect')]
    selections = []; people = set()
    for pid, population in cases:
        eligible = [r for r in labels if r['origin_year'] == 2022 and r['player_id'] == pid and r['population'] == population]
        assert eligible, (pid, population)
        def exposure(r):
            return r['history_outs'] if population == 'MLB_history' else r['minor_outs']
        focal = max(eligible, key=lambda r: (exposure(r), -r['position']))
        peers = sorted((r for r in labels if r['origin_year'] == 2022 and r['population'] == population
            and r['position'] == focal['position'] and r['level'] == focal['level'] and r['player_id'] != pid),
            key=lambda r: (abs(r['age']-focal['age']) if r['age'] is not None and focal['age'] is not None else 999.,
                abs(math.log1p(exposure(r))-math.log1p(exposure(focal))), r['player_id']))[:3]
        selections.append(dict(identity=list(identity(focal)), player_name=focal['player_name'],
            reason='Fixed source case; principal existing origin position by recorded exposure', peer_keys=[list(identity(p)) for p in peers]))
        people.update((population, 2022, r['player_id']) for r in (focal, *peers))
    write(PUBLIC/'player-selection.json.gz', dict(selections=selections, model_fits=0,
        peer_rule='Same population origin position level, lexicographic age/log-recorded-outs distance then ID; no outcomes used'))
    ids = sorted({pid for pop, year, pid in people})
    counts = pl.read_parquet(counts_path).filter(pl.col('player_id').is_in(ids)).to_dicts()
    official = pl.read_parquet(official_path).filter(pl.col('is_mlb') & pl.col('player_id').is_in(ids) & (pl.col('season') <= 2025)).to_dicts()
    walks = []
    for r in sorted((r for r in labels if (r['population'], r['origin_year'], r['player_id']) in people), key=identity):
        pid = r['player_id']; pos = r['position']; year = r['origin_year']
        history = [n for n in native if n['player_id'] == pid and n['position'] == pos and n['season'] <= year]
        usable = [n for n in history if n['exposure_valid'] and n['dp_runs'] is not None and year-2 <= n['season']]
        n = sum(s['native_outs'] for s in usable); total = sum(s['dp_runs'] for s in usable)
        annual = []
        for target_year in range(year+1, year+4):
            annual.append(dict(season=target_year, same_position_target=r['annual'][target_year-year-1],
                native_all_positions=[s for s in native if s['player_id'] == pid and s['season'] == target_year],
                official_all_positions=[s for s in official if s['player_id'] == pid and s['season'] == target_year]))
        walks.append(dict(identity=list(identity(r)), origin=r, native_known_history=history,
            recent_unshrunk_evidence=dict(runs=total, outs=n, innings=n/3, rate_per_500_innings=1500*total/n if n else None,
                actual_DP_opportunities=None, initial_pivot_roles=None, not_a_fitted_grade=True),
            minor_known_history=[s for s in counts if s['player_id'] == pid and year-2 <= s['season'] <= year],
            annual_MLB_paths=annual, predictions=None, forecast_changes=False))
    write(PUBLIC/'player-walkthrough.json.gz', dict(selections=selections, walks=walks, distinct_player_origins=len(people),
        position_walks=len(walks), model_fits=0, player_walkthrough_status='pending_main_review',
        hashes={str(p): sha256_file(p) for p in (Path(__file__), PUBLIC/'independent-review.json.gz',
            PUBLIC/'labels.json.gz', PUBLIC/'player-selection.json.gz', native_path, counts_path, official_path)}))
    for s in selections:
        w = next(w for w in walks if w['identity'] == s['identity'])
        print(dict(name=s['player_name'], position=w['origin']['position'], history=w['recent_unshrunk_evidence'],
            future=w['origin']['quality_rate'], status=w['origin']['quality_status'],
            annual=[(a['season'], a['same_position_target']['native']['dp_runs'] if a['same_position_target']['native'] else None,
                a['same_position_target']['official_outs'], a['same_position_target']['measurement_valid']) for a in w['annual_MLB_paths']]), flush=True)


if __name__ == '__main__':
    main()
