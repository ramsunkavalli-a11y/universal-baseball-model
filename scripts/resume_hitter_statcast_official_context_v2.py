"""Resolve actual played venues from final, not postponed, schedule listings."""
from pathlib import Path
from universal_baseball.mlb_contact_history import schedule_venues
from universal_baseball.storage import sha256_file
import capture_hitter_statcast_official_context as original


def metadata(year):
    assert year in range(2015,2023)
    schedule=original.capture(f'schedule-{year}','https://statsapi.mlb.com/api/v1/schedule',
        dict(sportId=1,season=year,gameType='R',hydrate='venue'))
    teams=original.capture(f'teams-{year}','https://statsapi.mlb.com/api/v1/teams',dict(sportId=1,season=year))
    all_games=[g for d in schedule['dates'] for g in d['games']]
    assert all(int(g['season'])==year and g['gameType']=='R' for g in all_games)
    final={'dates':[dict(games=[g for g in d['games'] if g['status']['abstractGameState']=='Final']) for d in schedule['dates']]}
    canonical=schedule_venues(final,year)
    played=[g for d in final['dates'] for g in d['games']]
    assert len(canonical)==len({g['gamePk'] for g in played}) and canonical['venue_id'].null_count()==0
    assert len([t for t in teams['teams'] if t.get('league',{}).get('id') in [103,104]])==30
    canonical.write_parquet(original.OUT/f'played-venues-{year}.parquet')
    original.write(original.OUT/f'played-schedule-review-{year}.json',dict(season=year,raw_schedule_entries=len(all_games),
        final_schedule_entries=len(played),unique_played_games=len(canonical),
        excluded_nonfinal_listings=len(all_games)-len(played),duplicate_final_listings=len(played)-len(canonical),
        conflicting_played_dates_or_venues=False,canonical_reducer_sha256=sha256_file(Path(schedule_venues.__code__.co_filename)),
        resume_runner_sha256=sha256_file(Path(__file__))))


if __name__=='__main__':
    assert not (original.OUT/'capture-report.json').exists(),'Do not restart completed capture'
    original.metadata=metadata
    original.main()
    original.write(original.OUT/'resume-receipt.json',dict(source_only=True,model_fits=0,
        capture_report_sha256=sha256_file(original.OUT/'capture-report.json'),resume_runner_sha256=sha256_file(Path(__file__)),
        correction='Only final played schedule listings determine actual venue. Postponed and cancelled listings remain in raw authority, not modeled venues.'))
