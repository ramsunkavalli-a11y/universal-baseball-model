"""Seal independent source review and all fixed case/peer arithmetic."""
from pathlib import Path
import math
import polars as pl
from universal_baseball.storage import sha256_file
from verify_double_play_support_v22 import ROOT, PUBLIC, read, write


def main():
    independent = read(PUBLIC/'independent-review.json.gz')
    assert independent['status'] == 'pass'
    ledger = pl.read_parquet(ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet').to_dicts()
    labels = { (r['population'], r['origin_year'], r['player_id'], r['position']):r for r in read(PUBLIC/'labels.json.gz') }
    walks = []; selections = []
    paths = [Path(__file__), ROOT/'docs/defense-double-play-source-v22-result.md']
    for name in ('preflight.json.gz', 'source-support.json.gz', 'independent-review.json.gz',
                 'player-walkthrough.json.gz', 'player-walkthrough-supplement.json.gz'):
        path = PUBLIC/name; record = read(path); paths.append(path)
        for file, digest in record.get('hashes', {}).items():
            assert sha256_file(Path(file)) == digest, file
        walks.extend(record.get('walks', [])); selections.extend(record.get('selections', []))
    for w in walks:
        k = tuple(w['identity']); assert w['origin'] == labels[k]
        for a in w['annual_MLB_paths']:
            assert a['same_position_target'] == labels[k]['annual'][a['season']-k[1]-1]
            assert a['native_all_positions'] == [n for n in ledger if n['player_id'] == k[2] and n['season'] == a['season']]
        if 'recent_unshrunk_evidence' in w:
            usable = [n for n in ledger if n['player_id'] == k[2] and n['position'] == k[3]
                and k[1]-2 <= n['season'] <= k[1] and n['exposure_valid'] and n['dp_runs'] is not None]
            h = w['recent_unshrunk_evidence']; outs = sum(n['native_outs'] for n in usable); runs = sum(n['dp_runs'] for n in usable)
            assert h['outs'] == outs and h['runs'] == runs
            assert h['rate_per_500_innings'] == (1500*runs/outs if outs else None)
        assert w['predictions'] is None
    expected = {543760, 665926, 596019, 571448, 502671, 677951, 687518}
    assert expected <= {s['identity'][2] for s in selections}
    assert any(s['identity'] == ['minor_prospect', 2022, 687518, 5] for s in selections)
    for s in selections:
        assert len(s['peer_keys']) == 3
        assert all(any(w['identity'] == k for w in walks) for k in [s['identity'], *s['peer_keys']])
    record = dict(status='source_review_complete', player_walkthrough_status='complete',
        distinct_player_origins=len({tuple(w['identity'][:3]) for w in walks}),
        position_walks=len({tuple(w['identity']) for w in walks}),
        independent_source_replay='pass', predictive_validation='not_run', deployment_approved=False,
        previous_goal_turn='No defense progress: read-only Lovich batting diagnosis. This turn completes double-play source/support replay and player review.',
        next_step='Separate contracted MLB history versus neutral DP quality comparison with explicit traffic limitation',
        source_scope_correction='Frick explicit 3B fixed case supplied by preserved supplement; principal 2B case retained',
        unresolved=['True eligible DP chances absent', 'Lower-level future-quality support', 'Historical measurement era and publication scope',
            'Defense development and delivered value integration', 'Separate Lovich batting defect'],
        model_fits=0, no_2026_selection=True, forecasts_unchanged=True,
        hashes={str(p):sha256_file(p) for p in paths})
    write(PUBLIC/'final-review.json.gz', record)
    print({k:v for k,v in record.items() if k != 'hashes'}, flush=True)


if __name__ == '__main__':
    main()
