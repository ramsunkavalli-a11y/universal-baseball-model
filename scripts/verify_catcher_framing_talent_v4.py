"""Independent native histories, mature training, fit replay and player review."""
from collections import Counter,defaultdict
import math
from pathlib import Path

import numpy as np
import polars as pl

from audit_catcher_framing_talent_v4 import ROOT,SOURCE,OUT,PUBLIC,read,write
from universal_baseball import catcher_framing_talent as talent
from universal_baseball.defense_native_range import paired_interval
from universal_baseball.storage import sha256_file
from audit_defensive_talent_support import verify
from run_hitter_finite_return_baseline import protections


def close(a,b):
    assert math.isclose(float(a),float(b),rel_tol=1e-9,abs_tol=1e-9),(a,b)


def main():
    protected=protections();source=read(OUT/'support-review.json');pre=read(OUT/'fit-preflight.json');report=read(OUT/'report.json')
    for r in (source,pre,report):
        verify(r['hashes']);assert r['protections']==protected
    assert source['before_fitting'] and source['player_walkthrough_status']=='complete'
    rows=pl.read_parquet(OUT/'predictions.parquet').to_dicts();labels=pl.read_parquet(OUT/'labels.parquet').to_dicts()
    original={(r['origin_year'],r['player_id']):r for r in labels}
    native=defaultdict(list)
    for r in pl.read_parquet(SOURCE/'framing-annual.parquet').to_dicts():
        assert 2018<=r['season']<=2025 and r['pitches']>0 and r['framing_measurement_valid']
        native[r['player_id']].append(r)
    assert len(rows)==len(original)==889
    for r in rows:
        for c,v in original[r['origin_year'],r['player_id']].items():
            assert r[c]==v
        y=r['origin_year'];past=[s for s in native[r['player_id']] if y-2<=s['season']<=y]
        n=sum(s['pitches']/2**(y-s['season']) for s in past);runs=sum(s['framing_runs']/2**(y-s['season']) for s in past)
        close(n,r['history_pitches']);close(runs,r['history_runs']);close(1000*runs/(n+6000),r['history'])
        if r['quality_rate'] is not None:
            future=[s for s in native[r['player_id']] if y<s['season']<=y+3]
            assert y+3<=2025 and len(future)>=2 and sum(s['pitches'] for s in future)>=6000 and r['missing_native_outs']==0
            close(1000*sum(s['framing_runs'] for s in future)/sum(s['pitches'] for s in future),r['quality_rate'])
    models={(m['origin'],m['fold']):m['model'] for m in read(OUT/'models.json')['models']};solves=0
    for c in pre['checks']:
        year,fold=c['origin'],c['fold']
        tr=[r for r in rows if r['window_end']<=year and r['quality_rate'] is not None and r['player_id']%5!=fold]
        te=[r for r in rows if r['origin_year']==year and r['player_id']%5==fold]
        assert set(map(tuple,c['train_keys']))=={(r['origin_year'],r['player_id']) for r in tr}
        assert set(map(tuple,c['test_keys']))=={(r['origin_year'],r['player_id']) for r in te}
        assert {r['player_id'] for r in tr}.isdisjoint(r['player_id'] for r in te)
        profiles=defaultdict(set)
        for r in tr:
            profiles[talent.profile(r)].add(r['player_id'])
        for r in te:
            assert r['profile_people']==len(profiles[talent.profile(r)])
        m=models[year,fold]
        if m is None:
            assert not c['fit_allowed']
            for r in te:
                close(r['calibrated'],r['history'])
            continue
        x=talent.matrix(tr);counts=Counter(r['player_id'] for r in tr);w=np.array([1/counts[r['player_id']] for r in tr]);y=np.array([r['quality_rate'] for r in tr])
        mean=np.average(x,axis=0,weights=w);sd=np.sqrt(np.average((x-mean)**2,axis=0,weights=w));sd[sd<1e-10]=1
        z=(x-mean)/sd;intercept=float(np.average(y,weights=w))
        beta=np.linalg.lstsq(np.vstack([np.sqrt(w)[:,None]*z,np.sqrt(10)*np.eye(len(talent.FEATURES))]),
                             np.concatenate([np.sqrt(w)*(y-intercept),np.zeros(len(talent.FEATURES))]),rcond=None)[0]
        assert np.allclose(beta,m['coef'],atol=1e-10,rtol=0)
        p=intercept+(talent.matrix(te)-mean)/sd@beta
        for r,value in zip(te,p):
            close(r['calibrated'],value)
        solves+=1
    for name in ['primary',*report['by_origin']]:
        subset=[r for r in rows if r['quality_rate'] is not None and r['origin_year']==(2022 if name=='primary' else int(name))]
        scores=report['primary'] if name=='primary' else report['by_origin'][name]
        for arm in ('neutral','history','calibrated'):
            e=np.array([r[arm]-r['quality_rate'] for r in subset])
            close(np.sqrt((e*e).mean()),scores['scores'][arm]['rmse']);close(e.mean(),scores['scores'][arm]['bias'])
            close(sum(r[arm]*r['future_pitches']/1000 for r in subset),scores['scores'][arm]['oracle_exposure_predicted_runs'])
        assert paired_interval(subset,'history','neutral')==scores['history_minus_neutral']
        assert paired_interval(subset,'calibrated','history')==scores['calibrated_minus_history']
    walk=read(OUT/'player-walkthrough.json');wc=read(OUT/'walk-review.json')
    assert walk['player_walkthrough_status']=='complete' and wc['hash']==sha256_file(OUT/'player-walkthrough.json')
    for c in walk['cases']:
        for p in [c['primary'],*c['peers']]:
            r=p['forecast'];m=models[r['origin_year'],r['fold']]
            if m:
                close(m['intercept']+sum(p['fitted_terms'].values()),r['calibrated'])
    # Independent dated metadata proves a concrete missing-age flaw. No later age
    # or 2026 performance is needed; these rows are context, not a retuned model.
    snapshots=Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated/opportunity-history-sources-v2/tables/hitter_snapshots.parquet')
    q=pl.read_parquet(snapshots,columns=['snapshot_year','player_id','age_years']).filter((pl.col('player_id')==668670)&(pl.col('snapshot_year')<=2022))
    evidence=q.to_dicts()
    assert any(r['snapshot_year']==2021 and r['age_years']==26 for r in evidence)
    diagnosis=dict(player_id=668670,name='Jake Rogers',origin=2022,old_age=None,dated_age_evidence=evidence,
                   implied_age_from_2021=27,source_sha256=sha256_file(snapshots),
                   old_missing_age_term=-0.968345669694125,
                   scope='Verified source/context defect in calibration, not an origin-known poor-framing trait; corrected metadata must precede any reuse.')
    write('age-source-diagnosis.json',diagnosis)
    result=dict(execution_integrity='pass',predictions_replayed=len(rows),independent_ridge_solves=solves,
                player_walkthrough_status='complete',walk_cases=wc['cases'],fully_replayed_peers=wc['fully_replayed_peers'],
                unknown_quality_peers=wc['unknown_quality_peers'],no_2026_outcomes=True,deployment_approved=False,
                predictive_status='Shrunk history has an uncertain ~10% ordinary-origin quality improvement versus neutral; age calibration loses and has source/support defects.',
                disposition='Retain transparent history as the practical MLB research baseline; do not adopt or tune this age calibration. This does not reject age or framing information generally.',
                source_age_repair_required=True,calibration_all_training_histories_left_truncated=True,
                small_group_interval_warning='A one-person subgroup bootstrap cannot estimate population uncertainty; do not interpret the repeated point as a population 95% interval.',
                protections=protected,hashes={str(p):sha256_file(p) for p in (OUT/'player-walkthrough.json',OUT/'walk-review.json',OUT/'age-source-diagnosis.json',Path(__file__))})
    write('final-review.json',result)
    for name in ('report.json','fit-preflight.json','models.json','player-walkthrough.json','walk-review.json','age-source-diagnosis.json','final-review.json'):
        p=PUBLIC/name;assert not p.exists();p.write_bytes((OUT/name).read_bytes())
    print({k:v for k,v in result.items() if k not in ('hashes','protections')})


if __name__=='__main__':
    main()
