"""Source arithmetic and fixed/small-sample player walks before extension."""
from pathlib import Path
import json
import math
import polars as pl
from universal_baseball.arm_receiving_source import (
    arm_metadata, receiving_metadata, normalize_arm, normalize_receiving)
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save
from source_defensive_positions_v2 import embedded

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/generated/arm-receiving-v6'
PUBLIC = ROOT/'reports/model-evidence/arm-receiving-v6'
FIXED = {'arm': [592450, 605141, 664023, 592206, 595281],
         'receiving': [518692, 621566, 572233, 624413, 656555]}


def main():
    protections()
    assert not (OUT/'pilot-review.json').exists()
    ledger_path = ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet'
    ledger = pl.read_parquet(ledger_path)
    hashes = {str(p): sha256_file(p) for p in [Path(__file__), ledger_path,
        ROOT/'src/universal_baseball/arm_receiving_source.py',
        ROOT/'docs/arm-receiving-v6-source-contract.md',
        ROOT/'docs/arm-receiving-v6-team-scope-amendment.md']}
    annual, walks, missing_fixed, summaries = [], [], [], []
    for kind in ('arm', 'receiving'):
        for year in (2022, 2025):
            path = OUT/f'{"arm-allteams" if kind == "arm" else kind}-{year}.response'
            hashes[str(path)] = sha256_file(path)
            text = path.read_text(encoding='utf8')
            raw = embedded(text, 'data')
            meta = embedded(text, 'serverParams')
            (arm_metadata(meta, year, False) if kind == 'arm' else receiving_metadata(meta, year))
            lut = {pid: rows.to_dicts() for (pid,), rows in
                   ledger.filter(pl.col('season') == year).group_by('player_id')}
            records, raw_by_id = [], {}
            for item in raw:
                pid = int(item['entity_id'] if kind == 'arm' else item['player_id'])
                assert pid not in raw_by_id
                raw_by_id[pid] = item
                records.append((normalize_arm if kind == 'arm' else normalize_receiving)(item, lut.get(pid, []), year))
            annual.extend(records)
            by_id = {r['player_id']: r for r in records}
            selections = {}
            for pid in FIXED[kind]:
                if pid not in by_id:
                    missing_fixed.append(dict(kind=kind, year=year, player_id=pid,
                        reason='No eligible source opportunity; not assigned zero talent.'))
                else:
                    selections.setdefault(pid, []).append('fixed_before_source_review')
            for r in sorted(records, key=lambda r: (r['opportunities'], r['player_id']))[:2]:
                selections.setdefault(r['player_id'], []).append('two_smallest_positive_opportunities')
            for r in records:
                if not r['native_match']:
                    selections.setdefault(r['player_id'], []).append('all_native_numerator_discrepancies')
            original = None
            if kind == 'arm':
                old_path = OUT/f'arm-{year}.response'
                hashes[str(old_path)] = sha256_file(old_path)
                original = {int(r['entity_id']): r for r in embedded(old_path.read_text(encoding='utf8'), 'data')}
                assert set(original) == set(by_id)
            for pid, rule in selections.items():
                focal = by_id[pid]
                peers = sorted((r for r in records if r['player_id'] != pid),
                               key=lambda r: (abs(math.log1p(r['opportunities'])-
                                                    math.log1p(focal['opportunities'])), r['player_id']))[:3]
                def trace(r):
                    i = r['player_id']
                    return dict(measurement=r, raw=raw_by_id[i], native_positions=lut.get(i, []),
                                source_path=str(path), source_sha256=hashes[str(path)],
                                forecast=None, future_quality=None,
                                scope_note='Source validation only; no future prediction or skill grade from small-sample raw rate.',
                                original_team_only_raw=None if original is None else original[i])
                walks.append(dict(kind=kind, year=year, player_id=pid, selection=rule,
                                  primary=trace(focal), peers=[trace(r) for r in peers],
                                  peer_selection='Three closest log opportunity counts; ties by ID, no future outcomes.'))
            bad = [r for r in records if not r['native_match']]
            summaries.append(dict(kind=kind, year=year, rows=len(records),
                opportunities=sum(r['opportunities'] for r in records),
                source_runs=sum(r['runs'] for r in records), native_discrepancies=bad,
                isolated_of_rows=sum(r.get('isolated_outfield_quality_valid', False) for r in records),
                mixed_position_rows=sum(r.get('scope') == 'mixed_position_exposure' for r in records)))
    assert len(annual) == 1193
    assert [(r['season'], r['player_id']) for r in annual if not r['native_match']] == [(2022,608703),(2025,668723)]
    assert all(r['native_match'] for r in annual if r['kind']=='receiving')
    pl.DataFrame(annual, infer_schema_length=None).write_parquet(OUT/'pilot-annual.parquet')
    walk_report = dict(walks=walks, absent_fixed_cases=missing_fixed,
                       focal_cases=len(walks), peer_cases=3*len(walks), player_walkthrough_status='complete',
                       no_model_fit=True, no_2026_outcomes=True, input_hashes=hashes)
    save(OUT/'pilot-player-walkthrough.json', walk_report)
    report = dict(summaries=summaries, player_walkthrough_status='complete',
        rows=len(annual), no_model_fit=True, no_2026_outcomes=True,
        arm_scope_correction='with_team_only=0 leaves pilot numbers unchanged; does not repair two discrepancies.',
        disposition='Receiving arithmetic/native scope passes. Two arm rows quarantined; mixed-position rates not isolated OF talent.',
        historical_extension_allowed=True, deployment_allowed=False, input_hashes=hashes,
        output_hashes={str(p):sha256_file(p) for p in [OUT/'pilot-annual.parquet', OUT/'pilot-player-walkthrough.json']})
    save(OUT/'pilot-review.json', report)
    PUBLIC.mkdir(parents=True,exist_ok=True)
    save(PUBLIC/'pilot-review.json', report)
    save(PUBLIC/'pilot-player-walkthrough.json', walk_report)
    print(json.dumps(dict(rows=len(annual),cases=len(walks),absent=missing_fixed,summaries=summaries),indent=2))


if __name__ == '__main__':
    main()
