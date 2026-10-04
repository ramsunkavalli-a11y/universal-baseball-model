"""Locked record versus coverage-control opportunity comparison and replay."""
from pathlib import Path
import json
import sys
import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from universal_baseball.forecast_validation import preflight
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights
from score_practical_hitter_v31 import paired
from score_hitter_readiness_v49 import probability_score
from evaluate_hitter_readiness_v49 import logit_trace
import source_hitter_team_record_v75 as source

ROOT, OUT = source.ROOT, source.OUT
PREVIOUS = source.previous.OUT
ARMS = ['coverage', 'record']


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def write(name, obj, compact=False):
    (OUT/name).write_text(json.dumps(obj, indent=None if compact else 2, ensure_ascii=False,
                                   allow_nan=False, default=str)+'\n', encoding='utf8')


def verify_hashes(mapping):
    for p, h in mapping.items():
        assert sha256_file(Path(p)) == h, p


def tagged(f):
    return source.previous.tagged(f).with_columns(
        pl.when(pl.col('org_record_known') == 0).then(-1)
        .when(pl.col('org_record_centered') < -.05).then(0)
        .when(pl.col('org_record_centered') <= .05).then(1).otherwise(2).alias('record_band'))


def prepare():
    assert not (OUT/'preflight.json').exists(), 'Preserve sealed preflight'
    sr = read(OUT/'source-review.json')
    assert sr['player_walkthrough_status'] == 'complete_for_source_only'
    verify_hashes(sr['source_hashes']); verify_hashes(sr['review_hashes'])
    assert sha256_file(OUT/'features.parquet') == sr['features_sha256']
    assert read(ROOT/'reports/generated/hitter-talent-bridge-v74/report.json')['player_walkthrough_status'] == 'complete'
    f = pl.read_parquet(OUT/'features.parquet').sort('row_id')
    old = pl.read_parquet(PREVIOUS/'features.parquet').sort('row_id')
    anchor = pl.read_parquet(PREVIOUS/'scored-predictions.parquet').sort('row_id')
    assert f.select(old.columns).equals(old) and len(f) == 63282 and len(anchor) == 30506
    previous = read(PREVIOUS/'preflight.json'); original = previous['pa_features']
    assert len(original) == 251
    columns = {'coverage': original+['org_record_known'], 'record': original+['org_record_known','org_record_centered']}
    supports, profiles, cells, ranges, baseline_heads = [], [], [], [], []
    with threadpool_limits(limits=2):
        for c in previous['cells']:
            tr = f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q = anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            assert te['row_id'].equals(q['row_id'])
            note = read(PREVIOUS/f"fit-{c['year']}-{c['fold']}.json")
            for h in note['heads']:
                assert sha256_file(Path(h['path'])) == h['sha256']
                m = joblib.load(h['path']); x = te.select(original).to_numpy()
                pred = m.predict_proba(x)[:,1] if h['head']=='participation' else m.predict(x)
                col = 'preseason_raw_p' if h['head']=='participation' else 'preseason_raw_conditional_pa'
                assert np.allclose(pred, q[col], atol=1e-10, rtol=0)
                baseline_heads.append(dict(year=c['year'], fold=c['fold'], **h))
            checks = {}
            for arm, cols in columns.items():
                for head, sub in [('participation', tr), ('conditional_pa', tr.filter(pl.col('next_pa')>0))]:
                    sup, n = preflight(sub, te, cutoff=c['year'], fold=c['fold'], features=cols,
                                       expected_keys=te.select('row_id','horizon').iter_rows())
                    checks[arm+'_'+head] = n
                    supports.append(sup.with_columns(pl.lit(arm).alias('arm'), pl.lit(head).alias('head')))
                    a, b = tagged(sub), tagged(te)
                    for kind, keys in [('broad', ['prior_debut','stage','age_band','rank_band','record_band']),
                                       ('refined', ['prior_debut','stage','age_band','rank_band','record_band','new_draftee','thin_pro'])]:
                        counts = a.group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
                        profiles.append(b.select('row_id',*keys).join(counts,on=keys,how='left',validate='m:1').with_columns(
                            pl.col('profile_people').fill_null(0),pl.lit(arm).alias('arm'),pl.lit(head).alias('head'),pl.lit(kind).alias('kind')))
                    known = sub.filter(pl.col('org_record_known')==1)['org_record_centered']
                    assert len(known)
                    outside = te.filter((pl.col('org_record_known')==1)&
                        ((pl.col('org_record_centered')<known.min())|(pl.col('org_record_centered')>known.max())))
                    ranges.append(dict(year=c['year'],fold=c['fold'],arm=arm,head=head,
                        minimum_known_win_pct=float(known.min()+.5),maximum_known_win_pct=float(known.max()+.5),
                        test_outside_rows=outside['row_id'].to_list()))
            cells.append(dict(**c,record_checks=checks))
    pl.concat(supports).write_parquet(OUT/'support.parquet')
    pl.concat(profiles,how='diagonal_relaxed').write_parquet(OUT/'profile-support.parquet')
    write('record-ranges.json', ranges)
    paths = [OUT/'source-review.json', OUT/'source-report.json', OUT/'features.parquet',
             PREVIOUS/'preflight.json',PREVIOUS/'scored-predictions.parquet',
             OUT/'support.parquet',OUT/'profile-support.parquet',OUT/'record-ranges.json',
             ROOT/'docs/hitter-team-record-v75-contract.md',ROOT/'docs/hitter-team-record-v75-source-amendment.md',
             Path(__file__),ROOT/'scripts/fit_practical_hitter_v31.py',ROOT/'src/universal_baseball/forecast_validation.py']
    write('preflight.json',dict(cells=cells,arms=columns,original_features=original,settings=previous['settings'],
        input_hashes={str(p):sha256_file(p) for p in paths},baseline_heads=baseline_heads,
        checks_before_fitting=140,baseline_heads_replayed=70,source_rows=63282,evaluation_rows=30506,
        new_rate_models=False,protected_outcomes_used=False),compact=True)
    print('All 140 full/active checks saved; 70 current heads replayed before fitting.',flush=True)


def fit():
    pre = read(OUT/'preflight.json'); verify_hashes(pre['input_hashes'])
    for h in pre['baseline_heads']:
        assert sha256_file(Path(h['path'])) == h['sha256']
    f = pl.read_parquet(OUT/'features.parquet')
    anchor = pl.read_parquet(PREVIOUS/'scored-predictions.parquet').sort('row_id')
    fits = []
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y, k = c['year'], c['fold']; path = OUT/f'forecast-{y}-{k}.parquet'
            if path.exists():
                note = read(OUT/f'fit-{y}-{k}.json')
                assert sha256_file(path) == note['prediction_sha256']
                for h in note['heads']:
                    assert sha256_file(Path(h['path'])) == h['sha256']
                fits.append(note); continue
            tr = f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q = anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            assert q['row_id'].equals(te['row_id'])
            q = q.with_columns(pl.col('preseason_p').alias('current_p'),
                               pl.col('preseason_conditional_pa').alias('current_conditional_pa'),
                               pl.col('preseason_pa').alias('current_pa'),pl.col('preseason_value').alias('current_value'))
            hard = (q['hard_unavailable']|q['reported_retired']).to_numpy()
            prior = q['prior_debut'].to_numpy().astype(bool); notes=[]
            for arm, cols in pre['arms'].items():
                raw = {}
                for head, sub in [('participation',tr),('conditional_pa',tr.filter(pl.col('next_pa')>0))]:
                    cls = HistGradientBoostingClassifier if head=='participation' else HistGradientBoostingRegressor
                    m = cls(**pre['settings']); x = sub.select(cols).to_numpy()
                    m.fit(x, sub['next_active' if head=='participation' else 'next_pa'].to_numpy(),sample_weight=weights(sub))
                    tx = te.select(cols).to_numpy(); raw[head] = m.predict_proba(tx)[:,1] if head=='participation' else m.predict(tx)
                    assert np.isfinite(raw[head]).all()
                    artifact = OUT/f'{arm}-{head}-{y}-{k}.joblib'; joblib.dump(m,artifact,compress=3)
                    notes.append(dict(arm=arm,head=head,path=str(artifact),sha256=sha256_file(artifact),
                        training_rows=len(sub),training_people=sub['player_id'].n_unique(),maximum_target_year=int(sub['target_year'].max())))
                p = raw['participation'].copy(); p[hard]=0.; conditional=np.clip(raw['conditional_pa'],1,800)
                q=q.with_columns(pl.Series(arm+'_raw_p',raw['participation']),pl.Series(arm+'_raw_conditional_pa',raw['conditional_pa']))
                for label, pp, cc in [(arm+'_all',p,conditional),
                                     (arm,np.where(prior,q['current_p'].to_numpy(),p),
                                      np.where(prior,q['current_conditional_pa'].to_numpy(),conditional))]:
                    pa=pp*cc
                    q=q.with_columns(pl.Series(label+'_p',pp),pl.Series(label+'_conditional_pa',cc),pl.Series(label+'_pa',pa),
                        pl.Series(label+'_value',pa*(q['baseline_rate'].to_numpy()/600+q['origin_replacement_rate'].to_numpy())))
                    # Preserve archived established means exactly, including float rounding.
                    if label==arm:
                        q=q.with_columns(pl.when(pl.col('prior_debut')==1).then(pl.col('current_pa')).otherwise(pl.col(label+'_pa')).alias(label+'_pa'),
                            pl.when(pl.col('prior_debut')==1).then(pl.col('current_value')).otherwise(pl.col(label+'_value')).alias(label+'_value'))
            assert q.select(anchor.columns).equals(anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id'))
            q.write_parquet(path); note=dict(year=y,fold=k,heads=notes,prediction_sha256=sha256_file(path))
            write(f'fit-{y}-{k}.json',note);fits.append(note)
            print(f'Record test {y}/{k}: four heads saved.',flush=True)
    q=pl.concat([pl.read_parquet(OUT/f"forecast-{c['year']}-{c['fold']}.parquet") for c in pre['cells']]).sort('row_id')
    assert len(q)==30506 and q.select(anchor.columns).equals(anchor)
    q.write_parquet(OUT/'predictions.parquet');write('fits.json',fits)
    write('fit-report.json',dict(new_heads=140,player_walkthrough_status='pending',unchanged_hitting=True,
        protected_outcomes_used=False,frozen_forecast_changed=False,preflight_sha256=sha256_file(OUT/'preflight.json')))


def scoring():
    pre=read(OUT/'preflight.json');verify_hashes(pre['input_hashes'])
    source_frame=pl.read_parquet(OUT/'features.parquet')
    anchor=pl.read_parquet(PREVIOUS/'scored-predictions.parquet').sort('row_id')
    q=pl.read_parquet(OUT/'predictions.parquet').sort('row_id');assert q.select(anchor.columns).equals(anchor)
    replayed=0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            te=source_frame.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            part=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            note=read(OUT/f"fit-{c['year']}-{c['fold']}.json")
            assert sha256_file(OUT/f"forecast-{c['year']}-{c['fold']}.parquet")==note['prediction_sha256']
            for h in note['heads']:
                assert sha256_file(Path(h['path']))==h['sha256'];m=joblib.load(h['path']);x=te.select(pre['arms'][h['arm']]).to_numpy()
                pred=m.predict_proba(x)[:,1] if h['head']=='participation' else m.predict(x)
                col=h['arm']+('_raw_p' if h['head']=='participation' else '_raw_conditional_pa')
                assert np.allclose(pred,part[col],atol=1e-10,rtol=0);replayed+=1
    arms=['current','coverage','record','coverage_all','record_all']
    for arm in arms[1:]:
        assert np.allclose(q[arm+'_pa'],q[arm+'_p']*q[arm+'_conditional_pa'],atol=1e-10,rtol=0)
        assert np.allclose(q[arm+'_value'],q[arm+'_pa']*(q['baseline_rate']/600+q['origin_replacement_rate']),atol=1e-10,rtol=0)
        assert q.filter(pl.col('hard_unavailable')|pl.col('reported_retired'))[arm+'_pa'].sum()==0
    for arm in ARMS:
        g=q.filter(pl.col('prior_debut')==1)
        for metric in ['p','conditional_pa','pa','value']:
            assert g[arm+'_'+metric].equals(g['current_'+metric])
    ctx=[c for c in source_frame.columns if c.startswith('org_record_') or c.startswith('context_')]
    q=q.join(source_frame.select('row_id',*ctx,pl.col('scout_rank_score_0').alias('fresh_rank'),
        pl.col('scout_listed_0').alias('fresh_listed')),on='row_id',validate='1:1')
    q=tagged(q);q.write_parquet(OUT/'scored-predictions.parquet')
    public=q.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null());assert len(public)==2627
    scopes=[('all',q),('never_debut',q.filter(pl.col('prior_debut')==0)),('public_matched',public),
        ('upper_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),
        ('lower_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))),
        ('new_draftees',q.filter((pl.col('draft_known')==1)&(pl.col('draft_year')==pl.col('origin_year'))))]
    scopes += [('origin_'+str(y),q.filter(pl.col('origin_year')==y)) for y in sorted(q['origin_year'].unique())]
    scopes += [('prospect_record_'+str(b),q.filter((pl.col('prior_debut')==0)&(pl.col('record_band')==b))) for b in [-1,0,1,2]]
    scopes += [('prospect_record_known',q.filter((pl.col('prior_debut')==0)&(pl.col('org_record_known')==1)))]
    scores=[];intervals=[]
    with threadpool_limits(limits=2):
        for label,g in scopes:
            if not len(g):continue
            scores.append(dict(scope=label,rows=len(g),people=g['player_id'].n_unique(),actual_pa=int(g['next_pa'].sum()),
                actual_value=float(g['next_value'].sum()),scores={a:score(g,a) for a in arms+(['steamer'] if label=='public_matched' else [])},
                probabilities={a:probability_score(g,a) for a in arms}))
            if label in ['all','never_debut','upper_never_debut','lower_never_debut','prospect_record_known','public_matched']:
                for a,b in [('record','coverage'),('record','current'),('coverage','current'),('record_all','coverage_all')]:
                    for metric in ['pa','value']:
                        intervals.append(dict(scope=label,**paired(g,a,b,metric)))
    write('scores.json',scores);write('intervals.json',intervals)
    chosen={}
    def choose(g,why):
        assert len(g);chosen.setdefault(g['row_id'][0],[]).append(why)
    for pid,year in source.FIXED:
        choose(q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==year)),'fixed before fitting')
    for arm in ARMS:
        err=q.filter(pl.col('prior_debut')==0).with_columns(
            ((pl.col('current_pa')-pl.col('next_pa'))**2-(pl.col(arm+'_pa')-pl.col('next_pa'))**2).alias('gain'),
            (pl.col(arm+'_pa')-pl.col('next_pa')).alias('error'))
        for why,g in [('largest PA gain',err.sort('gain',descending=True)),('largest PA harm',err.sort('gain')),
            ('major false high',err.sort('error',descending=True)),('major false low',err.sort('error')),
            ('ordinary active',err.filter(pl.col('next_pa').is_between(100,600)).sort(pl.col('error').abs()))]:choose(g,arm+': '+why)
    # Separately select largest incremental record effect, not only total refit effect.
    delta=q.filter(pl.col('prior_debut')==0).with_columns(
        ((pl.col('coverage_pa')-pl.col('next_pa'))**2-(pl.col('record_pa')-pl.col('next_pa'))**2).alias('gain'))
    choose(delta.sort('gain',descending=True),'record versus coverage largest incremental gain')
    choose(delta.sort('gain'),'record versus coverage largest incremental harm')
    counts=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet')
    profiles=pl.read_parquet(OUT/'profile-support.parquet');cases=[]
    with threadpool_limits(limits=2):
        for rid,why in chosen.items():
            r=q.filter(pl.col('row_id')==rid).row(0,named=True)
            te=source_frame.filter(pl.col('row_id')==rid);oldnote=read(PREVIOUS/f"fit-{r['origin_year']}-{r['outer_fold']}.json")
            note=read(OUT/f"fit-{r['origin_year']}-{r['outer_fold']}.json");traces={};probes={}
            for arm in ['current',*ARMS]:
                traces[arm]={}
                for head in ['participation','conditional_pa']:
                    h=next(h for h in (oldnote['heads'] if arm=='current' else note['heads']) if h['head']==head and (arm=='current' or h['arm']==arm))
                    cols=pre['original_features'] if arm=='current' else pre['arms'][arm]
                    m=joblib.load(h['path']);x=te.select(cols).to_numpy()[0]
                    traces[arm][head]=logit_trace(m,x,cols) if head=='participation' else trace(m,x,cols)
                    if arm=='record':
                        for pct in [.4,.5,.6]:
                            xx=x.copy();xx[cols.index('org_record_known')]=1;xx[cols.index('org_record_centered')]=pct-.5
                            probes.setdefault(str(pct),{})[head]=float(m.predict_proba(xx[None,:])[0,1] if head=='participation' else m.predict(xx[None,:])[0])
            peers=q.filter((pl.col('origin_year')==r['origin_year'])&(pl.col('stage')==r['stage'])&
                (pl.col('prior_debut')==r['prior_debut'])&(pl.col('player_id')!=r['player_id'])).with_columns(
                (((pl.col('age')-r['age'])/3)**2+((pl.col('minor_pa_0')-r['minor_pa_0'])/250)**2+
                 4*(pl.col('fresh_rank')-r['fresh_rank'])**2).alias('distance')).sort('distance','player_id').head(4)
            cases.append(dict(origin=r,selection=why,actual_inputs=te.select(pre['arms']['record']).to_dicts()[0],
                context={k:r[k] for k in ctx},saved_traces=traces,fixed_record_probes=probes,
                probe_scope='Same saved model at .400/.500/.600; artificial team scenarios, not causal evidence or validated replacement forecasts. Primary prior-debut forecasts do not use these refits.',
                source_history=counts.filter((pl.col('player_id')==r['player_id'])&pl.col('season').is_between(r['origin_year']-2,r['origin_year'])).sort('season','bucket').to_dicts(),
                actual_history=counts.filter((pl.col('player_id')==r['player_id'])&(pl.col('season')==r['target_year'])&(pl.col('bucket')=='MLB')).to_dicts(),
                training_profiles=profiles.filter(pl.col('row_id')==rid).to_dicts(),
                peers=peers.select('player_id','player_name','age','stage','minor_pa_0','fresh_rank','context_parent','org_record_known','org_record_centered',
                    *[a+'_'+m for a in ['current',*ARMS] for m in ['p','conditional_pa','pa','value']],'next_pa','next_value').to_dicts()))
    write('cases.json',cases)
    write('verification.json',dict(new_heads_replayed=replayed,baseline_heads_replayed_before_fits=70,
        baseline_rows_bit_exact=True,prior_debut_primary_bit_exact=True,unchanged_hitting=True,
        player_walkthrough_status='pending',cases=len(cases),PA_and_value_arithmetic_verified=True,
        conditional_clips={a:int(((q[a+'_raw_conditional_pa']<1)|(q[a+'_raw_conditional_pa']>800)).sum()) for a in ARMS},
        protected_outcomes_used=False,frozen_forecast_changed=False))
    for s in scores[:6]:
        print(s['scope'], {a:{k:round(v[k],6) for k in ['pa_rmse','pa_mae','value_rmse','pa_total']} for a,v in s['scores'].items()},flush=True)
    print('Saved-model case review pending:',len(cases),flush=True)


if __name__=='__main__':
    {'prepare':prepare,'fit':fit,'score':scoring}[sys.argv[1]]()
