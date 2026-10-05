"""Replay fixed models, score compatible targets and persist actual player paths.

Produces provisional evidence only. Manual review and disposition are separate.
"""
from pathlib import Path
import json

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.hitter_compatible_value import labels
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file
from prepare_hitter_evidence_representation import ROOT, GEN, OUT, OLD, read, save
from prepare_hitter_overseas_integration import ANCHOR, annual_labels
from prepare_practical_hitter_v33 import safe_matrix
from review_hitter_overseas_integration import score, errors, origin_weights
from supplement_hitter_overseas_scores import rate_score
from evaluate_hitter_readiness_v49 import logit_trace

NEW = ['repaired_domestic', 'repaired_overseas']


def verify(mapping):
    for p, h in mapping.items():
        assert sha256_file(Path(p)) == h, p


def interval(g, candidate, baseline):
    """Cluster players, retaining the original equal-origin row weights."""
    delta = errors(g, candidate) - errors(g, baseline)
    w = origin_weights(g)
    people, pi = np.unique(g['player_id'].to_numpy(), return_inverse=True)
    totals = np.zeros((len(people), 8)); den = np.zeros(len(people))
    np.add.at(totals, pi, delta * w[:, None]); np.add.at(den, pi, w)
    rng = np.random.default_rng(84); draws = []
    for b in range(2000):
        counts = np.bincount(rng.integers(len(people), size=len(people)), minlength=len(people))
        z = counts @ totals / (counts @ den)
        if b < 10:
            assert np.allclose(z, (delta * (w * counts[pi])[:, None]).sum(0) / (w * counts[pi]).sum())
        draws.append(z)
    draws = np.asarray(draws); point = w @ delta
    return [dict(metric=n, change=float(point[i]), lower=float(np.quantile(draws[:, i], .025)),
                 upper=float(np.quantile(draws[:, i], .975)), fixed_original_origin_weights=True,
                 nominal_exposed_development_interval=True)
            for i, n in enumerate(['pa_mse','pa_mae','pa_bias','value_mse','value_mae','value_bias','brier','logloss'])]


def linear_trace(m, x, names):
    effects = x * m.coef_; prediction = float(m.intercept_ + effects.sum())
    assert np.isclose(prediction, m.predict(x[None, :])[0], atol=1e-10, rtol=0)
    terms = [dict(feature=n, fixed_unit_input=float(a), coefficient=float(b), effect=float(e))
             for n, a, b, e in zip(names, x, m.coef_, effects, strict=True)]
    return dict(intercept=float(m.intercept_), prediction=prediction,
                feature_effects=sorted(terms, key=lambda r: -abs(r['effect'])),
                interpretation='Exact fixed-unit linear accounting, not causal attribution')


def main():
    assert not (OUT/'review-receipt.json').exists(), 'Preserve completed evidence'
    pre = read(OUT/'preflight.json'); verify(pre['source_hashes'])
    fit = read(OUT/'fit-report.json')
    assert sha256_file(OUT/'predictions.parquet') == fit['predictions_sha256']
    q = pl.read_parquet(OUT/'predictions.parquet').sort('row_id')
    stints = pl.read_parquet(GEN/'practical-hitter-v31/dated-stints.parquet')
    actual, env = annual_labels(stints)
    raw = np.array([actual.get((r['target_year'], r['player_id']), np.zeros(8)) for r in q.to_dicts()])
    lab = labels(raw, np.array([env[y] for y in q['origin_year']]),
                 np.array([env[y] for y in q['target_year']]), q['origin_replacement_rate'].to_numpy())
    assert np.array_equal(lab['pa'], q['next_pa'])
    for key in ['relative_rate', 'relative_value']:
        assert np.allclose(lab[key], q['actual_'+key], atol=1e-10)
    q = q.with_columns(pl.Series('actual_common_rate', lab['common_rate']))
    frames = {k: pl.read_parquet(OUT/f'features-{k}.parquet') for k in range(5)}
    with threadpool_limits(limits=2):
        for c in fit['cells']:
            y, k = c['origin'], c['fold']; verify(c['hashes'])
            g = q.filter((pl.col('origin_year') == y) & (pl.col('outer_fold') == k)).sort('row_id')
            f = frames[k].filter(pl.col('row_id').is_in(g['row_id'].to_list())).sort('row_id')
            assert f['row_id'].equals(g['row_id'])
            for h in c['heads']:
                m = joblib.load(h['path']); names = h['features']
                x = safe_matrix(f, names) if h['head'] == 'rate' else f.select(names).to_numpy()
                output = m.predict_proba(x)[:, 1] if h['head'] == 'participation' else m.predict(x)
                col = 'repaired_domestic_'+('raw_p' if h['head']=='participation' else 'raw_conditional_pa') if h['arm']=='common' else 'repaired_'+h['arm']+'_rate'
                assert np.allclose(output, g[col], atol=1e-10, rtol=0)
            for arm in NEW:
                assert np.allclose(g[arm+'_pa'], g[arm+'_p']*g[arm+'_conditional_pa'], atol=1e-10)
                assert np.allclose(g[arm+'_value'], g[arm+'_pa']*(g[arm+'_rate']/600+g['origin_replacement_rate']), atol=1e-10)
            print(f'Replayed four heads and value products: {y}/{k}', flush=True)
    anchor = pl.read_parquet(ANCHOR).select('row_id','steamer_pa','steamer_rate','steamer_index','zips_index','common_zips_rate')
    q = q.join(anchor, on='row_id', how='left', validate='1:1')
    original = q.filter(~pl.col('source_addition')); added = q.filter(pl.col('source_addition'))
    assert (original.height, added.height) == (30506, 13)
    public = original.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null())
    assert public.height == 2627
    foreign_ids = frames[0].filter(pl.col('evidence_foreign_source_present')>0)['row_id'].to_list()
    scopes = [('original_all', original), ('additions', added), ('public', public),
              ('original_foreign', original.filter(pl.col('row_id').is_in(foreign_ids))),
              ('original_upper_never_debut', original.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),
              ('original_lower_never_debut', original.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))),
              ('original_current_MLB', original.filter(pl.col('pa_0')>0)),
              ('current_regular', original.filter(pl.col('pa_0')>=400)),
              ('current_partial', original.filter(pl.col('pa_0').is_between(1,399))),
              ('absent_prior_debut', original.filter((pl.col('pa_0')==0)&(pl.col('prior_debut')==1))),
              ('original_no_arrival', original.filter(pl.col('next_pa')==0))]
    scopes += [('origin_'+str(y), original.filter(pl.col('origin_year')==y)) for y in sorted(original['origin_year'].unique())]
    scores = []; comparisons = []; rates = []
    with threadpool_limits(limits=2):
        for name, g in scopes:
            if not g.height: continue
            arms = NEW if name=='additions' else ['current','domestic','overseas',*NEW]
            mechanics = {}
            if name!='additions':
                for arm in NEW:
                    for head in ['workload_only','talent_only']:
                        err = (g[arm+'_'+head+'_value']-g['actual_relative_value']).to_numpy()
                        mechanics[arm+'_'+head] = dict(value_rmse=float(np.sqrt(origin_weights(g)@(err**2))),
                                                     value_bias=float(origin_weights(g)@err))
            scores.append(dict(scope=name, rows=g.height, players=g['player_id'].n_unique(),
                               actual_pa=int(g['next_pa'].sum()), actual_arrivals=int((g['next_pa']>0).sum()),
                               actual_value=float(g['actual_relative_value'].sum()),
                               scores={a:score(g,a) for a in arms}, mechanical_diagnostics=mechanics))
            active = g.filter(pl.col('next_pa')>0)
            if active.height:
                rates.append(dict(scope=name, active_rows=active.height,
                                  PA_weighted_relative_rmse={a:rate_score(active,a+'_rate','actual_relative_rate',True) for a in arms},
                                  PA_weighted_common_rmse={a:rate_score(active,a+'_rate','actual_common_rate',True) for a in arms}))
            if name in ['original_all','public','original_foreign','additions']:
                pairs = [('repaired_overseas','repaired_domestic')]
                if name!='additions': pairs += [(a,'current') for a in NEW]
                for a,b in pairs: comparisons.append(dict(scope=name,candidate=a,baseline=b,intervals=interval(g,a,b)))
    paerr = (public['steamer_pa']-public['next_pa']).to_numpy(); w=origin_weights(public)
    public_value = public['steamer_pa']*(public['steamer_rate']/600+public['origin_replacement_rate'])
    ve = (public_value-public['actual_relative_value']).to_numpy()
    benchmark = dict(rows=public.height,pa_rmse=float(np.sqrt(w@(paerr**2))),pa_mae=float(w@abs(paerr)),
                     value_rmse=float(np.sqrt(w@(ve**2))),
                     qualification='Raw public forecasts, origin-centered actual common rates; release, park and environment differences remain. ZiPS PA is not a certified workload estimate.')
    pubactive = public.filter(pl.col('next_pa')>0)
    benchmark['PA_weighted_common_rate_rmse'] = {a:rate_score(pubactive,c,'actual_common_rate',True)
        for a,c in [('steamer','steamer_rate'),('zips','common_zips_rate')]}
    save('scores.json',dict(scopes=scores,rates=rates,public_steamer=benchmark))
    save('intervals.json',dict(seed=84,repetitions=2000,comparisons=comparisons))
    chosen = {int(c['origin']['row_id']):['retained prior diagnostic'] for c in read(OLD/'reviewed-cases.json')['cases']}
    def choose(g,why):
        if g.height: chosen.setdefault(int(g['row_id'][0]),[]).append(why)
    for arm in NEW:
        z=original.with_columns(((pl.col(arm+'_value')-pl.col('actual_relative_value'))**2-(pl.col('current_value')-pl.col('actual_relative_value'))**2).alias('change'),
            (pl.col(arm+'_value')-pl.col('actual_relative_value')).alias('error'))
        choose(z.sort('change'),arm+' largest gain'); choose(z.sort('change',descending=True),arm+' largest harm')
        choose(z.sort('error'),arm+' false low'); choose(z.sort('error',descending=True),arm+' false high')
        choose(z.filter(pl.col('next_pa').is_between(200,399)).sort(pl.col('error').abs()),arm+' ordinary')
    oldcases={c['origin']['row_id']:c for c in read(OLD/'reviewed-cases.json')['cases']}
    sources={c['row_id']:c for c in read(OUT/'source-cases.json')}
    support=pl.read_parquet(OUT/'profile-support.parquet'); cases=[]
    with threadpool_limits(limits=2):
        for rid, why in chosen.items():
            o=q.filter(pl.col('row_id')==rid).row(0,named=True); y,k=o['origin_year'],o['outer_fold']
            one=frames[k].filter(pl.col('row_id')==rid); a=one.row(0,named=True)
            cell=next(c for c in fit['cells'] if c['origin']==y and c['fold']==k)
            mechanics={}
            for h in cell['heads']:
                m=joblib.load(h['path']);names=h['features']
                x=safe_matrix(one,names)[0] if h['head']=='rate' else one.select(names).to_numpy()[0]
                mechanics[h['arm']+'_'+h['head']]=linear_trace(m,x,names) if h['head']=='rate' else logit_trace(m,x,names) if h['head']=='participation' else trace(m,x,names)
            pool=frames[k].filter((pl.col('row_id')!=rid)&(pl.col('origin_year')==y)&pl.col('row_id').is_in(q['row_id'].to_list())&
                (pl.col('prior_debut')==a['prior_debut'])&(pl.col('status_major_link')==a['status_major_link'])&(pl.col('on_40man')==a['on_40man']))
            distance=(((pl.col('age')-a['age'])/5)**2+((pl.col('pa_0')-a['pa_0'])/250)**2+
                      ((pl.col('professional_work_0')-a['professional_work_0'])/1)**2+
                      ((pl.col('scout_rank_score_0')-a['scout_rank_score_0'])/.3)**2)
            peers=pool.with_columns(distance.alias('origin_distance')).sort('origin_distance','player_id').head(3).select(
                'row_id','player_id','player_name','age','pa_0','professional_work_0','origin_distance')
            peers=peers.join(q.select('row_id','next_pa','actual_relative_value',*[n for n in q.columns if n.startswith('repaired_')]),on='row_id',validate='1:1')
            cases.append(dict(origin=o,selection=why,actual_model_inputs=a,mechanics=mechanics,
                              source_representation=sources.get(rid),
                              retained_previous_walk=oldcases.get(rid),
                              recent_domestic_counts=stints.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(y-2,y)).sort('season','bucket','team_id').to_dicts(),
                              actual_future_MLB_counts=actual.get((y+1,o['player_id']),np.zeros(8)).tolist(),
                              profile_support=support.filter(pl.col('row_id')==rid).to_dicts(),origin_only_peers=peers.to_dicts()))
            print(f'Exact player trace: {o["player_name"]} {y}',flush=True)
    save('reviewed-cases.json',dict(cases=cases,player_walkthrough_status='machine_ready_manual_pending',
        peer_rule='Same origin, debut, major link and literal roster; nearest age, MLB PA, first-team work and prospect rank. No future outcomes used for selection.'))
    sparse=support.group_by('head').agg(pl.len().alias('rows'),(pl.col('profile_people')==0).sum().alias('unsupported'),
                                      (pl.col('profile_people')<20).sum().alias('under_20_people')).sort('head').to_dicts()
    save('review-receipt.json',dict(saved_heads_replayed=140,labels_independently_reconstructed=True,
        case_count=len(cases),scores_provisional=True,player_walkthrough_status='pending',profile_support=sparse,
        protected_outcomes_used=False,deployment_approved=False,
        input_hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'preflight.json',OUT/'fit-report.json',OUT/'predictions.parquet',ANCHOR]},
        output_hashes={str(OUT/n):sha256_file(OUT/n) for n in ['scores.json','intervals.json','reviewed-cases.json']}))
    print(json.dumps(scores[:3],indent=2),flush=True)


if __name__=='__main__': main()
