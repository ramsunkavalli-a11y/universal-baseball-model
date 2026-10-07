"""Independent source replay and all historical fixed/coverage case walks."""
from pathlib import Path
import json
import math
import polars as pl
from source_defensive_positions_v2 import embedded
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file
from review_arm_receiving_pilot_v6 import FIXED

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/arm-receiving-v6'
PUBLIC=ROOT/'reports/model-evidence/arm-receiving-v6'


def main():
    protections()
    capture=json.loads((OUT/'extension-capture.json').read_text())
    assert not (OUT/'extension-review.json').exists()
    for group in ('input_hashes','output_hashes'):
        for path,expected in capture[group].items():assert sha256_file(Path(path))==expected,path
    ledger_path=ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet'
    ledger=pl.read_parquet(ledger_path)
    lut={(year,pid):g.to_dicts() for (year,pid),g in ledger.group_by(['season','player_id'])}
    annual=pl.read_parquet(OUT/'annual.parquet')
    actual={(r['kind'],r['season'],r['player_id']):r for r in annual.iter_rows(named=True)}
    assert len(actual)==len(annual)
    source_keys=set();walks=[];missing=[];totals=[]
    for cap in capture['captures']:
        year,kind=cap['year'],cap['kind'];assert year<=2025
        path=Path(cap['path']);assert sha256_file(path)==cap['sha256']
        text=path.read_text(encoding='utf8');raw=embedded(text,'data')
        meta=embedded(text,'serverParams')
        assert meta==cap['metadata']
        source={int(r['entity_id'] if kind=='arm' else r['player_id']):r for r in raw}
        assert len(raw)==len(source)==cap['rows']
        group=[]
        for pid,s in source.items():
            key=(kind,year,pid);source_keys.add(key);r=actual[key];group.append(r)
            native=lut.get((year,pid),[])
            column='arm_runs' if kind=='arm' else 'fielding_runs_prevented_on_rec1b'
            measured=[n[column] for n in native if n[column] is not None and (kind=='arm' or n['position']==3)]
            native_runs=sum(measured) if measured else None
            n=int(s['n_opp_xb'] if kind=='arm' else s['n_plays'])
            runs=s['fielder_runs'] if kind=='arm' else s['total_oaa']*.75
            assert r['opportunities']==n and n>0 and r['runs']==runs
            assert r['native_runs']==native_runs
            good=runs is not None and native_runs is not None and abs(runs-native_runs)<=1e-8
            assert r['native_match']==good
            assert r['runs_per_100']==(None if runs is None else 100*runs/n)
            if kind=='arm':
                assert s['n_out']+s['n_safe']==s['n_att_xb']<=n
                assert r['holds']==n-s['n_att_xb']
                if runs is not None:assert abs(runs-sum(s['fielder_runs_'+k] for k in ('swipe','snipe','freeze')))<=1e-8
                of=sum(z['native_outs'] for z in native if z['position'] in (7,8,9))
                other=sum(z['native_outs'] for z in native if z['position'] not in (7,8,9))
                assert r['isolated_outfield_quality_valid']==bool(good and of>0 and other==0)
            else:
                assert abs(s['n_outs']-n*s['avg_expected_rate_out']-s['total_oaa'])<=1e-8
                bins=('on_target','low','high','scoop','wide','bounce')
                assert n==sum(s['n_'+k] for k in bins)
                assert s['n_outs']==sum(s['outs_'+k] for k in bins)
                assert abs(s['total_oaa']-sum(s['oaa_'+k] for k in bins))<=1e-8
                assert r['quality_valid']==good
        by_id={r['player_id']:r for r in group};selections={}
        for pid in FIXED[kind]:
            if pid in by_id:selections.setdefault(pid,[]).append('fixed_source_contract')
            else:missing.append(dict(kind=kind,year=year,player_id=pid,quality='unknown_no_eligible_opportunity'))
        for r in sorted(group,key=lambda r:(r['opportunities'],r['player_id']))[:2]:
            selections.setdefault(r['player_id'],[]).append('two_smallest_positive_opportunities')
        for r in group:
            if not r['native_match']:selections.setdefault(r['player_id'],[]).append('all_incomplete_native_measurements')
        def trace(r):
            pid=r['player_id']
            return dict(measurement=r,raw=source[pid],native_positions=lut.get((year,pid),[]),
                source_path=str(path),source_sha256=cap['sha256'],forecast=None,future_quality=None,
                explanation='Exact opportunity-adjusted observation, not yet a future skill prediction. Missing credit remains unknown; mixed-position credit is not isolated OF talent.')
        for pid,rule in selections.items():
            focal=by_id[pid]
            peers=sorted((r for r in group if r['player_id']!=pid),
                key=lambda r:(abs(math.log1p(r['opportunities'])-math.log1p(focal['opportunities'])),r['player_id']))[:3]
            walks.append(dict(kind=kind,year=year,player_id=pid,selection=rule,
                primary=trace(focal),peers=[trace(r) for r in peers],
                peer_selection='Three nearest log opportunity counts, ID tie-break, no outcomes.'))
        totals.append(dict(kind=kind,year=year,rows=len(group),opportunities=sum(r['opportunities'] for r in group),
            reconciled=sum(r['native_match'] for r in group),
            isolated_outfield_rows=sum(bool(r.get('isolated_outfield_quality_valid')) for r in group),
            measured_runs=sum(r['runs'] for r in group if r['runs'] is not None)))
    assert source_keys==set(actual)
    walk_report=dict(walks=walks,absent_fixed=missing,focal_cases=len(walks),peer_cases=3*len(walks),
        player_walkthrough_status='complete',no_model_fit=True,no_2026_outcomes=True)
    save(OUT/'extension-player-walkthrough.json',walk_report)
    report=dict(rows=len(actual),totals=totals,source_arithmetic_independent_replay_pass=True,
        invalid_measurements=[r for r in actual.values() if not r['native_match']],
        player_walkthrough_status='complete',support_audit_allowed=True,model_fit_allowed=False,
        disposition='Qualified receiving and OF-only source; preserve all scope/gap records. No talent accuracy claim.',
        no_2026_outcomes=True,no_model_fit=True,focal_cases=len(walks),peer_cases=3*len(walks),
        input_hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'annual.parquet',OUT/'extension-capture.json',ledger_path]},
        output_hashes={str(OUT/'extension-player-walkthrough.json'):sha256_file(OUT/'extension-player-walkthrough.json')})
    save(OUT/'extension-review.json',report)
    save(PUBLIC/'extension-review.json',report)
    save(PUBLIC/'extension-player-walkthrough.json',walk_report)
    print(json.dumps(dict(rows=len(actual),focal_cases=len(walks),peer_cases=3*len(walks),totals=totals),indent=2))


if __name__=='__main__':main()
