"""No-fit direct event conversion: prepare and seal first, then evaluate once."""
from collections import defaultdict
from pathlib import Path
import argparse

import numpy as np
import polars as pl

from universal_baseball.hitter_direct_events import convert, proper_losses, probabilities, rate_routing
from universal_baseball.hitter_shared_events import PROFILE, profile
from universal_baseball.hitter_talent_bridge import EVENTS
from universal_baseball.hitter_compatible_value import labels
from universal_baseball.storage import sha256_file
from prepare_hitter_shared_events import ROOT, GEN, BRIDGE, BORROWED, read, verify
from prepare_hitter_overseas_integration import annual_labels
from review_hitter_overseas_integration import score
from review_hitter_evidence_representation import interval, rate_interval
from supplement_hitter_overseas_scores import rate_score

OLD = GEN/'hitter-shared-events'
OUT = GEN/'hitter-direct-events'
ARMS = ['direct_domestic','direct_foreign']


def save(name, value):
    import json
    path = OUT/name
    assert not path.exists(), f'Preserve {path}'
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n',encoding='utf8',newline='\n')


def prepare():
    assert not OUT.exists() or not any(OUT.iterdir()), 'Preserve previous preparation'
    final = read(OLD/'final-review.json')
    assert final['player_walkthrough_status']=='complete' and final['cases']==45
    verify(final['artifact_hashes']); verify(read(OLD/'preflight.json')['input_hashes'])
    q = pl.read_parquet(OLD/'compatible-predictions.parquet').sort('row_id')
    assert q.height==30519 and q['origin_year'].max()==2024 and q['target_year'].max()==2025
    prior_cases = read(OLD/'completed-player-review.json')['cases']
    notes = {c['row_id']:c['source']['profile'] for c in prior_cases if c['source']}
    notes.update({c['row_id']:c['profile'] for c in read(OLD/'source-case-supplement.json')['cases']})
    assert len(notes)==45
    paths = [ROOT/'docs/hitter-direct-event-contract.md', Path(__file__),
        ROOT/'src/universal_baseball/hitter_direct_events.py', ROOT/'tests/test_hitter_direct_events.py',
        ROOT/'src/universal_baseball/hitter_compatible_value.py',ROOT/'src/universal_baseball/mlb_event_logit.py',
        OLD/'final-review.json',OLD/'compatible-predictions.parquet',OLD/'completed-player-review.json',
        OLD/'source-case-supplement.json',OLD/'profile-support.parquet',
        GEN/'practical-hitter-v31/dated-stints.parquet',GEN/'practical-hitter-v31/counts.parquet',
        GEN/'foreign-origin-inputs/origin-inputs.json',BORROWED/'profiles.json',BORROWED/'fits.json']
    parts = []
    for k in range(5):
        g = q.filter(pl.col('outer_fold')==k).sort('row_id')
        graphs = {r['cutoff']:r for r in read(BRIDGE/f'translation-{k}.json')['graphs']}
        refs = np.array([graphs[y]['mlb_reference'] for y in g['origin_year']])
        for y in g['origin_year'].unique():
            graph=graphs[y]
            assert graph['held_fold']==k and graph['max_source_year']<=y
        oldp = pl.read_parquet(BRIDGE/f'features-{k}.parquet').select('row_id','translation_supported_pa',
            *[f'translated_probability_{e}' for e in EVENTS])
        g = g.join(oldp,on='row_id',how='left',validate='1:1')
        past = g.select([f'translated_probability_{e}' for e in EVENTS]).to_numpy().astype(float)
        us = g['translation_supported_pa'].to_numpy().astype(float)
        for i,r in enumerate(g.iter_rows(named=True)):
            if r['source_addition']:
                note=notes[r['row_id']];past[i]=note['past_US_probability'];us[i]=note['US_supported_PA']
            elif r['row_id'] in notes:
                note=notes[r['row_id']]
                assert np.allclose(past[i],note['past_US_probability'],atol=1e-10,rtol=0)
                assert np.isclose(us[i],note['US_supported_PA'])
        probabilities(past); probabilities(refs)
        foreign_n = None
        for a in ['domestic','foreign']:
            path=OLD/f'{a}-features-{k}.parquet'
            f = pl.read_parquet(path).filter(pl.col('row_id').is_in(g['row_id'])).sort('row_id')
            assert f['row_id'].equals(g['row_id'])
            p = probabilities(refs + .1*f.select(PROFILE[:8]).to_numpy())
            total = np.expm1(f['shared_log_exposure'].to_numpy()*np.log(1201))
            if foreign_n is None: foreign_n=total-us
            assert np.allclose(total,us+foreign_n) and foreign_n.min()>-1e-6
            supported = (us>0) if a=='domestic' else (total>0)
            direct,terms=convert(p,refs)
            routed,used=rate_routing(direct,supported,g['prior_debut'],g['source_addition'],g['current_rate'],g['shared_'+a+'_rate'])
            pa=g['shared_'+a+'_pa'].to_numpy()
            g=g.with_columns(pl.Series('direct_'+a+'_probability',p.tolist()),pl.Series('direct_'+a+'_raw_rate',direct),
                pl.Series('direct_'+a+'_rate',routed),pl.Series('direct_'+a+'_used',used),pl.Series('direct_'+a+'_supported',supported),
                pl.Series('direct_'+a+'_pa',pa),pl.Series('direct_'+a+'_p',g['shared_'+a+'_p']),
                pl.Series('direct_'+a+'_conditional_pa',g['shared_'+a+'_conditional_pa']),
                pl.Series('direct_'+a+'_value',pa*(routed/600+g['origin_replacement_rate'].to_numpy())))
            for i,rid in enumerate(g['row_id']):
                if rid in notes:
                    assert np.allclose(p[i],notes[rid]['future_US_probability' if a=='domestic' else 'future_shared_probability'],atol=1e-10,rtol=0)
            paths.append(path)
        g=g.with_columns(pl.Series('direct_reference',refs.tolist()),pl.Series('past_US_probability',past.tolist()),
            pl.Series('US_supported_PA',us),pl.Series('foreign_supported_PA',np.maximum(foreign_n,0)))
        parts.append(g)
        paths += [BRIDGE/f'features-{k}.parquet',BRIDGE/f'translation-{k}.json']
    result=pl.concat(parts).sort('row_id')
    assert result.select(q.columns).equals(q)
    for a in ARMS:
        original=result.filter(~pl.col('source_addition'))
        assert original[a+'_pa'].equals(original['current_pa'])
        established=original.filter(pl.col('prior_debut')>0)
        assert established[a+'_rate'].equals(established['current_rate'])
    OUT.mkdir(exist_ok=True)
    result.write_parquet(OUT/'prepared.parquet')
    save('preflight.json',dict(rows=result.height,original_rows=30506,additions=13,retained_source_cases=45,
        source_profiles_checked=True,original_established_route_preserved=True,original_PA_preserved=True,
        new_fits=0,protected_outcomes_used=False,player_walkthrough_status='pending',
        prepared_sha256=sha256_file(OUT/'prepared.parquet'),input_hashes={str(p):sha256_file(p) for p in paths},
        support_limit='Existing graph, borrowed MLB persistence and active-head profile warnings remain; no new training fit'))
    print('45 saved source profiles checked; fixed 30,519 rows sealed. No scores or new fits.',flush=True)


def event_scores(g):
    rows=[]; bins=np.array([0,.05,.10,.20,.30,.50,1.])
    groups=[('US_supported',g.filter(pl.col('direct_domestic_supported')),
        [('origin_reference','direct_reference'),('past_US','past_US_probability'),('future_US','direct_domestic_probability')]),
        ('combined_supported',g.filter(pl.col('direct_foreign_supported')),
        [('origin_reference','direct_reference'),('future_combined','direct_foreign_probability')])]
    for label,h,forecasts in groups:
        h=h.filter(pl.col('next_pa')>0)
        if not h.height: continue
        counts=np.array(h['actual_events'].to_list());pa=counts.sum(1)
        years=h['origin_year'].to_numpy()
        weights=np.zeros(h.height)
        for y in np.unique(years):
            mask=years==y;weights[mask]=pa[mask]/pa[mask].sum()/len(np.unique(years))
        assert np.isclose(weights.sum(),1)
        scored={}; calibration={}
        for a,col in forecasts:
            p=np.array(h[col].to_list());ll,br=proper_losses(p,counts)
            scored[a]=dict(logloss=float(weights@ll),multiclass_brier=float(weights@br),
                predicted_frequency=(weights@p).tolist(),actual_frequency=(weights@(counts/pa[:,None])).tolist())
            c=[]
            for j,e in enumerate(EVENTS):
                for lo,hi in zip(bins[:-1],bins[1:]):
                    z=(p[:,j]>=lo)&(p[:,j]<hi if hi<1 else p[:,j]<=hi)
                    if z.any():c.append(dict(event=e,lower=float(lo),upper=float(hi),rows=int(z.sum()),actual_PA=float(pa[z].sum()),
                        equal_origin_weight=float(weights[z].sum()),predicted=float(np.average(p[z,j],weights=weights[z])),
                        actual=float(np.average(counts[z,j]/pa[z],weights=weights[z]))))
            calibration[a]=c
        rows.append(dict(population=label,rows=h.height,people=h['player_id'].n_unique(),actual_PA=float(pa.sum()),
            scores=scored,calibration=calibration,qualification='Conditional actual MLB participants; actual PA diagnostic weights, no arrival claim'))
    return rows


def evaluate():
    assert not (OUT/'scores.json').exists(),'Preserve prior evaluation'
    pre=read(OUT/'preflight.json');verify(pre['input_hashes'])
    assert sha256_file(OUT/'prepared.parquet')==pre['prepared_sha256']
    q=pl.read_parquet(OUT/'prepared.parquet')
    stints=pl.read_parquet(GEN/'practical-hitter-v31/dated-stints.parquet')
    actual,env=annual_labels(stints)
    raw=np.array([actual.get((r['target_year'],r['player_id']),np.zeros(8)) for r in q.to_dicts()])
    lab=labels(raw,np.array([env[y] for y in q['origin_year']]),np.array([env[y] for y in q['target_year']]),q['origin_replacement_rate'].to_numpy())
    assert np.array_equal(lab['pa'],q['next_pa'])
    assert np.allclose(lab['relative_rate'],q['actual_relative_rate'],atol=1e-10,rtol=0)
    assert np.allclose(lab['relative_value'],q['actual_relative_value'],atol=1e-10,rtol=0)
    q=q.with_columns(pl.Series('actual_events',raw.tolist()))
    q.write_parquet(OUT/'predictions.parquet')
    original=q.filter(~pl.col('source_addition'));add=q.filter(pl.col('source_addition'))
    never=original.filter(pl.col('prior_debut')==0)
    scopes=[('original_all',original),('additions',add),('all_never_debut',never),
        ('upper_never_debut',never.filter(pl.col('stage')=='Upper minors')),
        ('lower_never_debut',never.filter(pl.col('stage')=='Lower minors')),
        ('original_no_arrival',original.filter(pl.col('next_pa')==0)),
        ('foreign_never_debut',never.filter(pl.col('foreign_supported_PA')>0)),
        ('established_component_diagnostic',original.filter(pl.col('prior_debut')>0))]
    scopes += [('origin_'+str(y),original.filter(pl.col('origin_year')==y)) for y in sorted(original['origin_year'].unique())]
    for lo,hi in [(0,50),(50,200),(200,600),(600,float('inf'))]:
        scopes.append((f'never_exposure_{lo}_{hi}',never.filter((pl.col('US_supported_PA')+pl.col('foreign_supported_PA')>=lo)&(pl.col('US_supported_PA')+pl.col('foreign_supported_PA')<hi))))
    scores=[];intervals=[]
    for name,g in scopes:
        if not g.height:continue
        arms=ARMS+['shared_domestic','shared_foreign']+([] if name=='additions' else ['current'])
        active=g.filter(pl.col('next_pa')>0)
        scores.append(dict(scope=name,rows=g.height,people=g['player_id'].n_unique(),actual_PA=int(g['next_pa'].sum()),actual_value=float(g['actual_relative_value'].sum()),
            scores={a:score(g,a) for a in arms},PA_weighted_rate={a:rate_score(active,a+'_rate','actual_relative_rate',True) if active.height else None for a in arms},
            event_forecasts=event_scores(g)))
        if name in ['original_all','upper_never_debut','lower_never_debut','foreign_never_debut']:
            for a in ARMS:intervals.append(dict(scope=name,arm=a,value=interval(g,a,'current'),rate=rate_interval(g,a,'current') if active.height else None))
        print(name,{a:(round(v['value_rmse'],6),round(scores[-1]['PA_weighted_rate'][a],4) if active.height else None) for a,v in scores[-1]['scores'].items()},flush=True)
    save('scores.json',dict(scopes=scores));save('intervals.json',intervals)
    chosen={c['row_id']:['retained prior diagnostic'] for c in read(OLD/'completed-player-review.json')['cases']}
    for a in ARMS:
        z=never.filter(pl.col(a+'_used')).with_columns(
            ((pl.col('current_value')-pl.col('actual_relative_value'))**2-(pl.col(a+'_value')-pl.col('actual_relative_value'))**2).alias('gain'),
            (pl.col(a+'_value')-pl.col('actual_relative_value')).alias('error'))
        for why,h in [('largest gain',z.sort('gain',descending=True)),('largest harm',z.sort('gain')),
            ('false high',z.sort('error',descending=True)),('false low',z.sort('error')),
            ('ordinary',z.filter(pl.col('next_pa').is_between(100,600)).sort(pl.col('error').abs()))]:
            chosen.setdefault(h['row_id'][0],[]).append(a+' '+why)
    history=defaultdict(list)
    counts=pl.read_parquet(GEN/'practical-hitter-v31/counts.parquet')
    for r in counts.filter(pl.col('season')<=2024).to_dicts():history[r['player_id']].append(r)
    inputs={r['candidate_key']:r for r in read(GEN/'foreign-origin-inputs/origin-inputs.json')['rows']}
    fp={(r['candidate_key'],r['outer_fold']):r for r in read(BORROWED/'profiles.json')['profiles']}
    cal={(r['cutoff'],tuple(r['excluded_folds'])):r for r in read(BORROWED/'fits.json')['fits']}
    graphs={k:{g['cutoff']:g for g in read(BRIDGE/f'translation-{k}.json')['graphs']} for k in range(5)}
    peer=pl.read_parquet(OLD/'foreign-features-0.parquet').select('row_id','minor_pa_0','scout_rank_score_0')
    q=q.join(peer,on='row_id',how='left',validate='1:1');cases=[]
    support=pl.read_parquet(OLD/'profile-support.parquet')
    for rid,why in chosen.items():
        r=q.filter(pl.col('row_id')==rid).row(0,named=True);y,k,pid=r['origin_year'],r['outer_fold'],r['player_id'];key=f'{y}:{pid}'
        source_h=history[pid]
        _,note=profile(source_h,graphs[k][y],cal[y,tuple([k])],inputs.get(key),fp.get((key,k)),origin=y,outer_fold=k,own_fold=k)
        traces={}
        for a in ARMS:
            p=np.array(r[a+'_probability']);ref=np.array(r['direct_reference']);v,terms=convert(p,ref)
            assert np.isclose(v,r[a+'_raw_rate'],atol=1e-10,rtol=0)
            assert np.allclose(p,note['future_US_probability' if a.endswith('domestic') else 'future_shared_probability'],atol=1e-10,rtol=0)
            traces[a]=dict(probability=p.tolist(),reference=ref.tolist(),event_value_terms=dict(zip(EVENTS,terms.tolist(),strict=True)),
                raw_rate=float(v),used=r[a+'_used'],supported=r[a+'_supported'],routed_rate=r[a+'_rate'],
                p=r[a+'_p'],conditional_PA=r[a+'_conditional_pa'],PA=r[a+'_pa'],value=r[a+'_value'])
        used=[h for h in source_h if 0<=y-h['season']<3 and h['bucket'] in graphs[k][y]['offsets'] and h['plate_appearances']>0]
        small=min(used,key=lambda h:h['plate_appearances']) if used else None;removal=None
        if small:
            _,removed=profile([h for h in source_h if h is not small],graphs[k][y],cal[y,tuple([k])],inputs.get(key),fp.get((key,k)),origin=y,outer_fold=k,own_fold=k)
            removal=dict(removed={n:small[n] for n in ['season','bucket','plate_appearances']},
                foreign_raw_rate_change=float(convert(np.array(removed['future_shared_probability']),np.array(note['reference']))[0]-traces['direct_foreign']['raw_rate']),
                limit='Same saved transformations; not causal or a replacement forecast')
        peers=q.filter((pl.col('origin_year')==y)&(pl.col('prior_debut')==r['prior_debut'])&(pl.col('stage')==r['stage'])&(pl.col('player_id')!=pid)&~pl.col('source_addition')).with_columns(
            (((pl.col('age')-r['age'])/3)**2+((pl.col('minor_pa_0')-r['minor_pa_0'])/250)**2+(pl.col('scout_rank_score_0')-r['scout_rank_score_0'])**2).alias('distance')).sort('distance','player_id').head(4)
        cases.append(dict(row_id=rid,selection=why,origin={n:r[n] for n in ['player_id','player_name','origin_year','target_year','stage','age','prior_debut','outer_fold','source_addition']},
            source_history=used,foreign_source=inputs.get(key),profile=note,source_removal=removal,direct_traces=traces,
            benchmarks={a:{n:r[a+'_'+n] for n in ['rate','pa','value']} for a in ['shared_domestic','shared_foreign']+([] if r['source_addition'] else ['current'])},
            actual=dict(PA=r['next_pa'],rate=r['actual_relative_rate'] if r['next_pa']>0 else None,value=r['actual_relative_value'],events=r['actual_events']),
            actual_history=counts.filter((pl.col('player_id')==pid)&(pl.col('season')==y+1)&(pl.col('bucket')=='MLB')).to_dicts(),
            training_support=support.filter(pl.col('row_id')==rid).to_dicts(),
            peers=peers.select('player_id','player_name','age','minor_pa_0','scout_rank_score_0','current_pa','current_rate','direct_foreign_rate','direct_foreign_value','next_pa','actual_relative_rate','actual_relative_value').to_dicts(),
            player_walkthrough_status='pending'))
    save('reviewed-cases.json',dict(cases=cases,player_walkthrough_status='pending'))
    save('evaluation-receipt.json',dict(rows=q.height,cases=len(cases),new_fits=0,protected_outcomes_used=False,
        player_walkthrough_status='pending',compatible_actual_labels_reconstructed=True,
        hashes={str(OUT/n):sha256_file(OUT/n) for n in ['predictions.parquet','scores.json','intervals.json','reviewed-cases.json']}))
    print(f'{len(cases)} complete calculation traces saved; baseball review pending.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','evaluate'])
    args=parser.parse_args()
    prepare() if args.stage=='prepare' else evaluate()
