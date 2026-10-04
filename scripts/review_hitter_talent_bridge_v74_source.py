"""Expose the locked players' raw counts and fold-local graph features prefit."""
import polars as pl
from universal_baseball.hitter_talent_bridge import EVENTS, event_counts, translated_probability
from universal_baseball.storage import sha256_file
import evaluate_hitter_talent_bridge_v74 as e


def main():
    pre = e.read(e.OUT / 'preflight.json')
    for path, expected in pre['input_hashes'].items():
        assert sha256_file(e.Path(path)) == expected
    counts = pl.read_parquet(e.COUNTS).filter(pl.col('season') <= 2024)
    anchor = pl.read_parquet(e.previous.OUT / 'scored-predictions.parquet')
    cases = []
    for pid, year, name in e.FIXED:
        r = anchor.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == year)).row(0, named=True)
        fold = r['outer_fold']
        row = pl.read_parquet(e.OUT / f'features-{fold}.parquet').filter(pl.col('row_id') == r['row_id'])
        graph = next(g for g in e.read(e.OUT / f'translation-{fold}.json')['graphs'] if g['cutoff'] == year)
        history = counts.filter((pl.col('player_id') == pid) & pl.col('season').is_between(year - 2, year)).sort('season', 'bucket')
        joint = event_counts(history)
        stints = []
        for i, s in enumerate(history.iter_rows(named=True)):
            offset = graph['offsets'].get(s['bucket'])
            stints.append(dict(source=s, raw_events=dict(zip(EVENTS, joint[i].tolist())),
                               offset=offset, translated_events=None if offset is None else
                               dict(zip(EVENTS, translated_probability(joint[i], offset).tolist()))))
        cases.append(dict(player_id=pid, player_name=name, origin_year=year, fold=fold,
                          baseline_rate=r['baseline_rate'], unchanged_PA=r['preseason_pa'],
                          stints=stints, actual_profile=row.select(*e.PROFILE_FEATURES,
                          'translation_supported_pa', 'translation_total_pa', 'translation_buckets').to_dicts()[0],
                          source_supported_buckets=graph['connected_buckets']))
    coverage = []
    for k in range(5):
        graphs = e.read(e.OUT / f'translation-{k}.json')['graphs']
        for g in graphs:
            # Buckets without even one usable edge are absent from pair metadata,
            # not silently claimed connected because "disconnected" is empty.
            observed = set(counts.filter(pl.col('season') <= g['cutoff'])['bucket'])
            coverage.append(dict(fold=k, origin=g['cutoff'], pair_count=g['pair_count'],
                                 graph_people=len(g['people']), observed_buckets=sorted(observed),
                                 unsupported_buckets=sorted(observed - set(g['connected_buckets']))))
    e.write('prefit-source-cases.json', dict(cases=cases, graph_coverage=coverage,
                                            protected_outcomes_used=False, forecast_inputs_only=True))
    print('Nine raw-count-to-translated-profile source cases saved before new hitting fits.', flush=True)
    for c in cases:
        p = c['actual_profile']
        print(c['player_name'], c['origin_year'], 'supported PA', round(p['translation_supported_pa'], 1),
              'buckets', p['translation_buckets'], 'HR deviation / .1', round(p['translated_HR'], 3), flush=True)


if __name__ == '__main__':
    main()
