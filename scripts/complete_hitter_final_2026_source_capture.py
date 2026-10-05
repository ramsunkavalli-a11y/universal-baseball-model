"""Continue the unchanged source opening after resolving postponed schedule entries."""
from pathlib import Path
import json
import gzip
import capture_hitter_final_2026_source as source
from universal_baseball.hitter_final_schedule import completed_schedule
from universal_baseball.storage import sha256_file


def main():
    out=source.OUT;assert not (out/'source-review.json').exists(),'Preserve completed target source gate'
    manifest=source.read(source.FROZEN/'freeze-manifest.json')
    assert sha256_file(source.FROZEN/'freeze-manifest.json')==source.read(out/'authorization-and-freeze.json')['freeze_manifest_sha256']
    for f in manifest['files']:assert sha256_file(source.FROZEN/f['path'])==f['sha256']
    sp=out/'captures/regular-season-schedule-2026.json.gz';sr=sp.with_suffix('.receipt.json');meta=source.read(sr)
    assert sha256_file(sp)==meta['compressed_sha256'] and sha256_file(Path(source.__file__))==meta['collector_sha256']
    with gzip.open(sp,'rb') as f:raw=f.read()
    assert __import__('hashlib').sha256(raw).hexdigest()==meta['response_sha256']
    coverage=completed_schedule(json.loads(raw),2026)
    coverage.update(raw_schedule_sha256=sha256_file(sp),schedule_receipt_sha256=sha256_file(sr),
        source_only_reconciliation='29 postponed and completed listings may share a game ID; only coded F/O are played. No forecast/model changes.',
        resolver_sha256=sha256_file(source.ROOT/'src/universal_baseball/hitter_final_schedule.py'))
    source.write(out/'schedule-coverage.json',coverage)
    if not coverage['complete_regular_season_coverage']:
        source.write(out/'source-review.json',dict(status='completed_target_not_certified',coverage=coverage,
            source_stats_not_retrieved=True,forecasts_unchanged=True,evaluation_scored=False))
        print('Completed target coverage not certified; no scoring or zero outcomes assigned.',flush=True);return
    players,pp,pr=source.capture('all-player-batting-2026','/stats',dict(stats='season',group='hitting',season=2026,
        sportIds=1,gameType='R',playerPool='ALL',limit=5000))
    teams,tp,tr=source.capture('all-team-batting-2026','/teams/stats',dict(stats='season',group='hitting',season=2026,
        sportIds=1,gameType='R',limit=100))
    source.write(out/'source-review.json',dict(status='raw_completed_target_captured_reconciliation_pending',
        completed_regular_games=coverage['completed_games'],unique_regular_games=coverage['unique_regular_games'],
        team_game_counts=coverage['team_game_counts'],resolved_multiple_listing_games=len(coverage['resolved_multiple_listing_games']),
        initial_collector_schedule_assertion_preserved=True,source_stats_retrieved=True,forecasts_unchanged=True,
        protected_target_access_authorized_after_freeze=True,evaluation_scored=False,
        source_hashes={str(p):sha256_file(p) for p in [sp,sr,pp,pr,tp,tr,out/'schedule-coverage.json',Path(__file__),
            source.ROOT/'src/universal_baseball/hitter_final_schedule.py']},
        next_action='Reconcile event counts and complete league totals before the single frozen evaluation; do not refit.'))
    print(f'2026 source opened after published freeze: {coverage["completed_games"]} completed games, all 30 teams at 162; player/team stats captured, not yet scored.',flush=True)


if __name__=='__main__':main()
