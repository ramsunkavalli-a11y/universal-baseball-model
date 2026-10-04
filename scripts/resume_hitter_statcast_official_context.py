"""Reuse captured metadata with the existing canonical schedule reducer."""
from pathlib import Path
from universal_baseball.mlb_contact_history import schedule_venues
from universal_baseball.storage import sha256_file
import capture_hitter_statcast_official_context as original


def metadata(year):
    assert year in range(2015,2023)
    schedule=original.capture(f'schedule-{year}','https://statsapi.mlb.com/api/v1/schedule',
        dict(sportId=1,season=year,gameType='R',hydrate='venue'))
    teams=original.capture(f'teams-{year}','https://statsapi.mlb.com/api/v1/teams',dict(sportId=1,season=year))
    games=[g for day in schedule['dates'] for g in day['games']]
    assert all(int(g['season'])==year and g['gameType']=='R' for g in games)
    canonical=schedule_venues(schedule,year)
    assert len(canonical)==len({g['gamePk'] for g in games})
    assert canonical['venue_id'].null_count()==0
    assert len([t for t in teams['teams'] if t.get('league',{}).get('id') in [103,104]])==30
    original.write(original.OUT/f'schedule-review-{year}.json',dict(season=year,raw_schedule_entries=len(games),
        unique_games=len(canonical),duplicate_schedule_entries=len(games)-len(canonical),
        conflicting_dates_or_venues=False,canonical_reducer_sha256=sha256_file(Path(schedule_venues.__code__.co_filename)),
        resume_runner_sha256=sha256_file(Path(__file__))))


if __name__=='__main__':
    assert not (original.OUT/'capture-report.json').exists(),'Do not restart completed capture'
    original.metadata=metadata
    original.main()
    original.write(original.OUT/'resume-receipt.json',dict(source_only=True,model_fits=0,
        capture_report_sha256=sha256_file(original.OUT/'capture-report.json'),resume_runner_sha256=sha256_file(Path(__file__)),
        correction='Repeated schedule listings with identical game/date/venue collapse through the existing reducer; conflicts still fail.'))
