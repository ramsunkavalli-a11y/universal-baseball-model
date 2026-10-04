"""Locked contribution/count comparison; source review and support precede fits."""
from pathlib import Path
import json
import sys
import joblib
import numpy as np
import polars as pl
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_compatible_value import labels
from universal_baseball.hitter_talent_bridge import EVENTS, PROFILE_FEATURES, event_counts
from universal_baseball.hitter_value_integration import contribution, count_forecast, restricted_weights
from universal_baseball.mlb_event_logit import VALUES
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights
from prepare_practical_hitter_v33 import safe_matrix
import evaluate_hitter_preseason_readiness_v68 as previous

ROOT = previous.ROOT
OUT = ROOT/'reports/generated/hitter-value-integration-v76'
BRIDGE = ROOT/'reports/generated/hitter-talent-bridge-v74'
VALUE = ROOT/'reports/generated/hitter-compatible-value-v63'
COUNTS = ROOT/'reports/generated/practical-hitter-v31/counts.parquet'
CONTRACT = ROOT/'docs/hitter-value-integration-v76-contract.md'
FIXED = [(701762, 2024), (694671, 2023), (677594, 2021), (624413, 2018),
         (592450, 2024), (670867, 2017), (668804, 2018), (608475, 2017)]
HEADS = {'direct': 'full', 'active': 'active', **{'count_'+v: 'full' for v in EVENTS}}
META = ['row_id','player_id','player_name','origin_year','target_year','outer_fold',
        'horizon','next_active','next_pa','next_value','window_complete','elapsed',
        'current_state','regular_window','prior_debut','stage','minor_pa_0','age','pa_0',
        'draft_year','pick_number','draft_school_class','translation_buckets',
        'translation_total_pa','translation_supported_pa']


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def write(name, obj, compact=False):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/name).write_text(json.dumps(obj, indent=None if compact else 2,
        ensure_ascii=False, allow_nan=False, default=str)+'\n', encoding='utf8')


def verify(mapping):
    for p, h in mapping.items():
        assert sha256_file(Path(p)) == h, p


def tagged(f):
    upper = pl.col('AA_0_pa')+pl.col('AAA_0_pa')
    return previous.tagged(f).with_columns(
        pl.when(pl.col('pa_0')==0).then(0).when(pl.col('pa_0')<200).then(1)
          .when(pl.col('pa_0')<400).then(2).otherwise(3).alias('mlb_workload_band'),
        pl.when(upper==0).then(0).when(upper<100).then(1)
          .when(upper<300).then(2).otherwise(3).alias('upper_exposure_band'),
        pl.when(pl.col('quality_0') < -1).then(0).when(pl.col('quality_0')<=1)
          .then(1).otherwise(2).alias('quality_band'))


def materialize(source, unit, columns):
    assert source['row_id'].equals(unit['row_id'])
    assert source.select('player_id','origin_year','target_year','next_pa').equals(
        unit.select('player_id','origin_year','target_year','next_pa'))
    environment = ['origin_env_'+e for e in EVENTS]
    extra = unit.select('row_id', *environment, *['count_'+e for e in EVENTS],
        pl.col('origin_replacement_rate').alias('value_replacement_rate'),
        'origin_index', pl.col('common_value_label').alias('value_target'))
    f = source.join(extra, on='row_id', validate='1:1').sort('row_id')
    f = f.with_columns(pl.col('next_value').alias('legacy_next_value'),
                      pl.col('value_target').alias('next_value'))
    selected = list(dict.fromkeys([*META,*columns,'legacy_next_value','value_target',
        'origin_index',*['count_'+e for e in EVENTS],
        *['translated_probability_'+e for e in EVENTS]]))
    assert set(selected) <= set(f.columns), set(selected)-set(f.columns)
    return f.select(selected)


def prepare():
    assert not (OUT/'preflight.json').exists(), 'Preserve sealed preparation'
    prior_review = read(ROOT/'reports/generated/hitter-team-record-v75/report.json')
    assert prior_review['player_walkthrough_status']=='complete'
    verify(prior_review['source_and_execution_hashes']); verify(prior_review['review_hashes'])
    old_pre = read(previous.OUT/'preflight.json')
    bridge_pre = read(BRIDGE/'preflight.json')
    verify(bridge_pre['input_hashes'])
    assert read(BRIDGE/'report.json')['player_walkthrough_status']=='complete'
    anchor = pl.read_parquet(previous.OUT/'scored-predictions.parquet').sort('row_id')
    old = pl.read_parquet(previous.OUT/'features.parquet').sort('row_id')
    unit = pl.read_parquet(VALUE/'features.parquet').sort('row_id')
    assert len(old)==len(unit)==63282 and len(anchor)==30506
    cols = old_pre['pa_features']+PROFILE_FEATURES+['origin_env_'+e for e in EVENTS]+['value_replacement_rate']
    assert len(cols)==272 and len(set(cols))==len(cols)
    assert not any(c.startswith(('next_','count_','target_env_')) for c in cols)
    history = pl.read_parquet(COUNTS)
    assert history['season'].max()==2025
    mlb = history.filter(pl.col('bucket')=='MLB').sort('player_id','season')
    actual = event_counts(mlb)
    dated = mlb.select('player_id',pl.col('season').alias('target_year'),
        *[pl.Series('raw_'+e,actual[:,i]) for i,e in enumerate(EVENTS)])
    joined = unit.select('row_id','player_id','target_year','next_pa').join(dated,
        on=['player_id','target_year'],how='left',validate='m:1').sort('row_id')
    assert joined.filter(pl.col('raw_other').is_null() & (pl.col('next_pa')>0)).is_empty()
    raw = joined.select([pl.col('raw_'+e).fill_null(0) for e in EVENTS]).to_numpy()
    assert np.array_equal(raw, unit.select(['count_'+e for e in EVENTS]).to_numpy())
    assert np.array_equal(raw.sum(1), unit['next_pa'].to_numpy())
    origin = unit.select(['origin_env_'+e for e in EVENTS]).to_numpy()
    target = unit.select(['target_env_'+e for e in EVENTS]).to_numpy()
    z = labels(raw,origin,target,unit['origin_replacement_rate'].to_numpy())
    assert np.allclose(z['common_value'],unit['common_value_label'],atol=1e-10,rtol=0)
    assert np.allclose(origin@VALUES,unit['origin_index'],atol=1e-12,rtol=0)
    ev = unit.filter(pl.col('row_id').is_in(anchor['row_id'].to_list())).sort('row_id')
    assert ev['row_id'].equals(anchor['row_id'])
    assert np.allclose(ev['common_value_label'],anchor['next_value'],atol=1e-10,rtol=0)
    assert np.allclose(ev['origin_replacement_rate'],anchor['origin_replacement_rate'],atol=1e-12,rtol=0)
    assert np.allclose(anchor['preseason_pa']*(anchor['baseline_rate']/600+anchor['origin_replacement_rate']),
                       anchor['preseason_value'],atol=1e-10,rtol=0)
    paths = [CONTRACT, Path(__file__), ROOT/'src/universal_baseball/hitter_value_integration.py',
        ROOT/'src/universal_baseball/hitter_compatible_value.py',ROOT/'src/universal_baseball/hitter_talent_bridge.py',
        ROOT/'src/universal_baseball/forecast_validation.py',ROOT/'scripts/prepare_practical_hitter_v33.py',
        ROOT/'scripts/fit_practical_hitter_v31.py',previous.OUT/'features.parquet',previous.OUT/'preflight.json',
        previous.OUT/'scored-predictions.parquet',VALUE/'features.parquet',COUNTS,BRIDGE/'preflight.json',
        BRIDGE/'scored-predictions.parquet',BRIDGE/'report.json']
    graphs = []
    OUT.mkdir(parents=True, exist_ok=True)
    for k in range(5):
        path = BRIDGE/f'features-{k}.parquet'; gp = BRIDGE/f'translation-{k}.json'
        source = pl.read_parquet(path).sort('row_id')
        assert source.select(old.columns).equals(old)
        for g in read(gp)['graphs']:
            assert g['held_fold']==k and g['max_source_year']<=g['cutoff']
            assert all(player_fold(pid)!=k for pid in g['people'])
            graphs.append(dict(fold=k,cutoff=g['cutoff'],max_source_year=g['max_source_year'],
                               people=len(g['people']),pairs=g['pair_count']))
        materialize(source,unit,cols).write_parquet(OUT/f'features-{k}.parquet')
        paths += [path,gp,OUT/f'features-{k}.parquet']
    cells, supports, profiles, ranges, replays = [], [], [], [], []
    with threadpool_limits(limits=2):
        for c in old_pre['cells']:
            y,k = c['year'],c['fold']
            f = pl.read_parquet(OUT/f'features-{k}.parquet')
            tr = f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q = anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            assert te['row_id'].equals(q['row_id'])
            notes = {}
            for kind, sub in [('full',tr),('active',tr.filter(pl.col('next_pa')>0))]:
                sup,note = preflight(sub,te,cutoff=y,fold=k,features=cols,
                                     expected_keys=te.select('row_id','horizon').iter_rows())
                assert np.isfinite(sub['value_target'].to_numpy()).all()
                assert (sub.select(['count_'+e for e in EVENTS]).to_numpy()>=0).all()
                notes[kind] = note
                supports.append(sup.with_columns(pl.lit(kind).alias('subset')))
                a,b = tagged(sub),tagged(te)
                for label,keys in [('broad',['prior_debut','stage','age_band','rank_band']),
                    ('refined',['prior_debut','stage','age_band','rank_band','new_draftee','thin_pro',
                                'mlb_workload_band','upper_exposure_band','quality_band'])]:
                    n = a.group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
                    profiles.append(b.select('row_id',*keys).join(n,on=keys,how='left',validate='m:1').with_columns(
                        pl.col('profile_people').fill_null(0),pl.lit(kind).alias('subset'),pl.lit(label).alias('kind')))
                x,tx = sub.select(cols).to_numpy(),te.select(cols).to_numpy()
                for i,n in enumerate(cols):
                    lo,hi=float(x[:,i].min()),float(x[:,i].max())
                    ranges.append(dict(year=y,fold=k,subset=kind,feature=n,minimum=lo,maximum=hi,
                        outside=int(((tx[:,i]<lo)|(tx[:,i]>hi)).sum())))
            for h in read(previous.OUT/f'fit-{y}-{k}.json')['heads']:
                verify({h['path']:h['sha256']});m=joblib.load(h['path'])
                x=te.select(old_pre['pa_features']).to_numpy()
                pred=m.predict_proba(x)[:,1] if h['head']=='participation' else m.predict(x)
                label='preseason_raw_p' if h['head']=='participation' else 'preseason_raw_conditional_pa'
                assert np.allclose(pred,q[label],atol=1e-10,rtol=0)
                replays.append(h)
            oldrate=read(ROOT/f'reports/generated/practical-hitter-numeric-repair-v53/fit-{y}-{k}.json')
            h=next(h for h in oldrate['heads'] if h['head']=='rate')
            rate_cols=read(ROOT/'reports/generated/practical-hitter-numeric-repair-v53/preflight.json')['rate_features']
            verify({h['path']:h['sha256']})
            assert np.allclose(joblib.load(h['path']).predict(safe_matrix(te,rate_cols)),q['baseline_rate'],atol=1e-10,rtol=0)
            replays.append(h)
            cells.append(dict(**c,integration_checks=notes))
            print(f'Full/active checks and three current-head replays: {y}/{k}',flush=True)
    pl.concat(supports).write_parquet(OUT/'support.parquet')
    pl.concat(profiles,how='diagonal_relaxed').write_parquet(OUT/'profile-support.parquet')
    pl.DataFrame(ranges).write_parquet(OUT/'feature-ranges.parquet')
    paths += [OUT/'support.parquet',OUT/'profile-support.parquet',OUT/'feature-ranges.parquet']
    cases=[]
    for pid,y in FIXED:
        r=ev.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y))
        assert len(r)==1,(pid,y)
        o=r.row(0,named=True);q=anchor.filter(pl.col('row_id')==o['row_id']).row(0,named=True)
        counts=[o['count_'+e] for e in EVENTS]
        cases.append(dict(player_id=pid,name=o['player_name'],origin_year=y,next_pa=o['next_pa'],
            events=dict(zip(EVENTS,counts)),origin_environment={e:o['origin_env_'+e] for e in EVENTS},
            origin_index=o['origin_index'],replacement=o['origin_replacement_rate'],
            reconstructed_value=float(contribution(np.array([counts]),[o['origin_index']],[o['origin_replacement_rate']])[1][0]),
            saved_actual_value=q['next_value'],current_pa=q['preseason_pa'],current_rate=q['baseline_rate'],
            current_value=q['preseason_value'],history=history.filter((pl.col('player_id')==pid)&
                pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts()))
    write('source-reconciliation.json',dict(cases=cases,counts_exact=True,common_value_labels_reconstructed=True,
        target_environment_is_not_predictor=True,source_case_review_status='pending',rows=63282,evaluation_rows=30506))
    paths.append(OUT/'source-reconciliation.json')
    write('preflight.json',dict(cells=cells,features=cols,head_subsets=HEADS,settings=old_pre['settings'],
        input_hashes={str(p):sha256_file(p) for p in paths},baseline_heads=replays,baseline_heads_replayed=105,
        actual_full_active_checks=70,new_heads_expected=350,graph_provenance=graphs,
        sklearn_version=sklearn.__version__,fixed_cases=FIXED,protected_outcomes_used=False),compact=True)
    print('Preparation sealed; actual source review required before fits.',flush=True)


def fit():
    pre=read(OUT/'preflight.json');verify(pre['input_hashes'])
    review=read(OUT/'source-review.json')
    assert review['source_case_review_status']=='complete'
    assert review['preflight_sha256']==sha256_file(OUT/'preflight.json')
    verify(review['review_hashes'])
    anchor=pl.read_parquet(previous.OUT/'scored-predictions.parquet').sort('row_id')
    bridge=pl.read_parquet(BRIDGE/'scored-predictions.parquet').sort('row_id')
    assert bridge['row_id'].equals(anchor['row_id'])
    allnotes=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];pp=OUT/f'forecast-{y}-{k}.parquet'
            if pp.exists():
                note=read(OUT/f'fit-{y}-{k}.json');verify({str(pp):note['prediction_sha256']})
                verify({h['path']:h['sha256'] for h in note['heads']});allnotes.append(note);continue
            f=pl.read_parquet(OUT/f'features-{k}.parquet')
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q=anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            b=bridge.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            assert te['row_id'].equals(q['row_id']) and te['row_id'].equals(b['row_id'])
            q=q.with_columns(pl.col('preseason_pa').alias('current_pa'),pl.col('preseason_p').alias('current_p'),
                pl.col('preseason_conditional_pa').alias('current_conditional_pa'),
                pl.col('preseason_rate').alias('current_rate'),pl.col('preseason_value').alias('current_value'),
                b['translated_ridge_value'].alias('bridge_value'),pl.col('preseason_pa').alias('bridge_pa'))
            predictions={};heads=[];fullw=weights(tr);active=tr['next_pa'].to_numpy()>0
            tx=te.select(pre['features']).to_numpy()
            for head,kind in pre['head_subsets'].items():
                sub=tr.filter(pl.col('next_pa')>0) if kind=='active' else tr
                mp=OUT/f'{head}-{y}-{k}.joblib';npth=OUT/f'{head}-{y}-{k}.json'
                target='value_target' if head in ['direct','active'] else head
                if mp.exists() or npth.exists():
                    assert mp.exists() and npth.exists(),'Incomplete model save requires explicit recovery'
                    note=read(npth);verify({str(mp):note['sha256']})
                    assert note['preflight_sha256']==sha256_file(OUT/'preflight.json')
                    m=joblib.load(mp)
                else:
                    m=HistGradientBoostingRegressor(**pre['settings'],loss='poisson' if head.startswith('count_') else 'squared_error')
                    w=restricted_weights(fullw,active) if kind=='active' else fullw
                    m.fit(sub.select(pre['features']).to_numpy(),sub[target].to_numpy(),sample_weight=w)
                    joblib.dump(m,mp,compress=3)
                    note=dict(head=head,subset=kind,path=str(mp),sha256=sha256_file(mp),target=target,
                        training_rows=len(sub),training_people=sub['player_id'].n_unique(),
                        max_target_year=int(sub['target_year'].max()),preflight_sha256=sha256_file(OUT/'preflight.json'))
                    write(npth.name,note)
                pred=m.predict(tx);assert np.isfinite(pred).all()
                assert np.allclose(joblib.load(mp).predict(tx),pred,atol=1e-10,rtol=0)
                if head.startswith('count_'):assert (pred>=0).all()
                predictions[head]=pred;heads.append(note)
                print(f'Saved/replayed {y}/{k} {head}',flush=True)
            hard=q['hard_unavailable'].to_numpy()|q['reported_retired'].to_numpy()
            direct=predictions['direct'].copy();direct[hard]=0
            activevalue=q['current_p'].to_numpy()*predictions['active'];activevalue[hard]=0
            rawcounts=np.column_stack([predictions['count_'+e] for e in EVENTS])
            counts=count_forecast(rawcounts,hard,te['origin_index'].to_numpy(),te['value_replacement_rate'].to_numpy())
            q=q.with_columns(pl.Series('direct_raw',predictions['direct']),pl.Series('direct_value',direct),
                pl.Series('active_raw',predictions['active']),pl.Series('active_value',activevalue),
                pl.col('current_pa').alias('direct_pa'),pl.col('current_pa').alias('active_pa'),
                pl.Series('counts_pa',counts['pa']),pl.Series('counts_value',counts['value']),
                pl.Series('counts_capped',counts['capped']),pl.Series('counts_scale',counts['scale']),
                *[pl.Series('counts_raw_'+e,rawcounts[:,i]) for i,e in enumerate(EVENTS)],
                *[pl.Series('counts_mean_'+e,counts['counts'][:,i]) for i,e in enumerate(EVENTS)])
            assert q.select(anchor.columns).equals(anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id'))
            q.write_parquet(pp);note=dict(year=y,fold=k,heads=heads,prediction_sha256=sha256_file(pp))
            write(f'fit-{y}-{k}.json',note);allnotes.append(note)
    q=pl.concat([pl.read_parquet(OUT/f"forecast-{c['year']}-{c['fold']}.parquet") for c in pre['cells']]).sort('row_id')
    assert len(q)==30506 and q.select(anchor.columns).equals(anchor)
    q.write_parquet(OUT/'predictions.parquet');write('fits.json',allnotes)
    write('fit-report.json',dict(new_heads=350,baseline_heads_replayed_before_fits=105,
        original_forecasts_bit_exact=True,player_walkthrough_status='pending',protected_outcomes_used=False,
        current_candidate_changed=False,frozen_forecast_changed=False))


if __name__=='__main__':
    {'prepare':prepare,'fit':fit}[sys.argv[1]]()
