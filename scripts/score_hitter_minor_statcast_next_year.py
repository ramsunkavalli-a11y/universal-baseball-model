"""Matched rate/value scores and complete saved-fit/source player traces."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.hitter_minor_statcast_forecast import route, support_tags
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
from score_hitter_statcast_next_year import losses, interval
import prepare_hitter_minor_statcast_next_year as prep


def linear_trace(model,row,names):
    x = safe_matrix(row,names)[0]; terms = model.coef_*x
    predicted = float(model.intercept_+terms.sum())
    assert np.isclose(predicted,model.predict(x.reshape(1,-1))[0],atol=1e-10)
    return dict(intercept=float(model.intercept_),replayed_raw_rate=predicted,
        all_terms=[dict(feature=n,input=float(v),coefficient=float(b),signed_term=float(t))
                   for n,v,b,t in zip(names,x,model.coef_,terms)],
        sums={p:float(sum(t for n,t in zip(names,terms) if n.startswith(p))) for p in ['msc_112_','msc_117_','msc_123_','sc_','translated_','scout_']},
        interpretation='Exact fitted terms, not causal attribution or the net difference between models.')


def main():
    out = prep.OUT; assert not (out/'scores.json').exists(), 'Preserve completed scores'
    pre = prep.read(out/'preflight.json'); fit = prep.read(out/'fit-report.json')
    prep.verify_hashes(pre['input_hashes'])
    assert sha256_file(out/'predictions.parquet') == fit['predictions_sha256']
    q = pl.read_parquet(out/'predictions.parquet').sort('row_id')
    anchor = pl.read_parquet(out/'anchor.parquet').sort('row_id')
    assert q.select(anchor.columns).equals(anchor)
    replayed = 0; tags = []
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            f = pl.read_parquet(out/f'features-{c["fold"]}.parquet')
            _, te, context, disabled = route(f,c['training_row_ids'],c['test_row_ids'],pre['minimum_context_people'])
            assert context == c['league_context'] and disabled == c['disabled_features']
            r = q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert r['row_id'].equals(te['row_id']) and r['msc_eligible'].equals(te['msc_eligible'])
            note = prep.read(out/f'fit-{c["year"]}-{c["fold"]}.json')
            prep.verify_hashes(note['output_hashes'])
            for h in note['heads']:
                raw = joblib.load(h['path']).predict(safe_matrix(te,h['features']))
                assert np.allclose(raw,r[h['arm']+'_raw_rate'],atol=1e-12,rtol=0); replayed += 1
            tagged = support_tags(te)
            tags.append(tagged.select('row_id','msc_age_band','msc_exposure_band','msc_sample_band','msc_rank_band',
                'draft_known','draft_rank','scout_listed_0','scout_rank_score_0',
                'pooled_AAA_pa','pooled_AA_pa','pooled_Aplus_pa','pooled_A_pa','pooled_DSL_pa',
                *[f'msc_{l}_ev_n' for l in (112,117,123)]))
    q = q.join(pl.concat(tags),on='row_id',validate='1:1').sort('row_id')
    arms = ['preseason','ridge_measurements','combined',*pre['arms']]
    for arm in pre['arms']:
        assert q.filter(~pl.col('msc_eligible'))[arm+'_rate'].equals(q.filter(~pl.col('msc_eligible'))['combined_rate'])
        assert q.filter(~pl.col('msc_eligible'))[arm+'_value'].equals(q.filter(~pl.col('msc_eligible'))['combined_value'])
        assert np.allclose(q[arm+'_value'],q['preseason_pa']*(q[arm+'_rate']/600+q['origin_replacement_rate']),atol=1e-12,rtol=0)
    public = q.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null())
    assert len(public) == 2627
    scopes = [('all',q),('eligible',q.filter(pl.col('msc_eligible'))),
        ('eligible_predebut',q.filter(pl.col('msc_eligible')&(pl.col('prior_debut')==0))),
        ('eligible_prior_MLB',q.filter(pl.col('msc_eligible')&(pl.col('prior_debut')==1))),
        ('never_debut',q.filter(pl.col('prior_debut')==0)),('public',public),
        ('fallback',q.filter(~pl.col('msc_eligible')))]
    scopes += [(f'origin_{y}',q.filter(pl.col('origin_year')==y)) for y in sorted(q['origin_year'].unique())]
    scopes += [(f'eligible_origin_{y}',q.filter(pl.col('msc_eligible')&(pl.col('origin_year')==y))) for y in (2023,2024)]
    scopes += [(f'eligible_league_{l}',q.filter(pl.col('msc_eligible')&(pl.col(f'msc_{l}_ev_n')>0))) for l in (112,117,123)]
    scopes += [(f'eligible_sample_{s}',q.filter(pl.col('msc_eligible')&(pl.col('msc_sample_band')==s))) for s in ('under50','50to199','200plus')]
    scopes += [(f'eligible_exposure_{s}',q.filter(pl.col('msc_eligible')&(pl.col('msc_exposure_band')==s))) for s in ('AAA100plus','AAAbrief','AA100plus','AAbrief','belowAA')]
    profiles = pl.read_parquet(out/'profile-support.parquet')
    counts = profiles.group_by('row_id').agg(pl.col('profile_people').min().alias('minimum_profile_people'))
    q = q.join(counts,on='row_id',how='left',validate='1:1')
    scopes += [('eligible_absent_profile',q.filter(pl.col('msc_eligible')&(pl.col('minimum_profile_people')==0))),
               ('eligible_sparse_profile',q.filter(pl.col('msc_eligible')&(pl.col('minimum_profile_people')<20))),
               ('eligible_upper_minors',q.filter(pl.col('msc_eligible')&(pl.col('stage')=='Upper minors'))),
               ('eligible_lower_minors',q.filter(pl.col('msc_eligible')&(pl.col('stage')=='Lower minors')))]
    scores = []
    for name,g in scopes:
        if not len(g): continue
        rates = {arm:losses(g,arm,'rate') for arm in arms} if g.filter(pl.col('next_pa')>0).height else None
        unweighted = None
        active = g.filter(pl.col('next_pa')>0)
        if len(active):
            unweighted = {}
            for arm in arms:
                err = active[arm+'_rate'].to_numpy()-active['actual_future_relative_rate'].to_numpy()
                unweighted[arm] = dict(rmse=float(np.sqrt(np.mean(err**2))),mae=float(np.mean(np.abs(err))),rows=len(active))
        scores.append(dict(scope=name,rows=len(g),people=g['player_id'].n_unique(),participant_rate=rates,
            equal_active_row_rate=unweighted,actual_value=float(g['next_value'].sum()),actual_pa=int(g['next_pa'].sum()),
            predicted_pa=float(g['preseason_pa'].sum()),contribution={arm:dict(**losses(g,arm,'value'),
                predicted_total=float(g[arm+'_value'].sum())) for arm in arms+(['steamer'] if name=='public' else [])}))
    intervals = []
    for label,g in [('eligible',q.filter(pl.col('msc_eligible'))),('eligible_predebut',q.filter(pl.col('msc_eligible')&(pl.col('prior_debut')==0))),('all',q)]:
        for control in ['combined','minor_coverage']:
            for kind in ['rate','value']:
                if kind == 'rate' and label == 'all': continue
                intervals.append(dict(scope=label,**interval(g,'minor_measurements',control,kind)))
    selected = {}
    def select(frame,reason):
        if len(frame): selected.setdefault(frame['row_id'][0],[]).append(reason)
    fixed = prep.read(prep.SOURCE/'player-source-walkthrough.json')
    for c in fixed['cases']: select(q.filter(pl.col('row_id')==c['origin']['row_id']),'fixed source case before fit')
    err = q.filter(pl.col('msc_eligible')).with_columns(
        ((pl.col('combined_value')-pl.col('next_value'))**2-(pl.col('minor_measurements_value')-pl.col('next_value'))**2).alias('gain'),
        (pl.col('minor_measurements_value')-pl.col('next_value')).alias('error'))
    for frame,label in [(err.sort('gain','row_id',descending=[True,False]),'largest gain'),(err.sort('gain','row_id'),'largest harm'),
        (err.sort('error','row_id',descending=[True,False]),'false high'),(err.sort('error','row_id'),'false low'),
        (err.filter(pl.col('next_pa').is_between(100,600)).with_columns(pl.col('error').abs().alias('abs_error')).sort('abs_error','row_id'),'ordinary active')]:
        select(frame,label)
    dated = pl.read_parquet(prep.ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet')
    annual = pl.read_parquet(out/'annual-launch-features.parquet'); cases = []
    for rid,reasons in selected.items():
        o = q.filter(pl.col('row_id')==rid).row(0,named=True)
        c = next(c for c in pre['cells'] if (c['year'],c['fold'])==(o['origin_year'],o['outer_fold']))
        f = pl.read_parquet(out/f'features-{c["fold"]}.parquet')
        _, te, _, _ = route(f,c['training_row_ids'],c['test_row_ids'],pre['minimum_context_people'])
        row = te.filter(pl.col('row_id')==rid)
        traces = {}
        for h in prep.read(out/f'fit-{c["year"]}-{c["fold"]}.json')['heads']:
            t = linear_trace(joblib.load(h['path']),row,h['features'])
            assert np.isclose(t['replayed_raw_rate'],o[h['arm']+'_raw_rate'],atol=1e-10)
            traces[h['arm']] = t
        # Replay the actual saved head used by the combined fallback benchmark.
        if o['prior_debut'] == 0:
            p = prep.BRIDGE/f'translated_ridge-{c["year"]}-{c["fold"]}.joblib'
            names = prep.read(prep.BRIDGE/'preflight.json')['features']['translated_ridge']; branch = 'translated_prospect'
        elif o['sc_tracked']:
            p = prep.mlb.OUT/f'ridge_measurements-{c["year"]}-{c["fold"]}.joblib'
            names = prep.read(prep.mlb.OUT/'preflight.json')['arms']['ridge_measurements']; branch = 'MLB_tracking'
        else:
            old = prep.ROOT/f'reports/generated/practical-hitter-numeric-repair-v53/fit-{c["year"]}-{c["fold"]}.json'
            h = next(h for h in prep.read(old)['heads'] if h['head']=='rate'); p = Path(h['path'])
            names = prep.read(prep.ROOT/'reports/generated/practical-hitter-numeric-repair-v53/preflight.json')['rate_features']; branch = 'current_rate'
        traces['combined_benchmark'] = dict(branch=branch,path=str(p),sha256=sha256_file(p),**linear_trace(joblib.load(p),row,names))
        assert np.isclose(traces['combined_benchmark']['replayed_raw_rate'],o['combined_rate'],atol=1e-10)
        # Every distance term is origin-known. Real PA by level replaces a label.
        pool = q.filter((pl.col('origin_year')==o['origin_year'])&(pl.col('prior_debut')==o['prior_debut'])&(pl.col('player_id')!=o['player_id']))
        distance = ((pl.col('age')-o['age'])/3)**2+((pl.col('pa_0')-o['pa_0'])/300)**2
        for b in ['AAA','AA','Aplus','A','DSL']:
            distance += ((pl.col(f'pooled_{b}_pa')-o[f'pooled_{b}_pa'])/300)**2
        distance += (pl.col('scout_rank_score_0')-o['scout_rank_score_0'])**2+(pl.col('draft_rank')-o['draft_rank'])**2
        distance += .25*(pl.col('draft_known')-o['draft_known'])**2
        peers = pool.with_columns(distance.alias('peer_distance')).sort('peer_distance','player_id').head(4)
        peer_rows = []
        fields = ['row_id','player_id','player_name','age','snapshot_level','msc_eligible','msc_own_ev_n',
            'pooled_AAA_pa','pooled_AA_pa','pooled_Aplus_pa','pooled_A_pa','pooled_DSL_pa','draft_known','draft_rank',
            'scout_listed_0','scout_rank_score_0','preseason_pa','combined_rate','minor_coverage_rate','minor_measurements_rate',
            'combined_value','minor_measurements_value','next_pa','next_value','peer_distance']
        for p in peers.iter_rows(named=True):
            peer_rows.append(dict(**{k:p[k] for k in fields},actual_future_relative_rate=p['actual_future_relative_rate'] if p['next_pa']>0 else None,
                dated_production=dated.filter((pl.col('player_id')==p['player_id'])&pl.col('season').is_between(o['origin_year']-2,o['origin_year'])).to_dicts()))
        o['actual_future_relative_rate'] = o['actual_future_relative_rate'] if o['next_pa']>0 else None
        launch = annual.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(o['origin_year']-2,o['origin_year']))
        refs = prep.read(out/f'calibration-{c["fold"]}.json')['references']
        wanted = {(r['season'],r['league_id']) for r in launch.iter_rows(named=True)}
        cases.append(dict(origin=o,selection=reasons,actual_inputs=row.select(pre['arms']['minor_measurements']).to_dicts()[0],
            source_history=dated.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(o['origin_year']-2,o['origin_year'])).to_dicts(),
            actual_history=dated.filter((pl.col('player_id')==o['player_id'])&(pl.col('season')==o['target_year'])).to_dicts(),
            launch_history=launch.to_dicts(),league_references=[r for r in refs if (r['season'],r['league_id']) in wanted],
            training_context=c['league_context'],training_profiles=profiles.filter(pl.col('row_id')==rid).to_dicts(),
            saved_traces=traces,peers=peer_rows,exact_fallback=not o['msc_eligible']))
    prep.write('scores.json',dict(scopes=scores,intervals=intervals,replayed_heads=replayed,
        player_walkthrough_status='pending',no_final_disposition=True,score_runner_sha256=sha256_file(Path(__file__))))
    prep.write('cases.json',dict(cases=cases,player_walkthrough_status='pending',
        peer_rule='Same origin/debut; nearest actual level exposure, age, MLB PA, rank and draft pedigree. No future outcomes.'))
    q.write_parquet(out/'scored-predictions.parquet')
    for s in scores[:4]:
        print(s['scope'],'rate',{a:round(v['rmse'],5) for a,v in (s['participant_rate'] or {}).items()},
              'value',{a:round(v['rmse'],6) for a,v in s['contribution'].items()},flush=True)
    print('Scores provisional;',replayed,'heads replayed;',len(cases),'player-origin reviews required.',flush=True)


if __name__ == '__main__':
    main()
