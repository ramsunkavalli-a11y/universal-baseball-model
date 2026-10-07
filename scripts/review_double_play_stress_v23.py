"""Walk the three largest stress-origin harms and their origin-selected peers."""
from pathlib import Path
import math
import polars as pl
from universal_baseball.storage import sha256_file
from verify_double_play_talent_v23 import ROOT,PUBLIC,read,write


def key(r):return r['origin_year'],r['player_id'],r['position']


def main():
    rows=read(PUBLIC/'predictions.json.gz');stress=[r for r in rows if r['origin_year']==2021]
    focal=sorted((r for r in stress if r['quality_rate'] is not None),
        key=lambda r:abs(r['candidate']-r['quality_rate'])-abs(r['quality_rate']),reverse=True)[:3]
    selections=[];people=set()
    for r in focal:
        peers=sorted((s for s in stress if s['position']==r['position'] and s['player_id']!=r['player_id']),
            key=lambda s:(abs(s['age']-r['age']) if s['age'] is not None and r['age'] is not None else 999.,
                abs(math.log1p(s['dp_history_outs'])-math.log1p(r['dp_history_outs'])),s['player_id']))[:3]
        selections.append(dict(identity=list(key(r)),name=r['player_name'],reason='Three largest 2021 absolute-error deteriorations',
            peer_keys=[list(key(s)) for s in peers]))
        people.update((2021,s['player_id']) for s in (r,*peers))
    native_path=ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet';native=pl.read_parquet(native_path).to_dicts()
    walks=[]
    for r in sorted((r for r in stress if (2021,r['player_id']) in people),key=key):
        annual=[]
        for a in r['annual']:
            year=a['season'];n=a['native']
            annual.append(dict(**a,annual_rate=1500*n['dp_runs']/n['native_outs'] if a['measurement_valid'] else None,
                native_all_positions=[s for s in native if s['player_id']==r['player_id'] and s['season']==year]))
        walks.append(dict(identity=list(key(r)),forecast=r,
            known_all_position_history=[n for n in native if n['player_id']==r['player_id'] and 2019<=n['season']<=2021],
            arithmetic=dict(weighted_runs=r['dp_history_runs'],weighted_outs=r['dp_history_outs'],prior_outs=3000,
                reliability=r['dp_reliability'],neutral=r['neutral'],candidate=r['candidate'],same_position_only=True,
                actual_DP_chances=None,mechanical_conversion_talent=False),annual_MLB_paths=annual))
    write(PUBLIC/'player-walkthrough-stress.json.gz',dict(selections=selections,walks=walks,distinct_player_origins=len(people),
        position_walks=len(walks),model_refits=0,player_walkthrough_status='pending_main_review',
        hashes={str(p):sha256_file(p) for p in (Path(__file__),PUBLIC/'predictions.json.gz',PUBLIC/'player-walkthrough.json.gz',native_path)}))
    for s in selections:
        r=next(r for r in stress if list(key(r))==s['identity'])
        print(dict(name=s['name'],weighted_runs=r['dp_history_runs'],weighted_outs=r['dp_history_outs'],
            candidate=r['candidate'],actual=r['quality_rate'],support=r['distinct_profile_training_people'],
            source=[(t['source']['season'],t['source']['dp_runs'],t['source']['native_outs'],t['recency_weight']) for t in r['trace']],
            peers=s['peer_keys']),flush=True)


if __name__=='__main__':main()
