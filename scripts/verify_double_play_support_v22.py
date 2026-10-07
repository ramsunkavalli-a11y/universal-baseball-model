"""Independently replay saved double-play sources, quality windows and support."""
from collections import Counter, defaultdict
from pathlib import Path
import gzip
import json
import math
import re

import polars as pl
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'reports/model-evidence/defense-double-play-source-v22'


def read(path):
    with gzip.open(path, 'rt', encoding='utf8') as stream:
        return json.load(stream)


def write(path, value):
    assert not path.exists(), path
    with gzip.open(path, 'wt', encoding='utf8') as stream:
        json.dump(value, stream, allow_nan=False, separators=(',', ':'))


def extract(text, name):
    match = re.search(r'\b(?:const|var|let)\s+' + name + r'\s*=\s*', text)
    assert match, name
    return json.JSONDecoder().raw_decode(text[match.end():])[0]


def key(row):
    return row['population'], row['origin_year'], row['player_id'], row['position']


def replay():
    pre = read(PUBLIC / 'preflight.json.gz')
    report = read(PUBLIC / 'source-support.json.gz')
    for record in (pre, report):
        for path, digest in record['hashes'].items():
            assert sha256_file(Path(path)) == digest, path
    ledger_path = ROOT / 'reports/generated/defense-native-range-v3/component-ledger.parquet'
    official_path = ROOT / 'reports/generated/defense-position-opportunity-v7/source.parquet'
    ledger = pl.read_parquet(ledger_path).to_dicts()
    native = {(r['season'], r['player_id'], r['position']): r for r in ledger}
    assert len(native) == len(ledger)
    official = defaultdict(int)
    for r in pl.read_parquet(official_path).to_dicts():
        if r['is_mlb'] and 2016 <= r['season'] <= 2025 and r['position_code'].isdigit():
            official[r['season'], r['player_id'], int(r['position_code'])] += r['fielding_outs']
    components = ('range_runs', 'arm_runs', 'dp_runs', 'fielding_runs_prevented_on_rec1b',
                  'framing_runs', 'throwing_runs', 'blocking_runs')
    raw_by = {}
    summaries = []
    fields = []
    totals = []
    for year in range(2016, 2026):
        path = ROOT / f'reports/generated/defensive-talent-position-v2/position-{year}.response'
        text = path.read_text(encoding='utf8')
        params = extract(text, 'serverParams')
        assert int(params['seasonStart']) == int(params['seasonEnd']) == year
        raw = extract(text, 'data')
        assert len(raw) == len({(r['id'], r['pos_id']) for r in raw})
        for r in raw:
            assert math.isclose(sum(r[c] or 0 for c in components), r['total_runs'], abs_tol=1e-9)
            raw_by[year, r['id'], r['pos_id']] = r
            if 2 <= r['pos_id'] <= 9:
                saved = native[year, r['id'], r['pos_id']]
                for c in (*components, 'total_runs'):
                    assert saved[c] == r[c], (year, r['id'], c)
                n = int(r['outs_total'])
                o = official.get((year, r['id'], r['pos_id']), 0)
                certified = n > 0 and o > 0 and abs(n-o) <= 5 and abs(n-o) <= .01 * max(n, o)
                assert saved['native_outs'] == n and saved['official_outs'] == o
                assert bool(saved['exposure_valid']) == certified
        inf = [r for r in ledger if r['season'] == year and r['position'] in (3, 4, 5, 6)]
        summaries.append(dict(season=year, infield_rows=len(inf),
            known_credit=sum(r['dp_runs'] is not None for r in inf),
            qualified_credit=sum(r['dp_runs'] is not None and r['exposure_valid'] for r in inf),
            positive=sum(r['dp_runs'] is not None and r['dp_runs'] > 0 for r in inf),
            negative=sum(r['dp_runs'] is not None and r['dp_runs'] < 0 for r in inf),
            native_credit_total=sum(r['dp_runs'] or 0 for r in inf)))
        fields.append(dict(season=year, fields=sorted({k for r in raw for k in r
            if any(s in k.lower() for s in ('opportun', 'chance', 'pivot', 'initial', 'double', 'dp_'))})))
        total = sum(r['dp_runs'] or 0 for r in raw)
        assert math.isclose(total, summaries[-1]['native_credit_total'], abs_tol=1e-9)
        totals.append(dict(season=year, all_raw_DP_runs=total, forced_centering=False))
    assert summaries == report['years'] and fields == report['opportunity_fields']
    origins = []
    for population, source in (('MLB_history', 'defense-native-range-v3'), ('minor_prospect', 'defense-minor-counts-v18')):
        rows = pl.read_parquet(ROOT / f'reports/generated/{source}/origins.parquet').to_dicts()
        for r in rows:
            if r['origin_year'] > 2022 or r['position'] not in (3, 4, 5, 6):
                continue
            if population == 'minor_prospect' and r['prior_current_MLB_fielding']:
                continue
            if population == 'MLB_history':
                r['level'] = 'MLB'
            else:
                assert r['minor_outs'] >= 25
            origins.append(dict(r, population=population))
    labels = read(PUBLIC / 'labels.json.gz')
    saved = {key(r): r for r in labels}
    assert len(saved) == len(labels) == len(origins)
    for origin in origins:
        r = saved[key(origin)]
        assert all(r[k] == v for k, v in origin.items())
        outs = 0; runs = 0.; missing = 0; seasons = 0; official_outs = 0
        for index, year in enumerate(range(origin['origin_year']+1, origin['origin_year']+4)):
            n = native.get((year, origin['player_id'], origin['position']))
            o = official.get((year, origin['player_id'], origin['position']), 0)
            valid = n is not None and bool(n['exposure_valid']) and n['dp_runs'] is not None
            assert r['annual'][index] == dict(season=year, native=n, official_outs=o,
                measurement_valid=valid, unknown_source_year=not 2016 <= year <= 2025)
            official_outs += o
            if valid:
                outs += n['native_outs']; runs += n['dp_runs']; seasons += int(n['native_outs'] > 0)
            elif o > 0:
                missing += o
        end = origin['origin_year']+3
        mature = end <= 2025
        complete = origin['origin_year']+1 >= 2016 and end <= 2025
        q = 1500*runs/outs if mature and complete and outs >= 1500 and seasons >= 2 and not missing else None
        status = ('measured' if q is not None else 'immature_window' if not mature else
            'outside_native_history' if not complete else 'positive_exposure_missing_DP_measurement' if missing else
            'no_same_position_MLB_exposure' if not official_outs else 'insufficient_measured_sample')
        assert r['quality_rate'] == q and r['quality_status'] == status
        assert r['future_outs'] == outs and r['future_runs'] == runs and r['missing_official_outs'] == missing
    groups = []; folds = []
    for population in ('MLB_history', 'minor_prospect'):
        assert sum(r['population'] == population for r in origins) == report['MLB_origins' if population == 'MLB_history' else 'minor_origins']
        for year in (2021, 2022):
            current = [r for r in labels if r['population'] == population and r['origin_year'] == year]
            for level, position in sorted({(r['level'], r['position']) for r in current}):
                subset = [r for r in current if r['level'] == level and r['position'] == position]
                groups.append(dict(population=population, origin=year, level=level, position=position,
                    eligible=len(subset), measured_people=len({r['player_id'] for r in subset if r['quality_rate'] is not None}),
                    status_counts=dict(Counter(r['quality_status'] for r in subset))))
            for fold in range(5):
                train = [r for r in labels if r['population'] == population and r['window_end'] <= year
                    and r['quality_rate'] is not None and r['player_id'] % 5 != fold]
                test = [r for r in current if r['player_id'] % 5 == fold]
                assert {r['player_id'] for r in train}.isdisjoint(r['player_id'] for r in test)
                folds.append(dict(population=population, origin=year, held_fold=fold,
                    training_people=len({r['player_id'] for r in train}),
                    training_origins=sorted({r['origin_year'] for r in train}),
                    test_people=len({r['player_id'] for r in test}),
                    measured_test_people=len({r['player_id'] for r in test if r['quality_rate'] is not None}),
                    position_level_training_people=[dict(position=p, level=l, people=len({r['player_id'] for r in train
                        if r['position'] == p and r['level'] == l})) for p, l in sorted({(r['position'], r['level']) for r in train})]))
    assert groups == report['groups'] and folds == report['folds']
    assert report['source_rows_replayed'] == len(ledger) and report['model_fits'] == 0 and not report['accuracy_claim']
    return dict(status='pass', native_rows=len(ledger), origin_positions=len(origins), groups=len(groups), folds=len(folds),
        current_official_exposure_independently_replayed=True, raw_component_additivity_replayed=True,
        all_labels_and_unknown_reasons_replayed=True, no_opportunity_or_role_fields=all(f['fields'] == ['dp_runs'] for f in fields),
        annual_credit_totals=totals, source_era_break_2020_requires_scope_limit=True, no_2026_outcomes=True,
        source_audit_not_predictive_validation=True, model_fits=0,
        hashes={str(p): sha256_file(p) for p in (Path(__file__), PUBLIC/'preflight.json.gz', PUBLIC/'labels.json.gz', PUBLIC/'source-support.json.gz')})


if __name__ == '__main__':
    result = replay()
    write(PUBLIC/'independent-review.json.gz', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'hashes'}, indent=2), flush=True)
