"""Resolve completed historical schedules with feed authority for conflicts."""
from pathlib import Path
import polars as pl
from universal_baseball.storage import sha256_file
import capture_hitter_statcast_official_context as original

AMENDMENT=original.ROOT/'docs/hitter-statcast-played-venue-amendment.md'


def metadata(year):
    assert year in range(2015,2023)
    schedule=original.capture(f'schedule-{year}','https://statsapi.mlb.com/api/v1/schedule',
        dict(sportId=1,season=year,gameType='R',hydrate='venue'))
    teams=original.capture(f'teams-{year}','https://statsapi.mlb.com/api/v1/teams',dict(sportId=1,season=year))
    all_games=[g for d in schedule['dates'] for g in d['games']]
    assert all(int(g['season'])==year and g['gameType']=='R' for g in all_games)
    played=[g for g in all_games if g['status']['detailedState'].split(':')[0] in {'Final','Completed Early'}]
    groups={}
    for g in played:
        groups.setdefault(g['gamePk'],[]).append(dict(game_pk=g['gamePk'],schedule_season=year,
            official_date=g['officialDate'],venue_id=g['venue']['id'],venue_name=g['venue']['name']))
    canonical=[]; conflicts=[]
    for pk,rows in sorted(groups.items()):
        signatures={(r['official_date'],r['venue_id'],r['venue_name']) for r in rows}
        if len(signatures)==1:
            canonical.append(rows[0]); continue
        assert len(conflicts)<10,'Unexpected historical metadata expansion'
        feed=original.capture(f'feed-{year}-{pk}',f'https://statsapi.mlb.com/api/v1.1/game/{pk}/feed/live')
        assert feed['gamePk']==pk and feed['gameData']['game']['type']=='R'
        gd=feed['gameData']; date=gd['datetime']['officialDate']; venue=gd['venue']
        assert date.startswith(f'{year}-') and any(r['venue_id']==venue['id'] for r in rows)
        row=dict(game_pk=pk,schedule_season=year,official_date=date,venue_id=venue['id'],venue_name=venue['name'])
        canonical.append(row); conflicts.append(dict(game_pk=pk,schedule_candidates=rows,feed_resolution=row))
    frame=pl.DataFrame(canonical).sort('game_pk')
    assert len(frame)==frame['game_pk'].n_unique() and frame['venue_id'].null_count()==0
    assert len([t for t in teams['teams'] if t.get('league',{}).get('id') in [103,104]])==30
    frame.write_parquet(original.OUT/f'actual-venues-{year}.parquet')
    original.write(original.OUT/f'actual-schedule-review-{year}.json',dict(season=year,
        raw_schedule_entries=len(all_games),completed_entries=len(played),unique_played_games=len(frame),
        excluded_unplayed_entries=len(all_games)-len(played),duplicate_completed_entries=len(played)-len(frame),
        conflicts=conflicts,amendment_sha256=sha256_file(AMENDMENT),runner_sha256=sha256_file(Path(__file__))))


if __name__=='__main__':
    assert not (original.OUT/'capture-report.json').exists(),'Do not restart completed capture'
    original.metadata=metadata
    original.main()
    original.write(original.OUT/'resume-receipt-v3.json',dict(source_only=True,model_fits=0,
        capture_report_sha256=sha256_file(original.OUT/'capture-report.json'),runner_sha256=sha256_file(Path(__file__)),
        amendment_sha256=sha256_file(AMENDMENT)))
