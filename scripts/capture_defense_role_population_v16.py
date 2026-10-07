"""Resume-safe historical population capture; no fitting or selection."""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import json

import polars as pl

from universal_baseball.official_capture import capture_official_json
from universal_baseball.defense_role_logs import parse_logs, position_totals
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/defense-role-v16'
PUBLIC=ROOT/'reports/model-evidence/defense-role-v16'
OLD=ROOT/'reports/generated/defense-jobs-v14'
PRIOR=ROOT/'reports/generated/defense-role-v15'
SOURCE=ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet'
CONTRACT=ROOT/'docs/defense-role-v16-source-contract.md'
SPORTS={'MLB':1,'AAA':11,'AA':12,'Aplus':13,'A':14,'Aminus':15,
        'COMPLEX':16,'DSL':16,'ROOKIE_COMBINED':16,'ADVANCED_ROOKIE':16}


def read(path):return json.loads(path.read_text(encoding='utf8'))


def write(name,value):
    for folder in (OUT,PUBLIC):save(folder/name,value)


def endpoint(ids,year,sport):
    assert 2021<=year<=2024 and len(ids)<=32 and len(set(ids))==len(ids)
    people=','.join(str(p) for p in ids)
    return f'people?personIds={people}&hydrate=stats(group=fielding,type=gameLog,season={year},gameType=R,sportId={sport})'


def capture(name,target):
    path=OUT/'captures'/(name+'.json');meta=path.with_suffix('.capture.json')
    if path.exists():
        m=read(meta);assert m['endpoint']==target and sha256_file(path)==m['sha256']
        return read(path)
    assert not meta.exists()
    c=capture_official_json(target);c.write_raw(path)
    save(meta,dict(endpoint=target,url=c.url,status_code=c.status_code,
                  retrieved_at_utc=c.retrieved_at_utc.isoformat(),sha256=c.content_sha256))
    return c.data


def check():
    for path,expected in read(OUT/'capture-seal.json')['hashes'].items():
        assert sha256_file(Path(path))==expected,path


def people_logs(data,ids,year,sport,source_id):
    people=data.get('people');assert isinstance(people,list)
    assert len(people)==len(ids) and {p['id'] for p in people}==set(ids),'Unexpected or missing people'
    result={}
    for person in people:
        result[person['id']]=parse_logs(dict(stats=person.get('stats',[])),player_id=person['id'],
            season=year,sport_id=sport,source_id=source_id)
    return result


def probe():
    protections();OUT.mkdir(parents=True,exist_ok=True);PUBLIC.mkdir(parents=True,exist_ok=True)
    seal=dict(before_capture=True,previous_goal_turn='progress: reviewed source milestone 99f9e059 committed and pushed',
        no_fits=True,max_season=2024,hashes={str(p):sha256_file(p) for p in
            [CONTRACT,Path(__file__),ROOT/'src/universal_baseball/defense_role_logs.py',
             OLD/'features.parquet',OLD/'predictions.parquet',SOURCE,PRIOR/'final-review.json']})
    if (OUT/'capture-seal.json').exists():assert read(OUT/'capture-seal.json')==seal
    else:write('capture-seal.json',seal)
    check();cases=[([660271,621439],2024,1),([805811,800060],2024,12)];reviews=[]
    for ids,y,sport in cases:
        name=f'probe-{y}-{sport}';data=capture(name,endpoint(ids,y,sport))
        rows=people_logs(data,ids,y,sport,str(OUT/'captures'/(name+'.json')))
        for pid in ids:
            old=PRIOR/'captures'/f'log-{y}-{pid}-sport-{sport}.json'
            assert sha256_file(old)==read(old.with_suffix('.capture.json'))['sha256']
            single=parse_logs(read(old),player_id=pid,season=y,sport_id=sport,source_id=str(old))
            fields=['player_id','season','sport_id','league_id','team_id','game_id','date','period',
                    'position_code','fielding_outs','appearances','raw_starts']
            values=lambda rs:sorted(tuple(r[k] for k in fields) for r in rs)
            assert rows[pid] and values(rows[pid])==values(single),pid
            reviews.append(dict(player_id=pid,season=y,sport_id=sport,position_games=len(single),
                source_position_totals=[dict(sport_id=k[0],league_id=k[1],position_code=k[2],**v)
                                       for k,v in sorted(position_totals(rows[pid]).items())]))
    if not (OUT/'probe-review.json').exists():
        write('probe-review.json',dict(batch_scope_integrity='pass',cases=reviews,
            no_fits=True,no_accuracy_claim=True,hashes={str(p):sha256_file(p) for p in
                sorted((OUT/'captures').glob('probe-*.json'))}))
    protections();print('Both batch probes exactly match all four certified single-person logs.',flush=True)


def prepare():
    protections();check();assert read(OUT/'probe-review.json')['batch_scope_integrity']=='pass'
    for path,expected in read(OUT/'probe-review.json')['hashes'].items():assert sha256_file(Path(path))==expected,path
    assert not (OUT/'manifest.json').exists()
    f=pl.read_parquet(OLD/'features.parquet').filter(pl.col('origin_year').is_between(2021,2024))
    assert f.height==16674 and f['row_id'].n_unique()==16674
    s=pl.read_parquet(SOURCE)
    original=defaultdict(list)
    for r in s.filter(pl.col('season').is_between(2021,2024)).to_dicts():
        original[r['player_id'],r['season']].append(r)
    groups=defaultdict(set);cases=[];unknown=[]
    for r in f.to_dicts():
        pid,y=r['player_id'],r['origin_year'];rows=original[pid,y]
        sports=sorted({SPORTS[a['normalized_level']] for a in rows})
        cases.append(dict(row_id=r['row_id'],player_id=pid,origin=y,fold=r['outer_fold'],
            player_name=r['player_name'],stage=r['stage'],source_position=r['source_position'],
            declared_sports=sports,annual_source_rows=len(rows)))
        if not sports:unknown.append(cases[-1])
        for sport in sports:groups[y,sport].add(pid)
    requests=[]
    for (y,sport),ids in sorted(groups.items()):
        ordered=sorted(ids)
        for start in range(0,len(ordered),32):
            batch=ordered[start:start+32]
            requests.append(dict(origin=y,sport_id=sport,player_ids=batch,
                endpoint=endpoint(batch,y,sport),capture_name=f'batch-{y}-{sport}-{start//32:04d}'))
    manifest=dict(before_population_capture=True,no_fits=True,case_rows=16674,evaluation_rows=12432,
        input_cases=cases,unknown_current_source=unknown,requests=requests,
        source_scopes=sum(len(r['declared_sports']) for r in cases),batch_limit=32,max_concurrency=3,
        historical_source_only=True,max_season=2024)
    write('manifest.json',manifest);protections()
    print(f"Population locked: {len(cases)} feature rows, {manifest['source_scopes']} player/sport scopes, "
          f"{len(requests)} batch requests, {len(unknown)} explicitly unknown current-source cases.",flush=True)


def acquire():
    protections();check();manifest=read(OUT/'manifest.json')
    # The frozen manifest may resume, but must never change after a partial capture.
    seal=dict(manifest_sha256=sha256_file(OUT/'manifest.json'),runner_sha256=sha256_file(Path(__file__)),
              source_scopes=manifest['source_scopes'],batch_requests=len(manifest['requests']))
    if (OUT/'population-capture-seal.json').exists():assert read(OUT/'population-capture-seal.json')==seal
    else:write('population-capture-seal.json',seal)
    def one(job):
        capture(job['capture_name'],job['endpoint'])
        print(job['capture_name'],len(job['player_ids']),flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(one,manifest['requests']))
    if not (OUT/'capture-complete.json').exists():
        paths=[OUT/'captures'/(job['capture_name']+'.json') for job in manifest['requests']]
        write('capture-complete.json',dict(all_manifest_requests_completed=True,
            requests=len(paths),exact_bytes=sum(p.stat().st_size for p in paths),
            hashes={str(p):sha256_file(p) for p in paths},no_fits=True,no_accuracy_claim=True))
    protections();print('All manifest captures saved; source certification is still required.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['probe','prepare','acquire'])
    globals()[parser.parse_args().mode]()
