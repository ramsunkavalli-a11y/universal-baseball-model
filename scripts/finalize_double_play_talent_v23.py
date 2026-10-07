"""Seal fixed DP disposition after all forecast, peer and annual-path review."""
from pathlib import Path
import math
import polars as pl
from universal_baseball.storage import sha256_file
from verify_double_play_talent_v23 import ROOT,PUBLIC,read,write
from run_hitter_finite_return_baseline import protections


def key(r):return r['origin_year'],r['player_id'],r['position']


def main():
    protections()
    assert read(PUBLIC/'independent-review.json.gz')['status']=='pass'
    predictions=read(PUBLIC/'predictions.json.gz');by={key(r):r for r in predictions}
    native=pl.read_parquet(ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet').to_dicts()
    walks=[];selections=[];paths=[Path(__file__),ROOT/'docs/defense-double-play-talent-v23-result.md']
    for name in ('preflight.json.gz','report.json.gz','independent-review.json.gz','player-walkthrough.json.gz','player-walkthrough-stress.json.gz'):
        p=PUBLIC/name;paths.append(p);rec=read(p)
        for file,digest in rec['hashes'].items():assert sha256_file(Path(file))==digest,file
        walks.extend(rec.get('walks',[]));selections.extend(rec.get('selections',[]))
        if name=='player-walkthrough.json.gz':
            assert len(rec['prospect_source_walks'])==4
            assert all(not w['forecast']['validated_talent_grade'] and w['origin']['quality_rate'] is None for w in rec['prospect_source_walks'])
    for w in walks:
        k=tuple(w['identity']);r=by[k];assert w['forecast']==r
        a=w['arithmetic'];assert a['weighted_runs']==r['dp_history_runs'] and a['weighted_outs']==r['dp_history_outs']
        assert a['reliability']==r['dp_reliability']
        assert math.isclose(a['candidate'],1500*a['weighted_runs']/(a['weighted_outs']+3000),abs_tol=1e-12)
        assert w['known_all_position_history']==[n for n in native if n['player_id']==k[1] and k[0]-2<=n['season']<=k[0]]
        for ann in w['annual_MLB_paths']:
            target=r['annual'][ann['season']-k[0]-1]
            assert all(ann[c]==v for c,v in target.items())
            n=target['native'];assert ann['annual_rate']==(1500*n['dp_runs']/n['native_outs'] if target['measurement_valid'] else None)
            assert ann['native_all_positions']==[n for n in native if n['player_id']==k[1] and n['season']==ann['season']]
    for s in selections:
        focal=by[tuple(s['identity'])]
        peers=sorted((r for r in predictions if r['origin_year']==focal['origin_year'] and r['position']==focal['position'] and r['player_id']!=focal['player_id']),
            key=lambda r:(abs(r['age']-focal['age']) if r['age'] is not None and focal['age'] is not None else 999.,
                abs(math.log1p(r['dp_history_outs'])-math.log1p(focal['dp_history_outs'])),r['player_id']))[:3]
        assert s['peer_keys']==[list(key(r)) for r in peers]
        assert all(any(w['identity']==k for w in walks) for k in [s['identity'],*s['peer_keys']])
    report=read(PUBLIC/'report.json.gz');primary=next(r for r in report['results'] if r['origin']==2022)
    assert primary['quality_screen_failures'] and primary['paired_RMSE']['interval_95'][0]>0
    result=dict(status='review_complete',player_walkthrough_status='complete',model_fits=0,independent_replay='pass',
        predictive_quality='fixed_rule_fails_primary',disposition='retain_neutral_DP; no_weight_sweep_or_value_test_for_failed_rule',
        deployment_approved=False,primary_focal_selections=11,stress_focal_selections=3,
        distinct_MLB_player_origins=len({tuple(w['identity'][:2]) for w in walks}),position_walks=len({tuple(w['identity']) for w in walks}),
        prospect_source_walks=4,unit_checks=10,forecasts_replayed=len(predictions),
        previous_goal_turn='No defense progress: read-only Lovich diagnosis. Current turn completes source audit and fixed DP talent test with independent replay and player review.',
        next_step='Older compatible quality measurements and longer-path minor talent support; reviewed component assembly remains in scope',
        unresolved=['Lower-level range/development talent','Actual DP chances and vendor vintage','Older compatible labels',
            'Defensive position/arrival/exposure and delivered value integration','Separate Lovich batting defect'],
        goal_complete=False,no_2026_selection=True,frozen_forecasts_unchanged=True,
        hashes={str(p):sha256_file(p) for p in paths})
    write(PUBLIC/'final-review.json.gz',result)
    print({k:v for k,v in result.items() if k!='hashes'},flush=True)
    protections()


if __name__=='__main__':main()
