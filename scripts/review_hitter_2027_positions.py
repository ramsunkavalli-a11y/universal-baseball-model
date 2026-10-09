"""Check current position evidence and carry forward the reviewed P/DH rule."""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import gzip
import json
import polars as pl
import capture_hitter_2027_membership as capture_source
from universal_baseball.defense_budget_source import dual_start
from universal_baseball.storage import sha256_file
from capture_hitter_2027_origin_counts import ROOT,write_once

OUT=ROOT/'reports/generated/hitter-2027-position-source'
PUBLIC=ROOT/'reports/model-evidence/hitter-2027-v1'


def main():
    receipt=PUBLIC/'position-source-player-review.json';assert not receipt.exists()
    capture_source.OUT=OUT
    initial=json.loads((PUBLIC/'position-source-2026.json').read_text())
    for p,h in initial['output_hashes'].items():assert sha256_file(Path(p))==h
    fielding=pl.read_parquet(OUT/'fielding.parquet');annual=pl.read_parquet(OUT/'annual-usage.parquet')
    mlb=annual.filter(pl.col('is_mlb'))
    candidates=mlb.filter((pl.col('starts_10')>0)&(pl.col('outs_1')>0))
    corrections=[]
    for c in candidates.iter_rows(named=True):
        pid=c['player_id']
        params=dict(stats='gameLog',group='pitching',season=2026,gameType='R',sportIds=1)
        pitching=capture_source.capture(f'pitching-log-{pid}',f'/people/{pid}/stats',params)
        groups=[b for b in pitching['stats'] if b['group']['displayName']=='pitching']
        assert len(groups)==1 and groups[0]['type']['displayName']=='gameLog'
        starts=[r for r in groups[0]['splits'] if r['stat']['gamesStarted']==1]
        expected=fielding.filter((pl.col('player_id')==pid)&pl.col('is_mlb')&(pl.col('position_code')=='1'))['games_started'].sum()
        assert len(starts)==expected
        if not starts:continue
        fl=capture_source.capture(f'fielding-log-{pid}',f'/people/{pid}/stats',dict(stats='gameLog',group='fielding',season=2026,gameType='R',sportId=1))
        logged=[r for b in fl['stats'] if b['group']['displayName']=='fielding' for r in b['splits']]
        recorded_dh={r['game']['gamePk'] for r in logged if r['position']['code']=='10' and r['stat']['gamesStarted']==1}
        assert len(recorded_dh)==c['starts_10'],'Annual DH starts must match ordinary game logs before correction'
        def inspect(r):
            gid=r['game']['gamePk'];box=capture_source.capture(f'box-{gid}',f'/game/{gid}/boxscore',{})
            detail=dual_start(box,pid,2026)
            assert not detail['status'].startswith('unresolved')
            return dict(game_id=gid,date=r['date'],already_in_raw_dh=gid in recorded_dh,**detail)
        with ThreadPoolExecutor(max_workers=3) as pool:games=list(pool.map(inspect,starts))
        addition=sum(g['certified'] and not g['already_in_raw_dh'] for g in games)
        corrections.append(dict(player_id=pid,raw_starts=c['starts_10'],additional_starts=addition,reviewed_starts=c['starts_10']+addition,games=games))
    adjustment={r['player_id']:r['additional_starts'] for r in corrections}
    annual=annual.with_columns(pl.Series('dh_dual_start_addition',[adjustment.get(r['player_id'],0) if r['is_mlb'] else 0 for r in annual.iter_rows(named=True)]))
    annual=annual.with_columns(pl.col('starts_10').alias('raw_starts_10'),(pl.col('starts_10')+pl.col('dh_dual_start_addition')).alias('starts_10'))
    assert annual.filter(pl.col('is_mlb'))['starts_10'].sum()==4858,'Universal DH starts must cover both teams in each completed game'
    assert annual.filter(pl.col('is_mlb'))['defensive_outs'].sum()==8*129239,'Eight nonpitcher positions must cover official outs'
    base=json.loads(gzip.decompress((PUBLIC/'base-input-player-walks.json.gz').read_bytes()))['cases']
    walks=[]
    for c in base:
        for w in [c['primary'],*c['peers']]:
            pid=w['player_id'];history=fielding.filter(pl.col('player_id')==pid)
            a=annual.filter(pl.col('player_id')==pid)
            for o in a.iter_rows(named=True):
                raw=history.filter((pl.col('is_mlb')==o['is_mlb'])&(pl.col('normalized_level')==o['normalized_level']))
                for p in range(2,10):
                    assert o[f'outs_{p}']==raw.filter(pl.col('position_code')==str(p))['fielding_outs'].sum()
                    assert o[f'starts_{p}']==raw.filter(pl.col('position_code')==str(p))['games_started'].sum()
            walks.append(dict(player_id=pid,name=w['name'],source=history.select('season','normalized_level','position_abbreviation','source_innings','games_started','fielding_outs').to_dicts(),
                annual_usage=a.to_dicts(),interpretation='Use actual positions and denominators; short promotion stints do not erase larger minor experience. Pitching outs stay outside hitter fielding and DH contributes starts, not defensive outs.'))
    output=OUT/'annual-usage-reviewed.parquet';assert not output.exists();annual.write_parquet(output)
    walkpath=PUBLIC/'position-source-player-walks.json.gz';assert not walkpath.exists();walkpath.write_bytes(gzip.compress(json.dumps(walks,allow_nan=False,default=str).encode(),mtime=0))
    write_once(receipt,dict(source_walkthrough='complete',focal_cases=8,peers=24,dual_start_corrections=corrections,
        MLB_nonpitcher_outs=int(annual.filter(pl.col('is_mlb'))['defensive_outs'].sum()),MLB_DH_starts=4858,
        source_certified_for_position_evidence=True,projected_roles_not_yet_assembled=True,
        output_hashes={str(output):sha256_file(output),str(walkpath):sha256_file(walkpath)},runner_sha256=sha256_file(Path(__file__))))
    print([(r['player_id'],r['raw_starts'],r['additional_starts'],r['reviewed_starts']) for r in corrections],flush=True)


if __name__=='__main__':main()
