"""Independent channel arithmetic and scoped source corrections; no new fits."""

from collections import defaultdict
from pathlib import Path
import json
import math

import polars as pl

from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/generated/defense-value-v11'
PUBLIC = ROOT / 'reports/model-evidence/defense-value-v11'
SOURCE = ROOT / 'reports/generated/defense-position-opportunity-v7/source.parquet'
BRIDGE = ROOT / 'reports/generated/defense-transition-v10/predictions.parquet'
PATHS = {
    'range': ROOT / 'reports/generated/defense-native-range-v3/component-ledger.parquet',
    'framing': ROOT / 'reports/generated/catcher-native-opportunity-v3/modern/framing-annual.parquet',
    'catcher': ROOT / 'reports/generated/catcher-throw-block-v5/extension-annual.parquet',
    'other': ROOT / 'reports/generated/arm-receiving-v6/official-scope/annual.parquet',
    'cal': ROOT / 'reports/generated/defense-native-range-v3/predictions.parquet',
}


def read(p):
    return json.loads(p.read_text(encoding='utf8'))


def same(a, b):
    return (a is None and b is None) or (
        a is not None and b is not None and math.isclose(a, b, rel_tol=0, abs_tol=1e-8))


def weighted_history(channel, records, origin):
    """Deliberately reconstruct formulas without calling production history helpers."""
    past = []
    for r in records:
        if not origin - 2 <= r['season'] <= origin:
            continue
        if channel.startswith('range_'):
            valid = r['position'] == int(channel[-1]) and r['range_valid']
            n, v, prior, unit = r['native_outs'], r['range_runs'], 3000., 1500.
        elif channel == 'framing':
            valid = r['framing_measurement_valid'] and r['pitches'] > 0
            n, v, prior, unit = r['pitches'], r['framing_runs'], 6000., 1000.
        elif channel in ('throwing', 'blocking'):
            valid = r['component'] == channel and r['measurement_valid']
            n, v = r['opportunities'], r['runs']
            prior, unit = (100., 100.) if channel == 'throwing' else (3000., 1000.)
        else:
            key = 'isolated_outfield_quality_valid' if channel == 'arm' else 'quality_valid'
            valid = r['kind'] == channel and r[key]
            n, v, prior, unit = r['opportunities'], r['runs'], 300. if channel == 'arm' else 600., 100.
        if valid:
            assert n >= 0 and v is not None
            weight = 2. ** (r['season'] - origin)
            past.append(dict(source=r, weight=weight, weighted_runs=weight*v,
                             weighted_opportunities=weight*n))
    # Empty histories need the channel's defined constants too.
    prior, unit = ((3000., 1500.) if channel.startswith('range_') else
                   (6000., 1000.) if channel == 'framing' else
                   (100., 100.) if channel == 'throwing' else
                   (3000., 1000.) if channel == 'blocking' else
                   (300., 100.) if channel == 'arm' else (600., 100.))
    n = sum(p['weighted_opportunities'] for p in past)
    runs = sum(p['weighted_runs'] for p in past)
    return dict(opportunities=n, runs=runs, prior=prior, unit=unit,
                rate=unit*runs/(n+prior), reliability=n/(n+prior),
                measured=n > 0, eligible_sources=past)


def main():
    protections()
    assert not (OUT/'independent-source-verification.json').exists()
    initial = read(OUT/'source-review.json')
    for p, h in {**initial['hashes'], **initial['output_hashes']}.items():
        assert sha256_file(Path(p)) == h, p
    frames = {k: pl.read_parquet(p) for k, p in PATHS.items()}
    raw = {k: v.to_dicts() for k, v in frames.items()}
    histories = {k: defaultdict(list) for k in ('range', 'framing', 'catcher', 'other')}
    for k in histories:
        for r in raw[k]: histories[k][r['player_id']].append(r)
    native = {(r['season'], r['player_id'], r['position']): r for r in raw['range']}
    framing = {(r['season'], r['player_id']): r for r in raw['framing']}
    catcher = {(r['season'], r['player_id'], r['component']): r for r in raw['catcher']}
    other = {(r['season'], r['player_id'], r['kind']): r for r in raw['other']}
    cal = {(r['origin_year'], r['player_id'], r['position']): r for r in raw['cal']}
    q = pl.read_parquet(BRIDGE)
    forecasts = {r['row_id']: r for r in q.to_dicts()}
    source = pl.read_parquet(SOURCE).filter(pl.col('is_mlb'))
    official = defaultdict(int)
    for r in source.iter_rows(named=True):
        official[r['season'], r['player_id'], int(r['position_code'])] += r['fielding_outs']
    for r in forecasts.values():
        for pos in range(2, 10):
            assert r[f'actual_{pos}'] == official[r['target_year'], r['player_id'], pos]
    ledger = pl.read_parquet(OUT/'component-ledger.parquet')
    checked, fixes, conflicts = [], [], []
    h_cache = {}
    max_valid_out_gap = 0
    for r in ledger.iter_rows(named=True):
        c, pid, y, t = r['channel'], r['player_id'], r['origin_year'], r['target_year']
        qrow = forecasts[r['row_id']]
        group = 'range' if c.startswith('range_') else 'framing' if c == 'framing' else 'catcher' if c in ('throwing', 'blocking') else 'other'
        hk = (pid, y, c)
        if hk not in h_cache: h_cache[hk] = weighted_history(c, histories[group][pid], y)
        h = h_cache[hk]
        assert same(r['history_rate'], h['rate']) and same(r['history_opportunities'], h['opportunities'])
        assert same(r['reliability'], h['reliability']) and same(r['rate_unit'], h['unit'])
        assert bool(r['quality_evidence_observed']) == h['measured']
        run, den, valid, record = None, None, False, None
        if c.startswith('range_'):
            pos = int(c[-1]); exposure = official[t, pid, pos]
            record = native.get((t, pid, pos))
            valid = bool(record and record['range_valid'])
            if valid:
                run, den = record['range_runs'], record['native_outs']
                gap = abs(den-exposure); max_valid_out_gap = max(max_valid_out_gap, gap)
                assert gap <= 5 and gap <= .01*max(den, exposure)
            saved = cal.get((y, pid, pos))
            if saved:
                assert same(saved['history_rate'], h['rate'])
                assert same(saved['calibrated'], r['saved_range_calibration'])
                assert saved['fold'] == pid % 5
                assert saved['fit_allowed'] == r['range_calibration_fit_allowed']
                assert saved['profile_people'] == r['range_calibration_profile_people']
        elif c == 'framing':
            exposure = official[t, pid, 2]; record = framing.get((t, pid))
            valid = bool(record and record['exposure_valid'] and record['framing_measurement_valid'])
            if valid: run, den = record['framing_runs'], record['pitches']
        elif c in ('throwing', 'blocking'):
            exposure = official[t, pid, 2]; record = catcher.get((t, pid, c))
            valid = bool(record and record['exposure_valid'] and record['measurement_valid'])
            if valid: run, den = record['runs'], record['opportunities']
        elif c == 'receiving':
            exposure = official[t, pid, 3]; record = other.get((t, pid, c))
            valid = bool(record and record['quality_valid'])
            if valid: run, den = record['runs'], record['opportunities']
        else:
            exposure = sum(official[t, pid, p] for p in (7, 8, 9))
            ns = [native.get((t, pid, p)) for p in (7, 8, 9) if official[t, pid, p] > 0]
            valid = bool(ns) and all(n and n['exposure_valid'] and n['arm_runs'] is not None for n in ns)
            if valid: run = sum(n['arm_runs'] for n in ns)
            record = other.get((t, pid, c))
            if record and record['isolated_outfield_quality_valid']: den = record['opportunities']
        assert r['actual_official_exposure'] == exposure
        # Verify the original ledger before applying the declared correction.
        original_run = 0. if exposure == 0 else run if valid else None
        assert same(original_run, r['actual_runs']) and same(den, r['actual_native_opportunities'])
        if exposure == 0 and record:
            positive = record.get('native_outs', record.get('native_catcher_outs', record.get('of_outs', 0)))
            if positive and valid: conflicts.append(dict(row_id=r['row_id'], channel=c, source=record))
        result = dict(r, measurement_basis='zero_official_opportunity' if exposure == 0 else 'position_native_records' if valid else 'unmeasured')
        recover = (c == 'arm' and exposure > 0 and not valid and record and
                   record['isolated_outfield_quality_valid'] and record['adjustment_measured'] and
                   record['native_match'] and record['other_outs'] == 0 and record['of_outs'] == exposure)
        if recover:
            assert all(official[t, pid, p] == 0 for p in (2, 3, 4, 5, 6))
            assert record['runs'] is not None and record['non_outfield_arm_runs'] == 0
            result.update(actual_runs=record['runs'], target_status='measured_delivered_runs',
                          measurement_basis='reconciled_official_OF_only_aggregate')
            fixes.append(dict(row_id=r['row_id'], player_id=pid, player_name=r['player_name'],
                              target_year=t, old_runs=None, new_runs=record['runs'], source=record))
        checked.append(result)
    assert not conflicts, conflicts
    reviewed = pl.DataFrame(checked, infer_schema_length=None)
    reviewed.write_parquet(OUT/'reviewed-component-ledger.parquet')
    complete = reviewed.group_by('row_id', 'origin_year').agg(
        pl.col('actual_runs').null_count().alias('unknown_channels'),
        pl.col('actual_runs').sum().alias('observed_partial_native_runs')).with_columns(
            pl.when(pl.col('unknown_channels') == 0).then(pl.col('observed_partial_native_runs'))
            .otherwise(None).alias('complete_defined_native_runs'))
    complete.write_parquet(OUT/'reviewed-player-ledger.parquet')
    actual_outs = q.select('row_id', pl.sum_horizontal([f'actual_{p}' for p in range(2, 10)]).alias('actual_outs'))
    population = complete.join(actual_outs, on='row_id', validate='1:1')
    participant_coverage = population.filter(pl.col('actual_outs') > 0).group_by('origin_year').agg(
        pl.len().alias('actual_defenders'), (pl.col('unknown_channels') == 0).sum().alias('complete_defined_channels'),
        (pl.col('unknown_channels') > 0).sum().alias('partial_defined_channels'), pl.col('actual_outs').sum()).sort('origin_year').to_dicts()
    # Preserve the mistakenly selected Trout case and add the actual intended Kiermaier.
    selections = [{k: r[k] for k in ('focal_player_id', 'origin', 'player_id', 'player_name', 'row_id', 'is_focal')}
                  for r in read(OUT/'source-player-cases.json')['records']]
    krow = q.filter((pl.col('player_id') == 595281) & (pl.col('origin_year') == 2022)).row(0, named=True)
    assert 'Kiermaier' in krow['player_name']
    peers = q.filter((pl.col('origin_year') == 2022) & (pl.col('stage') == krow['stage']) &
                     (pl.col('repertoire_primary_role') == krow['repertoire_primary_role']) & (pl.col('player_id') != 595281)).to_dicts()
    peers = sorted(peers, key=lambda p: (abs((p['age'] or 27)-(krow['age'] or 27)),
                   abs(p['role_defensive_sample']-krow['role_defensive_sample']), p['row_id']))[:3]
    for r in [krow, *peers]:
        selections.append(dict(focal_player_id=595281, origin=2022, player_id=r['player_id'],
            player_name=r['player_name'], row_id=r['row_id'], is_focal=r['player_id'] == 595281))
    cases = []
    for s in selections:
        r = forecasts[s['row_id']]; pid, y = r['player_id'], r['origin_year']
        channels = reviewed.filter(pl.col('row_id') == s['row_id']).to_dicts()
        histories_detail = {c['channel']: h_cache[pid, y, c['channel']] for c in channels}
        cases.append(dict(**s, age=r['age'], stage=r['stage'], expected_PA=r['preseason_pa'], actual_PA=r['next_pa'],
            past_source_rows={k: [a for a in histories[k][pid] if y-2 <= a['season'] <= y] for k in histories},
            future_source_rows={k: [a for a in histories[k][pid] if a['season'] == y+1] for k in histories},
            history_calculations=histories_detail, channel_ledger=channels,
            actual_position_outs={p: r[f'actual_{p}'] for p in range(2, 10)},
            forecast_position_outs={a: {p: r[f'{a}_{p}'] for p in range(2, 10)} for a in ('ratio', 'repair', 'transition')},
            projected_channel_opportunities={c: r[f'transition_native_{c}'] for c in ('framing', 'throwing', 'blocking', 'arm', 'receiving')},
            complete_defined_native_runs=complete.filter(pl.col('row_id') == s['row_id'])['complete_defined_native_runs'][0]))
    for dest in (OUT, PUBLIC):
        save(dest/'reviewed-source-player-cases.json', dict(records=cases, fixed_focal_cases=9, preserved_original_case_records=32,
             selection='All original cases retained; corrected Kiermaier ID with same origin-only peer rule, no outcome replacement.'))
    report = dict(status='independently_verified_readable_review_pending', fits=0, original_channel_rows_replayed=ledger.height,
        quality_histories_replayed=len(h_cache), official_label_cells_replayed=q.height*8,
        valid_range_max_current_official_gap=max_valid_out_gap, positive_native_zero_official_conflicts=conflicts,
        recovered_OF_only_totals=fixes, participant_coverage=participant_coverage,
        preserved_initial_ledger=True, unknown_targets_remain_null=True, zero_opportunity_not_skill=True,
        player_walkthrough_status='pending', model_accuracy_claim=False, protected_outcomes_used=False,
        hashes={str(p): sha256_file(p) for p in [Path(__file__), OUT/'source-review.json', SOURCE, BRIDGE,
            ROOT/'docs/defense-value-v11-source-amendment.md', *PATHS.values()]},
        output_hashes={str(OUT/n): sha256_file(OUT/n) for n in ('reviewed-component-ledger.parquet',
            'reviewed-player-ledger.parquet', 'reviewed-source-player-cases.json')})
    for dest in (OUT, PUBLIC): save(dest/'independent-source-verification.json', report)
    protections()
    print(json.dumps(dict(replayed=ledger.height, recovered=len(fixes), participant_coverage=participant_coverage)))


if __name__ == '__main__':
    main()
