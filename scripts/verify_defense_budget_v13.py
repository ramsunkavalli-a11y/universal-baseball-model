"""Independent start evidence, source totals and saved forecast DH arithmetic."""

from collections import defaultdict
from pathlib import Path
import json
import math
import polars as pl
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/defense-budget-v13'
PUBLIC=ROOT/'reports/model-evidence/defense-budget-v13'


def read(p): return json.loads(p.read_text(encoding='utf8'))


def matches(r,k):
    if k[0].startswith('role') and str(r['repertoire_primary_role'])!=k[1]: return False
    if k[0].startswith('family') and r['repertoire_family']!=k[1]: return False
    return not (k[0].endswith('_stage') and r['stage']!=k[2])


def main():
    protections(); d=read(OUT/'source-review.json')
    for p,h in {**d['hashes'],**d['output_hashes']}.items(): assert sha256_file(Path(p))==h,p
    source=pl.read_parquet(ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet')
    mlb=source.filter(pl.col('is_mlb')); annual=pl.read_parquet(OUT/'reviewed-DH-starts.parquet')
    rawdh=defaultdict(int); dual=defaultdict(int)
    for r in mlb.filter(pl.col('position_code')=='10').iter_rows(named=True):
        rawdh[r['season'],r['player_id']]+=r['games_started']
    jobs=read(OUT/'captured-games.json')['games']; raw_starts=defaultdict(set); certified=defaultdict(set)
    for r in jobs:
        key=r['season'],r['player_id']; gid=r['game_id']; assert gid not in raw_starts[key]
        raw_starts[key].add(gid)
        box=read(OUT/f'captures/box-{gid}.json')
        players=[p for t in box['teams'].values() for p in t['players'].values() if p['person']['id']==r['player_id']]
        assert len(players)==1
        p=players[0]; assert p['stats']['pitching']['gamesStarted']==1
        role={x['code'] for x in p['allPositions']}; order=p.get('battingOrder')
        is_original = order is not None and str(order).isdigit() and str(order).endswith('00')
        if is_original:
            assert '1' in role and r['season']>=2022
            certified[key].add(gid)
    for c in d['corrections']:
        key=c['season'],c['player_id']
        assert c['pitching_starts']==len(raw_starts[key])
        log=read(OUT/f"captures/log-{c['season']}-{c['player_id']}.json")
        stat=next(s for s in log['stats'] if s['group']['displayName']=='pitching')
        ids={r['game']['gamePk'] for r in stat['splits'] if r['stat']['gamesStarted']==1}
        assert ids==raw_starts[key]
        assert c['certified_dual_starts']==len(certified[key]) and set(c['game_ids'])==certified[key]
        dual[key]=len(certified[key])
    assert annual.height==len(rawdh) and annual.unique(['season','player_id']).height==annual.height
    for r in annual.iter_rows(named=True):
        key=r['season'],r['player_id']
        assert r['raw_DH_starts']==rawdh[key]
        assert r['certified_dual_DH_starts']==dual[key]
        assert r['reviewed_DH_starts']==rawdh[key]+dual[key]
    for inv in d['inventory']:
        y=inv['season']; group=mlb.filter(pl.col('season')==y)
        for p in range(2,10):
            rows=group.filter(pl.col('position_code')==str(p))
            part=next(r for r in inv['fielding'] if r['position']==p)
            assert part['outs']==rows['fielding_outs'].sum() and part['starts']==rows['games_started'].sum()
        a=annual.filter(pl.col('season')==y)
        assert a['raw_DH_starts'].sum()==inv['raw_DH_starts']
        assert a['reviewed_DH_starts'].sum()==inv['reviewed_DH_starts']
        if y>=2022: assert inv['reviewed_DH_starts']==inv['fielding_team_games']
    f=pl.read_parquet(ROOT/'reports/generated/defense-repertoire-v9/features.parquet')
    rows={r['row_id']:r for r in f.iter_rows(named=True)}
    q=pl.read_parquet(ROOT/'reports/generated/defense-transition-v10/predictions.parquet')
    forecasts={r['row_id']:r for r in q.iter_rows(named=True)}
    checked_tables=0; checked_players=0; seen=set()
    for cell in d['cells']:
        y,k=cell['origin'],cell['fold']; model=read(ROOT/f'reports/generated/defense-repertoire-v9/model-{y}-{k}.json')
        train=[rows[rid] for rid in model['training_row_ids']]
        assert all(r['target_year']<=y for r in train)
        test=cell['players']; assert {r['player_id'] for r in train}.isdisjoint({r['player_id'] for r in test})
        tables={tuple(t['key']):t for t in model['tables']}
        for table in cell['tables']:
            key=tuple(table['key']); selected=[r for r in train if matches(r,key)]
            assert len({r['player_id'] for r in selected})==table['people']
            for part in table['regimes']:
                rs=[r for r in selected if (r['target_year']>=2022 or r['target_year']==2020)==(part['scope']=='both_leagues')]
                assert len(rs)==part['rows'] and len({r['player_id'] for r in rs})==part['people']
                assert sum(r['next_pa'] for r in rs)==part['PA'] and sum(r['actual_10'] for r in rs)==part['DH_starts']
                assert sorted({r['target_year'] for r in rs})==part['target_years']
            numerator=sum(r['actual_10'] for r in selected); den=sum(r['next_pa'] for r in selected)
            assert numerator==tables[key]['numerator_DH_starts'] and den==tables[key]['denominator_PA']
            if den: assert math.isclose(table['DH_starts_per_PA'],numerator/den,abs_tol=1e-12)
            else: assert table['DH_starts_per_PA'] is None and numerator==0
            checked_tables+=1
        for record in test:
            rid=record['row_id']; assert rid not in seen; seen.add(rid)
            r=rows[rid]; pred=forecasts[rid]; prior=tables[tuple(record['selected_prior'])]
            weight=r['pa_0']/(r['pa_0']+100.)
            own=pred['preseason_pa']*r['carry_10']/(r['pa_0']+100.)
            other=pred['preseason_pa']*(1-weight)*prior['DH_starts_per_PA']
            assert math.isclose(own,record['own_history_forecast_DH'],abs_tol=1e-9)
            assert math.isclose(other,record['prior_forecast_DH'],abs_tol=1e-9)
            assert math.isclose(own+other,pred['repair_10'],abs_tol=1e-9)
            assert record['reviewed_actual_DH']==r['actual_10']+dual[y+1,r['player_id']]
            delta=pred['preseason_pa']*dual[y,r['player_id']]/(r['pa_0']+100.)
            assert math.isclose(delta,record['own_source_only_DH_change'],abs_tol=1e-9)
            checked_players+=1
    assert seen==set(forecasts) and checked_players==12432
    for cohort in d['population']:
        y=cohort['origin']; g=q.filter(pl.col('origin_year')==y); ids=set(g['player_id'])
        for r in cohort['positions']:
            p=r['position']; col='fielding_outs' if p!=10 else 'games_started'
            for year,full_name,matched_name in [(y,'origin_full','origin_matched'),(y+1,'diagnostic_target_full','diagnostic_target_matched')]:
                s=mlb.filter((pl.col('season')==year)&(pl.col('position_code')==str(p)))
                alladd=sum(v for (yr,pid),v in dual.items() if yr==year) if p==10 else 0
                ownadd=sum(v for (yr,pid),v in dual.items() if yr==year and pid in ids) if p==10 else 0
                assert s[col].sum()+alladd==r[full_name]
                assert s.filter(pl.col('player_id').is_in(list(ids)))[col].sum()+ownadd==r[matched_name]
            assert math.isclose(g[f'repair_{p}'].sum(),r['forecast_repair'],abs_tol=1e-8)
            assert r['diagnostic_target_full']-r['diagnostic_target_matched']==r['diagnostic_target_remainder']
    result=dict(source_integrity='pass',captured_pitching_starts=len(jobs),certified_dual_starts=sum(len(v) for v in certified.values()),
        negative_control_pitching_starts=sum(len(raw_starts[k]) for k in raw_starts if not certified[k]),
        complete_reviewed_DH_seasons=[2022,2023,2024,2025],saved_prior_tables=checked_tables,
        forecast_DH_replays=checked_players,source_years=sorted(mlb['season'].unique().to_list()),
        no_new_fit=True,no_accuracy_claim=True,protected_outcomes_used=False,forecast_or_explorer_changed=False,
        hashes={str(OUT/'source-review.json'):sha256_file(OUT/'source-review.json'),str(Path(__file__)):sha256_file(Path(__file__))})
    for d in (OUT,PUBLIC): save(d/'independent-verification.json',result)
    protections();print(json.dumps({k:v for k,v in result.items() if k!='hashes'}),flush=True)


if __name__=='__main__': main()
