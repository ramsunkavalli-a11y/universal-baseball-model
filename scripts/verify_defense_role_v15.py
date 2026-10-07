"""Independent byte, integer-outs, annual and period replay; no shared role parser."""
from collections import defaultdict
from datetime import date
from pathlib import Path
import json

import polars as pl

from capture_defense_role_v15 import ROOT, OUT, SOURCE, read, receipt
from run_hitter_finite_return_baseline import protections
from universal_baseball.storage import sha256_file

LEVELS={'MLB':1,'AAA':11,'AA':12,'Aplus':13,'A':14,'Aminus':15,
        'DSL':16,'COMPLEX':16,'ROOKIE_COMBINED':16,'ADVANCED_ROOKIE':16}


def outs(text):
    parts=str(text).split('.')
    assert 1<=len(parts)<=2 and parts[0].isdigit()
    suffix=parts[1] if len(parts)==2 else '0'
    assert suffix in ['0','1','2']
    return int(parts[0])*3+int(suffix)


def main():
    protections()
    assert not (OUT/'independent-verification.json').exists()
    for name in ['capture-seal.json','scope-amendment-seal.json','source-seal.json','source-review.json','pbp-inventory.json']:
        for path,expected in read(OUT/name)['hashes'].items():assert sha256_file(Path(path))==expected,path
    annual=pl.read_parquet(SOURCE).to_dicts()
    lookup=defaultdict(list)
    for r in annual:lookup[r['player_id'],r['season'],LEVELS[r['normalized_level']]].append(r)
    manifest=read(OUT/'explicit-scope-manifest.json');review=read(OUT/'source-review.json')
    assert len(manifest['cases'])==review['cases']==74
    assert len(manifest['requests'])==review['requested_scopes']==114
    reconstructed=[];annual_checks=0
    for request in manifest['requests']:
        pid,y,sport=request['player_id'],request['season'],request['sport_id']
        path=OUT/'captures'/(request['capture_name']+'.json')
        meta=read(path.with_suffix('.capture.json'))
        assert meta['endpoint']==request['endpoint'] and sha256_file(path)==meta['sha256']
        data=read(path);assert len(data['stats'])==1
        group=data['stats'][0]
        assert group['type']['displayName']=='gameLog' and group['group']['displayName']=='fielding'
        raw=group['splits'];assert raw
        if 'totalSplits' in group:assert group['totalSplits']==len(raw)
        expected=defaultdict(lambda:[0,0,0]);actual=defaultdict(lambda:[0,0,0]);seen=set()
        for original in lookup[pid,y,sport]:
            key=(original['league_id'],int(original['position_code']))
            expected[key][0]+=original['fielding_outs']
            expected[key][1]+=original['games_started']
            expected[key][2]+=original['games_played']
        for r in raw:
            assert r['player']['id']==pid and int(r['season'])==y<=2024 and r['sport']['id']==sport
            assert r['gameType']=='R' and date.fromisoformat(r['date']).year==y
            code=int(r['position']['code']);game=r['game']['gamePk'];stat=r['stat']
            assert (game,code) not in seen;seen.add((game,code))
            assert stat['games']==stat['gamesPlayed']==1 and stat['gamesStarted'] in [0,1]
            n=outs(stat['innings']);assert code!=10 or n==0
            key=(r['league']['id'],code)
            actual[key][0]+=n;actual[key][1]+=stat['gamesStarted'];actual[key][2]+=1
            reconstructed.append(dict(player_id=pid,season=y,sport_id=sport,league_id=r['league']['id'],
                game_id=game,date=r['date'],period='before_August' if r['date']<f'{y}-08-01' else 'August_onward',
                position_code=code,fielding_outs=n,appearances=1,raw_starts=stat['gamesStarted'],
                reviewed_starts=stat['gamesStarted'],certified_dual_DH_addition=0))
        assert dict(expected)==dict(actual),(request,expected,actual)
        annual_checks+=len(expected)
    pairs={(r['player_id'],r['season']) for r in reconstructed if r['sport_id']==1}
    cert=read(ROOT/'reports/generated/defense-budget-v13/source-review.json')
    additions=0
    for c in cert['corrections']:
        if (c['player_id'],c['season']) not in pairs:continue
        for r in c['game_evidence']:
            if not r['certified']:continue
            box=ROOT/'reports/generated/defense-budget-v13/captures'/f"box-{r['game_id']}.json"
            assert sha256_file(box)==read(box.with_suffix('.capture.json'))['sha256']
            # Independently inspect original starting batting-order slot and P start.
            b=read(box)['teams'][r['side']]['players'][f"ID{r['player_id']}"]
            assert b['stats']['pitching']['gamesStarted']==1
            order=str(b['battingOrder']);assert order.endswith('00') and int(order)>0
            matches=[x for x in reconstructed if x['player_id']==r['player_id'] and x['game_id']==r['game_id']]
            pitcher=next(x for x in matches if x['position_code']==1)
            assert pitcher['date']==r['date'] and pitcher['raw_starts']==1
            dh=[x for x in matches if x['position_code']==10]
            if not dh:
                assert r['DH_evidence_basis']=='rule_5_11b_starting_pitcher_in_lineup'
                row=dict(pitcher,position_code=10,fielding_outs=0,appearances=0,raw_starts=0,reviewed_starts=0)
                reconstructed.append(row)
            else:assert len(dh)==1;row=dh[0]
            assert row['reviewed_starts']==0
            row['reviewed_starts']=1;row['certified_dual_DH_addition']=1;additions+=1
    saved=pl.read_parquet(OUT/'verified-role-games.parquet').to_dicts()
    columns=['player_id','season','sport_id','league_id','game_id','date','period','position_code',
             'fielding_outs','appearances','raw_starts','reviewed_starts','certified_dual_DH_addition']
    comparable=lambda rs:sorted(tuple(r[c] for c in columns) for r in rs)
    assert comparable(saved)==comparable(reconstructed)
    assert len(saved)==9396 and additions==51
    parts=defaultdict(lambda:[0,0,0,0,0,set(),[]])
    for r in reconstructed:
        key=tuple(r[c] for c in ['player_id','season','sport_id','league_id','period','position_code'])
        values=parts[key]
        for i,c in enumerate(['fielding_outs','appearances','raw_starts','reviewed_starts','certified_dual_DH_addition']):values[i]+=r[c]
        values[5].add(r['game_id']);values[6].append(r['date'])
    period=pl.read_parquet(OUT/'verified-role-periods.parquet').to_dicts()
    assert len(period)==len(parts)==424
    for r in period:
        key=tuple(r[c] for c in ['player_id','season','sport_id','league_id','period','position_code']);v=parts[key]
        assert [r[c] for c in ['fielding_outs','appearances','raw_starts','reviewed_starts','certified_dual_DH_addition']]==v[:5]
        assert r['position_games']==len(v[5]) and r['first_date']==min(v[6]) and r['last_date']==max(v[6])
    inventory=read(OUT/'pbp-inventory.json')
    assert inventory['files']==244 and inventory['rows']==7034246
    for r in inventory['source_files']:
        path=Path(r['source']);assert sha256_file(path)==r['sha256']
        # Independent projected scan of dates and each ID column, no fielding-outs inference.
        f=pl.read_parquet(path,columns=['game_date',*[f'fielder_{p}' for p in range(2,10)]])
        assert f.height==r['rows'] and f['game_date'].null_count()==r['missing_dates']
        for p in range(2,10):
            s=f[f'fielder_{p}']
            assert s.null_count()==r[f'fielder_{p}_missing']
            assert int((s<=0).fill_null(False).sum())==r[f'fielder_{p}_nonpositive']
    receipt('independent-verification.json',dict(source_integrity='pass',source_scopes_replayed=114,
        annual_position_totals_replayed=annual_checks,position_game_rows_replayed=len(saved),
        dated_DH_additions_replayed=additions,period_cells_replayed=len(period),
        pbp_files_replayed=244,pbp_rows=inventory['rows'],no_fits=True,no_accuracy_claim=True,
        player_walkthrough_status='pending',hashes={str(p):sha256_file(p) for p in
            [Path(__file__),OUT/'source-review.json',OUT/'pbp-inventory.json']}))
    protections();print('Independent replay passed: 114 source scopes, 9396 position-games, 424 period cells, '
                        '51 dated DH corrections and 244 PBP files.',flush=True)


if __name__=='__main__':main()
