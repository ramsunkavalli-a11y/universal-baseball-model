"""Demonstrate official sequence identity repair on ten adjudicated historical games."""
from pathlib import Path
import json
import polars as pl
from universal_baseball.storage import sha256_file
from audit_hitter_detailed_contact_compatibility import ROOT, OUT


def overlay_selected_sequences(source, authority):
    keys = ['game_pk', 'at_bat_index']
    if len(authority.unique(keys)) != len(authority):
        raise ValueError('Official participant authority is ambiguous')
    joined = source.join(authority, on=keys, how='left', validate='m:1')
    if joined['official_batter_id'].null_count():
        raise ValueError('Official participant authority must cover every selected contact')
    return joined.rename({'player_id': 'source_batter_id'}).with_columns(
        pl.col('official_batter_id').alias('player_id'),
        pl.lit('official_selected_game_sequence').alias('participant_authority'))


def main():
    if (OUT / 'repair-pilot.json').exists(): raise FileExistsError('Preserve the first pilot')
    adjudicated = json.loads((OUT / 'official-adjudication.json').read_text(encoding='utf8'))
    assert all(sha256_file(Path(p)) == h for p, h in adjudicated['input_hashes'].items())
    capture_paths = sorted({r['source_capture'] for r in adjudicated['rows']})
    sequences = []
    for path in capture_paths:
        obj = json.loads(Path(path).read_text(encoding='utf8'))
        game = int(Path(path).stem)
        sequences.extend(dict(game_pk=game, at_bat_index=p['about']['atBatIndex'],
                              official_batter_id=p['matchup']['batter']['id'])
                         for p in obj['payload']['allPlays'])
    rawpath = next(Path(p) for p in adjudicated['input_hashes'] if p.endswith('.parquet'))
    raw = pl.read_parquet(rawpath).filter(pl.col('game_pk').is_in([int(Path(p).stem) for p in capture_paths]))
    repaired = overlay_selected_sequences(raw, pl.DataFrame(sequences))
    assert len(raw) == len(repaired)
    physical = [c for c in raw.columns if c != 'player_id']
    assert raw.select(physical).equals(repaired.select(physical))
    assert raw['canonical_outcome'].to_list() == repaired['canonical_outcome'].to_list()
    before = raw.group_by('player_id').agg(pl.len().alias('contacts'),
        (pl.col('canonical_outcome') == 'HR').sum().alias('hr'))
    after = repaired.group_by('player_id').agg(pl.len().alias('contacts'),
        (pl.col('canonical_outcome') == 'HR').sum().alias('hr'))
    changed = repaired.filter(pl.col('player_id') != pl.col('source_batter_id'))
    changes = []
    for pid in sorted(set(changed['player_id']) | set(changed['source_batter_id'])):
        changes.append(dict(player_id=pid, before=before.filter(pl.col('player_id') == pid).to_dicts(),
                            after=after.filter(pl.col('player_id') == pid).to_dicts()))
    repaired.write_parquet(OUT / 'repaired-selected-game-contacts.parquet')
    report = dict(selected_games=len(capture_paths), selected_contacts=len(raw),
        changed_participant_contacts=len(changed), changed_rows=changed.to_dicts(),
        affected_player_totals=changes, physical_fields_unchanged=True,
        raw_event_results_unchanged=True, player_selection_by_future_outcomes=False,
        complete_season_repair=False, forecasts_changed=False, protected_2026_used=False,
        input_hashes={str(Path(p)): sha256_file(Path(p)) for p in
            [rawpath, Path(__file__), OUT / 'official-adjudication.json', *capture_paths]},
        repaired_artifact_sha256=sha256_file(OUT / 'repaired-selected-game-contacts.parquet'))
    (OUT / 'repair-pilot.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf8')
    print(json.dumps({k: v for k, v in report.items() if k not in ['input_hashes', 'changed_rows']}, indent=2))


if __name__ == '__main__':
    main()
