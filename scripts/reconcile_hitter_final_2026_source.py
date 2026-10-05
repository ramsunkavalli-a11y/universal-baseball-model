"""Certify official completed target counts before assigning any absent outcome zero."""
from pathlib import Path
import gzip
import json
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
from universal_baseball.mlb_event_logit import EVENTS,VALUES
import capture_hitter_final_2026_source as source


def load(p):
    with gzip.open(p,'rt',encoding='utf8') as f:return json.load(f)


def counts(stat):
    names=['plateAppearances','hits','doubles','triples','homeRuns','strikeOuts','baseOnBalls','intentionalWalks','hitByPitch']
    if set(names)-set(stat):raise ValueError('Missing official target denominator/event')
    if any(not isinstance(stat[c],int) or stat[c]<0 for c in names):raise ValueError('Invalid target event count')
    v=[stat['strikeOuts'],stat['baseOnBalls']-stat['intentionalWalks'],stat['hitByPitch'],
       stat['hits']-stat['doubles']-stat['triples']-stat['homeRuns'],stat['doubles'],stat['triples'],stat['homeRuns']]
    x=np.asarray([stat['plateAppearances']-sum(v),*v],dtype=np.int64)
    if (x<0).any() or x.sum()!=stat['plateAppearances']:raise ValueError('Nonexclusive/inconsistent official events')
    return x


def main():
    out=source.OUT;assert not (out/'reconciliation.json').exists(),'Preserve completed target reconciliation'
    r=source.read(out/'source-review.json');assert r['status']=='raw_completed_target_captured_reconciliation_pending'
    for p,h in r['source_hashes'].items():assert sha256_file(Path(p))==h,p
    schedule=source.read(out/'schedule-coverage.json');assert schedule['complete_regular_season_coverage']
    pp=out/'captures/all-player-batting-2026.json.gz';tp=out/'captures/all-team-batting-2026.json.gz'
    players=load(pp)['stats'];teams=load(tp)['stats']
    assert len(players)==len(teams)==1
    for b in [players[0],teams[0]]:
        assert b['type']['displayName']=='season' and b['group']['displayName']=='hitting'
    rows=[];team_rows=[]
    for s in players[0]['splits']:
        assert s['season']=='2026' and s['sport']['id']==1
        x=counts(s['stat']);rows.append(dict(player_id=s['player']['id'],actual_player_name=s['player']['fullName'],
            actual_pa=int(x.sum()),**{e:int(v) for e,v in zip(EVENTS,x)}))
    for s in teams[0]['splits']:
        assert s['season']=='2026'
        tid=s['team']['id'];assert s['stat']['gamesPlayed']==schedule['team_game_counts'][str(tid)]
        x=counts(s['stat']);team_rows.append(dict(team_id=tid,games=s['stat']['gamesPlayed'],actual_pa=int(x.sum()),
            **{e:int(v) for e,v in zip(EVENTS,x)}))
    a,t=pl.DataFrame(rows),pl.DataFrame(team_rows)
    assert len(a)==a['player_id'].n_unique()==751 and len(t)==t['team_id'].n_unique()==30
    av=a.select(EVENTS).to_numpy().sum(0);tv=t.select(EVENTS).to_numpy().sum(0)
    assert np.array_equal(av,tv),'Player and team event totals do not reconcile'
    assert a['actual_pa'].sum()==t['actual_pa'].sum()==av.sum()
    old_counts_path=source.ROOT/'reports/generated/practical-hitter-v31/counts.parquet'
    old=pl.read_parquet(old_counts_path).filter((pl.col('season')==2025)&(pl.col('bucket')=='MLB'))
    x=old.select('strike_outs','unintentional_walks','hit_by_pitch','babip_hits','doubles','triples','home_runs').to_numpy().sum(0)
    past=np.asarray([old['plate_appearances'].sum()-x[[0,1,2,3,6]].sum(),x[0],x[1],x[2],x[3]-x[4]-x[5],x[4],x[5],x[6]])
    assert past.min()>=0 and past.sum()==182926
    a.write_parquet(out/'actual-player-events-2026.parquet');t.write_parquet(out/'actual-team-events-2026.parquet')
    environments=pl.DataFrame([dict(season=y,league_pa=int(v.sum()),**{e:int(c) for e,c in zip(EVENTS,v)}) for y,v in [(2025,past),(2026,av)]])
    environments.write_parquet(out/'league-event-environments.parquet')
    source.write(out/'reconciliation.json',dict(status='completed_MLB_target_certified',completed_games=schedule['completed_games'],
        source_player_rows=len(a),league_pa=int(av.sum()),all_eight_events_match_player_team_totals=True,
        team_seasons_match_completed_schedule=True,schedule_game_count_distribution={'162':28,'161':2},
        collector_console_correction='Initial continuation printed all teams at 162; exact stored counts are 28 at 162 and two at 161. One canceled game is not missing target coverage.',
        origin_league_pa=182926,zero_outcome_assignment_allowed_for_fixed_cohort_absent_ids=True,
        predictions_or_models_changed=False,evaluation_scored=False,
        input_hashes={str(p):sha256_file(p) for p in [pp,tp,out/'source-review.json',out/'schedule-coverage.json',old_counts_path,Path(__file__)]},
        output_hashes={str(out/name):sha256_file(out/name) for name in ['actual-player-events-2026.parquet','actual-team-events-2026.parquet','league-event-environments.parquet']}))
    print(f'Completed target certified: {len(a)} players, {int(av.sum())} PA, all eight events match thirty team totals.',flush=True)


if __name__=='__main__':main()
