"""Small, repeatable source reconciliation; never copies archives or fits a model."""
from collections import Counter
import csv
from pathlib import Path
import json

import polars as pl

from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
LOCAL = Path('C:/Users/ramav/Documents/Baseball/2026 Data')
OLD = Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated')
OUT = ROOT / 'reports/model-evidence/hitter-2027-v1/source-inventory.json'


def csv_source(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        columns = reader.fieldnames
    ids = Counter(r.get('MLBAMID', r.get('mlbid', '')) for r in rows)
    meta = dict(path=str(path), sha256=sha256_file(path), bytes=path.stat().st_size,
                rows=len(rows), columns=columns, missing_id_rows=ids.get('', 0),
                repeated_ids=sum(n > 1 for key, n in ids.items() if key),
                pa=sum(float(r['PA']) for r in rows) if 'PA' in columns else None)
    if 'Level' in columns:
        meta['level_labels'] = dict(sorted(Counter(r['Level'] for r in rows).items()))
        meta['combined_level_rows'] = sum(',' in r['Level'] for r in rows)
        meta['usable_for_level_specific_translation'] = False
    return meta, rows


def main():
    sources, exports = [], {}
    for path in sorted(LOCAL.glob('*.csv')):
        if path.name.startswith(('BP_Batting_', 'FanGraphs_MiLB_Batting_', 'FanGraphs_MLB_Batting_')):
            meta, rows = csv_source(path)
            sources.append(meta)
            exports[path.name] = rows
    fg = exports['FanGraphs_MLB_Batting_Summary_2026-09-28.csv']
    ids = [int(r['MLBAMID']) for r in fg]
    if len(set(ids)) != len(ids):
        raise ValueError('FanGraphs repeated identities require a split policy')
    fg = {int(r['MLBAMID']): r for r in fg}
    official_path = ROOT/'reports/generated/hitter-final-2026-source/actual-player-events-2026.parquet'
    official = pl.read_parquet(official_path).to_dicts()
    official_ids = {r['player_id'] for r in official}
    differences = []
    for r in official:
        f = fg.get(r['player_id'])
        if f is None or int(f['PA']) != r['actual_pa'] or int(f['HR']) != r['HR']:
            differences.append(dict(player_id=r['player_id'], player_name=r['actual_player_name'],
                official_pa=r['actual_pa'], fg_pa=int(f['PA']) if f else None,
                official_hr=r['HR'], fg_hr=int(f['HR']) if f else None))
    absent = [r for r in differences if r['fg_pa'] is None]
    legacy = []
    for relative in [
        'league-control-chronology-safe-release/2026-09-08/league-control-snapshot.parquet',
        'league-control-chronology-safe-release/2026-09-08/contract-year-liabilities.parquet',
        'league-control-chronology-safe-release/2026-09-08/future-control-path.parquet',
        'current-contract-economics-inputs-v2/2026-09-08/annual-contract-economics-inputs.parquet',
        'current-and-future-contract-economics-v2/2026-09-08/annual-contract-economics.parquet',
    ]:
        path = OLD/relative
        frame = pl.read_parquet(path)
        legacy.append(dict(path=str(path), sha256=sha256_file(path), bytes=path.stat().st_size,
                           rows=frame.height, columns=frame.columns,
                           usable_as_current_2027_forecast=False))
    fixed = ['Jackson Lovich', 'Bryce Eldridge', 'Carlos Concepcion', 'Aaron Judge',
             'Fernando Tatis Jr.', 'Shohei Ohtani', 'Patrick Bailey', 'Francisco Lindor']
    cases = []
    minor = exports['FanGraphs_MiLB_Batting_2026-09-28.csv']
    for name in fixed:
        rows = [r for r in [*fg.values(), *minor]
                if r.get('NameASCII') == name or r['Name'] == name]
        cases.append(dict(requested_name=name, matched_export_rows=rows,
                          interpretation='Source evidence only; no new forecast or player override'))
    result = dict(
        status='source_inventory_not_model_release', source_season=2026, forecast_season=2027,
        user_build_date='2026-10-08', sources=sources, legacy_reuse_candidates=legacy,
        official_source=dict(path=str(official_path), sha256=sha256_file(official_path),
                             rows=len(official), pa=sum(r['actual_pa'] for r in official)),
        mlb_reconciliation=dict(fg_players=len(fg), fg_pa=sum(int(r['PA']) for r in fg.values()),
            fg_ids_outside_official=sorted(set(fg)-official_ids),
            official_players_absent_fg=len(absent), absent_fg_pa=sum(r['official_pa'] for r in absent),
            matched_differences=[r for r in differences if r['fg_pa'] is not None],
            absent_nonzero_pa_players=[r for r in absent if r['official_pa'] > 0]),
        fixed_source_cases=cases,
        pending=['level-specific 2026 minor event counts and coverage',
                 '2026 native fielding/running measurements and roster/service refresh',
                 'actual 2027 model assembly and all historical/player release checks'],
        forecasts_changed=False, full_war_or_dollar_value_ready=False)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+'\n'
    if OUT.exists() and OUT.read_text(encoding='utf8') != raw:
        raise ValueError('Source inventory changed; save a new dated version rather than overwrite')
    if not OUT.exists():
        OUT.write_text(raw, encoding='utf8', newline='\n')
    print(json.dumps(result['mlb_reconciliation'], indent=2), flush=True)
    print(f'Saved {OUT}; no model or forecast changed', flush=True)


if __name__ == '__main__':
    main()
