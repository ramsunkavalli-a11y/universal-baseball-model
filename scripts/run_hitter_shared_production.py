"""Source preparation then sealed fixed historical hitting-only comparison."""
from collections import defaultdict
from pathlib import Path
import argparse
import json
import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits
from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_shared_production import FEATURES, profile
from universal_baseball.hitter_talent_bridge import SCOUT_FEATURES, event_counts, make_pairs, fit_graph
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights
from prepare_practical_hitter_v33 import safe_matrix

ROOT=Path(__file__).resolve().parents[1]; GEN=ROOT/'reports/generated'
OUT=GEN/'hitter-shared-production'; OLD=GEN/'hitter-evidence-representation'
CONTRACT=ROOT/'docs/hitter-shared-production-contract.md'
FIXED_NAMES=[('Yordan Alvarez',2018),('Aaron Judge',2016),('Nick Kurtz',2024),
             ('Seiya Suzuki',2021),('Jung Hoo Lee',2024),('Masataka Yoshida',2024),('Kevin Maitan',2017)]


def read(p):return json.loads(Path(p).read_text(encoding='utf8'))


def save(name,obj):
    p=OUT/name;assert not p.exists(),f'Preserve {p}'
    p.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n',encoding='utf8',newline='\n')


def verify(mapping):
    for p,h in mapping.items():assert sha256_file(Path(p))==h,p


def source_data():
    raw=pl.read_parquet(GEN/'practical-hitter-v31/counts.parquet').filter(pl.col('season')<=2024)
    history=defaultdict(list)
    for r in raw.to_dicts():history[r['player_id']].append(r)
    sources={r['candidate_key']:r for r in read(GEN/'foreign-origin-inputs/origin-inputs.json')['rows']}
    foreign={(r['candidate_key'],r['outer_fold']):r for r in read(GEN/'foreign-borrowed-stability/profiles.json')['profiles']}
    return raw,history,sources,foreign


def tagged(f):
    return f.with_columns((pl.col('age')//5).cast(pl.Int64).alias('age_group'),
        pl.when(pl.col('pa_0')==0).then(0).when(pl.col('pa_0')<200).then(1).otherwise(2).alias('mlb_exposure'),
        (pl.col('shared_foreign_share')>0).alias('foreign_production'),
        (pl.col('scout_rank_score_0')>=.8).alias('scout_high'))


def prepare():
    assert not OUT.exists(),'Do not restart source preparation'
    assert read(OLD/'final-review.json')['player_walkthrough_status']=='complete'
    OUT.mkdir(parents=True)
    raw,history,sources,foreign=source_data(); counts=event_counts(raw); pairs=make_pairs(raw,counts)
    base=read(GEN/'practical-hitter-numeric-repair-v53/preflight.json')['rate_features']
    tracking=read(GEN/'hitter-statcast-next-year/preflight.json')['arms']['ridge_measurements']
    removed=[n for n in base if n.startswith('pooled_') and n.rsplit('_',1)[-1] in {'K','BB','HBP','HR','BABIP','2B','3B'}]
    assert len(removed)==98
    kept=[n for n in base if n not in removed]
    arms={'base':kept+FEATURES,'prospect':kept+SCOUT_FEATURES+FEATURES,
          'tracking':[n for n in tracking if n not in removed]+FEATURES}
    assert all(len(n)==len(set(n)) for n in arms.values())
    paths=[CONTRACT,Path(__file__),ROOT/'src/universal_baseball/hitter_shared_production.py',
        ROOT/'tests/test_hitter_shared_production.py',ROOT/'src/universal_baseball/hitter_talent_bridge.py',
        ROOT/'src/universal_baseball/hitter_evidence_representation.py',ROOT/'scripts/prepare_practical_hitter_v33.py',
        ROOT/'scripts/fit_practical_hitter_v31.py',ROOT/'src/universal_baseball/forecast_validation.py',
        GEN/'practical-hitter-v31/counts.parquet',GEN/'foreign-origin-inputs/origin-inputs.json',
        GEN/'foreign-borrowed-stability/profiles.json',OLD/'preflight.json',OLD/'predictions.parquet',
        GEN/'hitter-nonmedical-opportunity/predictions.parquet']
    notes=[];all_graphs={};supports=[];profile_support=[];ranges=[];cells=[]
    with threadpool_limits(limits=2):
        for k in range(5):
            f=pl.read_parquet(OLD/f'features-{k}.parquet');assert f['origin_year'].max()==2024 and f['target_year'].max()==2025
            graphs={}
            for y in sorted(f['origin_year'].unique()):
                for j in range(5):
                    excluded={j,k}
                    _,g=fit_graph([p for p in pairs if p['fold'] not in excluded],cutoff=y,held_fold=k)
                    mask=np.array([r['season']==y and r['bucket']=='MLB' and player_fold(r['player_id']) not in excluded for r in raw.iter_rows(named=True)])
                    ref=counts[mask].sum(0)+.5;assert mask.any();ref/=ref.sum()
                    g.update(excluded_folds=sorted(excluded),mlb_reference=ref.tolist(),
                        mlb_reference_people=raw.filter(pl.Series(mask))['player_id'].to_list())
                    assert all(player_fold(pid) not in excluded for pid in g['people']+g['mlb_reference_people'])
                    graphs[f'{y}:{j}']=g
            all_graphs[k]=graphs;overlay=[]
            for o in f.iter_rows(named=True):
                y,pid=o['origin_year'],o['player_id'];key=f'{y}:{pid}'
                values,note=profile(history[pid],graphs[f'{y}:{o["outer_fold"]}'],sources.get(key),foreign.get((key,k)),
                    origin=y,outer_fold=k,own_fold=o['outer_fold'])
                overlay.append(dict(row_id=o['row_id'],**values))
                if o['outer_fold']==k and (o['player_name'],y) in FIXED_NAMES:
                    notes.append(dict(row_id=o['row_id'],player_name=o['player_name'],origin_year=y,
                        source=note,features=values,raw_history=[r for r in history[pid] if y-2<=r['season']<=y]))
            f=f.join(pl.DataFrame(overlay),on='row_id',validate='1:1');assert np.isfinite(safe_matrix(f,arms['tracking'])).all()
            f.write_parquet(OUT/f'features-{k}.parquet');save(f'graphs-{k}.json',graphs)
            paths += [OLD/f'features-{k}.parquet',OUT/f'features-{k}.parquet',OUT/f'graphs-{k}.json']
            print(f'Prepared held fold {k}: shared event profiles and both-fold-excluded graphs.',flush=True)
        for c in read(OLD/'preflight.json')['cells']:
            y,k=c['year'],c['fold'];f=pl.read_parquet(OUT/f'features-{k}.parquet')
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id');active=tr.filter(pl.col('next_pa')>0)
            assert tr['target_year'].max()<=y and tr['ctx_information_date'].max()<te['ctx_information_date'].min()
            assert not set(tr['player_id']) & set(te['player_id'])
            checks={};keys=['prior_debut','stage','age_group','mlb_exposure','foreign_production','scout_high']
            for arm,names in arms.items():
                sup,note=preflight(active,te,cutoff=y,fold=k,features=names,expected_keys=te.select('row_id','horizon').iter_rows())
                checks[arm]=note;supports.append(sup.with_columns(pl.lit(arm).alias('arm'),pl.lit(k).alias('test_fold')))
                for label,sub in [('full',tr),('active',active)]:
                    cnt=tagged(sub).group_by(keys).agg(pl.col('player_id').n_unique().alias('people'))
                    profile_support.append(tagged(te).select('row_id',*keys).join(cnt,on=keys,how='left',validate='m:1').with_columns(
                        pl.col('people').fill_null(0),pl.lit(label).alias('subset'),pl.lit(arm).alias('arm'),pl.lit(y).alias('origin_year'),pl.lit(k).alias('test_fold')))
                a=safe_matrix(active,names);b=safe_matrix(te,names)
                for i,n in enumerate(names):
                    lo,hi=float(a[:,i].min()),float(a[:,i].max());outside=(b[:,i]<lo)|(b[:,i]>hi)
                    if outside.any():ranges.append(dict(origin=y,fold=k,arm=arm,feature=n,min=lo,max=hi,row_ids=te.filter(pl.Series(outside))['row_id'].to_list()))
            cells.append(dict(year=y,fold=k,training_row_ids=c['training_row_ids'],test_row_ids=c['test_row_ids'],checks=checks))
        pl.concat(supports).write_parquet(OUT/'support.parquet');pl.concat(profile_support).write_parquet(OUT/'profile-support.parquet')
        save('feature-ranges.json',ranges);save('source-walks.json',notes)
        paths += [OUT/n for n in ['support.parquet','profile-support.parquet','feature-ranges.json','source-walks.json']]
        save('preflight.json',dict(cells=cells,arms=arms,removed=removed,checks_before_fits=105,
            before_fitting=True,source_hashes={str(p):sha256_file(p) for p in paths},ridge_alpha=100,
            source_walkthrough_status='pending',player_walkthrough_status='pending',protected_outcomes_used=False))
    print('All source preparation and 105 actual head gates sealed; source review required before fit.',flush=True)


def fit():
    pre=read(OUT/'preflight.json');verify(pre['source_hashes']);review=read(OUT/'source-review.json');verify(review['hashes'])
    assert review['approved_for_fit'] and review['source_walkthrough_status']=='complete'
    assert not (OUT/'fit-report.json').exists()
    seal=dict(runner_sha256=sha256_file(Path(__file__)),preflight_sha256=sha256_file(OUT/'preflight.json'),source_review_sha256=sha256_file(OUT/'source-review.json'))
    if (OUT/'fit-seal.json').exists():assert read(OUT/'fit-seal.json')==seal
    else:save('fit-seal.json',seal)
    old=pl.read_parquet(OLD/'predictions.parquet').sort('row_id')
    jobs=pl.read_parquet(GEN/'hitter-nonmedical-opportunity/predictions.parquet')
    # Additions use the declared research job reference; originals stay incumbent.
    print('Job reference columns:',[n for n in jobs.columns if n.endswith('_pa') and 'conditional' not in n],flush=True)
    jobs=jobs.select('row_id','observation_pa').rename({'observation_pa':'addition_pa'})
    receipts=[];forecasts=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];path=OUT/f'forecast-{y}-{k}.parquet'
            if path.exists():
                note=read(OUT/f'fit-{y}-{k}.json');verify(note['hashes']);receipts.append(note);forecasts.append(pl.read_parquet(path));continue
            f=pl.read_parquet(OUT/f'features-{k}.parquet');tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])&(pl.col('next_pa')>0)).sort('row_id')
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id');q=old.filter(pl.col('row_id').is_in(te['row_id'])).sort('row_id').join(jobs,on='row_id',validate='1:1')
            assert q['row_id'].equals(te['row_id']);w=weights(tr)*tr['next_pa'].to_numpy();w*=len(w)/w.sum();pred={};heads=[];hashes={}
            for arm,names in pre['arms'].items():
                m=Ridge(alpha=pre['ridge_alpha']);m.fit(safe_matrix(tr,names),tr['actual_relative_rate'].to_numpy(),sample_weight=w)
                pred[arm]=m.predict(safe_matrix(te,names));p=OUT/f'{arm}-rate-{y}-{k}.joblib';assert not p.exists();joblib.dump(m,p,compress=3)
                hashes[str(p)]=sha256_file(p);heads.append(dict(arm=arm,path=str(p),sha256=hashes[str(p)],features=names,training_rows=tr.height,training_people=tr['player_id'].n_unique()))
            rate=np.where(te['prior_debut'].to_numpy()==0,pred['prospect'],np.where(te['sc_tracked'].to_numpy(),pred['tracking'],pred['base']))
            pa=np.where(q['source_addition'].to_numpy(),q['addition_pa'].to_numpy(),q['current_pa'].to_numpy())
            q=q.with_columns(pl.Series('shared_rate',rate),pl.Series('shared_pa',pa),
                pl.Series('shared_value',pa*(rate/600+q['origin_replacement_rate'].to_numpy())),
                pl.Series('shared_branch',['prospect' if a==0 else 'tracking' if b else 'base' for a,b in zip(te['prior_debut'],te['sc_tracked'],strict=True)]))
            assert np.isfinite(q.select('shared_rate','shared_pa','shared_value').to_numpy()).all()
            q.write_parquet(path);hashes[str(path)]=sha256_file(path);note=dict(origin=y,fold=k,heads=heads,hashes=hashes)
            save(f'fit-{y}-{k}.json',note);receipts.append(note);forecasts.append(q)
            print(f'Fitted {y}/{k}: three shared-event talent heads; no job fits.',flush=True)
    q=pl.concat(forecasts).sort('row_id');assert q.height==30519
    assert q.select(old.columns).equals(old)
    original=q.filter(~pl.col('source_addition'));assert original['shared_pa'].equals(original['current_pa'])
    q.write_parquet(OUT/'predictions.parquet');save('fit-report.json',dict(cells=receipts,new_heads=105,rows=q.height,
        predictions_sha256=sha256_file(OUT/'predictions.parquet'),player_walkthrough_status='pending',protected_outcomes_used=False,deployment_approved=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','fit']);args=parser.parse_args()
    {'prepare':prepare,'fit':fit}[args.phase]()
