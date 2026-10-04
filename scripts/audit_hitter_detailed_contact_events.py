"""Append raw-event provenance to the preserved contact compatibility inventory."""
from pathlib import Path
import json
import polars as pl
from universal_baseball.storage import sha256_file
from audit_hitter_detailed_contact_compatibility import ROOT, OUT


def main():
    target = OUT / 'event-provenance.json'
    if target.exists():
        raise FileExistsError('Preserve the original supplementary evidence')
    prior = json.loads((OUT / 'report.json').read_text(encoding='utf8'))
    assert all(sha256_file(Path(p)) == h for p, h in prior['input_hashes'].items())
    source = json.loads((ROOT / 'reports/generated/hitter-value-panel-v2/report.json').read_text(encoding='utf8'))
    conflicts = pl.read_parquet(OUT / 'source-conflicts.parquet')
    context_path = ROOT / 'reports/generated/defensive-venue-context-v1/affiliated-game-context.parquet'
    context = pl.read_parquet(context_path).select('season', 'game_pk', 'game_date',
        'home_team_id', 'away_team_id', 'venue_name', 'venue_country', 'sport_id')
    assert context.unique(['season', 'game_pk']).height == len(context)
    hashes = {str(context_path): sha256_file(context_path), str(OUT / 'report.json'): sha256_file(OUT / 'report.json'),
              str(Path(__file__)): sha256_file(Path(__file__))}
    summaries, examples = [], []
    for y in [2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024]:
        specification = next(s for s in source['sources'] if f'full-bip-context-{y}' in s['path'])
        path = Path(specification['path']); hashes[str(path)] = sha256_file(path)
        assert hashes[str(path)] == specification['sha256']
        raw = pl.read_parquet(path)
        assert set(raw['season']) == {y}
        keys = ['season', 'game_pk', 'at_bat_index']
        repeated = raw.group_by(keys).len().filter(pl.col('len') > 1)
        tagged = raw.join(context, on=['season', 'game_pk'], how='left', validate='m:1')
        conflicts_year = conflicts.filter(pl.col('season') == y)
        collided = raw.join(repeated.drop('len'), on=keys, how='semi')
        summaries.append(dict(season=y, raw_events=len(raw),
            exact_duplicate_rows=len(raw) - len(raw.unique()),
            repeated_terminal_keys=len(repeated), events_on_repeated_keys=len(collided),
            hr_on_repeated_keys=len(collided.filter(pl.col('canonical_outcome') == 'HR')),
            source_levels=tagged.group_by('source_level', 'league_id', 'venue_country').agg(
                pl.len().alias('contacts')).sort('contacts', descending=True).to_dicts(),
            conflict_events_by_country=tagged.join(conflicts_year.select('season', 'player_id'),
                on=['season', 'player_id'], how='semi').group_by('venue_country').agg(pl.len()).to_dicts()))
        if y in [2018, 2024]:
            # Origin/source-selected conflicts, not selected by subsequent MLB success.
            candidates = conflicts_year.with_columns(
                (pl.col('reconstructed_contact_hr') - pl.col('official_all_hr')).alias('hr_excess'))
            chosen = pl.concat([candidates.filter(pl.col('official_missing')).sort('player_id').head(2),
                candidates.filter(~pl.col('official_missing')).sort('hr_excess', 'player_id',
                    descending=[True, False]).head(3)]).unique(['season', 'player_id'])
            partitions = sorted((ROOT / f'data/working/pbp-opportunity-foundation-v1/season={y}').glob('level=*/terminal/*.parquet'))
            cols = ['season', 'game_pk', 'at_bat_index', 'level', 'league_id', 'batter', 'terminal_outcome_group']
            foundation = pl.concat([pl.read_parquet(p, columns=cols) for p in partitions], how='diagonal_relaxed').unique()
            for p in partitions: hashes[str(p)] = sha256_file(p)
            for row in chosen.to_dicts():
                events = tagged.filter(pl.col('player_id') == row['player_id']).sort('game_pk', 'at_bat_index')
                sample = events.filter(pl.col('canonical_outcome') == 'HR').head(4)
                if sample.is_empty(): sample = events.head(4)
                identities = sample.join(foundation, on=keys, how='left', validate='m:m')
                examples.append(dict(count_conflict=row,
                    raw_source_profile=events.group_by('source_level', 'league_id', 'venue_country').agg(pl.len()).to_dicts(),
                    sample_raw_to_rebuilt_terminal=identities.to_dicts(),
                    sample_limit='Direct stored source join, not complete game adjudication or verification that official totals are correct'))
    result = dict(seasons=summaries, source_examples=examples, input_hashes=hashes,
                  forecasts_changed=False, new_models_fitted=False, protected_2026_used=False,
                  interpretation='Count conflicts and league provenance require source-specific treatment, not blanket zero imputation')
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False, default=str) + '\n', encoding='utf8')
    print(json.dumps([dict(season=s['season'], repeated_terminal_keys=s['repeated_terminal_keys'],
                           exact_duplicate_rows=s['exact_duplicate_rows'],
                           conflict_events_by_country=s['conflict_events_by_country']) for s in summaries], indent=2))
    for e in examples:
        print('Example', e['count_conflict'], e['raw_source_profile'])


if __name__ == '__main__':
    main()
