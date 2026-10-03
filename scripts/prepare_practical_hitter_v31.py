"""Rebuild broad cutoff-known source features, without fitting models."""
import gzip
import json
from pathlib import Path
import numpy as np
import polars as pl
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.forecast_validation import preflight
from universal_baseball.practical_hitter_v30 import EVENTS
from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/practical-hitter-v31'
OLD=Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated')
RAW=ROOT/'model_artifacts/prospect-destination-v3-source-repaired/repaired_hitting_components.parquet'
BUCKETS=['MLB','AAA','AA','Aplus','A','Aminus','DSL','RK120','RK121','RK124','RK128','RK134','RKother','MEX']
POS=[str(i) for i in range(1,11)]+['Y','UNKNOWN']
YEARS=[2016,2017,2018,2021,2022,2023,2024]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(n,o):(OUT/n).write_text(json.dumps(o,indent=2,allow_nan=False,default=str),encoding='utf8')
def bucket(s):
    if s['league_id']==125:return 'MEX'
    if s['sport_id']==1:return 'MLB'
    if s['league_id']==130:return 'DSL'
    if s['sport_id'] in [11,12,13,14,15]:return {11:'AAA',12:'AA',13:'Aplus',14:'A',15:'Aminus'}[s['sport_id']]
    if s['league_id'] in [120,121,124,128,134]:return 'RK'+str(s['league_id'])
    return 'RKother'

def source():
    manifest=read(ROOT/'model_artifacts/prospect-destination-v3-source-repaired/source_manifest.json')
    paths=sorted({Path(s['path']) for s in manifest['sources'] if Path(s['path']).name.startswith('hitting-offset-') or
        ('advanced-rookie-repair-v3' in s['path'] and Path(s['path']).name=='hitting.json.gz')})
    rows=[];hashes={str(RAW):sha256_file(RAW)}
    for path in paths:
        hashes[str(path)]=sha256_file(path)
        with gzip.open(path,'rt',encoding='utf8') as stream:payload=json.load(stream)
        for stat in payload['stats']:
            for s in stat['splits']:
                y=int(s['season']);assert 2008<=y<=2025
                rows.append(dict(season=y,player_id=int(s['player']['id']),sport_id=int(s['sport']['id']),team_id=int(s['team']['id']),
                    league_id=int(s['league']['id']),position=str(s.get('position',{}).get('code') or 'UNKNOWN'),
                    metadata_pa=int(s['stat'].get('plateAppearances') or 0)))
    meta=pl.DataFrame(rows).unique();keys=['season','player_id','sport_id','team_id']
    assert meta.unique(keys).height==meta.height,'Conflicting dated metadata'
    raw=pl.read_parquet(RAW)
    assert raw.unique(keys).height==raw.height
    f=raw.join(meta,on=keys,how='left',validate='1:1')
    assert f['metadata_pa'].null_count()==0 and f['metadata_pa'].equals(f['plate_appearances'])
    f=f.with_columns(pl.Series('bucket',[bucket(s) for s in f.iter_rows(named=True)]),
        (pl.col('hits')-pl.col('home_runs')-pl.col('doubles')-pl.col('triples')).alias('singles'),
        (pl.col('base_on_balls')-pl.col('intentional_walks')).alias('unintentional_walks'),
        (pl.col('hits')-pl.col('home_runs')).alias('babip_hits'),
        (pl.col('at_bats')-pl.col('strike_outs')-pl.col('home_runs')+pl.col('sac_flies')).alias('babip_opportunities'))
    assert f.filter(pl.any_horizontal(pl.col('plate_appearances','singles','unintentional_walks','babip_hits','babip_opportunities')<0)).is_empty()
    assert f.filter(pl.sum_horizontal('strike_outs','unintentional_walks','hit_by_pitch','singles','doubles','triples','home_runs')>pl.col('plate_appearances')).is_empty()
    assert f.filter((pl.col('season')==2020)&(pl.col('bucket')!='MLB')).is_empty()
    f.write_parquet(OUT/'dated-stints.parquet')
    countcols=list(dict.fromkeys(['plate_appearances',*[v[0] for v in EVENTS.values()],*[v[1] for v in EVENTS.values()]]))
    counts=f.group_by('season','player_id','bucket').agg(pl.col(countcols).sum())
    counts.write_parquet(OUT/'counts.parquet')
    return f,counts,hashes

def materialize(stints,counts):
    frames=[pl.read_parquet(ROOT/f'model_artifacts/advanced-rookie-repair-v3/{y}/hitter_snapshots.parquet') for y in range(2011,2020)]
    frames.append(pl.scan_parquet(OLD/'opportunity-history-sources-v2/tables/hitter_snapshots.parquet').filter(pl.col('snapshot_year').is_between(2021,2024)).collect())
    snaps=pl.concat(frames).rename({'snapshot_year':'origin_year','age_years':'age'})
    assert snaps.unique(['origin_year','player_id']).height==snaps.height
    back=pl.scan_parquet(ROOT/'model_artifacts/post-arrival-support-v17/panel.parquet').filter(pl.col('window_complete')).select('origin_year','player_id','age').collect()
    extra=back.join(snaps.select('origin_year','player_id'),on=['origin_year','player_id'],how='anti').with_columns(pl.lit('INACTIVE').alias('as_of_level_group'))
    snaps=pl.concat([snaps,extra.select(snaps.columns)],how='vertical_relaxed').sort('origin_year','player_id')
    targets=pl.read_parquet(ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet')
    assert set(targets['season'])==set(range(2009,2026))
    mlb=counts.filter(pl.col('bucket')=='MLB').select('season','player_id','plate_appearances')
    q=targets.join(mlb,on=['season','player_id'],validate='1:1')
    assert len(q)==len(targets) and q['mlb_pa'].equals(q['plate_appearances'])
    env={s['season']:(s['schedule_fraction'],570*s['schedule_fraction']/s['league_pa']) for s in targets.unique('season').iter_rows(named=True)}
    env[2008]=(1,570/mlb.filter(pl.col('season')==2008)['plate_appearances'].sum())
    values={(s['season'],s['player_id']):s for s in targets.iter_rows(named=True)}
    lookup={(s['season'],s['player_id'],s['bucket']):s for s in counts.iter_rows(named=True)}
    ann=stints.filter(pl.col('plate_appearances')>0).group_by('season','player_id').agg(pl.col('reported_age').drop_nulls().median().alias('reported_age'))
    primary=stints.filter(pl.col('plate_appearances')>0).sort(['season','player_id','plate_appearances','team_id'],descending=[False,False,True,False]).unique(['season','player_id'],keep='first')
    metadata=primary.join(ann,on=['season','player_id'],validate='1:1',suffix='_annual').sort('season')
    debuts={s['player_id']:s['mlb_debut_date'].year for s in pl.read_parquet(ROOT/'reports/generated/hitter-arrival-source-repair-v1/debut-dates.parquet').iter_rows(named=True)}
    roster=pl.read_parquet(ROOT/'reports/generated/hitter-arrival-source-repair-v1/year-end-rosters.parquet')
    assert roster.unique(['season','player_id']).height==roster.height
    listing={(s['season'],s['player_id']):s['team_id'] for s in roster.iter_rows(named=True)}
    histories={}
    for s in metadata.iter_rows(named=True):histories.setdefault(s['player_id'],[]).append(s)
    rows=[]
    for idx,s in enumerate(snaps.iter_rows(named=True)):
        y,pid=s['origin_year'],s['player_id'];past=[v for v in histories.get(pid,[]) if v['season']<=y];last=past[-1] if past else None
        age=s['age'];fallback=False
        if age is None and last and last['reported_age_annual'] is not None:age=last['reported_age_annual']+y-last['season']
        if age is None:age=27.;fallback=True
        d=debuts.get(pid);elapsed=y-d if d is not None and d<=y else -1
        row=dict(row_id=idx,origin_year=y,target_year=y+1,horizon=1,player_id=pid,outer_fold=player_fold(pid),age=float(age),
            age_unknown=int(fallback),age_centered=(age-27)/5,age_squared=((age-27)/5)**2,
            elapsed=elapsed,elapsed_scaled=max(-1,elapsed)/10,prior_debut=int(elapsed>=0),window_complete=True,
            player_name=last['player_name'] if last else None,team_id=listing.get((y,pid),last['team_id'] if last else None),
            on_40man=int((y,pid) in listing),reorganized=int(y>=2021),last_stat_gap=min(5,y-last['season']) if last else 5,
            source_position=last['position'] if last else 'UNKNOWN',snapshot_level=s['as_of_level_group'])
        for pos in POS:row['position_'+pos]=int(row['source_position']==pos)
        total_mlb=0;regular=0;absence=0
        for lag in range(3):
            year=y-lag;row['milb_canceled_'+str(lag)]=int(year==2020)
            allpa=0;mpa=0
            for b in BUCKETS:
                c=lookup.get((year,pid,b));pa=c['plate_appearances'] if c else 0;allpa+=pa
                key=f'{b}_{lag}_';row[key+'pa']=float(pa);row[key+'present']=int(pa>0)
                for e,(num,den,prior) in EVENTS.items():row[key+e]=((c[num] if c else 0)+100*prior)/((c[den] if c else 0)+100)
                if b=='MLB':mpa=pa
            row[f'pa_{lag}']=mpa;row[f'work_{lag}']=mpa/env[year][0];row[f'minor_pa_{lag}']=allpa-mpa
            target=values.get((year,pid));v=target['component_war'] if target else 0
            # 2008 has no certified value target: preserve unknown quality.
            assert year>=2009
            row[f'quality_{lag}']=600*(v-env[year][1]*mpa)/(mpa+1200)
            row[f'quality_present_{lag}']=int(mpa>0);regular+=row[f'work_{lag}']>=400;absence+=mpa==0;total_mlb+=mpa
        row['regular_window']=int(regular);row['regular_window_scaled']=regular/3;row['absence_window_scaled']=absence/3
        row['current_state']=0 if row['pa_0']==0 else 1 if row['pa_0']<200 else 2 if row['pa_0']<400 else 3
        row['stage']='Current MLB' if row['pa_0']>0 else 'Upper minors' if row['AAA_0_pa']+row['AA_0_pa']>0 else 'Lower minors' if row['minor_pa_0']>0 else 'Inactive / unknown'
        row['origin_replacement_rate']=env[y][1]/env[y][0]
        row['career_mlb_observed_pa']=sum(v['plate_appearances'] for v in past if v['sport_id']==1)
        row['career_mlb_left_truncated']=int(d is not None and d<2008)
        nxt=values.get((y+1,pid));pa=nxt['mlb_pa'] if nxt else 0;v=nxt['component_war'] if nxt else 0
        row['next_pa']=pa;row['next_value']=v;row['next_state']=0 if pa==0 else 1 if pa<200 else 2 if pa<400 else 3
        row['next_batting_rate']=600*(v-env[y+1][1]*pa)/pa if pa else 0.
        row['hard_unavailable']=False;row['needs_availability_scenario']=False
        rows.append(row)
    f=pl.DataFrame(rows)
    status=pl.read_parquet(ROOT/'reports/generated/availability-context-v29b/predictions.parquet').select('origin_year','player_id',
        pl.col('hard_unavailable').alias('_hard'),pl.col('needs_availability_scenario').alias('_scenario'))
    f=f.join(status,on=['origin_year','player_id'],how='left',validate='1:1').with_columns(pl.col('_hard').fill_null(False).alias('hard_unavailable'),
        pl.col('_scenario').fill_null(False).alias('needs_availability_scenario')).drop('_hard','_scenario')
    base=['age_centered','age_squared','age_unknown','elapsed_scaled','prior_debut','on_40man','reorganized','last_stat_gap','career_mlb_observed_pa','career_mlb_left_truncated',
        'regular_window_scaled','absence_window_scaled',*[f'position_{p}' for p in POS],*[f'milb_canceled_{k}' for k in range(3)],
        *[f'{b}_{k}_pa' for b in BUCKETS for k in range(3)],*[f'{v}_{k}' for k in range(3) for v in ['work','quality','quality_present']]]
    detail=base+ [f'{b}_{k}_{v}' for b in BUCKETS for k in range(3) for v in ['present',*EVENTS]]
    assert np.isfinite(f.select(detail).to_numpy()).all()
    return f,base,detail,dict(extra_exit_rows=len(extra),reconciled_mlb_targets=len(q),raw_source_seasons=sorted(counts['season'].unique()))

def main():
    OUT.mkdir(exist_ok=True);assert not (OUT/'preflight.json').exists()
    assert read(ROOT/'reports/generated/practical-hitter-v30b/report.json')['player_walkthrough_status']=='complete'
    stints,counts,hashes=source();print(f'Dated metadata reconciled: {len(stints)} stints',flush=True)
    f,base,detail,note=materialize(stints,counts);f.write_parquet(OUT/'features.parquet')
    cells=[];support=[]
    for y in YEARS:
        for k in range(5):
            tr=f.filter((pl.col('target_year')<=y)&(pl.col('target_year')!=2020)&(pl.col('outer_fold')!=k));te=f.filter((pl.col('origin_year')==y)&(pl.col('outer_fold')==k))
            sup,c=preflight(tr,te,cutoff=y,fold=k,features=detail,expected_keys=te.select('row_id','horizon').iter_rows())
            # Add stage-by-age support and missing/new-regime diagnostics.
            keys=['stage','prior_debut'];cnt=tr.group_by(keys).agg(pl.col('player_id').n_unique().alias('stage_debut_players'))
            sup=sup.join(te.select('row_id',*keys),on='row_id',validate='1:1').join(cnt,on=keys,how='left',validate='m:1').with_columns(pl.col('stage_debut_players').fill_null(0))
            support.append(sup);cells.append(dict(year=y,fold=k,**c,stage_debut_sparse=int((sup['stage_debut_players']<20).sum()),
                training_row_ids=tr['row_id'].to_list(),test_row_ids=te['row_id'].to_list()))
    pl.concat(support).write_parquet(OUT/'support.parquet')
    old=pl.read_parquet(ROOT/'reports/generated/opportunity-shrinkage-v24/predictions.parquet')
    match=old.select('origin_year','player_id','next_pa','next_value').join(f.select('origin_year','player_id',pl.col('next_pa').alias('_pa'),pl.col('next_value').alias('_value')),on=['origin_year','player_id'],validate='1:1')
    assert len(match)==len(old) and match['next_pa'].equals(match['_pa']) and match['next_value'].equals(match['_value'])
    coverage=[];targets=pl.read_parquet(ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet')
    for y in YEARS:
        g=f.filter(pl.col('origin_year')==y);outside=targets.filter(pl.col('season')==y+1).join(g.select('player_id'),on='player_id',how='anti')
        coverage.append(dict(origin_year=y,rows=len(g),mlb_pa_in_cohort=int(g['next_pa'].sum()),mlb_pa_outside=int(outside['mlb_pa'].sum()),
            value_in_cohort=float(g['next_value'].sum()),value_outside=float(outside['component_war'].sum()),age_unknown=int(g['age_unknown'].sum())))
    for path in [ROOT/'docs/practical-hitter-v31-contract.md',Path(__file__),ROOT/'reports/generated/practical-hitter-v30b/report.json',
        ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet',ROOT/'reports/generated/hitter-arrival-source-repair-v1/debut-dates.parquet',
        ROOT/'reports/generated/hitter-arrival-source-repair-v1/year-end-rosters.parquet',ROOT/'reports/generated/opportunity-shrinkage-v24/predictions.parquet',
        ROOT/'reports/generated/public-benchmark-v2/matched-public.parquet',OUT/'features.parquet',OUT/'dated-stints.parquet',OUT/'counts.parquet',OUT/'support.parquet',
        ROOT/'reports/generated/availability-context-v29b/predictions.parquet',*[ROOT/f'model_artifacts/advanced-rookie-repair-v3/{y}/hitter_snapshots.parquet' for y in range(2011,2020)],
        OLD/'opportunity-history-sources-v2/tables/hitter_snapshots.parquet',ROOT/'model_artifacts/post-arrival-support-v17/panel.parquet']:
        hashes[str(path)]=sha256_file(path)
    write('preflight.json',dict(input_hashes=hashes,before_fitting=True,base_features=base,detail_features=detail,cells=cells,
        coverage=coverage,source_checks=note,all_old_rows_retained=len(match),source_rows=len(f),protected_outcomes_used=False))
    print(json.dumps(dict(source_rows=len(f),base_features=len(base),detail_features=len(detail),coverage=coverage,source_checks=note),indent=2))

if __name__=='__main__':main()
