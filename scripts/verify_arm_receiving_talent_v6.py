"""Independent arithmetic, official scope, full label/support and score replay."""
from collections import defaultdict
from pathlib import Path
import json
import math
import numpy as np
import polars as pl
from evaluate_arm_receiving_talent_v6 import ROOT,SOURCE,OUT,PUBLIC
from source_defensive_positions_v2 import embedded
from run_hitter_finite_return_baseline import protections,save
from universal_baseball.storage import sha256_file


def verify_hashes(report):
    for group in ('input_hashes','output_hashes'):
        for p,h in report.get(group,{}).items():assert sha256_file(Path(p))==h,p


def main():
    protections()
    assert not (OUT/'final-review.json').exists()
    records=pl.read_parquet(SOURCE/'annual.parquet').to_dicts()
    source_review=json.loads((SOURCE/'extension-review.json').read_text());verify_hashes(source_review)
    support=json.loads((SOURCE/'talent-support-review.json').read_text());verify_hashes(support)
    report=json.loads((OUT/'report.json').read_text());verify_hashes(report)
    walk=json.loads((OUT/'player-walkthrough.json').read_text());verify_hashes(walk)
    assert walk['player_walkthrough_status']=='complete'
    official_note=json.loads((ROOT/'reports/generated/multiyear-hitter-components-v1/source-audit.json').read_text())['mlb_fielding']
    official_path=Path(official_note['path']);assert sha256_file(official_path)==official_note['sha256']
    usage=defaultdict(lambda:[0,0])
    for s in pl.read_parquet(official_path).filter(pl.col('season').is_between(2016,2025)).to_dicts():
        usage[s['season'],s['player_id']][0 if str(s['position_code']) in ('7','8','9') else 1]+=s['fielding_outs'] or 0
    native=defaultdict(list)
    for s in pl.read_parquet(ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet').to_dicts():native[s['season'],s['player_id']].append(s)
    histories=defaultdict(list)
    for s in records:
        histories[s['kind'],s['player_id']].append(s)
        if s['kind']=='arm':
            of,other=usage[s['season'],s['player_id']]
            assert s['of_outs']==of and s['other_outs']==other
            assert s['isolated_outfield_quality_valid']==bool(s['native_match'] and of>0 and other==0)
    labels=pl.read_parquet(SOURCE/'talent-labels.parquet').to_dicts()
    predictions=pl.read_parquet(OUT/'predictions.parquet').to_dicts()
    lut={(r['kind'],r['origin_year'],r['player_id']):r for r in predictions}
    keys=set()
    for (kind,pid),sources in histories.items():
        valid='isolated_outfield_quality_valid' if kind=='arm' else 'quality_valid'
        for y in range(2016 if kind=='arm' else 2021,2025):
            if y==2020:continue
            seen=[s for s in sources if y-2<=s['season']<=y]
            if not seen or (kind=='arm' and not any(s['of_outs']>0 for s in seen)):continue
            key=(kind,y,pid);keys.add(key);r=lut[key]
            past=[s for s in seen if s[valid]]
            n=sum(s['opportunities']*2.**(s['season']-y) for s in past)
            runs=sum(s['runs']*2.**(s['season']-y) for s in past)
            assert r['history_opportunities']==n and r['history_runs']==runs
            assert r['history']==100*runs/(n+(300 if kind=='arm' else 600))
            future=[s for s in sources if y<s['season']<=min(y+3,2025)]
            measured=[s for s in future if s[valid]]
            gaps=sum(not s[valid] for s in future)
            for year in range(y+1,min(y+3,2025)+1):
                if any(s['season']==year for s in future):continue
                col='arm_runs' if kind=='arm' else 'fielding_runs_prevented_on_rec1b'
                relevant=[s for s in native.get((year,pid),[]) if (s['position'] in (7,8,9) if kind=='arm' else s['position']==3)]
                gaps+=any(s[col] is not None and abs(s[col])>1e-12 for s in relevant)
            fn=sum(s['opportunities'] for s in measured);fr=sum(s['runs'] for s in measured)
            good=y+3<=2025 and len(measured)>=2 and fn>=(600 if kind=='arm' else 1000) and gaps==0
            assert r['future_opportunities']==fn and r['future_runs']==fr and r['coverage_gap_seasons']==gaps
            assert r['quality_rate']==(100*fr/fn if good else None)
    assert keys==set(lut)=={(r['kind'],r['origin_year'],r['player_id']) for r in labels}
    def profile(r):
        a=r['age'];n=r['history_opportunities'];lo,hi=(50,300) if r['kind']=='arm' else (100,500)
        return ('unknown' if a is None else '<=24' if a<=24 else '25-29' if a<=29 else '30+',
                'tiny' if n<lo else 'medium' if n<hi else 'large')
    for c in support['cells']:
        tr=[r for r in predictions if r['kind']==c['kind'] and r['window_end']<=c['origin'] and r['quality_rate'] is not None and r['player_id']%5!=c['fold']]
        te=[r for r in predictions if r['kind']==c['kind'] and r['origin_year']==c['origin'] and r['player_id']%5==c['fold']]
        assert c['train_keys']==[[r['origin_year'],r['player_id']] for r in tr]
        assert c['test_keys']==[[r['origin_year'],r['player_id']] for r in te]
        assert len({r['player_id'] for r in tr})==c['training_people']
        assert {r['player_id'] for r in tr}.isdisjoint(r['player_id'] for r in te)
        assert c['joint_profile_people']==[len({t['player_id'] for t in tr if profile(t)==profile(r)}) for r in te]
    for summary in report['reports']:
        rr=[r for r in predictions if r['kind']==summary['kind'] and r['origin_year']==summary['origin'] and r['quality_rate'] is not None]
        y=np.array([r['quality_rate'] for r in rr]);pred=np.array([r['history'] for r in rr]);rng=np.random.default_rng(70633647)
        for label,p in [('neutral',np.zeros(len(rr))),('history',pred)]:
            m=summary[label];e=p-y
            for name,value in [('rmse',np.sqrt(np.mean(e**2))),('mae',np.mean(abs(e))),('bias',np.mean(e)),
                ('predicted_runs_actual_exposure',sum(v*r['future_opportunities']/100 for v,r in zip(p,rr))),('actual_runs',sum(r['future_runs'] for r in rr))]:
                assert abs(m[name]-value)<1e-10
        idx=rng.integers(0,len(rr),size=(2000,len(rr)))
        d=np.sqrt(np.mean((pred[idx]-y[idx])**2,axis=1))-np.sqrt(np.mean(y[idx]**2,axis=1))
        assert abs(summary['paired_interval']['low']-np.quantile(d,.025))<1e-12
        assert abs(summary['paired_interval']['high']-np.quantile(d,.975))<1e-12
    for w in walk['walks']:
        for t in [w['primary'],*w['peers']]:
            r=t['origin_forecast'];assert r==lut[r['kind'],r['origin_year'],r['player_id']]
            assert len(w['peers'])==3 and w['player_id'] not in [t['origin_forecast']['player_id'] for t in w['peers']]
            for s in t['past']+t['future']:
                assert sha256_file(Path(s['source_path']))==s['source_sha256']
    final=dict(status='qualified_research_baseline_comparison',rows=len(predictions),source_records=len(records),
        official_position_scope_replay=True,all_quality_labels_replay=True,all_chronological_support_replay=True,
        all_score_and_interval_replay=True,player_walkthrough_status='complete',focal_cases=walk['focal_cases'],peer_cases=walk['peer_cases'],
        learned_age_model=False,no_2026_outcomes=True,frozen_forecasts_unchanged=True,deployment_allowed=False,
        disposition='Retain transparent qualified history as research baseline; uncertain gains, young-arm failures, sparse survivors and receiving chronology limit claims.',
        input_hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'report.json',OUT/'player-walkthrough.json',OUT/'predictions.parquet',SOURCE/'talent-support-review.json']})
    save(OUT/'final-review.json',final);save(PUBLIC/'final-review.json',final)
    print(json.dumps({k:v for k,v in final.items() if k!='input_hashes'},indent=2))


if __name__=='__main__':main()
