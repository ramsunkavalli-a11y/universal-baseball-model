"""No-fit independent raw-count reconstruction and seventeen actual source walks."""
from pathlib import Path
import json

import numpy as np
import polars as pl

from universal_baseball.hitter_mlb_events import DETAIL, EVENTS, reconstruct
from universal_baseball.storage import sha256_file
from run_hitter_count_baseline import ROOT, GEN, OUT as COUNT, read, verify, matrix

OUT = GEN / 'hitter-mlb-events-source-audit'
PREVIOUS = GEN / 'hitter-mlb-detail-restoration'


def save(name, obj):
    path = OUT / name
    assert not path.exists(), f'Preserve {path}'
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8', newline='\n')


def main():
    assert not OUT.exists()
    final = read(PREVIOUS / 'final-review.json'); verify(final['hashes'])
    assert final['player_walkthrough_status'] == 'complete'
    verify({final['public_report']: final['public_report_sha256']})
    previous_pre = read(PREVIOUS / 'preflight.json'); verify(previous_pre['source_hashes'])
    stints_path = GEN / 'practical-hitter-v31/dated-stints.parquet'
    counts_path = GEN / 'practical-hitter-v31/counts.parquet'
    stints = pl.read_parquet(stints_path)
    assert stints['season'].max() == 2025
    mlb = stints.filter(pl.col('sport_id') == 1)
    covered = set(mlb['season'])
    assert covered == set(range(2008, 2026))
    assert mlb.unique(['season', 'player_id', 'sport_id', 'team_id']).height == mlb.height
    mlb = mlb.with_columns(
        (pl.col('base_on_balls') - pl.col('intentional_walks')).alias('unintentional_walks'),
        (pl.col('hits') - pl.col('home_runs')).alias('babip_hits'),
        (pl.col('at_bats') - pl.col('strike_outs') - pl.col('home_runs') + pl.col('sac_flies')).alias('babip_opportunities'))
    fields = sorted({f for definition in EVENTS.values() for f in definition[:2]})
    ann = mlb.group_by('season', 'player_id').agg(pl.col(fields).sum()).sort('season', 'player_id')
    saved = pl.read_parquet(counts_path).filter(pl.col('bucket') == 'MLB').select('season', 'player_id', *fields).sort('season', 'player_id')
    assert ann.select(saved.columns).equals(saved)
    counts = {(r['season'], r['player_id']): r for r in ann.iter_rows(named=True)}
    f0 = pl.read_parquet(COUNT / 'features-0.parquet').sort('row_id')
    assert f0.height == 63314 and f0['origin_year'].max() == 2024
    old_walks = {r['row_id']: r for r in read(PREVIOUS / 'player-walks.json')['cases']}
    assert len(old_walks) == 17
    rows, walks = [], []
    for o in f0.iter_rows(named=True):
        values, source = reconstruct(o['player_id'], o['origin_year'], counts, covered)
        rows.append(dict(row_id=o['row_id'], **values))
        if o['row_id'] in old_walks:
            year = o['origin_year']; changed = dict(counts)
            for future in [year + 1, year + 2]:
                changed[(future, o['player_id'])] = dict.fromkeys(fields, 99999.)
            assert reconstruct(o['player_id'], year, changed, covered | {year + 1, year + 2}) == (values, source)
            coords = matrix(pl.DataFrame([o], schema=f0.schema), DETAIL)[0]
            assert np.allclose(coords, [source['events'][e]['model_coordinate'] for e in EVENTS], atol=1e-12)
            old = old_walks[o['row_id']]
            walks.append(dict(row_id=o['row_id'], player_id=o['player_id'], player_name=o['player_name'],
                              origin=year, fold=o['outer_fold'], information_date=o['ctx_information_date'],
                              source=source, features=values, future_mutation_unchanged=True,
                              raw_annual_MLB_counts=[counts[(s, o['player_id'])] for s in range(year-2, year+1) if (s, o['player_id']) in counts],
                              previous_forecast_unchanged={a: old['forecast'][a + '_rate'] for a in ['current', 'scalar', 'restored']},
                              previous_source_and_peer_walk=str(PREVIOUS / 'player-walks.json')))
    f = pl.DataFrame(rows).sort('row_id')
    paths = [Path(__file__), ROOT / 'src/universal_baseball/hitter_mlb_events.py',
             ROOT / 'tests/test_hitter_mlb_events.py', ROOT / 'docs/hitter-mlb-events-source-audit-contract.md',
             counts_path, stints_path, PREVIOUS / 'final-review.json', PREVIOUS / 'player-walks.json',
             ROOT / 'src/universal_baseball/practical_hitter_v30.py', ROOT / 'scripts/prepare_practical_hitter_v33.py']
    for k in range(5):
        path = COUNT / f'features-{k}.parquet'; other = pl.read_parquet(path).sort('row_id')
        assert f['row_id'].equals(other['row_id']) and other.select(DETAIL).equals(f0.select(DETAIL))
        assert np.allclose(f.select(DETAIL).to_numpy(), other.select(DETAIL).to_numpy(), atol=1e-12, rtol=0)
        paths.append(path)
    assert len(walks) == 17 and {r['row_id'] for r in walks} == set(old_walks)
    OUT.mkdir(parents=True)
    save('source-walks.json', walks)
    paths.append(OUT / 'source-walks.json')
    save('audit.json', dict(before_fitting=True, fitted_models=0,
                           annual_MLB_rows=ann.height, covered_source_seasons=sorted(covered),
                           reconstructed_rows=f.height, matrices=5, column_checks=f.height*7*5,
                           source_cases=17, future_mutation_cases=17,
                           new_features=DETAIL, protected_outcomes_used=False,
                           completed_2026_evaluation_unchanged=True, deployment_approved=False,
                           source_walkthrough_status='pending_readable_review',
                           hashes={str(p): sha256_file(p) for p in paths}))
    print(f'No fits: {ann.height} annual MLB rows match independent aggregation; {f.height*7*5} feature checks and 17 cutoff mutation/source walks pass.')


if __name__ == '__main__':
    main()
