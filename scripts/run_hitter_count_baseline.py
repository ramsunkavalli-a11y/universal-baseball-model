"""One prospectively fixed past-only, count-likelihood historical comparison."""
from pathlib import Path
import argparse
import json
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.hitter_count_baseline import FEATURES, past_profile, assemble, fit, probabilities
from universal_baseball.hitter_talent_bridge import EVENTS, SCOUT_FEATURES
from universal_baseball.hitter_evidence_representation import check_cutoff
from universal_baseball.forecast_validation import preflight
from universal_baseball.mlb_event_logit import VALUES, batting_rate
from universal_baseball.storage import sha256_file
from run_hitter_shared_production import ROOT,GEN,OLD,source_data,read,verify
from prepare_hitter_overseas_integration import annual_labels
from prepare_practical_hitter_v33 import safe_matrix
from fit_practical_hitter_v31 import weights

OUT=GEN/'hitter-count-baseline'; SHARED=GEN/'hitter-shared-production'
CONTRACT=ROOT/'docs/hitter-count-baseline-contract.md'
FIXED=[(r['forecast']['player_name'],r['forecast']['origin_year']) for r in read(SHARED/'player-walks.json')['cases']]
TARGET=[f'count_target_{e}' for e in EVENTS]
REF=[f'count_ref_{e}' for e in EVENTS]
FUTURE=[f'count_training_environment_{e}' for e in EVENTS]


def save(name,obj):
    p=OUT/name;assert not p.exists(),f'Preserve {p}'
    p.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n',encoding='utf8',newline='\n')


def matrix(f,names):
    x=safe_matrix(f,names)
    for i,n in enumerate(names):
        if n in {'work_0','work_1','work_2'}:x[:,i]/=600
    assert np.isfinite(x).all()
    return x


def offset(f,training=False):
    ref=f.select(FUTURE if training else REF).to_numpy()
    assert (ref>0).all() and np.allclose(ref.sum(1),1)
    return np.log(ref)+f.select(FEATURES[:8]).to_numpy()


def tagged(f):
    return f.with_columns((pl.col('age')//5).cast(pl.Int64).alias('age_group'),
        pl.when(pl.col('pa_0')==0).then(0).when(pl.col('pa_0')<200).then(1).otherwise(2).alias('mlb_exposure'),
        (pl.col('count_NPB_share')>0).alias('has_NPB'),(pl.col('count_KBO_share')>0).alias('has_KBO'),
        (pl.col('scout_rank_score_0')>=.8).alias('scout_high'))


def prepare():
    assert not OUT.exists();OUT.mkdir(parents=True)
    assert read(SHARED/'final-review.json')['player_walkthrough_status']=='complete'
    oldpre=read(SHARED/'preflight.json');verify(oldpre['source_hashes'])
    raw,history,sources,foreign=source_data()
    actual,env=annual_labels(pl.read_parquet(GEN/'practical-hitter-v31/dated-stints.parquet'))
    base=read(GEN/'practical-hitter-numeric-repair-v53/preflight.json')['rate_features']
    tracking=read(GEN/'hitter-statcast-next-year/preflight.json')['arms']['ridge_measurements']
    removed=[n for n in base if n.startswith('pooled_') and n.rsplit('_',1)[-1] in {'K','BB','HBP','HR','BABIP','2B','3B'}]
    assert len(removed)==98
    removed+=['quality_0','quality_1','quality_2','pooled_mlb_quality']
    kept=[n for n in base if n not in removed]
    arms=dict(base=kept+FEATURES,prospect=kept+SCOUT_FEATURES+FEATURES,
        tracking=[n for n in tracking if n not in removed]+FEATURES)
    assert all(len(n)==len(set(n)) for n in arms.values())
    paths=[CONTRACT,Path(__file__),ROOT/'src/universal_baseball/hitter_count_baseline.py',
        ROOT/'tests/test_hitter_count_baseline.py',ROOT/'docs/hitter-shared-production-horizon-qualification.md',
        ROOT/'scripts/prepare_hitter_overseas_integration.py',ROOT/'scripts/prepare_practical_hitter_v33.py',
        ROOT/'scripts/fit_practical_hitter_v31.py',ROOT/'src/universal_baseball/forecast_validation.py',
        GEN/'practical-hitter-v31/dated-stints.parquet',OLD/'predictions.parquet',
        GEN/'hitter-nonmedical-opportunity/predictions.parquet',SHARED/'preflight.json',SHARED/'player-walks.json']
    paths += [Path(p) for p in oldpre['source_hashes'] if Path(p).suffix in {'.py','.parquet','.json'}]
    walks=[];checks=[];support=[];ranges=[];cells=[];foreign_checks=0
    with threadpool_limits(limits=2):
        for k in range(5):
            f=pl.read_parquet(OLD/f'features-{k}.parquet');graphs=read(SHARED/f'graphs-{k}.json');rows=[]
            for o in f.iter_rows(named=True):
                y,pid=o['origin_year'],o['player_id'];key=f'{y}:{pid}'
                check_cutoff(o,sources.get(key))
                values,note=past_profile(history[pid],graphs[f'{y}:{o["outer_fold"]}'],sources.get(key),foreign.get((key,k)),
                    origin=y,outer_fold=k,own_fold=o['outer_fold'])
                counts=actual.get((o['target_year'],pid),np.zeros(8))
                assert counts.sum()==o['next_pa']
                row=dict(row_id=o['row_id'],**values,**dict(zip(TARGET,counts,strict=True)),
                    **dict(zip(REF,note['reference'],strict=True)),**dict(zip(FUTURE,env[o['target_year']],strict=True)))
                rows.append(row)
                foreign_checks+=sum(c['source'] in {'NPB','KBO'} for c in note['contributions'])
                if o['outer_fold']==k and (o['player_name'],y) in FIXED:
                    walks.append(dict(row_id=o['row_id'],player_name=o['player_name'],origin_year=y,
                        source=note,features=values,raw_history=[r for r in history[pid] if y-2<=r['season']<=y],
                        past_baseline_rate=float(batting_rate(np.array([note['past_probability']]),np.array([note['reference']]))[0])))
            f=f.join(pl.DataFrame(rows),on='row_id',validate='1:1');assert f.height==63314
            assert np.allclose(f.select(FEATURES[:8]).to_numpy().sum(1),0,atol=1e-10)
            f.write_parquet(OUT/f'features-{k}.parquet');paths += [OUT/f'features-{k}.parquet',SHARED/f'graphs-{k}.json']
            print(f'Prepared fold {k}: past-only source meanings and independently paired target counts.',flush=True)
            for c in [c for c in oldpre['cells'] if c['fold']==k]:
                y=c['year'];tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
                te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id');active=tr.filter(pl.col('next_pa')>0)
                assert tr['target_year'].max()<=y and 2020 not in tr['target_year']
                assert not set(tr['player_id']) & set(te['player_id'])
                assert tr['ctx_information_date'].max()<te['ctx_information_date'].min()
                keys=['prior_debut','stage','age_group','mlb_exposure','has_NPB','has_KBO','scout_high'];notes={}
                for arm,names in arms.items():
                    sup,n=preflight(active,te,cutoff=y,fold=k,features=names,expected_keys=te.select('row_id','horizon').iter_rows())
                    notes[arm]=n;checks.append(sup.with_columns(pl.lit(arm).alias('arm'),pl.lit(k).alias('test_fold')))
                    for subset,g in [('full',tr),('active',active)]:
                        a=tagged(g).group_by(keys).agg(pl.col('player_id').n_unique().alias('people'))
                        support.append(tagged(te).select('row_id',*keys).join(a,on=keys,how='left',validate='m:1').with_columns(
                            pl.col('people').fill_null(0),pl.lit(subset).alias('subset'),pl.lit(arm).alias('arm'),pl.lit(y).alias('origin_year'),pl.lit(k).alias('test_fold')))
                    a=matrix(active,names);b=matrix(te,names)
                    for i,nm in enumerate(names):
                        lo,hi=float(a[:,i].min()),float(a[:,i].max());outside=(b[:,i]<lo)|(b[:,i]>hi)
                        if outside.any():ranges.append(dict(origin=y,fold=k,arm=arm,feature=nm,min=lo,max=hi,row_ids=te.filter(pl.Series(outside))['row_id'].to_list()))
                    assert np.isfinite(offset(active,True)).all() and np.isfinite(offset(te)).all()
                cells.append(dict(year=y,fold=k,training_row_ids=c['training_row_ids'],test_row_ids=c['test_row_ids'],checks=notes))
        assert len(walks)==10 and len(cells)==35
        pl.concat(checks).write_parquet(OUT/'support.parquet');pl.concat(support).write_parquet(OUT/'profile-support.parquet')
        save('source-walks.json',walks);save('feature-ranges.json',ranges)
        paths += [OUT/n for n in ['support.parquet','profile-support.parquet','source-walks.json','feature-ranges.json']]
        save('preflight.json',dict(cells=cells,arms=arms,removed=removed,checks_before_fits=105,
            foreign_past_contributions_reconstructed=foreign_checks,before_fitting=True,
            source_hashes={str(p):sha256_file(p) for p in paths},source_walkthrough_status='pending',
            player_walkthrough_status='pending',protected_outcomes_used=False))
    print('105 head gates saved. Read the ten source cases and certify before fitting.',flush=True)


def certify():
    assert not (OUT/'source-review.json').exists()
    pre=read(OUT/'preflight.json');verify(pre['source_hashes'])
    doc=ROOT/'docs/hitter-count-baseline-source-review.md';assert doc.exists()
    walks=read(OUT/'source-walks.json');assert {(r['player_name'],r['origin_year']) for r in walks}==set(FIXED)
    num_checks=0
    for a in walks:
        note=a['source'];ref=np.asarray(note['reference']);num=1200*ref.copy();mass=0.
        for c in note['contributions']:
            if c['source'] in {'NPB','KBO'}:
                own=np.zeros(8);local=np.zeros(8);n=0.
                for r in c['observed_seasons']:
                    counts=np.asarray(r['counts']);w=r['recency']*counts.sum()
                    own+=w*(counts+.5)/(counts.sum()+4);local+=w*np.asarray(r['reference']);n+=w
                assert np.isclose(n,c['precision_PA']);own/=n;local/=n
                z=np.log(own/local)+np.log(ref)
            else:
                r=next(r for r in a['raw_history'] if r['season']==c['season'] and r['bucket']==c['bucket'])
                known=np.array([r['strike_outs'],r['unintentional_walks'],r['hit_by_pitch'],r['babip_hits']-r['doubles']-r['triples'],r['doubles'],r['triples'],r['home_runs']])
                counts=np.r_[r['plate_appearances']-known.sum(),known];assert np.array_equal(counts,c['counts'])
                graph=read(SHARED/f'graphs-{__import__("universal_baseball.post_arrival_history",fromlist=["player_fold"]).player_fold(r["player_id"])}.json')
                j=__import__('universal_baseball.post_arrival_history',fromlist=['player_fold']).player_fold(r['player_id'])
                z=np.log((counts+.5)/(counts.sum()+4));z-=z.mean();z-=np.asarray(graph[f'{a["origin_year"]}:{j}']['offsets'][c['bucket']])
            z-=z.max();p=np.exp(z);p/=p.sum();assert np.allclose(p,c['probability'],atol=1e-12)
            num+=c['precision_PA']*p;mass+=c['precision_PA'];num_checks+=1
        p=num/(1200+mass);z=np.log(p/ref);z-=z.mean()
        assert np.allclose(p,note['past_probability'],atol=1e-12)
        assert np.allclose(z,[a['features'][n] for n in FEATURES[:8]],atol=1e-12)
        assert note['future_foreign_probabilities_used'] is False
    save('source-review.json',dict(approved_for_fit=True,source_walkthrough_status='complete',
        independently_reconstructed_contributions=num_checks,checks_before_fits=105,
        hashes={str(p):sha256_file(p) for p in [Path(__file__),doc,OUT/'preflight.json',OUT/'source-walks.json']},
        deployment_approved=False,protected_outcomes_used=False))
    print('Past meaning, raw counts and source arithmetic certified; fixed historical fit can proceed.',flush=True)


def run_fit():
    pre=read(OUT/'preflight.json');verify(pre['source_hashes']);review=read(OUT/'source-review.json');verify(review['hashes'])
    assert review['approved_for_fit'] and not (OUT/'fit-report.json').exists()
    seal=dict(runner_sha256=sha256_file(Path(__file__)),preflight_sha256=sha256_file(OUT/'preflight.json'),source_review_sha256=sha256_file(OUT/'source-review.json'))
    if (OUT/'fit-seal.json').exists():assert read(OUT/'fit-seal.json')==seal
    else:save('fit-seal.json',seal)
    old=pl.read_parquet(OLD/'predictions.parquet').sort('row_id')
    jobs=pl.read_parquet(GEN/'hitter-nonmedical-opportunity/predictions.parquet').select('row_id','observation_pa')
    forecasts=[];receipts=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];path=OUT/f'forecast-{y}-{k}.parquet'
            if path.exists():
                note=read(OUT/f'fit-{y}-{k}.json');verify(note['hashes']);receipts.append(note);forecasts.append(pl.read_parquet(path));continue
            f=pl.read_parquet(OUT/f'features-{k}.parquet');tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])&(pl.col('next_pa')>0)).sort('row_id')
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id');q=old.filter(pl.col('row_id').is_in(te['row_id'])).sort('row_id').join(jobs,on='row_id',validate='1:1')
            assert q['row_id'].equals(te['row_id']);ps={};heads=[];hashes={}
            for arm,names in pre['arms'].items():
                m=fit(matrix(tr,names),tr.select(TARGET).to_numpy(),offset(tr,True),weights(tr))
                p=OUT/f'{arm}-rate-{y}-{k}.joblib';assert not p.exists();joblib.dump(m,p,compress=3)
                hashes[str(p)]=sha256_file(p);ps[arm]=probabilities(m['beta'],matrix(te,names),offset(te))
                heads.append(dict(arm=arm,path=str(p),features=names,optimizer=m['optimizer'],training_rows=tr.height,
                    training_people=tr['player_id'].n_unique(),max_target_year=int(tr['target_year'].max()),
                    transformations='Fixed units; past offset; symmetric 8-event learner; no internally fitted scaler'))
            p=np.where((te['prior_debut'].to_numpy()==0)[:,None],ps['prospect'],np.where(te['sc_tracked'].to_numpy()[:,None],ps['tracking'],ps['base']))
            rate=batting_rate(p,te.select(REF).to_numpy())
            pa=np.where(q['source_addition'].to_numpy(),q['observation_pa'].to_numpy(),q['current_pa'].to_numpy())
            q=q.with_columns(pl.Series('count_rate',rate),pl.Series('count_pa',pa),
                pl.Series('count_value',pa*(rate/600+q['origin_replacement_rate'].to_numpy())),
                pl.Series('count_branch',['prospect' if a==0 else 'tracking' if b else 'base' for a,b in zip(te['prior_debut'],te['sc_tracked'],strict=True)]),
                *[pl.Series(f'count_probability_{e}',p[:,i]) for i,e in enumerate(EVENTS)])
            assert np.isfinite(q.select('count_rate','count_pa','count_value').to_numpy()).all()
            q.write_parquet(path);hashes[str(path)]=sha256_file(path)
            note=dict(origin=y,fold=k,heads=heads,hashes=hashes);save(f'fit-{y}-{k}.json',note);receipts.append(note);forecasts.append(q)
            print(f'Fitted {y}/{k}: 3 converged count heads; no playing-time fits.',flush=True)
    q=pl.concat(forecasts).sort('row_id');assert q.height==30519 and q.select(old.columns).equals(old)
    g=q.filter(~pl.col('source_addition'));assert g['count_pa'].equals(g['current_pa'])
    q.write_parquet(OUT/'predictions.parquet')
    save('fit-report.json',dict(cells=receipts,new_heads=105,rows=q.height,predictions_sha256=sha256_file(OUT/'predictions.parquet'),
        player_walkthrough_status='pending',deployment_approved=False,protected_outcomes_used=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','certify','fit']);a=parser.parse_args()
    {'prepare':prepare,'certify':certify,'fit':run_fit}[a.phase]()
