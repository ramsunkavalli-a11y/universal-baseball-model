"""Append the declared reference/report correction, preserving first results."""
import gzip
import json
import math
import polars as pl
from check_hitter_2027_historical_full_value import BASE, OUT, PUBLIC, loss, interval
from capture_hitter_2027_origin_counts import write_once
from universal_baseball.hitter_full_value_review import recenter_positive_pa, forecast_pa_column
from universal_baseball.storage import sha256_file


def score(rows, arm):
    result = loss(rows, arm)
    result['expected_PA'] = math.fsum(r[forecast_pa_column(arm)] for r in rows)
    return result


def main():
    source = OUT / 'predictions.parquet'
    output = OUT / 'predictions-reviewed.parquet'
    assert not output.exists()
    rows = pl.read_parquet(source).to_dicts()
    stints = pl.read_parquet(BASE / 'stints.parquet').filter(pl.col('level_group') == 'MLB')
    totals = stints.group_by('season', 'player_id').agg(pl.col('plate_appearances').sum())
    origin = {(r['season'], r['player_id']): r['plate_appearances'] for r in totals.to_dicts()}
    corrected, receipt = recenter_positive_pa(rows, origin)
    for old, new in zip(rows, corrected):
        assert all(old[k] == new[k] for k in old if k not in ('league_runs', 'combined'))
    index = {r['row_id']: r for r in corrected}
    groups = [('all', corrected),
              ('public_steamer', [r for r in corrected if r['steamer'] is not None]),
              ('origin_MLB_public', [r for r in corrected if r['steamer'] is not None and origin.get((r['origin_year'], r['player_id']), 0) > 0]),
              ('actual_participants_public', [r for r in corrected if r['steamer'] is not None and r['actual_PA'] > 0]),
              ('public_both', [r for r in corrected if r['steamer'] is not None and r['zips'] is not None])]
    for field in ('target_year', 'stage', 'position'):
        groups += [(f'{field}_{v}', [r for r in corrected if r[field] == v]) for v in sorted({r[field] for r in corrected})]
    scores = []
    for label, rr in groups:
        arms = ['combined', 'batting_anchor', 'simple_history'] + [a for a in ('steamer', 'zips') if all(r[a] is not None for r in rr)]
        scores.append(dict(scope=label, scores={a: score(rr, a) for a in arms}))
    intervals = [dict(scope=label, **interval(rr, 'combined', 'steamer')) for label, rr in groups if label in ('public_steamer', 'origin_MLB_public')]
    intervals += [dict(scope='all', **interval(corrected, 'combined', a)) for a in ('simple_history', 'batting_anchor')]
    pl.DataFrame(corrected).write_parquet(output)
    # Unverified similarly named website fields must not leak into later accounting.
    actual = OUT / 'fg-actual-hitter-war.parquet'
    verified = OUT / 'fg-actual-hitter-war-verified.parquet'
    assert not verified.exists()
    pl.read_parquet(actual).select('season', 'player_id', 'name', 'fangraphs_id', 'PA', 'WAR', 'source').write_parquet(verified)
    oldwalk = PUBLIC / 'historical-full-value-player-walks.json.gz'
    walks = json.loads(gzip.decompress(oldwalk.read_bytes()))
    for walk in walks:
        for case in [walk['primary'], *walk['peers']]:
            case['forecast'] = index[case['forecast']['row_id']]
            for key in ('actual_source',):
                data = case['detail'][key]
                if data is not None: case['detail'][key] = {k: v for k, v in data.items() if k in ('season', 'player_id', 'name', 'fangraphs_id', 'PA', 'WAR', 'source')}
            case['detail']['simple_history'] = [{k: v for k, v in h.items() if k in ('season', 'player_id', 'name', 'fangraphs_id', 'PA', 'WAR', 'source')} for h in case['detail']['simple_history']]
    walkpath = PUBLIC / 'historical-full-value-reviewed-player-walks.json.gz'
    assert not walkpath.exists()
    walkpath.write_bytes(gzip.compress(json.dumps(walks, allow_nan=False).encode(), mtime=0))
    write_once(PUBLIC / 'historical-full-value-reviewed-scores.json', dict(
        scores=scores, intervals=intervals, reference_correction=receipt,
        correction='Positive origin MLB PA reference; public PA metadata; verified label-only schema',
        no_refit=True, unchanged_identities_rates_roles_workloads_labels=True,
        source_hashes={str(p): sha256_file(p) for p in (source, actual, oldwalk)},
        output_hashes={str(p): sha256_file(p) for p in (output, verified, walkpath)},
        player_walkthrough_status='initial_review_complete_cohort_review_pending', release_approved=False))
    print(json.dumps(dict(reference=receipt, scores=scores[:5], intervals=intervals), indent=2))


if __name__ == '__main__':
    main()
