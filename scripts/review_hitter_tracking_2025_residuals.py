"""Localize every preserved 2025 contact residual using official game plays."""
import polars as pl
from universal_baseball.hitter_statcast_measurement import interference_award
import audit_hitter_tracking_2025 as audit

OUT = audit.OUT


def main():
    assert not (OUT/'residual-play-review.json').exists(), 'Preserve review'
    initial = audit.read(OUT/'initial-audit.json')
    raw = pl.concat([pl.read_parquet(audit.source.OUT/f'2025-{m:02}.parquet') for m in range(3, 11)])
    normal = raw.filter((pl.col('type') == 'X') & pl.col('events').fill_null('').str.strip_chars().ne('') & ~interference_award())
    schedule = audit.read(OUT/'captures/schedule-2025.json')
    known_games = {g['gamePk'] for d in schedule['dates'] for g in d['games']}
    cases = []
    for case in initial['residuals']:
        pid = case['player_id']
        data = audit.capture(f'gamelog-2025-{pid}', f'https://statsapi.mlb.com/api/v1/people/{pid}/stats',
            dict(stats='gameLog', group='hitting', season=2025, sportId=1, gameType='R'))
        records = []
        for group in data['stats']:
            for s in group.get('splits', []):
                assert str(s['date']).startswith('2025-')
                st = s['stat']
                records.append(dict(game_pk=s['game']['gamePk'],
                    official_contacts=st.get('atBats', 0)-st.get('strikeOuts', 0)+st.get('sacFlies', 0)+st.get('sacBunts', 0),
                    AB=st.get('atBats', 0), K=st.get('strikeOuts', 0), SF=st.get('sacFlies', 0), SH=st.get('sacBunts', 0),
                    PA=st.get('plateAppearances', 0), hits=st.get('hits', 0)))
        official = pl.DataFrame(records).group_by('game_pk').agg(pl.exclude('game_pk').sum())
        source = normal.filter(pl.col('batter') == str(pid)).group_by(pl.col('game_pk').cast(pl.Int64)).len(name='source_contacts')
        joined = official.join(source, on='game_pk', how='full', coalesce=True).fill_null(0).with_columns(
            (pl.col('source_contacts')-pl.col('official_contacts')).alias('residual'))
        assert joined['official_contacts'].sum() == case['official_contacts'], 'Season revision, do not assume source unchanged'
        errors = joined.filter(pl.col('residual') != 0); games = []
        assert len(errors) <= 5, 'Bounded diagnosis expanded unexpectedly'
        for game in errors.to_dicts():
            pk = game['game_pk']; assert pk in known_games
            feed = audit.capture(f'feed-2025-{pk}', f'https://statsapi.mlb.com/api/v1.1/game/{pk}/feed/live', {})
            assert feed['gamePk'] == pk and feed['gameData']['datetime']['officialDate'].startswith('2025-')
            plays = []
            for play in feed['liveData']['plays']['allPlays']:
                if play['matchup']['batter']['id'] != pid:
                    continue
                num = play['atBatIndex']+1
                source_play = raw.filter((pl.col('game_pk') == str(pk)) & (pl.col('batter') == str(pid)) & (pl.col('at_bat_number') == str(num)))
                plays.append(dict(at_bat_number=num, result=play['result'], about=play['about'],
                    inplay_pitch_events=[p for p in play['playEvents'] if p.get('details', {}).get('isInPlay')],
                    source=source_play.select('type', 'events', 'des', 'launch_speed', 'launch_angle').to_dicts()))
            games.append(dict(comparison=game, official_player_plays=plays))
        cases.append(dict(season=2025, player_id=pid, player_name=case['player_name'],
            season_residual=case['contact_residual'], gamelog_matches_saved_season=True, games=games))
    audit.write(OUT/'residual-play-review.json', dict(cases=cases, model_fits=0, protected_outcomes_used=False))
    print(f'Localized {len(cases)} residual players with actual dated game feeds', flush=True)


if __name__ == '__main__':
    main()
