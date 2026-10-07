"""All forecast arithmetic and annual paths for fixed cases, misses and peers."""
from pathlib import Path
import math
import json
import polars as pl
from universal_baseball.storage import sha256_file
from verify_double_play_talent_v23 import ROOT,PUBLIC,V22,read,write


def key(r):return r['origin_year'],r['player_id'],r['position']


def main():
    assert read(PUBLIC/'independent-review.json.gz')['status']=='pass'
    rows=read(PUBLIC/'predictions.json.gz');primary=[r for r in rows if r['origin_year']==2022];measured=[r for r in primary if r['quality_rate'] is not None]
    fixed=read(V22/'player-selection.json.gz')['selections'];requests=[]
    for s in fixed:
        if s['identity'][0]=='MLB_history':requests.append((tuple(s['identity'][1:]),'Fixed source case'))
    loss=lambda r:abs(r['neutral']-r['quality_rate'])-abs(r['candidate']-r['quality_rate'])
    for reason,r in [('Largest absolute-error improvement',max(measured,key=loss)),('Largest absolute-error deterioration',min(measured,key=loss)),
        ('Largest false high',max(measured,key=lambda r:r['candidate']-r['quality_rate'])),
        ('Largest false low',min(measured,key=lambda r:r['candidate']-r['quality_rate'])),
        ('Median candidate absolute error',sorted(measured,key=lambda r:abs(r['candidate']-r['quality_rate']))[len(measured)//2])]:requests.append((key(r),reason))
    selections=[];people=set()
    for k,reason in requests:
        r=next(r for r in rows if key(r)==k)
        peers=sorted((s for s in primary if s['position']==r['position'] and s['player_id']!=r['player_id']),
            key=lambda s:(abs(s['age']-r['age']) if s['age'] is not None and r['age'] is not None else 999.,
                abs(math.log1p(s['dp_history_outs'])-math.log1p(r['dp_history_outs'])),s['player_id']))[:3]
        selections.append(dict(identity=list(k),name=r['player_name'],reason=reason,peer_keys=[list(key(s)) for s in peers]))
        people.update((s['origin_year'],s['player_id']) for s in (r,*peers))
    write(PUBLIC/'player-selection.json.gz',dict(selections=selections,peer_rule='Same origin position, age/log-weighted-DP-outs distance then ID; no outcomes used for peers',model_fits=0))
    native_path=ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet';native=pl.read_parquet(native_path).to_dicts()
    walks=[]
    for r in sorted((r for r in rows if (r['origin_year'],r['player_id']) in people),key=key):
        annual=[]
        for a in r['annual']:
            year=a['season'];n=a['native']
            annual.append(dict(**a,annual_rate=1500*n['dp_runs']/n['native_outs'] if a['measurement_valid'] else None,
                native_all_positions=[s for s in native if s['player_id']==r['player_id'] and s['season']==year]))
        assert math.isclose(r['candidate'],1500*r['dp_history_runs']/(r['dp_history_outs']+3000),abs_tol=1e-12)
        walks.append(dict(identity=list(key(r)),forecast=r,
            known_all_position_history=[n for n in native if n['player_id']==r['player_id'] and r['origin_year']-2<=n['season']<=r['origin_year']],
            arithmetic=dict(weighted_runs=r['dp_history_runs'],weighted_outs=r['dp_history_outs'],prior_outs=3000,
                reliability=r['dp_reliability'],neutral=r['neutral'],candidate=r['candidate'],same_position_only=True,
                actual_DP_chances=None,mechanical_conversion_talent=False),annual_MLB_paths=annual))
    minor=read(V22/'player-walkthrough-supplement.json.gz')
    minor_selected=minor['selections'][0];minor_keys={tuple(k) for k in [minor_selected['identity'],*minor_selected['peer_keys']]}
    prospect_walks=[dict(w,forecast=dict(neutral_DP_fallback=0.,known_quality=False,validated_talent_grade=False)) for w in minor['walks'] if tuple(w['identity']) in minor_keys]
    assert len(prospect_walks)==4 and all(w['origin']['quality_rate'] is None for w in prospect_walks)
    write(PUBLIC/'player-walkthrough.json.gz',dict(selections=selections,walks=walks,prospect_source_walks=prospect_walks,
        distinct_player_origins=len(people),position_walks=len(walks),model_fits=0,player_walkthrough_status='pending_main_review',
        hashes={str(p):sha256_file(p) for p in (Path(__file__),PUBLIC/'predictions.json.gz',PUBLIC/'independent-review.json.gz',
            PUBLIC/'player-selection.json.gz',native_path,V22/'player-walkthrough-supplement.json.gz')}))
    for s in selections:
        w=next(w for w in walks if w['identity']==s['identity']);r=w['forecast']
        print(json.dumps(dict(name=s['name'],reason=s['reason'],position=r['position'],age=r['age'],rate=r['dp_raw_rate'],
            grade=[r['neutral'],r['candidate'],r['quality_rate']],weighted_runs=r['dp_history_runs'],weighted_outs=r['dp_history_outs'],
            reliability=r['dp_reliability'],training_profile_people=r['distinct_profile_training_people'],
            annual=[a['annual_rate'] for a in w['annual_MLB_paths']])),flush=True)


if __name__=='__main__':main()
