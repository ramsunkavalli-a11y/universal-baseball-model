"""Independent raw-source, membership, profile, score and player replay."""
from collections import defaultdict
import csv
import json
import math
from pathlib import Path

import numpy as np
import polars as pl

from source_catcher_throw_block_v5 import ROOT,OUT
from review_catcher_throw_block_source_v5 import PUBLIC
from source_defensive_positions_v2 import embedded
from audit_defensive_talent_support import verify
from run_hitter_finite_return_baseline import protections,save
from universal_baseball.storage import sha256_file


def close(a,b):assert math.isclose(a,b,abs_tol=1e-8,rel_tol=1e-9),(a,b)


def read(name):return json.loads((OUT/name).read_text(encoding='utf8'))


def main():
    protected=protections()
    for name in ('pilot-review.json','extension-review.json','talent-support-review.json','comparison-preflight.json','talent-report.json','talent-walk-review.json'):
        report=read(name);verify(report['hashes'])
        if 'protections' in report:assert report['protections']==protected
    assert read('talent-walk-review.json')['player_walkthrough_status']=='complete'
    annual=pl.read_parquet(OUT/'extension-annual.parquet').to_dicts()
    raw_native={}
    for y in range(2016,2026):
        raw_native.update({(y,r['id']):r for r in embedded((ROOT/f'reports/generated/defensive-talent-position-v2/position-{y}.response').read_text(encoding='utf8'),'data') if r['pos_id']==2})
    bypid=defaultdict(list);raw_index={}
    for k in ('throwing','blocking'):
        for y in range(2016 if k=='throwing' else 2018,2026):
            for s in csv.DictReader((OUT/f'{k}-{y}.response').open(encoding='utf-8-sig')):raw_index[k,y,int(s['player_id'])]=s
    for a in annual:
        k,y,pid=a['component'],a['season'],a['player_id'];s=raw_index[k,y,pid];n=raw_native[y,pid]
        assert int(s['start_year'])==y
        close(a['native_outs'],n['outs_total']);close(a['runs'],n[k+'_runs'])
        if k=='throwing':
            num=float(s['caught_stealing_above_average']);op=int(s['sb_attempts']);runs=.65*num
            valid=math.isclose(num,float(s['n_cs'])-op*float(s['est_cs_pct']),abs_tol=1e-8)
            assert valid==a['context_identity_valid'];assert valid or y in (2016,2017)
            if valid:close(float(s['cs_aa_per_throw']),num/op)
        else:
            num=float(s['x_pbwp'])-float(s['n_pbwp']);op=int(s['pitches']);runs=.25*num
            close(float(s['blocks_above_average_per_game']),40*num/op)
            close(sum(float(s['diff_pbwp_'+suffix]) for suffix in ('easy','medium','tough')),num)
            assert a['context_identity_valid']
        close(a['opportunities'],op);close(a['numerator'],num);close(a['runs'],runs)
        assert a['measurement_valid']==(a['context_identity_valid'] and a['exposure_valid'] and a['native_outs']>0)
        bypid[k,pid].append(a)
    assert len(raw_index)==len(annual) and len({(a['component'],a['season'],a['player_id']) for a in annual})==len(annual)
    rows=pl.read_parquet(OUT/'talent-predictions.parquet').to_dicts();keys={(r['component'],r['origin_year'],r['player_id']) for r in rows};expected=set()
    for (k,pid),ss in bypid.items():
        for y in range(2016 if k=='throwing' else 2018,2025):
            if y!=2020 and any(y-2<=s['season']<=y for s in ss):expected.add((k,y,pid))
    assert keys==expected and len(keys)==len(rows)
    for r in rows:
        k,y,pid=r['component'],r['origin_year'],r['player_id'];ss=bypid[k,pid]
        past=[s for s in ss if y-2<=s['season']<=y and s['measurement_valid']]
        n=sum(s['opportunities']*2**(s['season']-y) for s in past);runs=sum(s['runs']*2**(s['season']-y) for s in past)
        prior,unit=(100.,100.) if k=='throwing' else (3000.,1000.)
        close(n,r['history_opportunities']);close(runs,r['history_runs']);close(unit*runs/(n+prior),r['history']);close(n/(n+prior),r['reliability'])
        assert r['quality_evidence_observed']==(n>0) and r['neutral']==0.
        future=[s for s in ss if y<s['season']<=min(y+3,2025) and s['measurement_valid']]
        missing=sum(raw_native.get((year,pid),{}).get('outs_total',0) for year in range(y+1,min(y+3,2025)+1) if not any(s['season']==year for s in future))
        fn=sum(s['opportunities'] for s in future);fr=sum(s['runs'] for s in future)
        valid=y+3<=2025 and len(future)>=2 and fn>=(100 if k=='throwing' else 3000) and missing==0
        assert valid==(r['quality_rate'] is not None);close(fn,r['future_opportunities']);close(fr,r['future_runs']);close(missing,r['missing_native_outs'])
        if valid:close(unit*fr/fn,r['quality_rate'])
    def profile(r):
        age=r['age'];n=r['history_opportunities'];cut=(10,50) if r['component']=='throwing' else (500,3000)
        return ('unknown' if age is None else '<=24' if age<=24 else '25-29' if age<=29 else '30+', 'tiny' if n<cut[0] else 'medium' if n<cut[1] else 'large')
    for c in read('talent-support-review.json')['cells']:
        tr=[r for r in rows if r['component']==c['component'] and r['window_end']<=c['origin'] and r['quality_rate'] is not None and r['player_id']%5!=c['fold']]
        te=[r for r in rows if r['component']==c['component'] and r['origin_year']==c['origin'] and r['player_id']%5==c['fold']]
        assert [[r['origin_year'],r['player_id']] for r in tr]==c['train_keys'] and [[r['origin_year'],r['player_id']] for r in te]==c['test_keys']
        assert {r['player_id'] for r in tr}.isdisjoint(r['player_id'] for r in te)
        counts=defaultdict(set)
        for r in tr:counts[profile(r)].add(r['player_id'])
        assert len({r['player_id'] for r in tr})==c['training_people']
        for r,n in zip(te,c['joint_profile_people']):assert n==len(counts[profile(r)])==r['profile_people']
    def check_score(rr,score):
        unit=100. if rr[0]['component']=='throwing' else 1000.
        for arm in ('neutral','history'):
            y=np.array([r['quality_rate'] for r in rr]);p=np.array([r[arm] for r in rr]);e=p-y
            for key,value in dict(rmse=np.sqrt(np.mean(e**2)),mae=np.mean(abs(e)),bias=np.mean(e),
                    predicted_runs_actual_exposure=sum(r[arm]*r['future_opportunities']/unit for r in rr),actual_runs=sum(r['future_runs'] for r in rr)).items():close(value,score[arm][key])
        rng=np.random.default_rng(7053257);idx=rng.integers(0,len(rr),size=(2000,len(rr)));p=np.array([r['history'] for r in rr])
        diff=np.sqrt(np.mean((p[idx]-y[idx])**2,axis=1))-np.sqrt(np.mean(y[idx]**2,axis=1))
        close(np.quantile(diff,.025),score['interval']['low']);close(np.quantile(diff,.975),score['interval']['high'])
    report=read('talent-report.json')
    for s in report['scores']:check_score([r for r in rows if r['component']==s['component'] and r['origin_year']==s['origin'] and r['quality_rate'] is not None],s)
    for s in report['groups']:
        i=0 if s['family']=='age' else 1
        check_score([r for r in rows if r['component']==s['component'] and r['origin_year']==2022 and r['quality_rate'] is not None and profile(r)[i]==s['group']],s)
    walks=read('talent-player-walkthrough.json');assert walks['player_walkthrough_status']=='complete'
    indexed={(r['component'],r['origin_year'],r['player_id']):r for r in rows}
    for c in walks['cases']:
        focal=c['primary']['forecast'];peers=sorted([r for r in rows if r['component']==focal['component'] and r['origin_year']==focal['origin_year'] and r['player_id']!=focal['player_id']],key=lambda p:(abs((p['age'] or 27)-(focal['age'] or 27)),abs(p['history_opportunities']-focal['history_opportunities']),p['player_id']))[:3]
        assert [p['player_id'] for p in peers]==[p['forecast']['player_id'] for p in c['peers']]
        for case in (c['primary'],*c['peers']):
            r=case['forecast'];assert r==indexed[r['component'],r['origin_year'],r['player_id']]
            m=case['intermediate'];close(m['weighted_numerator'],r['history_runs']);close(m['history_forecast'],r['history'])
            unit=100 if r['component']=='throwing' else 1000
            close(unit*m['weighted_numerator']/m['denominator'],r['history'])
            assert case['future_annual_path']==[s for s in bypid[r['component'],r['player_id']] if r['origin_year']<s['season']<=r['window_end']]
    paths=[OUT/'talent-report.json',OUT/'talent-player-walkthrough.json',OUT/'extension-review.json',Path(__file__)]
    final=OUT/'talent-final-review.json';assert not final.exists()
    save(final,dict(execution_integrity='pass',source_rows=len(annual),all_origin_forecasts_replayed=len(rows),player_walkthrough_status='complete',
        focal_cases=len(walks['cases']),fully_replayed_peers=sum(len(c['peers']) for c in walks['cases']),
        predictive_status='both primary point gains uncertain',profile_support='qualified_sparse',reasonability='mixed_named_gains_and_losses_retained',
        retained='transparent history research baselines; no age fit, retuning or lower-minors talent claim',no_2026_outcomes=True,
        full_value_validated=False,deployment_approved=False,protections=protected,hashes={str(p):sha256_file(p) for p in paths}))
    (PUBLIC/final.name).write_bytes(final.read_bytes());print(json.dumps(read('talent-final-review.json'),indent=2))


if __name__=='__main__':main()
