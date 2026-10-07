"""Additional raw-source checks and compact complete selected-player calculations."""
from collections import defaultdict
from pathlib import Path
import argparse
import json
import polars as pl
from universal_baseball.storage import sha256_file
from verify_defense_reference_history_v26 import ROOT,PUBLIC,NATIVE,read,eq
from verify_double_play_support_v22 import write


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--first',type=int,default=0)
    parser.add_argument('--last',type=int,default=16);parser.add_argument('--save',action='store_true')
    args=parser.parse_args();walk=read(PUBLIC/'player-walks.json.gz')
    native=pl.read_parquet(NATIVE/'component-ledger.parquet').to_dicts()
    nmap={(s['season'],s['player_id'],s['position']):s for s in native}
    centers={}
    for y in range(2016,2026):
        for p in (7,8,9):
            rs=[r for r in native if r['season']==y and r['position']==p and r['range_valid']]
            centers[y,p]=1500*sum(r['range_runs'] for r in rs)/sum(r['native_outs'] for r in rs)
    minor=pl.read_parquet(ROOT/'reports/generated/defense-minor-counts-v18/counts.parquet').to_dicts()
    captures={};splits=annual=0
    for gi,g in enumerate(walk['groups']):
        show=args.first<=gi<args.last
        if show:print('\nGROUP',gi,json.dumps(g['selection']))
        for rec in g['records']:
            pid,y=rec['player_id'],rec['origin'];v=rec['value_prediction']
            names=[s['player_name'] for s in rec['quality_predictions']]
            name=v['player_name'] if v else names[0] if names else str(pid)
            assert rec['origin_minor_source_counts']==[s for s in minor if s['player_id']==pid and y-2<=s['season']<=y]
            for s in rec['origin_minor_source_counts']:
                path=Path(s['capture_path']);assert sha256_file(path)==rec['source_hashes'][str(path)]
                if path not in captures:captures[path]=read(path)
                data=captures[path];rows=data['splits'] if 'splits' in data else data['stats'][0]['splits']
                raw=rows[s['capture_split_index']]
                assert raw['player']['id']==pid and int(raw['season'])==s['season'] and str(raw['position']['code'])==s['position_code']
                for k in ('putOuts','assists','errors','chances','throwingErrors','doublePlays'):
                    assert raw['stat'].get(k)==s[k],(pid,k)
                splits+=1
            if show:print(name,pid,'focal',rec['is_focal'],'minor',[(s['season'],s['level_group'],s['position_code'],s['fielding_outs'],s['errors'],s['assists']) for s in rec['origin_minor_source_counts']])
            for p,h in rec['history_arithmetic'].items():
                if show and (h['history_outs'] or (rec['is_focal'] and int(p) in (7,8,9))):
                    print('H',p,'n',round(h['history_outs'],2),'weightedRaw/relative',round(h['weighted_raw_runs'],4),round(h['weighted_relative_runs'],4),'reliability',round(h['reliability'],4),'raw/C',round(h['legacy_raw'],4),round(h['centered'],4),
                          'annual(y,n,r,ref,w)',[(s['season'],s['native_outs'],round(s['raw_runs'],3),round(s['reference_rate'],3),s['weight']) for s in h['history_sources']])
            for s in rec['quality_predictions']:
                if show:print('Q',s['position'],'age',s['age'],'L/C/N/actual',*[None if s[k] is None else round(s[k],4) for k in ('legacy','centered','neutral','quality_rate')],'futureOuts/seasons/missing',s['future_outs'],s['future_seasons'],s['future_missing_outs'],s['quality_status'])
            for year in rec['annual_positions']:
                for s in year['positions']:
                    p=s['position'];raw=nmap.get((year['season'],pid,p));assert s['native']==raw
                    expected=centers.get((year['season'],p)) if year['season']>y else None
                    eq(s['observed_reference_rate'],expected)
                    relative=None if raw is None or not raw['range_valid'] else raw['range_runs']-(centers[year['season'],p]*raw['native_outs']/1500 if p in (7,8,9) else 0)
                    eq(relative,s['relative_observed_runs']);annual+=1
                if show and year['season']>y:
                    print('A',year['season'],[(s['position'],s['official_outs'],None if s['native'] is None else s['native']['native_outs'],None if s['native'] is None else s['native']['range_runs'],s['relative_observed_runs']) for s in year['positions']])
            if show and v:
                print('V PA',round(v['expected_PA'],2),v['actual_PA'],'positions expected/actual',rec['position_exposure'])
                print('V other',round(v['non_OF_history_runs'],4),'def L/C/N/actual',*[None if v[k] is None else round(v[k],4) for k in ('legacy_defense','centered_defense','neutral_defense','actual_defense')],
                    'bat/pos',round(v['batting_forecast'],4),round(v['position_runs'],4),'expanded L/C/N/actual',*[None if v[k] is None else round(v[k],4) for k in ('legacy_expanded','centered_expanded','neutral_expanded','actual_expanded')])
    if args.save:
        path=PUBLIC/'raw-player-source-review.json.gz';assert not path.exists()
        write(path,dict(model_fits=0,raw_minor_splits_replayed=splits,annual_position_records_replayed=annual,
            groups=16,player_records=64,all_selected_native_and_relative_observations_replayed=True,
            main_baseball_review_pending=True,hashes={str(p):sha256_file(p) for p in [Path(__file__),PUBLIC/'player-walks.json.gz',ROOT/'reports/generated/defense-minor-counts-v18/counts.parquet',*captures]}))
        print('Raw selected-player checks passed',splits,annual)


if __name__=='__main__':main()
