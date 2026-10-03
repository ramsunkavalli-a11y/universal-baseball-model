"""Prepare a separately dated preseason rank overlay, without fitting forecasts."""
from pathlib import Path
from datetime import datetime, timezone
import json
import requests
import polars as pl
from universal_baseball.historical_prospect_rank import project, features
from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/hitter-preseason-readiness-v67'
OLD=ROOT/'reports/generated/practical-hitter-scouting-v47'
BASE=ROOT/'reports/generated/practical-hitter-numeric-repair-v53/features.parquet'
FIXED=[(701762,2024),(694671,2023),(641355,2016),(624413,2018),
       (666160,2016),(669394,2017),(806956,2024),(592450,2016)]

def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(n,o):(OUT/n).write_text(json.dumps(o,indent=2,ensure_ascii=False,allow_nan=False,default=str),encoding='utf8')

def capture_2025():
    p=OUT/'captures/mlb-top100-2025.html';url='https://www.mlb.com/prospects/2025/top100/'
    if p.exists():
        meta=read(p.with_suffix('.html.metadata.json'))
        assert meta['url']==url and sha256_file(p)==meta['sha256']
        return p,meta
    response=requests.get(url,timeout=45,headers={'User-Agent':'UBM historical preseason-source research'})
    response.raise_for_status();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(response.content)
    meta=dict(url=url,final_url=response.url,captured_utc=datetime.now(timezone.utc).isoformat(),sha256=sha256_file(p),bytes=p.stat().st_size)
    p.with_suffix('.html.metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
    return p,meta

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assert read(ROOT/'reports/generated/hitter-school-opportunity-v66/report.json')['player_walkthrough_status']=='complete'
    ranks=[];sources=[];hashes={str(BASE):sha256_file(BASE)}
    for y in range(2011,2026):
        p,meta=capture_2025() if y==2025 else (OLD/f'captures/mlb-top100-{y}.html',read(OLD/f'captures/mlb-top100-{y}.html.metadata.json'))
        assert meta['sha256']==sha256_file(p);hashes[str(p)]=meta['sha256']
        ranks.extend(project(p.read_text(encoding='utf8'),y,allow_2025=True));sources.append(dict(year=y,**meta))
    rank=pl.DataFrame(ranks);rank.write_parquet(OUT/'ranks.parquet')
    lookup={(r['season'],r['player_id']):r['rank'] for r in ranks}
    capacity={r['season']:r['list_capacity'] for r in ranks}
    f=pl.read_parquet(BASE).sort('row_id');scout=[n for n in f.columns if n.startswith('scout_')];assert len(scout)==12
    overlay=pl.DataFrame([dict(row_id=r['row_id'],**features(r['player_id'],r['origin_year']+1,lookup,capacity)) for r in f.iter_rows(named=True)],
        schema={'row_id':f.schema['row_id'],**{n:pl.Float64 for n in scout}})
    # Preserve V53's explicit unknown sentinel; do not also change missing-value
    # representation while testing which ranking vintage enters the forecast.
    overlay=overlay.with_columns(pl.col(scout).fill_null(-1.))
    new=f.drop(scout).join(overlay,on='row_id',how='left',validate='1:1').select(f.columns)
    assert len(new)==len(f)==63282 and new.drop(scout).equals(f.drop(scout))
    assert new.select(scout).null_count().to_numpy().sum()==0
    new.write_parquet(OUT/'features.parquet')
    cases=read(ROOT/'reports/generated/hitter-school-opportunity-v66/cases.json');bykey={(c['origin']['player_id'],c['origin']['origin_year']):c for c in cases}
    out=[]
    for pid,y in FIXED:
        c=bykey[pid,y];a=f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y));b=new.filter(pl.col('row_id')==a['row_id'][0])
        peerkeys=[(p['player_id'],y) for p in c['peers']]
        out.append(dict(player_id=pid,origin_year=y,player_name=c['origin']['player_name'],source_history=c['source_history'],
            baseline_forecast={k:c['origin'][k] for k in ['baseline_p','baseline_conditional_pa','baseline_pa','baseline_rate','on_40man']},
            old_scouting=a.select(scout).to_dicts()[0],preseason_scouting=b.select(scout).to_dicts()[0],
            old_rank=lookup.get((y,pid)),preseason_rank=lookup.get((y+1,pid)),preseason_list_year=y+1,
            peers=[dict(player_id=p,origin_year=t,player_name=next(v['player_name'] for v in c['peers'] if v['player_id']==p),
                old_rank=lookup.get((t,p)),preseason_rank=lookup.get((t+1,p))) for p,t in peerkeys]))
    write('source-cases.json',out)
    q=f.select('row_id','origin_year','player_id','stage','draft_year','pick_number','scout_listed_0').join(
        new.select('row_id',pl.col('scout_listed_0').alias('preseason_listed')),on='row_id',validate='1:1')
    groups=q.group_by('origin_year','stage').agg(pl.len().alias('rows'),
        ((pl.col('scout_listed_0')==0)&(pl.col('preseason_listed')==1)).sum().alias('newly_listed'),
        ((pl.col('scout_listed_0')==-1)&(pl.col('preseason_listed')==1)).sum().alias('previously_unknown_now_listed'),
        ((pl.col('scout_listed_0')==1)&(pl.col('preseason_listed')==0)).sum().alias('no_longer_listed'),
        (pl.col('preseason_listed')==-1).sum().alias('unknown_preseason_absence')).sort('origin_year','stage').to_dicts()
    outside=rank.rename({'season':'target_year'}).join(f.select('player_id','target_year'),on=['player_id','target_year'],how='anti')
    outside=outside.filter(pl.col('target_year').is_in(f['target_year'].unique().implode()))
    outside.write_parquet(OUT/'ranked-outside-source.parquet')
    write('source-report.json',dict(rows=len(f),scouting_columns=scout,input_hashes=hashes,sources=sources,groups=groups,
        source_review_status='pending',release_date_review_status='pending',outside_membership_rows=len(outside),
        retrospective_tables=True,non_scouting_fields_unchanged=True,fitted=False,protected_outcomes_used=False,
        information_cutoff='Coming-season preseason rankings; other inputs through prior December; not a December forecast',
        output_hashes={str(p):sha256_file(p) for p in [OUT/'features.parquet',OUT/'ranks.parquet',OUT/'source-cases.json',OUT/'ranked-outside-source.parquet']}))
    for c in out:print(c['player_name'],c['origin_year'],'old rank',c['old_rank'],'preseason',c['preseason_rank'],flush=True)
    print('Source overlay prepared; publication/source review required before fits.',flush=True)

if __name__=='__main__':main()
