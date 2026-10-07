"""Source-only DH correction and physical job inventory; no fits or selection."""

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import json
import math

import polars as pl

from universal_baseball.defense_budget_source import dual_start, reviewed_dh_starts
from universal_baseball.defense_repertoire import group_matches, keys, supported
from universal_baseball.official_capture import capture_official_json
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/generated/defense-budget-v13'
PUBLIC = ROOT/'reports/model-evidence/defense-budget-v13'
SOURCE = ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet'
OLD = ROOT/'reports/generated/defense-repertoire-v9'
BRIDGE = ROOT/'reports/generated/defense-transition-v10/predictions.parquet'
CONTRACT = ROOT/'docs/defense-budget-v13-source-contract.md'


def read(p): return json.loads(p.read_text(encoding='utf8'))


def write(name, value):
    for d in (OUT, PUBLIC): save(d/name, value)


def candidates(source):
    m = source.filter(pl.col('is_mlb') & pl.col('season').is_between(2022,2025))
    p = m.filter(pl.col('position_code')=='1').group_by(['season','player_id']).agg(
        pl.col('games_started').sum().alias('pitching_starts'))
    dh = m.filter(pl.col('position_code')=='10').group_by(['season','player_id','player_name']).agg(
        pl.col('games_started').sum().alias('raw_dh_starts'),
        pl.col('games_played').sum().alias('dh_appearances'))
    return p.join(dh,on=['season','player_id']).filter(pl.col('pitching_starts')>0).sort(['season','player_id']).to_dicts()


def capture(endpoint, path):
    receipt = path.with_suffix('.capture.json')
    if path.exists():
        meta = read(receipt)
        assert meta['endpoint']==endpoint and sha256_file(path)==meta['sha256']
        return read(path)
    assert not receipt.exists()
    c = capture_official_json(endpoint)
    c.write_raw(path)
    save(receipt, dict(endpoint=endpoint,url=c.url,status_code=c.status_code,
                       retrieved_at_utc=c.retrieved_at_utc.isoformat(),sha256=c.content_sha256))
    return c.data


def log_starts(payload, season):
    groups = [s for s in payload['stats'] if s['group']['displayName']=='pitching']
    assert len(groups)==1 and groups[0]['type']['displayName']=='gameLog'
    rows = groups[0]['splits']
    assert all(int(r['season'])==season for r in rows)
    assert all('gamesStarted' in r['stat'] for r in rows)
    games = [dict(game_id=r['game']['gamePk'],date=r['date']) for r in rows if r['stat']['gamesStarted']==1]
    assert len({r['game_id'] for r in games})==len(games)
    return games


def acquire():
    protections(); OUT.mkdir(parents=True,exist_ok=True); PUBLIC.mkdir(parents=True,exist_ok=True)
    source = pl.read_parquet(SOURCE)
    selected = candidates(source)
    seal = dict(before_capture=True,new_fits=0,protected_outcomes_used=False,
                candidates=selected,source_sha256=sha256_file(SOURCE),
                contract_sha256=sha256_file(CONTRACT),runner_sha256=sha256_file(Path(__file__)),
                module_sha256=sha256_file(ROOT/'src/universal_baseball/defense_budget_source.py'))
    if (OUT/'capture-seal.json').exists():
        original=read(OUT/'capture-seal.json')
        if (OUT/'execution-amendment.json').exists():
            amendment=read(OUT/'execution-amendment.json')
            assert original['runner_sha256']==amendment['original_sha256']
            if (OUT/'rule-source-amendment.json').exists():
                rule=read(OUT/'rule-source-amendment.json')
                assert rule['previous_runner_sha256']==amendment['corrected_sha256']
                assert seal['runner_sha256']==rule['corrected_runner_sha256']
                original={**original,'module_sha256':seal['module_sha256']}
            else: assert seal['runner_sha256']==amendment['corrected_sha256']
            original={**original,'runner_sha256':seal['runner_sha256']}
        assert original==seal
    else: write('capture-seal.json',seal)
    jobs = []
    for c in selected:
        y,pid = c['season'],c['player_id']
        endpoint=f'people/{pid}/stats?stats=gameLog&group=pitching&season={y}&gameType=R&sportIds=1'
        games=log_starts(capture(endpoint,OUT/f'captures/log-{y}-{pid}.json'),y)
        assert len(games)==c['pitching_starts'],(c,len(games))
        jobs.extend(dict(**c,**g) for g in games)
    def one(r):
        capture(f"game/{r['game_id']}/boxscore",OUT/f"captures/box-{r['game_id']}.json")
        print(f"Captured {r['season']} player {r['player_id']} game {r['game_id']}.",flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(one,jobs))
    assert not (OUT/'captured-games.json').exists()
    write('captured-games.json',dict(games=jobs,requests=len(selected)+len(jobs),max_season=2025))
    protections()


def audit():
    protections(); assert not (OUT/'source-review.json').exists()
    seal=read(OUT/'capture-seal.json')
    assert seal['source_sha256']==sha256_file(SOURCE) and seal['contract_sha256']==sha256_file(CONTRACT)
    amendment=read(OUT/'execution-amendment.json') if (OUT/'execution-amendment.json').exists() else None
    if amendment:
        assert seal['runner_sha256']==amendment['original_sha256']
        assert sha256_file(Path(amendment['original_snapshot']))==amendment['original_sha256']
        if (OUT/'rule-source-amendment.json').exists():
            rule=read(OUT/'rule-source-amendment.json')
            assert rule['previous_runner_sha256']==amendment['corrected_sha256']
            assert sha256_file(Path(rule['previous_runner_snapshot']))==rule['previous_runner_sha256']
            assert sha256_file(Path(__file__))==rule['corrected_runner_sha256']
        else: assert sha256_file(Path(__file__))==amendment['corrected_sha256']
    else: assert seal['runner_sha256']==sha256_file(Path(__file__))
    if (OUT/'rule-source-amendment.json').exists():
        rule=read(OUT/'rule-source-amendment.json')
        assert seal['module_sha256']==rule['previous_module_sha256']
        assert sha256_file(Path(rule['previous_module_snapshot']))==rule['previous_module_sha256']
        assert sha256_file(ROOT/'src/universal_baseball/defense_budget_source.py')==rule['corrected_module_sha256']
    else: assert seal['module_sha256']==sha256_file(ROOT/'src/universal_baseball/defense_budget_source.py')
    source=pl.read_parquet(SOURCE); mlb=source.filter(pl.col('is_mlb'))
    captured=read(OUT/'captured-games.json')['games']; by_case=defaultdict(list)
    for r in captured:
        path=OUT/f"captures/box-{r['game_id']}.json"
        assert sha256_file(path)==read(path.with_suffix('.capture.json'))['sha256']
        detail=dual_start(read(path),r['player_id'],r['season'])
        detail['box_pitching_starts']=detail.pop('pitching_starts',None)
        result=dict(**r,**detail)
        by_case[r['season'],r['player_id']].append(result)
    corrections=[]
    for c in seal['candidates']:
        rs=by_case[c['season'],c['player_id']]
        assert len(rs)==c['pitching_starts']
        correction=reviewed_dh_starts(c['raw_dh_starts'],rs)
        corrections.append(dict(**c,**correction,game_evidence=rs))
    add={(r['season'],r['player_id']):r['certified_dual_starts'] for r in corrections}
    annual=[]; inventory=[]
    for y in sorted(mlb['season'].unique()):
        yr=mlb.filter(pl.col('season')==y)
        sums=[]
        for p in range(2,10):
            x=yr.filter(pl.col('position_code')==str(p))
            sums.append(dict(position=p,outs=x['fielding_outs'].sum(),starts=x['games_started'].sum()))
        assert len({r['outs'] for r in sums})==len({r['starts'] for r in sums})==1
        raw=yr.filter(pl.col('position_code')=='10')['games_started'].sum()
        added=sum(v for (year,pid),v in add.items() if year==y)
        inventory.append(dict(season=y,fielding=sums,raw_DH_starts=raw,certified_dual_DH_starts=added,
            reviewed_DH_starts=raw+added,fielding_team_games=sums[0]['starts'],
            raw_DH_slots_per_team_game=raw/sums[0]['starts'],
            reviewed_DH_slots_per_team_game=(raw+added)/sums[0]['starts'],
            universal_DH_season=y==2020 or y>=2022,short_MLB_season=y==2020))
        for (pid,),g in yr.filter(pl.col('position_code')=='10').group_by('player_id'):
            raw=g['games_started'].sum()
            annual.append(dict(season=y,player_id=pid,raw_DH_starts=raw,
                certified_dual_DH_starts=add.get((y,pid),0),reviewed_DH_starts=raw+add.get((y,pid),0)))
    pl.DataFrame(annual).write_parquet(OUT/'reviewed-DH-starts.parquet')
    q=pl.read_parquet(BRIDGE); features=pl.read_parquet(OLD/'features.parquet')
    assert q.height==12432 and q['target_year'].max()==2025
    cells=[]; paths=[SOURCE,BRIDGE,OLD/'features.parquet',CONTRACT,Path(__file__),
                    ROOT/'src/universal_baseball/defense_budget_source.py']
    for y in (2022,2023,2024):
        for fold in range(5):
            path=OLD/f'model-{y}-{fold}.json'; paths.append(path); m=read(path)
            tr=features.filter(pl.col('row_id').is_in(m['training_row_ids'])).to_dicts()
            test=q.filter((pl.col('origin_year')==y)&(pl.col('outer_fold')==fold)).to_dicts()
            assert max(r['target_year'] for r in tr)<=y
            assert {r['player_id'] for r in tr}.isdisjoint({r['player_id'] for r in test})
            table={(tuple(t['key'])):t for t in m['tables']}; table_regimes=[]
            for k,t in table.items():
                members=[r for r in tr if group_matches(r,k)]
                assert sum(r['next_pa'] for r in members)==t['denominator_PA']
                assert sum(r['actual_10'] for r in members)==t['numerator_DH_starts']
                assert sum(sum(r[f'actual_{p}'] for p in range(2,10)) for r in members)==t['numerator_outs']
                regime=[]
                for scope in ('one_league','both_leagues'):
                    selected=[r for r in members if ('both_leagues' if r['target_year']==2020 or r['target_year']>=2022 else 'one_league')==scope]
                    regime.append(dict(scope=scope,rows=len(selected),people=len({r['player_id'] for r in selected}),
                        target_years=sorted({r['target_year'] for r in selected}),
                        PA=sum(r['next_pa'] for r in selected),DH_starts=sum(r['actual_10'] for r in selected)))
                table_regimes.append(dict(key=list(k),regimes=regime,people=t['people'],DH_starts_per_PA=t['DH_starts_per_PA']))
            parts=[]
            for r in test:
                fr=features.filter(pl.col('row_id')==r['row_id']).row(0,named=True)
                t=next(table[k] for k in keys(fr) if supported(table[k])); a=fr['repertoire_weight']
                own=r['preseason_pa']*a*(r['carry_10']/r['pa_0'] if r['pa_0'] else 0.)
                prior=r['preseason_pa']*(1-a)*t['DH_starts_per_PA']
                assert math.isclose(own+prior,r['repair_10'],abs_tol=1e-9)
                parts.append(dict(row_id=r['row_id'],player_id=r['player_id'],origin=y,fold=fold,
                    expected_PA=r['preseason_pa'],current_MLB_PA=r['pa_0'],weight=a,
                    raw_current_DH_starts=r['carry_10'],certified_current_dual_DH_starts=add.get((y,r['player_id']),0),
                    selected_prior=list(t['key']),prior_people=t['people'],prior_DH_per_PA=t['DH_starts_per_PA'],
                    own_history_forecast_DH=own,prior_forecast_DH=prior,forecast_DH=own+prior,
                    raw_actual_DH=r['actual_10'],reviewed_actual_DH=r['actual_10']+add.get((y+1,r['player_id']),0),
                    own_source_only_DH_change=r['preseason_pa']*a*add.get((y,r['player_id']),0)/r['pa_0'] if r['pa_0'] else 0.,
                    qualification='Source sensitivity with unchanged prior, not a corrected refit or validated candidate.'))
            cells.append(dict(origin=y,fold=fold,training_rows=len(tr),training_people=len({r['player_id'] for r in tr}),
                max_target_year=max(r['target_year'] for r in tr),tables=table_regimes,
                own_history_DH=sum(r['own_history_forecast_DH'] for r in parts),
                prior_DH=sum(r['prior_forecast_DH'] for r in parts),players=parts))
    population=[]
    for y in (2022,2023,2024):
        ids=set(q.filter(pl.col('origin_year')==y)['player_id']); row=[]
        for p in range(2,11):
            units='outs' if p!=10 else 'starts'
            own=mlb.filter((pl.col('season')==y)&(pl.col('position_code')==str(p)))
            matched=own.filter(pl.col('player_id').is_in(list(ids)))
            later=mlb.filter((pl.col('season')==y+1)&(pl.col('position_code')==str(p)))
            lm=later.filter(pl.col('player_id').is_in(list(ids)))
            col='fielding_outs' if p!=10 else 'games_started'
            current_add=sum(v for (year,pid),v in add.items() if year==y) if p==10 else 0
            later_add=sum(v for (year,pid),v in add.items() if year==y+1) if p==10 else 0
            m_add=sum(v for (year,pid),v in add.items() if year==y and pid in ids) if p==10 else 0
            lm_add=sum(v for (year,pid),v in add.items() if year==y+1 and pid in ids) if p==10 else 0
            f=q.filter(pl.col('origin_year')==y)
            row.append(dict(position=p,units=units,origin_full=own[col].sum()+current_add,
                origin_matched=matched[col].sum()+m_add,forecast_repair=f[f'repair_{p}'].sum(),
                diagnostic_target_full=later[col].sum()+later_add,
                diagnostic_target_matched=lm[col].sum()+lm_add,
                diagnostic_target_remainder=later[col].sum()+later_add-lm[col].sum()-lm_add))
        population.append(dict(origin=y,rows=len(ids),positions=row,
            expected_PA=q.filter(pl.col('origin_year')==y)['preseason_pa'].sum(),
            unknown_role_outs=q.filter(pl.col('origin_year')==y)['repair_unallocated_outs'].sum(),
            origin_coverage_known=True,target_coverage_not_a_budget_input=True))
    paths.extend(sorted((OUT/'captures').glob('*.json')))
    paths.extend([OUT/'capture-seal.json',OUT/'captured-games.json'])
    if amendment: paths.extend([OUT/'execution-amendment.json',Path(amendment['original_snapshot'])])
    if (OUT/'rule-source-amendment.json').exists():
        rule=read(OUT/'rule-source-amendment.json')
        paths.extend([OUT/'rule-source-amendment.json',Path(rule['previous_runner_snapshot']),
                      Path(rule['previous_module_snapshot']),ROOT/'docs/defense-budget-v13-rule-source-amendment.md'])
    write('source-review.json',dict(status='source_audited_pending_independent_and_player_review',new_fits=0,
        corrections=corrections,inventory=inventory,cells=cells,population=population,
        preserved_position_outs=True,protected_outcomes_used=False,forecast_or_explorer_changed=False,
        hashes={str(p):sha256_file(p) for p in paths},
        output_hashes={str(OUT/'reviewed-DH-starts.parquet'):sha256_file(OUT/'reviewed-DH-starts.parquet')}))
    protections(); print('Job source and 15 saved conditional DH-prior cells audited.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('capture','audit'));a=p.parse_args()
    acquire() if a.action=='capture' else audit()
