"""Complete the contract's explicit Frick 3B case without changing prior receipts."""
import math
from pathlib import Path
import polars as pl
from universal_baseball.storage import sha256_file
from verify_double_play_support_v22 import ROOT, PUBLIC, read, write


def main():
    labels = read(PUBLIC/'labels.json.gz')
    focal = next(r for r in labels if (r['population'], r['origin_year'], r['player_id'], r['position']) == ('minor_prospect', 2022, 687518, 5))
    peers = sorted((r for r in labels if r['population'] == focal['population'] and r['origin_year'] == 2022
        and r['position'] == 5 and r['level'] == focal['level'] and r['player_id'] != 687518),
        key=lambda r: (abs(r['age']-focal['age']) if r['age'] is not None and focal['age'] is not None else 999.,
            abs(math.log1p(r['minor_outs'])-math.log1p(focal['minor_outs'])), r['player_id']))[:3]
    people = {r['player_id'] for r in (focal, *peers)}
    counts_path = ROOT/'reports/generated/defense-minor-counts-v18/counts.parquet'
    native_path = ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet'
    official_path = ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet'
    counts = pl.read_parquet(counts_path).filter(pl.col('player_id').is_in(sorted(people)) & pl.col('season').is_between(2020, 2022)).to_dicts()
    native = pl.read_parquet(native_path).filter(pl.col('player_id').is_in(sorted(people)) & (pl.col('season') <= 2025)).to_dicts()
    official = pl.read_parquet(official_path).filter(pl.col('player_id').is_in(sorted(people)) & pl.col('is_mlb') & (pl.col('season') <= 2025)).to_dicts()
    walks = []
    for r in labels:
        if r['population'] != 'minor_prospect' or r['origin_year'] != 2022 or r['player_id'] not in people:
            continue
        pid = r['player_id']
        walks.append(dict(identity=[r['population'], 2022, pid, r['position']], origin=r,
            minor_known_history=[n for n in counts if n['player_id'] == pid],
            native_known_history=[n for n in native if n['player_id'] == pid and n['season'] <= 2022],
            actual_DP_opportunities=None, initial_pivot_roles=None, predictions=None,
            annual_MLB_paths=[dict(season=y, same_position_target=r['annual'][y-2023],
                native_all_positions=[n for n in native if n['player_id'] == pid and n['season'] == y],
                official_all_positions=[n for n in official if n['player_id'] == pid and n['season'] == y]) for y in (2023, 2024, 2025)]))
    selection = dict(identity=['minor_prospect', 2022, 687518, 5], player_name=focal['player_name'],
        peer_keys=[['minor_prospect', 2022, r['player_id'], 5] for r in peers],
        reason='Contract explicitly fixes Frick 3B; first selection instead chose principal 2B. Preserve and supplement it.')
    write(PUBLIC/'player-walkthrough-supplement.json.gz', dict(selections=[selection], walks=walks,
        distinct_player_origins=len(people), position_walks=len(walks), model_fits=0,
        player_walkthrough_status='pending_main_review', hashes={str(p):sha256_file(p) for p in
            (Path(__file__), PUBLIC/'labels.json.gz', PUBLIC/'player-walkthrough.json.gz', counts_path, native_path, official_path)}))
    print(selection, flush=True)
    for r in (focal, *peers):
        print(dict(name=r['player_name'], outs=r['minor_outs'], double_plays=r['doublePlays'],
            known_count_outs=r['doublePlays_known_outs'], quality=r['quality_rate'], status=r['quality_status']), flush=True)


if __name__ == '__main__':
    main()
