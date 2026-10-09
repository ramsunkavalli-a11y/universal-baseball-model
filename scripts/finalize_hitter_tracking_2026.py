"""Resolve physical shift awards without discarding measured contact evidence."""
from pathlib import Path
import gzip
import json
import math
import polars as pl
from universal_baseball.storage import sha256_file
from capture_hitter_2027_membership import capture
from audit_hitter_tracking_2026 import ROOT,SOURCE,OUT,PUBLIC,write_once


def main():
    assert not (PUBLIC/'tracking-2026-final-review.json').exists()
    initial_path=PUBLIC/'tracking-2026-initial-review.json'
    initial=json.loads(initial_path.read_text())
    for p,h in initial['output_hashes'].items():assert sha256_file(Path(p))==h
    raw=pl.concat([pl.read_parquet(SOURCE/f'2026-{m:02}.parquet') for m in range(3,11)])
    schedule_path=ROOT/'reports/generated/hitter-final-2026-source/captures/regular-season-schedule-2026.json.gz'
    schedule=json.loads(gzip.decompress(schedule_path.read_bytes()))
    expected={g['gamePk'] for day in schedule['dates'] for g in day['games']
        if g['status']['codedGameState'] in ('F','O') and g['status']['abstractGameState']=='Final'}
    assert len(expected)==2429 and set(raw['game_pk'].cast(pl.Int64))==expected
    corrections=[]
    for case in initial['residuals']:
        pid=case['player_id'];assert case['contact_residual']==1
        for c in ['singles','doubles','triples','home_runs']:assert case[c]==case[c+'_source']
        candidate=raw.filter((pl.col('batter')==str(pid))&(pl.col('events')=='field_error')&
            pl.col('des').str.to_lowercase().str.contains('reaches on a defensive shift violation error'))
        assert len(candidate)==1,'Unexpected source discrepancy requires separate diagnosis'
        r=candidate.row(0,named=True);pk=int(r['game_pk']);num=int(r['at_bat_number'])
        feed=capture(f'tracking-shift-{pk}',f'/game/{pk}/playByPlay',{})
        plays=[p for p in feed['allPlays'] if p['atBatIndex']+1==num and p['matchup']['batter']['id']==pid]
        assert len(plays)==1;play=plays[0]
        assert play['result']['eventType']=='field_error' and 'defensive shift violation' in play['result']['description'].lower()
        pitches=[p for p in play['playEvents'] if p.get('details',{}).get('isInPlay')]
        assert len(pitches)==1;pitch=pitches[0]
        assert pitch['details']['violation']['type']=='defensive_shift'
        assert math.isclose(pitch['hitData']['launchSpeed'],float(r['launch_speed']),abs_tol=1e-9)
        assert math.isclose(pitch['hitData']['launchAngle'],float(r['launch_angle']),abs_tol=1e-9)
        gamelog=capture(f'tracking-gamelog-{pid}',f'/people/{pid}/stats',dict(stats='gameLog',group='hitting',season=2026,sportId=1,gameType='R'))
        log=[s for group in gamelog['stats'] for s in group['splits']]
        n=sum(s['stat']['atBats']-s['stat']['strikeOuts']+s['stat']['sacFlies']+s['stat']['sacBunts'] for s in log)
        assert n==case['official_contacts']
        selected=[s for s in log if s['game']['gamePk']==pk];assert len(selected)==1
        st=selected[0]['stat'];game_contacts=st['atBats']-st['strikeOuts']+st['sacFlies']+st['sacBunts']
        n_source=len(raw.filter((pl.col('game_pk')==str(pk))&(pl.col('batter')==str(pid))&(pl.col('type')=='X')))
        assert n_source==game_contacts+1
        corrections.append(dict(player_id=pid,player_name=case['player_name'],game_pk=pk,at_bat_number=num,
            physical_contacts_without_AB=1,source=r,official_result=play['result'],official_hit_data=pitch['hitData'],
            interpretation='Real measured batted ball with a shift-violation award. Preserve EV/LA even though AB-based contact count excludes it.'))
    reconciliation=pl.read_parquet(OUT/'player-reconciliation.parquet')
    adjust={r['player_id']:r['physical_contacts_without_AB'] for r in corrections}
    assert all(r['source_contacts']==r['official_contacts']+adjust.get(r['player_id'],0) for r in reconciliation.to_dicts())
    old_path=ROOT/'reports/generated/hitter-tracking-2025-audit/annual-launch-features-through-2025.parquet'
    old=pl.read_parquet(old_path);current=pl.read_parquet(OUT/'annual-features.parquet')
    assert old['season'].max()==2025 and set(current['season'])=={2026}
    combined=pl.concat([old,current],how='diagonal_relaxed').sort('season','player_id')
    assert combined.unique(['season','player_id']).height==len(combined)
    path=OUT/'annual-launch-features-through-2026.parquet';assert not path.exists();combined.write_parquet(path)
    write_once(PUBLIC/'tracking-2026-final-review.json',dict(source_approved_for_estimation=True,
        source_season=2026,first_projection_year=2027,complete_game_coverage=2429,
        measured_people=len(current),features='Same seven tracking measurements; no substitution of EV90 for EV95',
        physical_award_corrections=corrections,player_walkthrough_status='complete_for_source_inputs',
        source_walkthrough=initial['source_player_cases'],forecast_fitted=False,full_model_complete=False,
        output_hashes={str(path):sha256_file(path)},input_hashes={str(p):sha256_file(p) for p in [old_path,initial_path,OUT/'annual-features.parquet',schedule_path,Path(__file__)]}))
    print(f'2026 tracking approved: {len(current)} players, all 2429 games, two physical shift awards explained; unchanged metric definitions.')


if __name__=='__main__':main()
