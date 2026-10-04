"""Matched conditional training populations; no arrival or rate refits."""
from pathlib import Path
import json
import shutil
import sys

import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

from fit_practical_hitter_v31 import weights
from prepare_hitter_extended_training import ROOT, BUCKETS, profile, verify, read
from review_hitter_extended_training import highest, distance
from score_practical_hitter_v31 import paired
from universal_baseball.forecast_validation import preflight
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.storage import sha256_file

OUT = ROOT/'reports/generated/hitter-prospect-workload-specialization'
EARLIER = ROOT/'reports/generated/hitter-extended-training'
CURRENT = ROOT/'reports/generated/hitter-preseason-readiness-v68'
ARMS = ['preseason', 'translated_ridge', 'pooled_extended', 'prospect_restricted', 'prospect_extended']
NEW = ['prospect_restricted', 'prospect_extended']
FIXED = [(701762,2024),(694671,2023),(624413,2018),(660670,2017),(677594,2021),(702616,2023)]


def write(name, data):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/name).write_text(json.dumps(data, indent=2, allow_nan=False, ensure_ascii=False, default=str)+'\n', encoding='utf8')


def specialize(frame):
    return frame.filter((pl.col('prior_debut')==0)&(pl.col('next_pa')>0)).sort('row_id')


def connect(q, arm, raw):
    mask = q['prior_debut'].to_numpy()==0
    assert len(raw)==int(mask.sum()) and np.isfinite(raw).all()
    x = q['preseason_raw_conditional_pa'].to_numpy().copy()
    x[mask] = raw
    cp = np.clip(x,1,800)
    # Established outputs are copied rather than recomputed to preserve bytes.
    pa = q['preseason_pa'].to_numpy().copy()
    pa[mask] = q['preseason_p'].to_numpy()[mask]*cp[mask]
    value = q['preseason_value'].to_numpy().copy()
    value[mask] = pa[mask]*(q['baseline_rate'].to_numpy()[mask]/600+q['origin_replacement_rate'].to_numpy()[mask])
    tv = q['translated_ridge_value'].to_numpy().copy()
    tv[mask] = pa[mask]*(q['translated_ridge_rate'].to_numpy()[mask]/600+q['origin_replacement_rate'].to_numpy()[mask])
    return q.with_columns(pl.Series(arm+'_raw_conditional_pa',x),pl.Series(arm+'_conditional_pa',cp),
        pl.Series(arm+'_pa',pa),pl.col('preseason_p').alias(arm+'_p'),pl.col('baseline_rate').alias(arm+'_rate'),
        pl.Series(arm+'_value',value),pl.Series(arm+'_translated_value',tv),pl.Series(arm+'_translated_pa',pa))


def legacy_audit():
    path = ROOT/'reports/generated/hitter-arrival-source-repair-v1/repaired-panel.parquet'
    f = pl.read_parquet(path)
    from universal_baseball.hitter_arrival_value_transfer import FOLDS, training
    rows = []
    for y,h in FOLDS:
        a = training(f,y,h).filter(pl.col(f'pa_h{h}')>0)
        b = f.filter(pl.col('origin_year')==y)
        overlapping = a.filter(pl.col('player_id').is_in(b['player_id'].to_list()))
        queried_prospects = b.filter(pl.col('prior_debut')==False)
        overlap_prospects = a.filter(pl.col('player_id').is_in(queried_prospects['player_id'].to_list()))
        rows.append(dict(origin=y,horizon=h,active_training_rows=len(a),active_training_people=a['player_id'].n_unique(),
            active_never_debut_rows=len(a.filter(pl.col('prior_debut')==False)),
            active_prior_debut_rows=len(a.filter(pl.col('prior_debut')==True)),
            query_rows=len(b),overlapping_query_people=overlapping['player_id'].n_unique(),
            overlapping_query_training_rows=len(overlapping),overlapping_prospect_people=overlap_prospects['player_id'].n_unique(),
            overlapping_prospect_training_rows=len(overlap_prospects),
            latest_label=int(a['origin_year'].max())+h))
    return dict(cells=rows, hashes={str(p):sha256_file(p) for p in [path,
        ROOT/'src/universal_baseball/hitter_arrival_value_transfer.py',ROOT/'src/universal_baseball/hitter_conditional_workload.py']},
        interpretation='Old chronological fits include repeated query identities and both prior-debut and never-debut active training. Forecast routing is not training specialization; scores are not held-player evidence.')


def prepare():
    assert not (OUT/'preflight.json').exists(), 'Preserve frozen preflight'
    prior = read(EARLIER/'preflight.json')
    final = read(EARLIER/'final-report.json')
    assert final['player_walkthrough_status']=='complete'
    verify(prior['input_hashes'])
    f = pl.read_parquet(EARLIER/'features.parquet')
    q = pl.read_parquet(EARLIER/'scored-predictions.parquet').sort('row_id')
    anchor = pl.read_parquet(CURRENT/'scored-predictions.parquet').sort('row_id')
    assert len(q)==30506 and q.select(anchor.columns).equals(anchor)
    audit = legacy_audit()
    write('legacy-audit.json',audit)
    cells, supports, profiles, replayed = [],[],[],0
    with threadpool_limits(limits=2):
        for c in prior['cells']:
            y,k = c['year'],c['fold']
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])&(pl.col('prior_debut')==0)).sort('row_id')
            pooled_query = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            scored = q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            checks, ids, controls = {},{},{}
            for history in ['restricted','extended']:
                tr = f.filter(pl.col('row_id').is_in(c['training_row_ids'][history])).sort('row_id')
                active = tr.filter(pl.col('next_pa')>0)
                entrant = specialize(tr)
                assert len(entrant)>30
                ids[history] = entrant['row_id'].to_list()
                for training_kind,sub in [('pooled',active),('prospect',entrant)]:
                    sup,note = preflight(sub,te,cutoff=y,fold=k,features=prior['pa_features'],expected_keys=te.select('row_id','horizon').iter_rows())
                    key = history+'_'+training_kind
                    checks[key] = note
                    supports.append(sup.with_columns(pl.lit(key).alias('training_arm')))
                    for kind,keys in [('broad',['prior_debut','dominant_level','age_band']),
                                      ('refined',['prior_debut','dominant_level','age_band','rank_band','thin_pro','new_draftee'])]:
                        n = profile(sub).group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
                        profiles.append(profile(te).select('row_id',*keys).join(n,on=keys,how='left',validate='m:1').with_columns(
                            pl.col('profile_people').fill_null(0),pl.lit(key).alias('training_arm'),pl.lit(kind).alias('kind')))
                heads = read(EARLIER/f'fit-{y}-{k}.json')['heads']
                head = next(h for h in heads if h['arm']==history and h['head']=='conditional_pa')
                verify({head['path']:head['sha256']})
                m = joblib.load(head['path'])
                pred = m.predict(pooled_query.select(prior['pa_features']).to_numpy())
                np.testing.assert_allclose(pred,scored[history+'_raw_conditional_pa'],atol=1e-10,rtol=0)
                if history=='restricted':
                    np.testing.assert_array_equal(pred,scored['preseason_raw_conditional_pa'])
                controls[history] = head
                replayed += 1
            cells.append(dict(year=y,fold=k,test_row_ids=c['test_row_ids'],prospect_test_ids=te['row_id'].to_list(),
                training_row_ids=ids,checks=checks,controls=controls))
    pl.concat(supports).write_parquet(OUT/'support.parquet')
    pl.concat(profiles,how='diagonal_relaxed').write_parquet(OUT/'profile-support.parquet')
    paths = [Path(__file__),ROOT/'docs/hitter-prospect-workload-specialization-contract.md',
        ROOT/'tests/test_hitter_prospect_workload_specialization.py',
        ROOT/'scripts/fit_practical_hitter_v31.py',ROOT/'scripts/review_hitter_extended_training.py',
        ROOT/'scripts/score_practical_hitter_v31.py',ROOT/'src/universal_baseball/forecast_validation.py',
        ROOT/'src/universal_baseball/histogram_prediction_trace.py',
        EARLIER/'features.parquet',EARLIER/'preflight.json',EARLIER/'final-report.json',EARLIER/'scored-predictions.parquet',
        CURRENT/'scored-predictions.parquet',OUT/'legacy-audit.json',OUT/'support.parquet',OUT/'profile-support.parquet']
    write('preflight.json',dict(before_fitting=True,cells=cells,features=prior['pa_features'],settings=prior['settings'],
        checks_before_fits=140,pooled_controls_replayed=replayed,evaluation_rows=30506,
        input_hashes={str(p):sha256_file(p) for p in paths},new_heads=70,protected_outcomes_used=False,
        fixed_probability_and_hitting=True,established_unchanged=True,player_walkthrough_status='pending'))
    print('140 actual preflights and 70 pooled control replays sealed; no new fit yet.',flush=True)
    print(json.dumps(audit['cells'],indent=2),flush=True)
    print('First/last specialized training counts',[(c['year'],c['fold'],{a:len(v) for a,v in c['training_row_ids'].items()}) for c in [cells[0],cells[-1]]],flush=True)


def fit():
    pre = read(OUT/'preflight.json')
    verify(pre['input_hashes'])
    f = pl.read_parquet(EARLIER/'features.parquet')
    anchor = pl.read_parquet(EARLIER/'scored-predictions.parquet').sort('row_id')
    fits = []
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k = c['year'],c['fold']
            pp = OUT/f'forecast-{y}-{k}.parquet'
            if pp.exists():
                n = read(OUT/f'fit-{y}-{k}.json')
                verify({str(pp):n['prediction_sha256'],**{h['path']:h['sha256'] for h in n['heads']}})
                fits.append(n)
                continue
            te = f.filter(pl.col('row_id').is_in(c['prospect_test_ids'])).sort('row_id')
            q = anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert q.filter(pl.col('prior_debut')==0)['row_id'].equals(te['row_id'])
            q = connect(q,'pooled_extended',q.filter(pl.col('prior_debut')==0)['extended_raw_conditional_pa'].to_numpy())
            heads = []
            for history in ['restricted','extended']:
                arm = 'prospect_'+history
                tr = f.filter(pl.col('row_id').is_in(c['training_row_ids'][history])).sort('row_id')
                assert tr.equals(specialize(tr))
                mp,hp = OUT/f'{arm}-{y}-{k}.joblib',OUT/f'{arm}-{y}-{k}.json'
                if hp.exists():
                    n = read(hp)
                    verify({str(mp):n['sha256']})
                    model = joblib.load(mp)
                else:
                    assert not mp.exists(), 'Unsealed model needs explicit recovery'
                    model = HistGradientBoostingRegressor(**pre['settings'])
                    w = weights(tr)
                    model.fit(tr.select(pre['features']).to_numpy(),tr['next_pa'].to_numpy(),sample_weight=w)
                    joblib.dump(model,mp,compress=3)
                    n = dict(arm=arm,path=str(mp),sha256=sha256_file(mp),training_rows=len(tr),
                        training_people=tr['player_id'].n_unique(),min_target_year=int(tr['target_year'].min()),max_target_year=int(tr['target_year'].max()),
                        weight_sum=float(w.sum()),weighted_mean_target=float(np.average(tr['next_pa'],weights=w)))
                    write(hp.name,n)
                q = connect(q,arm,model.predict(te.select(pre['features']).to_numpy()))
                heads.append(n)
            assert q.select(anchor.columns).equals(anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id'))
            q.write_parquet(pp)
            n = dict(year=y,fold=k,heads=heads,prediction_sha256=sha256_file(pp))
            write(f'fit-{y}-{k}.json',n)
            fits.append(n)
            print(f'First-arrival workload {y}/{k}: two heads saved.',flush=True)
    q = pl.concat([pl.read_parquet(OUT/f"forecast-{c['year']}-{c['fold']}.parquet") for c in pre['cells']]).sort('row_id')
    assert q.select(anchor.columns).equals(anchor)
    q.write_parquet(OUT/'predictions.parquet')
    write('fits.json',fits)


def conditional_score(g, arm):
    a = g.filter(pl.col('next_pa')>0)
    if not len(a):
        return dict(rows=0,rmse=None,mae=None,predicted_total=None,actual_total=None)
    per = []
    for _,s in a.group_by('target_year'):
        e = s[arm+'_conditional_pa'].to_numpy()-s['next_pa'].to_numpy()
        per.append([np.mean(e**2),np.mean(abs(e)),np.mean(e)])
    v = np.mean(per,axis=0)
    return dict(rows=len(a),people=a['player_id'].n_unique(),rmse=float(np.sqrt(v[0])),mae=float(v[1]),bias=float(v[2]),
        predicted_total=float(a[arm+'_conditional_pa'].sum()),actual_total=int(a['next_pa'].sum()),
        interpretation='Actual-debutant diagnostic only; all non-arrivals remain in primary scoring.')


def scoring():
    assert not (OUT/'verification.json').exists(), 'Preserve completed scoring'
    pre = read(OUT/'preflight.json')
    verify(pre['input_hashes'])
    f = pl.read_parquet(EARLIER/'features.parquet')
    anchor = pl.read_parquet(EARLIER/'scored-predictions.parquet').sort('row_id')
    q = pl.read_parquet(OUT/'predictions.parquet').sort('row_id')
    assert q.select(anchor.columns).equals(anchor)
    replays = []
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            te = f.filter(pl.col('row_id').is_in(c['prospect_test_ids'])).sort('row_id')
            sub = q.filter(pl.col('row_id').is_in(c['prospect_test_ids'])).sort('row_id')
            n = read(OUT/f"fit-{c['year']}-{c['fold']}.json")
            verify({str(OUT/f"forecast-{c['year']}-{c['fold']}.parquet"):n['prediction_sha256']})
            for h in n['heads']:
                verify({h['path']:h['sha256']})
                pred = joblib.load(h['path']).predict(te.select(pre['features']).to_numpy())
                error = float(np.max(abs(pred-sub[h['arm']+'_raw_conditional_pa'].to_numpy())))
                assert error<1e-10
                replays.append(dict(origin=c['year'],fold=c['fold'],arm=h['arm'],maximum_error=error))
    established = q.filter(pl.col('prior_debut')==1)
    for arm in ['pooled_extended',*NEW]:
        for suffix in ['pa','value','p']:
            assert established[arm+'_'+suffix].equals(established['preseason_'+suffix])
        assert np.allclose(q[arm+'_pa'],q['preseason_p']*q[arm+'_conditional_pa'],atol=1e-10,rtol=0)
        assert np.allclose(q[arm+'_value'],q[arm+'_pa']*(q['baseline_rate']/600+q['origin_replacement_rate']),atol=1e-10,rtol=0)
    never = q.filter(pl.col('prior_debut')==0)
    public = q.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null())
    assert len(public)==2627
    scopes = [('all',q),('never_debut',never),('upper_never_debut',never.filter(pl.col('stage')=='Upper minors')),
        ('lower_never_debut',never.filter(pl.col('stage')=='Lower minors')),('public',public),
        ('thin_pro',never.filter(pl.col('thin_pro'))),('new_draftees',never.filter(pl.col('new_draftee'))),
        ('teenage_dsl',never.filter((pl.col('DSL_0_pa')>0)&(pl.col('age')<=17)))]
    scopes += [('never_origin_'+str(y),never.filter(pl.col('origin_year')==y)) for y in sorted(never['origin_year'].unique())]
    scores, intervals = [],[]
    for name,g in scopes:
        if not len(g): continue
        candidates = ARMS+['pooled_extended_translated',*[a+'_translated' for a in NEW]]+(['steamer'] if name=='public' else [])
        scores.append(dict(scope=name,rows=len(g),people=g['player_id'].n_unique(),actual_pa=int(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
            scores={a:score(g,a) for a in candidates},conditional={a:conditional_score(g,a) for a in ['preseason','pooled_extended',*NEW]}))
        if name not in ['all','never_debut','upper_never_debut','lower_never_debut']: continue
        contrasts = [('prospect_restricted','preseason'),('prospect_extended','pooled_extended'),('prospect_extended','preseason'),
            ('prospect_extended','prospect_restricted')]
        for a,b in contrasts:
            intervals.extend(dict(scope=name,**paired(g,a,b,metric)) for metric in ['pa','value'])
        intervals.extend(dict(scope=name,**paired(g,a+'_translated','translated_ridge','value')) for a in NEW)
    write('scores.json',scores)
    write('intervals.json',intervals)
    q.write_parquet(OUT/'scored-predictions.parquet')
    chosen = {}
    def choose(g,why):
        assert len(g),why
        chosen.setdefault(g['row_id'][0],[]).append(why)
    for pid,y in FIXED:
        choose(never.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed before fit')
    choose(never.filter((pl.col('DSL_0_pa')>0)&(pl.col('age')<=17)).sort('row_id'),'first eligible teenage DSL by row ID')
    for arm in NEW:
        err = never.with_columns(((pl.col('preseason_value')-pl.col('next_value'))**2-(pl.col(arm+'_value')-pl.col('next_value'))**2).alias('gain'),
            (pl.col(arm+'_value')-pl.col('next_value')).alias('error'))
        for why,g in [('largest gain',err.sort('gain',descending=True)),('largest harm',err.sort('gain')),
            ('false high',err.sort('error',descending=True)),('false low',err.sort('error')),
            ('ordinary active',err.filter(pl.col('next_pa').is_between(100,600)).sort(pl.col('error').abs()))]:
            choose(g,arm+' '+why)
    write('selected-cases.json',[dict(row_id=rid,reasons=why) for rid,why in chosen.items()])
    write('verification.json',dict(new_head_replays=replays,old_controls_replayed=70,anchors_exact=True,
        established_exact=True,arrival_and_hitting_unchanged=True,player_walkthrough_status='pending',
        hashes={str(OUT/n):sha256_file(OUT/n) for n in ['predictions.parquet','scored-predictions.parquet','scores.json','intervals.json','selected-cases.json']},
        clips={a:never.filter((pl.col(a+'_raw_conditional_pa')<1)|(pl.col(a+'_raw_conditional_pa')>800)).height for a in ['pooled_extended',*NEW]},
        protected_outcomes_used=False,frozen_forecast_changed=False,deployment_approved=False))
    for s in scores:
        print(s['scope'],{a:(round(v['pa_rmse'],3),round(v['pa_mae'],3),round(v['value_rmse'],6),round(v['pa_total'])) for a,v in s['scores'].items()},flush=True)


def review():
    assert not (OUT/'cases.json').exists(), 'Preserve player evidence'
    pre = read(OUT/'preflight.json')
    verify(pre['input_hashes'])
    verify(read(OUT/'verification.json')['hashes'])
    source = profile(pl.read_parquet(EARLIER/'features.parquet')).with_columns(
        pl.Series('highest_level',[highest(r) for r in pl.read_parquet(EARLIER/'features.parquet').iter_rows(named=True)]))
    q = pl.read_parquet(OUT/'scored-predictions.parquet')
    stints = pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet')
    support = pl.read_parquet(OUT/'profile-support.parquet')
    cases = []
    with threadpool_limits(limits=2):
        for selected in read(OUT/'selected-cases.json'):
            rid = selected['row_id']
            f = source.filter(pl.col('row_id')==rid)
            o = f.row(0,named=True)
            result = q.filter(pl.col('row_id')==rid).row(0,named=True)
            c = next(c for c in pre['cells'] if c['year']==o['origin_year'] and c['fold']==o['outer_fold'])
            paths = {}
            for history in ['restricted','extended']:
                h = c['controls'][history]
                verify({h['path']:h['sha256']})
                m = joblib.load(h['path'])
                a = 'preseason' if history=='restricted' else 'pooled_extended'
                paths[a] = trace(m,f.select(pre['features']).to_numpy()[0],pre['features'])
                assert np.isclose(paths[a]['raw_prediction'],result[a+'_raw_conditional_pa'],atol=1e-8,rtol=0)
                h = read(OUT/f"prospect_{history}-{o['origin_year']}-{o['outer_fold']}.json")
                verify({h['path']:h['sha256']})
                m = joblib.load(h['path'])
                a = 'prospect_'+history
                paths[a] = trace(m,f.select(pre['features']).to_numpy()[0],pre['features'])
                paths[a]['training'] = h
                assert np.isclose(paths[a]['raw_prediction'],result[a+'_raw_conditional_pa'],atol=1e-8,rtol=0)
            peers = source.filter((pl.col('origin_year')==o['origin_year'])&(pl.col('prior_debut')==0)&
                (pl.col('dominant_level')==o['dominant_level'])&(pl.col('highest_level')==o['highest_level'])&
                (pl.col('age_unknown')==o['age_unknown'])&(abs(pl.col('age')-o['age'])<=2)&(pl.col('player_id')!=o['player_id']))
            peers = peers.with_columns(distance(peers,o).alias('distance')).sort('distance','player_id').head(4)
            columns = ['row_id','player_id','player_name','origin_year','age','source_position','dominant_level','highest_level',
                'minor_pa_0','scout_rank_score_0','draft_rank',*[b+'_0_pa' for b in BUCKETS]]
            if o['dominant_level'] in BUCKETS:
                columns += ['pooled_'+o['dominant_level']+'_'+e for e in ['HR','BB','K']]
            peer_rows = []
            for p in peers.iter_rows(named=True):
                forecast = q.filter(pl.col('row_id')==p['row_id']).row(0,named=True)
                peer_rows.append(dict(origin={n:p[n] for n in columns},distance=p['distance'],
                    forecasts={n:forecast[n] for n in ['preseason_pa',*[a+'_pa' for a in NEW],'next_pa','next_value']}))
            arms = {}
            for a in ['preseason','pooled_extended',*NEW]:
                arms[a] = dict(probability=result['preseason_p'],conditional_pa=result[a+'_conditional_pa'],
                    expected_pa=result[a+'_pa'],batting_rate=result['baseline_rate'],value=result[a+'_value'],
                    translated_value=result['translated_ridge_value'] if a=='preseason' else result[a+'_translated_value'])
            cases.append(dict(selection=selected,origin={n:o[n] for n in columns},actual_inputs=f.select(pre['features']).row(0,named=True),
                dated_stats=stints.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(o['origin_year']-2,o['origin_year'])).sort('season','bucket','team_id').to_dicts(),
                actual_target_stats=stints.filter((pl.col('player_id')==o['player_id'])&(pl.col('season')==o['target_year'])&(pl.col('bucket')=='MLB')).to_dicts(),
                saved_paths=paths,forecasts=arms,origin_replacement_rate=result['origin_replacement_rate'],translated_rate=result['translated_ridge_rate'],
                reality=dict(next_pa=result['next_pa'],common_origin_value=result['next_value'],
                    realized_batting_rate=result['realized_season_rate'] if result['next_pa']>0 else None),
                actual_fold_support=support.filter(pl.col('row_id')==rid).to_dicts(),peers=peer_rows,
                peer_rule='Same origin, never-debut, dominant/highest level, known-age status, age within two; nearest exposure, position, draft/rank and HR/BB/K. No future outcomes used.',
                mechanism_not_causality=True))
    write('cases.json',cases)
    write('review-preparation.json',dict(player_walkthrough_status='pending',case_count=len(cases),
        hashes={str(OUT/n):sha256_file(OUT/n) for n in ['preflight.json','verification.json','scores.json','intervals.json','selected-cases.json','cases.json','scored-predictions.parquet']},
        model_hashes={h['path']:h['sha256'] for c in pre['cells'] for h in c['controls'].values()}|
            {h['path']:h['sha256'] for n in read(OUT/'fits.json') for h in n['heads']}))
    for c in cases:
        print(c['selection'],c['origin']['player_name'],c['origin']['age'],c['origin']['minor_pa_0'],
            c['forecasts'],c['reality'],'support',[(s['training_arm'],s['kind'],s['profile_people']) for s in c['actual_fold_support']],flush=True)


def finalize():
    assert not (OUT/'final-report.json').exists(), 'Preserve completed decision'
    prep = read(OUT/'review-preparation.json')
    verify(prep['hashes']); verify(prep['model_hashes'])
    notes_path = ROOT/'config/hitter_prospect_workload_specialization_review.json'
    result_path = ROOT/'docs/hitter-prospect-workload-specialization-result.md'
    notes = read(notes_path)
    cases = read(OUT/'cases.json')
    assert set(notes)=={str(c['selection']['row_id']) for c in cases}
    assert all(n['review_status']=='complete' and n['assessment'] for n in notes.values())
    write('reviewed-cases.json',[dict(row_id=c['selection']['row_id'],name=c['origin']['player_name'],**notes[str(c['selection']['row_id'])]) for c in cases])
    pre = read(OUT/'preflight.json')
    write('preflight-summary.json',{k:v for k,v in pre.items() if k!='cells'}|dict(cells=[
        {k:v for k,v in c.items() if k not in ['test_row_ids','prospect_test_ids','training_row_ids','controls']}|
        dict(test_rows=len(c['test_row_ids']),prospect_rows=len(c['prospect_test_ids']),training_counts={a:len(ids) for a,ids in c['training_row_ids'].items()}) for c in pre['cells']],
        full_memberships_path=str(OUT/'preflight.json'),full_memberships_sha256=sha256_file(OUT/'preflight.json')))
    write('final-report.json',dict(player_walkthrough_status='complete',reviewed_cases=len(cases),
        disposition='See reviewed result; no automatic promotion',protected_outcomes_used=False,frozen_forecast_changed=False,
        explorer_changed=False,deployment_approved=False,full_goal_complete=False,
        source_hashes=pre['input_hashes'],review_hashes=prep['hashes'],model_hashes=prep['model_hashes'],
        final_hashes={str(p):sha256_file(p) for p in [notes_path,result_path,OUT/'reviewed-cases.json',OUT/'preflight-summary.json']}))
    evidence = ROOT/'reports/model-evidence/hitter-prospect-workload-specialization'
    evidence.mkdir(parents=True,exist_ok=True)
    for name in ['legacy-audit.json','scores.json','intervals.json','selected-cases.json','cases.json','verification.json','reviewed-cases.json','preflight-summary.json','final-report.json']:
        shutil.copyfile(OUT/name,evidence/name)
        assert sha256_file(OUT/name)==sha256_file(evidence/name)
    print('Actual player review completed; full goal remains active.',flush=True)


if __name__=='__main__':
    {'prepare':prepare,'fit':fit,'score':scoring,'review':review,'finalize':finalize}[sys.argv[1]]()
