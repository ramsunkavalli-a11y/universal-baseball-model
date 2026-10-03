"""Audit historical rank coverage and source cases before any predictive fit."""
from pathlib import Path
from collections import Counter
import csv
import json
import polars as pl
from universal_baseball.historical_prospect_rank import project, features
from universal_baseball.storage import sha256_file
from inspect_historical_scouting_v47 import InitialState

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/practical-hitter-scouting-v47'
FIXED=[(592450,2016),(641355,2016),(683011,2022),(701762,2024),(808393,2024),
       (621446,2016),(640449,2016),(666160,2016),(608369,2016)]


def write(name, obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False,default=str),encoding='utf8')


def main():
    rows=[]; sources=[]; coverage={}; entities={}; issues=[]; year_sources={}
    for year in range(2011,2025):
        p=OUT/f'captures/mlb-top100-{year}.html'; metadata=json.loads(p.with_suffix('.html.metadata.json').read_text(encoding='utf8'))
        assert sha256_file(p)==metadata['sha256']
        year_sources[year]=metadata
        html=p.read_text(encoding='utf8')
        parsed=project(html,year)
        if not parsed[0]['list_complete']:
            issues.append(dict(year=year,reason='Only ranks 1–99 returned',policy='Positive ranks usable; absent players have unknown listed/score inputs, not unranked zero',source=metadata))
        rows.extend(parsed)
        coverage[year]=len(parsed);sources.append(metadata)
        parser=InitialState();parser.feed(html);state=parser.states[0]
        key=f'getPlayerRankingsFromSelection({{"limit":100,"slug":"sel-pr-{year}-top100"}})'
        for item in state['payload']['ROOT_QUERY'][key]:
            entity=item['playerEntity'];pid=int(entity['player']['__ref'][7:]);entities[year,pid]=entity
    ranks=pl.DataFrame(rows);ranks.write_parquet(OUT/'ranks.parquet')
    lookup={(r['season'],r['player_id']):r['rank'] for r in rows}
    counts=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet')
    panel=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v38/features.parquet')
    dataset=list(csv.DictReader((OUT/'captures/twtc.csv').open(encoding='utf-8-sig')))
    sourcecases=[]
    for pid,year in FIXED:
        q=panel.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==year));assert len(q)==1,(pid,year,len(q))
        origin=q.select('row_id','player_id','player_name','origin_year','target_year','age','stage','prior_debut','pa_0','minor_pa_0').to_dicts()[0]
        history=counts.filter((pl.col('player_id')==pid)&pl.col('season').is_between(year-2,year)).select('season','bucket','plate_appearances','home_runs','strike_outs','unintentional_walks').sort('season','bucket').to_dicts()
        e=entities.get((year,pid)); reports=[]
        if e:
            reports=[dict(title=b['contentTitle'],matches_origin=str(year)==b['contentTitle']) for b in e['prospectBio']]
        dataset_matches=[{k:r[k] for k in ['name','key_mlbam','year','source','eta','Hit','Power']} for r in dataset if r['key_mlbam']==str(pid) and int(r['year'])<=year]
        sourcecases.append(dict(origin=origin,inputs=features(pid,year,lookup,coverage),source_history=history,
            current_list_rank=lookup.get((year,pid)),list_source=year_sources[year],
            report_titles_not_predictors=reports,dataset_records_not_predictors=dataset_matches,
            publisher_eta_not_predictor=None if not e else e.get('eta')))
    write('source-cases.json',sourcecases)
    valid=[r for r in dataset if r['key_mlbam'].isdigit() and int(r['key_mlbam'])>0]
    groups=Counter((r['key_mlbam'],r['year'],r['source']) for r in valid)
    conflicts=[]
    for key,n in groups.items():
        if n>1:
            rs=[r for r in valid if (r['key_mlbam'],r['year'],r['source'])==key]
            if len({(r['eta'],r['Hit'],r['Power']) for r in rs})>1:conflicts.append(key)
    manifest=dict(observed_lists=coverage,complete_lists={y:n for y,n in coverage.items() if n in [50,100]},ranking_rows=len(rows),ranking_sha256=sha256_file(OUT/'ranks.parquet'),sources=sources,issues=issues,
        accepted_fields=['report season','MLBAM identity','rank','complete list capacity'],
        withheld_fields=['current team','current level','current age','listed position','ETA','grades','scouting text','TWTC outcome labels'],
        retrospective_not_archived_publication_capture=True,source_review_status='pending',fitted=False,
        twtc_rows=len(dataset),valid_numeric_id_rows=len(valid),duplicate_id_year_source_groups=sum(n>1 for n in groups.values()),
        discordant_grade_or_eta_groups=len(conflicts),protected_2026_outcomes_used=False)
    write('source-audit.json',manifest)
    print(json.dumps({k:v for k,v in manifest.items() if k not in ['sources']},indent=2))
    print(json.dumps([dict(name=c['origin']['player_name'],year=c['origin']['origin_year'],rank=c['current_list_rank'],
        source_history=[h for h in c['source_history'] if h['season']==c['origin']['origin_year']]) for c in sourcecases],indent=2))


if __name__=='__main__':main()
