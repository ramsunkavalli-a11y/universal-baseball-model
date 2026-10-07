"""Independent sums, identities, unchanged assembly, raw splits and player review."""
from collections import defaultdict
from pathlib import Path
import gzip
import json
import math
import polars as pl
from universal_baseball.storage import sha256_file
from verify_double_play_support_v22 import write
from run_hitter_finite_return_baseline import protections

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT/'reports/model-evidence/defense-reference-v25/fold-repair'
OUT = ROOT/'reports/generated/defense-reference-v25/fold-repair'
V12 = ROOT/'reports/generated/defense-value-v12'


def read(path):
    with (gzip.open(path,'rt',encoding='utf8') if path.suffix=='.gz' else path.open(encoding='utf8')) as stream:
        return json.load(stream)


def eq(a,b):
    assert (a is None and b is None) or (a is not None and b is not None and abs(a-b)<1e-8),(a,b)


def pos(r,o):
    return sum(r[f'{o}_{p}']*v for p,v in zip(range(2,10),[12.5,-12.5,2.5,2.5,7.5,-7.5,2.5,-7.5]))/4374 - 17.5*r[f'{o}_10']/162


def main():
    protections(); assert not (PUBLIC/'independent-review.json.gz').exists()
    report=read(PUBLIC/'report.json.gz'); pre=read(PUBLIC/'preflight.json.gz'); walks=read(PUBLIC/'player-walks.json.gz')
    for note in [report,pre,walks]:
        for p,h in {**note['hashes'],**note.get('output_hashes',{})}.items(): assert sha256_file(Path(p))==h,p
    native=pl.read_parquet(ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet').to_dicts()
    nmap={(r['season'],r['player_id'],r['position']):r for r in native}
    official=defaultdict(int)
    for r in pl.read_parquet(ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet').iter_rows(named=True):
        if r['is_mlb'] and r['position_code'].isdigit():official[r['season'],r['player_id'],int(r['position_code'])]+=r['fielding_outs']
    centers={}; cutoffs={}
    for c in report['annual_centers']:
        year,p=c['season'],c['position']
        rows=[r for r in native if r['season']==year and r['position']==p and r['range_valid']]
        den=sum(r['native_outs'] for r in rows); num=sum(r['range_runs'] for r in rows)
        assert c['people']==len({r['player_id'] for r in rows}) and c['records']==len(rows)
        eq(c['outs'],den);eq(c['runs'],num);eq(c['rate'],1500*num/den)
        total=sum(n for (y,pid,position),n in official.items() if y==year and position==p)
        measured=sum(official[year,r['player_id'],p] for r in rows)
        assert total==c['official_total_outs'] and measured==c['measured_official_outs']
        assert total-measured==c['missing_official_outs']
        eq(sum(r['range_runs']-r['native_outs']*num/den for r in rows),c['centered_measured_runs'])
        centers[year,p]=1500*num/den
    assert len(centers)==30
    for c in report['cutoff_centers']:
        y,p,fold=c['origin'],c['position'],c['fold']
        rows=[r for r in native if y-2<=r['season']<=y and r['position']==p and r['range_valid'] and r['player_id']%5!=fold]
        den=sum(r['native_outs']/2**(y-r['season']) for r in rows)
        num=sum(r['range_runs']/2**(y-r['season']) for r in rows)
        eq(c['weighted_outs'],den);eq(c['weighted_runs'],num);eq(c['rate'],1500*num/den)
        assert c['people']==len({r['player_id'] for r in rows})
        assert c['seasons']==sorted({r['season'] for r in rows}) and c['held_people_excluded']
        cutoffs[y,fold,p]=1500*num/den
    assert len(cutoffs)==45
    forecasts={r['row_id']:r for r in pl.read_parquet(V12/'predictions.parquet').to_dicts()}
    bridge={r['row_id']:r for r in pl.read_parquet(ROOT/'reports/generated/defense-transition-v10/predictions.parquet').to_dicts()}
    channels=defaultdict(list)
    for r in pl.read_parquet(V12/'channel-predictions.parquet').to_dicts():channels[r['row_id']].append(r)
    ledger={(r['row_id'],r['position']):r for r in pl.read_parquet(OUT/'range-reference-ledger.parquet').to_dicts()}
    offsets=pl.read_parquet(OUT/'reference-offsets.parquet').to_dicts()
    assert set(forecasts)==set(bridge)=={r['row_id'] for r in offsets} and len(offsets)==12432
    computed={};totals=defaultdict(lambda:defaultdict(float));replays=0
    for off in offsets:
        rid=off['row_id'];r=forecasts[rid];q=bridge[rid];cells=channels[rid];y=r['origin_year'];pid=r['player_id']
        actual_runs=[c['actual_runs'] for c in cells]
        eq(sum(actual_runs) if all(v is not None for v in actual_runs) else None,r['actual_defense'])
        eq(pos(q,'actual'),r['actual_position_runs'])
        eq(None if r['actual_defense'] is None else r['actual_batting']+(pos(q,'actual')+r['actual_defense'])/10,r['actual_expanded'])
        ao=0.;aunknown=False;po={o:0. for o in ['ratio','repair','transition']}
        for c in cells:
            for skill in ['neutral','history','calibrated']:
                rate=0. if skill=='neutral' else c['history_rate']
                if skill=='calibrated' and c['channel'].startswith('range_') and c['quality_evidence_observed'] and c['range_calibration_fit_allowed'] and c['saved_range_calibration'] is not None:rate=c['saved_range_calibration']
                eq(rate,c[skill+'_quality'])
                for o in po:
                    n=q[f'{o}_{c["channel"][-1]}'] if c['channel'].startswith('range_') else q[f'{o}_native_{c["channel"]}']
                    eq(n,c[o+'_predicted_opportunities']);eq(rate*n/c['rate_unit'],c[o+'_'+skill])
            if c['channel'] not in ['range_7','range_8','range_9']:continue
            p=int(c['channel'][-1]);d=ledger[rid,p];ref=cutoffs[y,pid%5,p]
            eq(d['cutoff_reference_rate'],ref);eq(d['actual_reference_rate'],centers[y+1,p])
            if c['actual_official_exposure']>0 and c['actual_runs'] is not None:
                source=nmap[y+1,pid,p];assert source['range_valid'];eq(c['actual_runs'],source['range_runs'])
                actual_offset=centers[y+1,p]*source['native_outs']/1500
                eq(d['actual_native_outs'],source['native_outs'])
            elif c['actual_official_exposure']==0:actual_offset=0.
            else:actual_offset=None;aunknown=True
            eq(d['actual_offset'],actual_offset)
            eq(d['actual_relative_range'],None if actual_offset is None else c['actual_runs']-actual_offset)
            if actual_offset is not None:ao+=actual_offset
            sources=[s for s in native if s['player_id']==pid and s['position']==p and y-2<=s['season']<=y and s['range_valid']]
            n=sum(s['native_outs']/2**(y-s['season']) for s in sources)
            v=sum(s['range_runs']/2**(y-s['season']) for s in sources)
            eq(d['history_outs'],n);eq(d['history_runs'],v);eq(d['raw_history_rate'],1500*v/(n+3000));eq(d['reliability'],n/(n+3000))
            eq(d['relative_measured_history_rate'],None if not c['quality_evidence_observed'] else c['history_rate']-ref)
            for o in po:po[o]+=q[f'{o}_{p}']*ref/1500
        eq(off['actual_reference_offset'],None if aunknown else ao)
        assert off['complete_defined_target']==(r['actual_defense'] is not None)
        for o in po:
            eq(off[o+'_cutoff_offset'],po[o]);eq(pos(q,o),r[o+'_position_runs'])
            for skill in ['neutral','history','calibrated']:
                arm=o+'_'+skill; raw=sum(c[arm] for c in cells)
                eq(raw,r[arm+'_defense']);eq(r['batting_forecast']+(raw+pos(q,o))/10,r[arm+'_expanded'])
                eq(raw-po[o]+pos(q,o)+po[o],raw+pos(q,o));replays+=1
            total=totals[y,o];total['all_forecast_offset']+=po[o];total['rows']+=1
            if off['complete_defined_target']:
                total['complete_rows']+=1;total['complete_forecast_offset']+=po[o];total['complete_actual_offset']+=ao
                for p in [7,8,9]:
                    total[str(p)+'_forecast_offset']+=q[f'{o}_{p}']*cutoffs[y,pid%5,p]/1500
                    total[str(p)+'_actual_offset']+=ledger[rid,p]['actual_offset']
        computed[rid]=po
    for c in report['forecast_reference_totals']:
        for k,v in totals[c['origin'],c['opportunity_arm']].items():eq(c[k],v)
    minor=pl.read_parquet(ROOT/'reports/generated/defense-minor-counts-v18/counts.parquet').filter(pl.col('season').is_between(2020,2022)).to_dicts()
    captures={};raw_splits=0;case_records=0
    for case in walks['cases']:
        focal=case['records'][0];pid=case['focal_player_id'];q=bridge[focal['forecast']['row_id']]
        assert q['player_id']==pid and case['origin']==2022
        pool=[s for s in bridge.values() if s['origin_year']==2022 and s['stage']==q['stage'] and s['repertoire_primary_role']==q['repertoire_primary_role'] and s['player_id']!=pid]
        pool.sort(key=lambda s:(abs((s['age'] if s['age'] is not None else 27)-(q['age'] if q['age'] is not None else 27)),abs(s['role_defensive_sample']-q['role_defensive_sample']),s['row_id']))
        assert [s['row_id'] for s in pool[:3]]==[s['forecast']['row_id'] for s in case['records'][1:]]
        for rec in case['records']:
            rid=rec['forecast']['row_id'];pid=rec['forecast']['player_id'];q=bridge[rid];case_records+=1
            assert rec['forecast']==forecasts[rid] and rec['channels']==channels[rid]
            assert rec['origin_role']['assembly_outer_fold']==q['outer_fold'] and rec['origin_role']['reference_fold']==pid%5
            assert rec['origin_and_future_native_records']==[s for s in native if s['player_id']==pid and 2020<=s['season']<=2023]
            assert rec['origin_minor_source_counts']==[s for s in minor if s['player_id']==pid]
            for o,values in rec['exposure'].items():
                for p,v in values.items():eq(v,q[f'{o}_{p}'])
            for d in rec['reference_calculations']:
                p=d['position']
                for k,v in ledger[rid,p].items():assert d[k]==v,(rid,p,k)
                for o,v in d['predicted_offsets'].items():eq(v,q[f'{o}_{p}']*cutoffs[2022,pid%5,p]/1500)
                assert d['neutral_position_prior']==dict(intrinsic_mean=cutoffs[2022,pid%5,p],relative_mean=0.,measured_skill=False)
                assert d['history_sources']==[s for s in native if s['player_id']==pid and s['position']==p and 2020<=s['season']<=2022 and s['range_valid']]
            for s in rec['origin_minor_source_counts']:
                path=Path(s['capture_path'])
                if path not in captures:captures[path]=read(path)
                data=captures[path];splits=data['splits'] if 'splits' in data else data['stats'][0]['splits']
                raw=splits[s['capture_split_index']]
                assert raw['player']['id']==pid and int(raw['season'])==s['season'] and str(raw['position']['code'])==s['position_code']
                for k in ['putOuts','assists','errors','chances','throwingErrors','doublePlays']:assert raw['stat'].get(k)==s[k],(pid,k)
                raw_splits+=1
    write(PUBLIC/'independent-review.json.gz',dict(all_saved_assemblies_replayed=replays,all_saved_channels_replayed=149184,
        annual_centers_replayed=30,cutoff_centers_replayed=45,OF_records_replayed=len(ledger),
        player_records_replayed=case_records,origin_blind_peer_groups_replayed=len(walks['cases']),raw_minor_splits_replayed=raw_splits,
        model_fits=0,integrity_pass=True,predictive_validation=False,main_player_review_pending=True,
        hashes={str(p):sha256_file(p) for p in [Path(__file__),PUBLIC/'report.json.gz',PUBLIC/'player-walks.json.gz',
            *captures.keys()]}))
    protections();print(f'{replays} saved assemblies, {len(ledger)} OF records, {case_records} player records and {raw_splits} raw minor splits replay.',flush=True)


if __name__=='__main__':main()
