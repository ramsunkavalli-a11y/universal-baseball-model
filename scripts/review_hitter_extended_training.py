"""Walk actual dated stats through saved matched heads before disposition."""
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file
from evaluate_hitter_readiness_v49 import logit_trace
from prepare_practical_hitter_v33 import safe_matrix
from prepare_hitter_extended_training import ROOT,OUT,read,write,verify,profile,BUCKETS


def linear(model,f,names):
    x = safe_matrix(f,names)[0]
    terms = x*model.coef_
    result = dict(intercept=float(model.intercept_),prediction=float(model.intercept_+sum(terms)),
        effects=sorted([dict(feature=n,input=float(v),coefficient=float(c),effect=float(t))
            for n,v,c,t in zip(names,x,model.coef_,terms)],key=lambda r:abs(r['effect']),reverse=True))
    assert np.isclose(result['prediction'],model.predict(x[None,:])[0],atol=1e-10,rtol=0)
    return result


def distance(f,o):
    return (abs(pl.col('age')-o['age'])/2+
        abs(pl.col('minor_pa_0')-o['minor_pa_0'])/300+
        abs(pl.col('pa_0')-o['pa_0'])/300+
        abs(pl.col('scout_rank_score_0')-o['scout_rank_score_0'])+
        abs(pl.col('draft_rank')-o['draft_rank'])+
        pl.when(pl.col('source_position')!=o['source_position']).then(.5).otherwise(0.)+
        abs(pl.col('pooled_'+o['dominant_level']+'_HR')-o['pooled_'+o['dominant_level']+'_HR'])/.04+
        abs(pl.col('pooled_'+o['dominant_level']+'_BB')-o['pooled_'+o['dominant_level']+'_BB'])/.1+
        abs(pl.col('pooled_'+o['dominant_level']+'_K')-o['pooled_'+o['dominant_level']+'_K'])/.2) if o['dominant_level'] in BUCKETS else abs(pl.col('age')-o['age'])/2


def highest(row):
    order = {'MLB':6,'AAA':5,'AA':4,'Aplus':3,'A':2,'Aminus':1,'DSL':0,
             'RK120':0,'RK121':0,'RK124':0,'RK128':0,'RK134':0,'RKother':0,'MEX':4}
    return max([order[b] for b in BUCKETS if row[b+'_0_pa']>0],default=-1)


def main():
    assert not (OUT/'cases.json').exists(), 'Preserve actual case review'
    pre = read(OUT/'preflight.json')
    check = read(OUT/'verification.json')
    verify(pre['input_hashes'])
    verify(check['hashes'])
    source = profile(pl.read_parquet(OUT/'features.parquet'))
    source = source.with_columns(pl.Series('highest_level',[highest(s) for s in source.iter_rows(named=True)]))
    q = pl.read_parquet(OUT/'scored-predictions.parquet')
    stints = pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet')
    support = pl.read_parquet(OUT/'profile-support.parquet')
    cases, models = [],{}
    with threadpool_limits(limits=2):
        for selected in read(OUT/'selected-cases.json'):
            rid = selected['row_id']
            f = source.filter(pl.col('row_id')==rid)
            o = f.row(0,named=True)
            result = q.filter(pl.col('row_id')==rid).row(0,named=True)
            note = read(OUT/f"fit-{o['origin_year']}-{o['outer_fold']}.json")
            paths = {}
            for h in note['heads']:
                verify({h['path']:h['sha256']})
                if h['path'] not in models:
                    models[h['path']] = joblib.load(h['path'])
                m,names = models[h['path']],h['features']
                if h['head']=='rate':
                    path = linear(m,f,names)
                    expected = result[h['arm']+'_rate']
                else:
                    x = f.select(names).to_numpy()[0]
                    path = logit_trace(m,x,names) if h['head']=='participation' else trace(m,x,names)
                    expected = result[h['arm']+'_raw_p' if h['head']=='participation' else h['arm']+'_raw_conditional_pa']
                actual = path['linked_probability'] if h['head']=='participation' else path['prediction'] if h['head']=='rate' else path['raw_prediction']
                assert np.isclose(actual,expected,atol=1e-8,rtol=0)
                paths[h['arm']+'_'+h['head']] = dict(**path,model_path=h['path'],model_sha256=h['sha256'])
            candidates = source.filter((pl.col('origin_year')==o['origin_year'])&
                (pl.col('prior_debut')==o['prior_debut'])&(pl.col('dominant_level')==o['dominant_level'])&
                (pl.col('highest_level')==o['highest_level'])&(pl.col('age_unknown')==o['age_unknown'])&
                (abs(pl.col('age')-o['age'])<=2)&(pl.col('player_id')!=o['player_id']))
            peers = candidates.with_columns(distance(candidates,o).alias('distance')).sort('distance','player_id').head(4)
            columns = ['row_id','player_id','player_name','origin_year','age','prior_debut','source_position','dominant_level','highest_level',
                'minor_pa_0','pa_0','scout_listed_0','scout_rank_score_0','draft_known','draft_rank',
                *[b+'_0_pa' for b in BUCKETS]]
            if o['dominant_level'] in BUCKETS:
                columns += ['pooled_'+o['dominant_level']+'_'+e for e in ['HR','BB','K']]
            peer_rows = []
            for peer in peers.iter_rows(named=True):
                forecasts = q.filter(pl.col('row_id')==peer['row_id']).row(0,named=True)
                peer_rows.append(dict(origin={n:peer[n] for n in columns},distance=peer['distance'],
                    forecasts={n:forecasts[n] for n in ['restricted_pa','extended_pa','restricted_rate','extended_rate','restricted_value','extended_value','next_pa','next_value']}))
            cell = next(c for c in pre['cells'] if c['year']==o['origin_year'] and c['fold']==o['outer_fold'])
            added = source.filter(pl.col('row_id').is_in(cell['training_row_ids']['extended'])&(pl.col('origin_year')<=2010)&
                (pl.col('prior_debut')==o['prior_debut'])&(pl.col('dominant_level')==o['dominant_level'])&
                (pl.col('highest_level')==o['highest_level'])&(pl.col('age_unknown')==o['age_unknown'])&(abs(pl.col('age')-o['age'])<=2))
            added = added.with_columns(distance(added,o).alias('distance')).sort('distance','player_id','origin_year').unique('player_id',keep='first',maintain_order=True).head(4)
            arms = {}
            for arm in ['preseason','translated_ridge','restricted','extended']:
                arms[arm] = {n:result[arm+'_'+n] for n in ['pa','rate','value']}
                if arm != 'translated_ridge':
                    arms[arm].update(probability=result[arm+'_p'],conditional_pa=result[arm+'_conditional_pa'])
            stats = stints.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(o['origin_year']-2,o['origin_year'])).sort('season','bucket','team_id')
            cases.append(dict(selection=selected,origin={n:o[n] for n in columns},
                actual_inputs=f.select(list(dict.fromkeys(pre['pa_features']+pre['rate_features']))).row(0,named=True),
                dated_stats=stats.to_dicts(),saved_model_accounting=paths,forecasts=arms,
                reality=dict(next_pa=result['next_pa'],common_origin_value=result['next_value'],
                    target_season_batting_rate=result['realized_season_rate'] if result['next_pa']>0 else None),
                actual_fold_support=support.filter(pl.col('row_id')==rid).to_dicts(),
                head_training_counts=[{n:h[n] for n in ['arm','head','training_rows','training_people','min_target_year','max_target_year']} for h in note['heads']],
                peers=peer_rows,peer_count=len(peers),
                peer_rule='Same origin, prior-participation, dominant and highest level, known-age status and age within two; distance on PA, position, ranks/draft and HR/BB/K. No future outcomes used.',
                added_training_peers=added.select(*columns,'distance','next_pa','next_batting_rate').to_dicts(),
                earlier_peer_rule='Same profile, actual held-fold training membership; nearest distinct people by origin-known inputs. Source labels shown only after selection.',
                mechanisms_are_not_causal=True))
    write('cases.json',cases)
    write('review-preparation.json',dict(player_walkthrough_status='pending',case_count=len(cases),
        hashes={str(OUT/n):sha256_file(OUT/n) for n in ['preflight.json','verification.json','scores.json','intervals.json','selected-cases.json','cases.json','scored-predictions.parquet']},
        model_hashes={h['path']:h['sha256'] for n in read(OUT/'fits.json') for h in n['heads']}))
    for c in cases:
        print(c['selection'],c['forecasts'],c['reality'],'SUPPORT',[(s['arm'],s['head'],s['kind'],s['profile_people']) for s in c['actual_fold_support']],
            'PEERS',[(p['origin']['player_name'],p['forecasts']['next_pa']) for p in c['peers']],
            'EARLIER',[(p['player_name'],p['origin_year'],p['next_pa']) for p in c['added_training_peers']],flush=True)


if __name__=='__main__':
    main()
