"""Authorized target opening AFTER the published candidate freeze, with coverage gate.

No forecasts, inputs or fitted settings can be changed by this collector. Do not
score partial seasons or reinterpret an empty official response as zero outcomes.
"""
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import gzip
import hashlib
import json
import requests
from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
FROZEN=ROOT/'model_artifacts/hitter-selected-2026-frozen-2026-10-05'
OUT=ROOT/'reports/generated/hitter-final-2026-source'
CONTRACT=ROOT/'docs/hitter-2026-final-evaluation-contract.md'


def read(p):return json.loads(p.read_text(encoding='utf8'))


def write(p,o):
    assert not p.exists(),f'Preserve {p}'
    p.write_text(json.dumps(o,indent=2,allow_nan=False,default=str)+'\n',encoding='utf8',newline='\n')


def capture(name,endpoint,params):
    assert params.get('season')==2026,'Only the declared final target'
    p=OUT/'captures'/f'{name}.json.gz';receipt=p.with_suffix('.receipt.json')
    if receipt.exists():
        r=read(receipt);assert r['params']==params and r['endpoint']==endpoint
        assert r['collector_sha256']==sha256_file(Path(__file__)) and r['compressed_sha256']==sha256_file(p)
        with gzip.open(p,'rb') as f:raw=f.read()
        assert hashlib.sha256(raw).hexdigest()==r['response_sha256']
    else:
        assert not p.exists(),'Unreceipted capture'
        response=requests.get('https://statsapi.mlb.com/api/v1'+endpoint,params=params,timeout=(15,45))
        response.raise_for_status();raw=response.content;payload=json.loads(raw);assert isinstance(payload,dict)
        p.parent.mkdir(parents=True,exist_ok=True)
        with gzip.GzipFile(filename=str(p),mode='wb',mtime=0) as f:f.write(raw)
        write(receipt,dict(endpoint=endpoint,params=params,requested_url=response.url,
            captured_utc=datetime.now(timezone.utc).isoformat(),collector_sha256=sha256_file(Path(__file__)),
            compressed_sha256=sha256_file(p),response_sha256=hashlib.sha256(raw).hexdigest(),
            authorization_sha256=sha256_file(OUT/'authorization-and-freeze.json')))
    return json.loads(raw),p,receipt


def main():
    manifest=read(FROZEN/'freeze-manifest.json');digest=sha256_file(FROZEN/'freeze-manifest.json')
    assert digest==(FROZEN/'freeze-manifest.sha256').read_text().strip()
    assert manifest['user_authorized_final_evaluation'] and not manifest['protected_outcomes_used_before_freeze']
    for f in manifest['files']:assert sha256_file(FROZEN/f['path'])==f['sha256'],f['path']
    frozen_contract=FROZEN/'hitter-2026-final-evaluation-contract.md'
    assert sha256_file(CONTRACT)==sha256_file(frozen_contract),'Changed final evaluation contract'
    OUT.mkdir(parents=True,exist_ok=True);authorization=OUT/'authorization-and-freeze.json'
    if not authorization.exists():
        write(authorization,dict(user_authorization='Yes—evaluate once the candidate is frozen',
            freeze_manifest_sha256=digest,frozen_at_utc=manifest['frozen_at_utc'],
            freeze_commit='e661958',branch='audit/data-methodology-v3',freeze_pushed_before_access=True,
            opening_recorded_utc=datetime.now(timezone.utc).isoformat(),fixed_forecast_population=4030,
            forecasts_and_models_immutable=True,contract_sha256=sha256_file(CONTRACT),first_outcome_access_not_yet_performed=True))
    else:assert read(authorization)['freeze_manifest_sha256']==digest
    assert not (OUT/'source-review.json').exists(),'Preserve completed source review'
    fields='dates,date,games,gamePk,gameType,officialDate,status,abstractGameState,codedGameState,detailedState,teams,away,home,team,id,totalGames,totalItems'
    schedule,sp,sr=capture('regular-season-schedule-2026','/schedule',dict(sportId=1,season=2026,gameType='R',fields=fields))
    games={}
    for d in schedule.get('dates',[]):
        for g in d.get('games',[]):
            assert g['gameType']=='R' and str(g['officialDate']).startswith('2026-')
            if g['gamePk'] in games:assert games[g['gamePk']]==g,'Conflicting game versions'
            games[g['gamePk']]=g
    final=[g for g in games.values() if g['status']['abstractGameState']=='Final']
    unresolved=[dict(game_pk=g['gamePk'],date=g['officialDate'],status=g['status']) for g in games.values()
        if g['status']['abstractGameState']!='Final' and g['status']['detailedState']!='Cancelled']
    counts=Counter(t['team']['id'] for g in final for t in g['teams'].values())
    completed=len(final)>=2400 and len(counts)==30 and min(counts.values(),default=0)>=160 and not unresolved
    coverage=dict(schedule_games=len(games),completed_games=len(final),team_game_counts=dict(counts),unresolved_games=unresolved,
        complete_regular_season_coverage=completed,empty_response_is_not_zero_outcomes=True,
        raw_schedule_sha256=sha256_file(sp),schedule_receipt_sha256=sha256_file(sr),freeze_manifest_sha256=digest)
    write(OUT/'schedule-coverage.json',coverage)
    if not completed:
        write(OUT/'source-review.json',dict(status='completed_target_not_certified',coverage=coverage,
            source_stats_not_retrieved=True,forecasts_unchanged=True,evaluation_scored=False,
            next_action='Require a certified completed 2026 official/public export or resolve the target-source discrepancy; never score missing results as zero.'))
        print(json.dumps(dict(status='completed_target_not_certified',schedule_games=len(games),completed_games=len(final),
            unresolved=len(unresolved),evaluation_scored=False,forecasts_unchanged=True)),flush=True)
        return
    players,pp,pr=capture('all-player-batting-2026','/stats',dict(stats='season',group='hitting',season=2026,
        sportIds=1,gameType='R',playerPool='ALL',limit=5000))
    teams,tp,tr=capture('all-team-batting-2026','/teams/stats',dict(stats='season',group='hitting',season=2026,
        sportIds=1,gameType='R',limit=100))
    write(OUT/'source-review.json',dict(status='raw_completed_target_captured_reconciliation_pending',coverage=coverage,
        source_stats_retrieved=True,forecasts_unchanged=True,evaluation_scored=False,
        source_hashes={str(p):sha256_file(p) for p in [sp,sr,pp,pr,tp,tr]},
        next_action='Reconcile event counts and league totals before the single fixed evaluation; do not fit or change forecasts.'))
    print('Completed 2026 schedule certified; official player/team batting captured. Reconciliation required before scoring.',flush=True)


if __name__=='__main__':main()
