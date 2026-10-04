"""Compare mature calendar follow-up and actual-fold talent support; no fits."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from universal_baseball.hitter_followup import annual_followup, support_membership
from universal_baseball.storage import sha256_file
from audit_hitter_rate_support import tagged
import evaluate_hitter_preseason_readiness_v68 as current

ROOT=current.ROOT
OUT=ROOT/'reports/generated/hitter-followup-support'
FIXED=[(600524,2011,'Renato Núñez'),(600869,2011,'Jeimer Candelario'),
       (624641,2013,'Edmundo Sosa'),(642423,2013,'Magneuris Sierra'),
       (646240,2014,'Rafael Devers'),(660670,2015,'Ronald Acuña Jr.'),
       (670867,2017,'Kevin Maitan'),(624413,2018,'Pete Alonso'),
       (592450,2024,'Aaron Judge'),(701762,2024,'Nick Kurtz'),(821181,2024,'Juneiker Caceres')]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def write(name, obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf8')


def counts_for(train, test, keys, prefix):
    counts=train.filter(pl.col('mlb_pa')>0).group_by(keys).agg(
        pl.col('player_id').n_unique().alias(prefix+'_people'),pl.len().alias(prefix+'_observations'),
        pl.col('mlb_pa').sum().alias(prefix+'_pa'))
    return test.select('row_id',*keys).join(counts,on=keys,how='left',validate='m:1').select(
        'row_id',pl.col(prefix+'_people',prefix+'_observations',prefix+'_pa').fill_null(0))


def case(frame, annual, stints, predictions, support, row):
    candidates=frame.filter((pl.col('origin_year')==row['origin_year'])&
        (pl.col('dominant_level')==row['dominant_level'])&(pl.col('audit_age_band')==row['audit_age_band'])&
        (pl.col('prior_debut')==row['prior_debut'])&(pl.col('player_id')!=row['player_id']))
    candidates=candidates.with_columns((abs(pl.col('age')-row['age'])+
        abs(pl.col('minor_pa_0')-row['minor_pa_0'])/300+
        abs(pl.col('pa_0')-row['pa_0'])/300+
        pl.when(pl.col('source_position')!=row['source_position']).then(1.).otherwise(0.)+
        abs(pl.col('scout_rank_score_0')-row['scout_rank_score_0'])).alias('peer_distance'))
    peers=candidates.sort('peer_distance','player_id').head(4)
    ids=[row['player_id'],*peers['player_id'].to_list()]
    paths=[]
    for pid in ids:
        origin=frame.filter((pl.col('origin_year')==row['origin_year'])&(pl.col('player_id')==pid)).row(0,named=True)
        paths.append(dict(player_id=pid,player_name=origin['player_name'],age=origin['age'],position=origin['source_position'],
            dominant_level=origin['dominant_level'],minor_pa=origin['minor_pa_0'],mlb_pa=origin['pa_0'],
            rank_score=origin['scout_rank_score_0'],annual_outcomes=annual.filter(pl.col('row_id')==origin['row_id']).to_dicts()))
    saved=predictions.filter(pl.col('row_id')==row['row_id'])
    stats=stints.filter((pl.col('player_id')==row['player_id'])&
        pl.col('season').is_between(row['origin_year']-2,row['origin_year'])).sort('season','bucket','team_id')
    return dict(origin={k:row[k] for k in ['row_id','player_id','player_name','origin_year','outer_fold','age','age_unknown',
        'source_position','dominant_level','audit_age_band','prior_debut','rank_band','new_draftee','thin_pro',
        'minor_pa_0','pa_0','scout_listed_0','scout_rank_score_0','on_40man','milb_canceled_0']},
        dated_stats=stats.to_dicts(),annual_paths=paths,
        support=support.filter(pl.col('row_id')==row['row_id']).to_dicts(),
        current_forecast=saved.select('preseason_p','preseason_conditional_pa','preseason_pa','baseline_rate','preseason_value','next_pa').to_dicts(),
        peer_selection='Same origin, dominant level, age band, debut; nearest age/PA/position/rank with player-ID tie break; no future outcomes',
        unknown_followup_years=annual.filter((pl.col('row_id')==row['row_id'])&~pl.col('observed'))['followup_year'].to_list())


def main():
    assert not (OUT/'report.json').exists(),'Preserve completed audit'
    previous=read(ROOT/'reports/generated/hitter-rate-support-audit/final-report.json')
    assert previous['player_walkthrough_status']=='complete'
    for group in ['source_and_execution_hashes','review_hashes']:
        for path,digest in previous[group].items(): assert sha256_file(Path(path))==digest,path
    target_path=ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet'
    manifest_path=target_path.parent/'manifest.json'; manifest=read(manifest_path)
    assert sha256_file(target_path)==manifest['artifacts']['targets']['file_sha256']
    certificate=manifest['source_certification_report']; cert_path=Path(certificate['path'])
    assert sha256_file(cert_path)==certificate['sha256']
    complete=read(cert_path)['complete_seasons']
    f=current.tagged(tagged(pl.read_parquet(current.OUT/'features.parquet'))).sort('row_id')
    target=pl.read_parquet(target_path); assert len(f)==63282
    stints_path=ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet'
    counts_path=stints_path.parent/'counts.parquet';stints=pl.read_parquet(stints_path)
    mlb=pl.read_parquet(counts_path).filter(pl.col('bucket')=='MLB').filter(pl.col('season')>=2009)
    reconciled=target.join(mlb.select('season','player_id','plate_appearances'),on=['season','player_id'],how='full',coalesce=True,validate='1:1')
    extra_zero=reconciled.filter(pl.col('mlb_pa').is_null())
    assert (extra_zero['plate_appearances']==0).all(), 'Missing positive-PA inventory person'
    positive=reconciled.filter(pl.col('mlb_pa').is_not_null())
    assert len(positive)==len(target) and positive['mlb_pa'].equals(positive['plate_appearances'])
    annual=annual_followup(f,target,complete)
    first=annual.filter(pl.col('followup_year')==1).sort('row_id')
    assert first['mlb_pa'].equals(f['next_pa'])
    active=first.filter(pl.col('mlb_pa')>0)
    raw=f.filter(pl.col('row_id').is_in(active['row_id'])).sort('row_id')
    assert np.allclose(active['batting_rate'],raw['next_batting_rate'],atol=1e-10,rtol=0)
    assert annual.filter(~pl.col('observed'))['mlb_pa'].null_count()==annual.filter(~pl.col('observed')).height
    assert annual.filter(pl.col('mlb_pa')==0)['batting_rate'].null_count()==annual.filter(pl.col('mlb_pa')==0).height
    tags=['dominant_level','audit_age_band','prior_debut','rank_band','new_draftee','thin_pro']
    enriched=annual.join(f.select('row_id',*tags),on='row_id',validate='m:1')
    pre=read(current.OUT/'preflight.json'); predictions=pl.read_parquet(current.OUT/'scored-predictions.parquet')
    support=[];cells=[]
    for c in pre['cells']:
        y,k=c['year'],c['fold'];te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
        assert te['origin_year'].unique().to_list()==[y] and te['outer_fold'].unique().to_list()==[k]
        s=te.select('row_id','player_id','origin_year','outer_fold',*tags,'age','age_unknown')
        for horizon in [1,3,6]:
            for design in ['annual','complete_window']:
                tr=support_membership(enriched,y,k,horizon,cumulative=design=='complete_window')
                assert not set(tr['player_id'])&set(te['player_id'])
                assert tr.is_empty() or tr['season'].max()<=y
                prefix=f'{design}_{horizon}'
                for profile,keys in [('coarse',tags[:3]),('refined',tags)]:
                    s=s.join(counts_for(tr,te,keys,prefix+'_'+profile),on='row_id',validate='1:1')
                active=tr.filter(pl.col('mlb_pa')>0)
                cells.append(dict(origin=y,fold=k,horizon=horizon,design=design,
                    training_origins=sorted(tr['origin_year'].unique().to_list()),training_observations=len(tr),
                    training_people=tr['player_id'].n_unique(),active_observations=len(active),active_people=active['player_id'].n_unique(),
                    by_horizon=active.group_by('followup_year').agg(pl.col('player_id').n_unique().alias('people'),
                        pl.len().alias('observations'),pl.col('mlb_pa').sum()).sort('followup_year').to_dicts()))
        for h in range(1,7):
            tr=support_membership(enriched,y,k,6).filter(pl.col('followup_year')==h)
            s=s.join(counts_for(tr,te,tags[:3],f'exact_horizon_{h}'),on='row_id',validate='1:1')
        support.append(s)
    support=pl.concat(support).sort('row_id')
    assert len(support)==30506 and set(support['row_id'])==set(predictions['row_id'])
    cohorts=[]
    for label,condition in [('DSL_at_most_17', (pl.col('dominant_level')=='DSL')&(pl.col('age')<=17)&(pl.col('age_unknown')==0)&(pl.col('prior_debut')==0)),
        ('lower_under_21',pl.col('dominant_level').is_in(['DSL','RK120','RK121','RK124','RK128','RK134','RKother','Aminus','A','Aplus'])&(pl.col('age')<21)&(pl.col('age_unknown')==0)&(pl.col('prior_debut')==0)),
        ('all',pl.lit(True))]:
        g=support.filter(condition)
        counts=[]
        for h in [1,3,6]:
            for design in ['annual','complete_window']:
                col=f'{design}_{h}_coarse_people';fine=f'{design}_{h}_refined_people'
                counts.append(dict(horizon=h,design=design,no_coarse_support=g.filter(pl.col(col)==0).height,
                    sparse_coarse_support=g.filter(pl.col(col)<20).height,median_coarse_people=float(g[col].median()),
                    no_refined_support=g.filter(pl.col(fine)==0).height,median_refined_people=float(g[fine].median())))
        cohorts.append(dict(scope=label,rows=len(g),people=g['player_id'].n_unique(),support=counts))
    # One common, fully observed 2011-18 origin subset for timing comparisons.
    timing=enriched.filter((pl.col('origin_year')<=2018)&(pl.col('dominant_level')=='DSL')&
        (pl.col('audit_age_band')=='<=17')&(pl.col('prior_debut')==0))
    timing_report=timing.group_by('followup_year').agg(pl.len().alias('origin_observations'),
        pl.col('player_id').n_unique().alias('origin_people'),pl.col('player_id').filter(pl.col('mlb_pa')>0).n_unique().alias('active_people_including_2020'),
        pl.col('player_id').filter((pl.col('mlb_pa')>0)&(pl.col('season')!=2020)).n_unique().alias('active_people_excluding_2020'),
        pl.col('mlb_pa').sum(),pl.col('mlb_pa').filter(pl.col('season')==2020).sum().alias('pa_in_2020')).sort('followup_year').to_dicts()
    cases=[]
    for pid,y,name in FIXED:
        row=f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)).row(0,named=True)
        assert row['player_name']==name,(pid,name,row['player_name'])
        cases.append(case(f,annual,stints,predictions,support,row))
    OUT.mkdir(parents=True,exist_ok=True);annual.write_parquet(OUT/'annual.parquet');support.write_parquet(OUT/'support.parquet')
    write('cases.json',cases)
    paths=[Path(__file__),ROOT/'src/universal_baseball/hitter_followup.py',ROOT/'docs/hitter-followup-support-contract.md',
        manifest_path,target_path,cert_path,stints_path,counts_path,current.OUT/'features.parquet',current.OUT/'preflight.json',
        current.OUT/'scored-predictions.parquet',ROOT/'reports/generated/hitter-rate-support-audit/final-report.json',
        OUT/'annual.parquet',OUT/'support.parquet',OUT/'cases.json']
    write('report.json',dict(no_new_fits=True,source_rows=len(f),evaluation_rows=len(support),annual_rows=len(annual),
        right_censored_annual_rows=annual.filter(~pl.col('observed')).height,
        all_next_year_pa_and_active_rates_reproduced=True,all_inventory_pa_reconciled=True,
        extra_raw_zero_pa_person_seasons=len(extra_zero),
        cohorts=cohorts,cells=cells,young_DSL_timing=timing_report,player_walkthrough_status='pending',
        protected_outcomes_used=False,current_forecasts_changed=False,input_and_output_hashes={str(p):sha256_file(p) for p in paths}))
    print(json.dumps(dict(cohorts=cohorts,young_DSL_timing=timing_report),indent=2),flush=True)


if __name__=='__main__': main()
