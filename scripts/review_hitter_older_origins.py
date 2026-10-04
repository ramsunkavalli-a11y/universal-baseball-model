"""Recover missing static ages and walk older source players; no model fits."""
from __future__ import annotations

import argparse
from datetime import date
import gzip
import json
from pathlib import Path

import polars as pl
import requests

from audit_hitter_older_origins import ROOT, OLD, OUT, REPAIR, read, write, checked_receipt
from universal_baseball.storage import sha256_file

FIXED=[(545361,2009,'Mike Trout'),(547180,2010,'Bryce Harper'),
       (543333,2008,'Eric Hosmer'),(519058,2008,'Mike Moustakas'),
       (524968,2008,'Jesus Montero'),(474832,2010,'Brandon Belt'),
       (405395,2008,'Albert Pujols')]


def check_audit():
    report=read(OUT/'report.json')
    for path,digest in report['input_and_output_hashes'].items():
        assert sha256_file(Path(path))==digest,path
    return report


def birth_age(birth,origin):
    cutoff=date(origin,6,30)
    return cutoff.year-birth.year-((cutoff.month,cutoff.day)<(birth.month,birth.day))


def ages():
    check_audit()
    assert not (OUT/'age-receipt.json').exists(),'Preserve completed age correction'
    f=pl.read_parquet(OUT/'population.parquet')
    report_path=OLD/'player-demographics/report.json'
    demo_path=checked_receipt(read(report_path)['storage'])
    d=pl.read_parquet(demo_path).select('player_id','birth_date')
    g=f.join(d,on='player_id',how='left',validate='m:1')
    ids=sorted(g.filter(pl.col('age').is_null()&pl.col('birth_date').is_null())['player_id'].unique().to_list())
    captures=[];rows=[]
    for start in range(0,len(ids),100):
        batch=ids[start:start+100]
        params=dict(personIds=','.join(map(str,batch)),fields='people,id,fullName,birthDate')
        path=REPAIR/f'raw/birth-dates-{start//100:03}.json.gz'
        if not path.exists():
            response=requests.get('https://statsapi.mlb.com/api/v1/people',params=params,timeout=45)
            response.raise_for_status()
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(gzip.compress(json.dumps(response.json(),sort_keys=True).encode('utf8'),mtime=0))
        payload=json.loads(gzip.decompress(path.read_bytes()))
        assert set(payload)=={'people'}
        assert {int(s['id']) for s in payload['people']}==set(batch)
        for s in payload['people']:
            assert set(s)<= {'id','fullName','birthDate'},'Unexpected profile or outcome hydration'
            rows.append(dict(player_id=int(s['id']),birth_date=date.fromisoformat(s['birthDate']) if s.get('birthDate') else None,
                             player_name=s.get('fullName')))
        captures.append(dict(path=str(path),sha256=sha256_file(path),parameters=params,returned=len(payload['people'])))
    captured=pl.DataFrame(rows,schema={'player_id':pl.Int64,'birth_date':pl.Date,'player_name':pl.String})
    assert captured.unique('player_id').height==captured.height
    g=g.join(captured.rename({'birth_date':'captured_birth_date','player_name':'captured_name'}),on='player_id',how='left',validate='m:1')
    g=g.with_columns(pl.coalesce('birth_date','captured_birth_date').alias('birth_date'),pl.col('age').alias('reported_age'))
    resolved=[birth_age(s['birth_date'],s['origin_year']) if s['age'] is None and s['birth_date'] is not None else s['age'] for s in g.iter_rows(named=True)]
    g=g.with_columns(pl.Series('resolved_age',resolved,dtype=pl.Float64),
        pl.when(pl.col('reported_age').is_not_null()).then(pl.lit('season_reported'))
        .when(pl.col('captured_birth_date').is_not_null()).then(pl.lit('official_birth_date_capture'))
        .when(pl.col('birth_date').is_not_null()).then(pl.lit('cached_official_birth_date'))
        .otherwise(pl.lit('unknown')).alias('age_basis'))
    g.write_parquet(OUT/'population-with-ages.parquet')
    paths=[report_path,demo_path,Path(__file__),ROOT/'docs/hitter-older-origin-age-amendment.md',OUT/'population-with-ages.parquet']
    receipt=dict(original_missing_age_rows=f['age'].null_count(),missing_after=g['resolved_age'].null_count(),
        requested_identities=len(ids),age_bases=g.group_by('age_basis').len().to_dicts(),captures=captures,
        input_and_output_hashes={str(p):sha256_file(p) for p in paths},
        protected_outcomes_used=False,current_forecasts_changed=False)
    write(OUT/'age-receipt.json',receipt)
    print(json.dumps({k:receipt[k] for k in ['original_missing_age_rows','missing_after','requested_identities','age_bases']},indent=2))


def prepare():
    report=check_audit();age_receipt=read(OUT/'age-receipt.json')
    for path,digest in age_receipt['input_and_output_hashes'].items(): assert sha256_file(Path(path))==digest
    for capture in age_receipt['captures']: assert sha256_file(Path(capture['path']))==capture['sha256']
    f=pl.read_parquet(OUT/'population-with-ages.parquet');h=pl.read_parquet(OUT/'history.parquet')
    current_targets=pl.read_parquet(ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet')
    independent=f.join(current_targets.select((pl.col('season')-1).alias('origin_year'),'player_id',pl.col('mlb_pa').alias('independent_pa')),
        on=['origin_year','player_id'],how='left',validate='1:1').with_columns(pl.col('independent_pa').fill_null(0))
    assert independent['next_pa'].equals(independent['independent_pa'])
    roster_names={}
    for year in [2008,2009,2010]:
        roster=pl.read_parquet(OLD/f'opportunity-history-sources-pre2020/tables/{year}/full_roster_details.parquet')
        for s in roster.iter_rows(named=True): roster_names[(year,s['player_id'])]=s['player_name']
    info=[]
    for row in f.iter_rows(named=True):
        q=h.filter((pl.col('player_id')==row['player_id'])&(pl.col('season')==row['origin_year']))
        if len(q):
            dominant=q.sort(['plate_appearances','sport_id','team_id'],descending=[True,False,False]).row(0,named=True)
            level=dominant['sport_id'];league=dominant['league_id'];pa=q['plate_appearances'].sum();pos=dominant['position'];name=dominant['player_name']
        else:
            level=0;league=0;pa=0;pos='UNKNOWN';name=roster_names.get((row['origin_year'],row['player_id'])) or row['captured_name']
        info.append(dict(origin_year=row['origin_year'],player_id=row['player_id'],dominant_sport=level,dominant_league=league,
                         origin_pa=pa,source_position=pos,source_name=name))
    f=f.join(pl.DataFrame(info),on=['origin_year','player_id'],validate='1:1')
    fixed=[dict(player_id=pid,origin_year=y,expected_name=name,selection='fixed diagnostic') for pid,y,name in FIXED]
    ordinary=f.filter((pl.col('snapshot_level')=='INACTIVE')&pl.col('resolved_age').is_not_null()).sort('origin_year','player_id').head(1)
    assert len(ordinary)==1
    fixed.append(dict(player_id=ordinary['player_id'][0],origin_year=ordinary['origin_year'][0],expected_name=None,selection='First origin/player-ID inactive roster hitter with resolved age; no outcome selection'))
    # Ensure the repair itself is visible: choose the lowest-ID 2008 snapshot
    # hitter with 2006/07 A-minus exposure, without examining future outcomes.
    exposed=h.filter((pl.col('sport_id')==15)&pl.col('season').is_in([2006,2007]))['player_id'].unique()
    repaired=f.filter((pl.col('origin_year')==2008)&pl.col('player_id').is_in(exposed.implode())).sort('player_id').head(1)
    assert len(repaired)==1
    fixed.append(dict(player_id=repaired['player_id'][0],origin_year=2008,expected_name=None,selection='Lowest-ID eligible 2008 hitter with recovered 2006/07 A-minus exposure; no outcome selection'))
    cases=[]
    for selection in fixed:
        row=f.filter((pl.col('player_id')==selection['player_id'])&(pl.col('origin_year')==selection['origin_year'])).row(0,named=True)
        name=row['source_name'] or selection['expected_name']
        if selection['expected_name'] and row['source_name']: assert row['source_name']==selection['expected_name']
        # Do not use future-recorded versus no-recorded debut to match peers:
        # the three-way source category would reveal future arrival information.
        prior=row['debut_evidence']=='prior_debut'
        candidates=f.filter((pl.col('origin_year')==row['origin_year'])&(pl.col('dominant_sport')==row['dominant_sport'])&
            ((pl.col('debut_evidence')=='prior_debut')==prior)&(pl.col('player_id')!=row['player_id'])&pl.col('resolved_age').is_not_null())
        candidates=candidates.with_columns((abs(pl.col('resolved_age')-row['resolved_age'])+abs(pl.col('origin_pa')-row['origin_pa'])/300+
            pl.when(pl.col('source_position')!=row['source_position']).then(1.).otherwise(0.)).alias('distance'))
        peers=candidates.sort('distance','player_id').head(4)
        dated=h.filter((pl.col('player_id')==row['player_id'])&pl.col('season').is_between(row['origin_year']-2,row['origin_year'])).sort(KEYS)
        counts=dated.group_by('season').agg(pl.col('plate_appearances').sum(),pl.col('home_runs').sum(),pl.col('base_on_balls').sum(),pl.col('strike_outs').sum()).sort('season').to_dicts()
        cases.append(dict(selection=selection,origin={**row,'display_name':name},dated_stats=dated.to_dicts(),annual_stat_totals=counts,
            peers=peers.select('player_id','source_name','resolved_age','snapshot_level','dominant_sport','dominant_league','source_position','origin_pa','next_pa','debut_evidence').to_dicts(),
            history_scope='All three calendar predictor years 2006+ covered by cached source plus A-minus repair; absence means no observed affiliated counts, not healthy or no prior professional experience',
            peer_rule='Same origin, dominant sport and prior-debut state (unknown is not certified pre-MLB); nearest age/PA/position, then ID; no future success used',
            future_target='Following calendar year MLB PA; rate is unobserved if zero PA; no projection fitted'))
    write(OUT/'cases.json',cases)
    write(OUT/'review-preparation.json',dict(cases=len(cases),independently_checked_pa_labels=len(independent),player_walkthrough_status='pending',
        hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'cases.json',OUT/'report.json',OUT/'age-receipt.json',ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet']}))
    print(json.dumps([dict(name=c['origin']['display_name'],origin=c['origin']['origin_year'],age=c['origin']['resolved_age'],age_basis=c['origin']['age_basis'],stage=c['origin']['snapshot_level'],dominant=c['origin']['dominant_sport'],pa=c['origin']['origin_pa'],next_pa=c['origin']['next_pa'],peers=c['peers'],stats=c['annual_stat_totals']) for c in cases],indent=2,ensure_ascii=False,default=str))


KEYS=['season','sport_id','team_id']
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['ages','prepare']);args=parser.parse_args()
    ages() if args.action=='ages' else prepare()
