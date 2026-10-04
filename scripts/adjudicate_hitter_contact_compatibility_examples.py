"""Check fixed stored contact conflicts against official matchup authority."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import json
import requests
import polars as pl
from universal_baseball.storage import sha256_file
from audit_hitter_detailed_contact_compatibility import ROOT, OUT


def main():
    dest = OUT / 'official-adjudication.json'
    if dest.exists(): raise FileExistsError('Preserve the first official adjudication')
    report = json.loads((ROOT / 'reports/generated/hitter-value-panel-v2/report.json').read_text())
    path = Path(next(s['path'] for s in report['sources'] if 'full-bip-context-2024' in s['path']))
    raw = pl.read_parquet(path).filter(pl.col('player_id').is_in([647228, 543482, 665888]) &
                                     (pl.col('canonical_outcome') == 'HR'))
    games = sorted(raw['game_pk'].unique().to_list())
    captures = OUT / 'official-captures'; captures.mkdir(exist_ok=True)

    def fetch(game):
        captured = captures / f'{game}.json'
        if not captured.exists():
            url = f'https://statsapi.mlb.com/api/v1/game/{game}/playByPlay'
            response = requests.get(url, timeout=30, headers={'User-Agent': 'UBM-contact-source-review/1.0'})
            response.raise_for_status()
            value = dict(url=url, captured_at=datetime.now(timezone.utc).isoformat(), payload=response.json())
            captured.write_text(json.dumps(value, ensure_ascii=False) + '\n', encoding='utf8')
        value = json.loads(captured.read_text(encoding='utf8'))
        assert value['url'] == f'https://statsapi.mlb.com/api/v1/game/{game}/playByPlay'
        plays = value['payload']['allPlays']
        assert len({p['about']['atBatIndex'] for p in plays}) == len(plays)
        return game, (captured, {p['about']['atBatIndex']: p for p in plays})

    with ThreadPoolExecutor(max_workers=4) as executor:
        official = dict(executor.map(fetch, games))
    rows = []
    for r in raw.to_dicts():
        captured, plays = official[r['game_pk']]
        play = plays.get(r['at_bat_index'])
        if play is None: raise ValueError('Missing official matchup sequence')
        batter = play['matchup']['batter']
        rows.append(dict(source=r, official_batter=batter, official_result=play['result'],
            participant_mismatch=(batter['id'] != r['player_id']),
            authority='current official top-level matchup, not a name-string correction',
            source_capture=str(captured), source_sha256=sha256_file(captured)))
    result = dict(selected_players=[647228, 543482, 665888], source_hr_events=len(rows),
        official_games=len(games), participant_mismatches=sum(r['participant_mismatch'] for r in rows),
        rows=rows, input_hashes={str(path): sha256_file(path), str(Path(__file__)): sha256_file(Path(__file__))},
        source_review_only=True, forecasts_changed=False, new_models_fitted=False,
        protected_2026_used=False,
        vintage_limit='Official captures are acquired now, not certified original game-day vintages; only adjudicate historical participant attribution')
    dest.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8')
    print(json.dumps({k: v for k, v in result.items() if k not in ['rows', 'input_hashes']}, indent=2))
    for r in rows:
        if r['participant_mismatch']:
            print(r['source']['game_pk'], r['source']['at_bat_index'],
                  r['source']['player_id'], '->', r['official_batter'], r['official_result'])


if __name__ == '__main__':
    main()
