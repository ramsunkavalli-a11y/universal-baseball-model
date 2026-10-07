"""Preserve fixed source peers and add all declared gains, losses and false ratings."""
from collections import defaultdict
from pathlib import Path
import polars as pl
from universal_baseball.defense_reference_history import history
from universal_baseball.storage import sha256_file
from verify_double_play_support_v22 import write
from run_defense_reference_history_v26 import ROOT,OUT,PUBLIC,V25,V12,BRIDGE,read,verify,sources
from run_hitter_finite_return_baseline import protections


def main():
    protections();assert not (PUBLIC/'player-walks.json.gz').exists()
    pre=read(PUBLIC/'preflight.json.gz');verify(pre);report=read(PUBLIC/'report.json.gz');verify(report)
    native,people,refs,measured,official=sources()
    q=pl.read_parquet(OUT/'quality-predictions.parquet').to_dicts()
    f=pl.read_parquet(OUT/'value-predictions.parquet').to_dicts()
    qm={(r['origin_year'],r['player_id'],r['position']):r for r in q}
    fm={r['row_id']:r for r in f};fp={(r['origin_year'],r['player_id']):r for r in f}
    bridge=pl.read_parquet(BRIDGE).to_dicts();bm={r['row_id']:r for r in bridge}
    cs=defaultdict(list)
    for c in pl.read_parquet(OUT/'OF-predictions.parquet').to_dicts():cs[c['row_id']].append(c)
    oldcs=defaultdict(list)
    for c in pl.read_parquet(V12/'channel-predictions.parquet').to_dicts():oldcs[c['row_id']].append(c)
    selections=[]
    old=read(V25/'player-walks.json.gz')
    for c in old['cases']:
        focal=c['records'][0]['forecast']
        selections.append(dict(kind='fixed_value',origin=2022,player_id=c['focal_player_id'],position=None,
            categories=['fixed_source'],peer_ids=[r['forecast']['player_id'] for r in c['records'][1:]]))
    primary=[r for r in q if r['origin_year']==2022 and r['position'] in (7,8,9) and r['quality_rate'] is not None]
    key=lambda r:((r['centered']-r['quality_rate'])**2-(r['legacy']-r['quality_rate'])**2,r['player_id'],r['position'])
    quality_picks=[('quality_largest_gain',min(primary,key=key)),('quality_largest_loss',max(primary,key=key)),
        ('quality_false_high',max(primary,key=lambda r:(r['centered']-r['quality_rate'],-r['player_id'],-r['position']))),
        ('quality_false_low',min(primary,key=lambda r:(r['centered']-r['quality_rate'],r['player_id'],r['position'])))]
    median=float(pl.Series([abs(r['centered']-r['quality_rate']) for r in primary]).median())
    quality_picks.append(('quality_ordinary',min(primary,key=lambda r:(abs(abs(r['centered']-r['quality_rate'])-median),r['player_id'],r['position']))))
    combined=defaultdict(list)
    for category,r in quality_picks:combined[r['origin_year'],r['player_id'],r['position']].append(category)
    for (y,pid,p),categories in combined.items():
        focal=qm[y,pid,p]
        pool=[r for r in q if r['origin_year']==y and r['position']==p and r['player_id']!=pid]
        pool.sort(key=lambda r:(r['age'] is None or focal['age'] is None,
            abs(r['age']-focal['age']) if r['age'] is not None and focal['age'] is not None else 0,
            abs(r['history_outs']-focal['history_outs']),r['player_id']))
        selections.append(dict(kind='quality',origin=y,player_id=pid,position=p,categories=categories,peer_ids=[r['player_id'] for r in pool[:3]]))
    complete=[r for r in f if r['actual_defense'] is not None]
    value_picks=defaultdict(list)
    for metric in ('defense','expanded'):
        loss=lambda r:((r['centered_'+metric]-r['actual_'+metric])**2-(r['legacy_'+metric]-r['actual_'+metric])**2,r['row_id'])
        for cat,row in [('gain',min(complete,key=loss)),('loss',max(complete,key=loss))]:
            value_picks[row['row_id']].append(metric+'_largest_'+cat)
    for rid,categories in value_picks.items():
        focal=bm[rid];y=focal['origin_year'];pid=focal['player_id']
        # A new origin is kept even if the same player was a fixed 2022 case.
        existing=next((s for s in selections if s['origin']==y and s['player_id']==pid and s['position'] is None),None)
        if existing:existing['categories'].extend(categories);continue
        pool=[r for r in bridge if r['origin_year']==y and r['stage']==focal['stage'] and
              r['repertoire_primary_role']==focal['repertoire_primary_role'] and r['player_id']!=pid]
        pool.sort(key=lambda r:(abs((r['age'] if r['age'] is not None else 27)-(focal['age'] if focal['age'] is not None else 27)),
            abs(r['role_defensive_sample']-focal['role_defensive_sample']),r['row_id']))
        selections.append(dict(kind='value',origin=y,player_id=pid,position=None,categories=categories,peer_ids=[r['player_id'] for r in pool[:3]]))
    counts_path=ROOT/'reports/generated/defense-minor-counts-v18/counts.parquet'
    minor=defaultdict(list)
    for r in pl.read_parquet(counts_path).to_dicts():minor[r['player_id']].append(r)
    groups=[]
    for sel in selections:
        y=sel['origin'];records=[]
        for pid in [sel['player_id'],*sel['peer_ids']]:
            value=fp.get((y,pid));rid=value['row_id'] if value else None
            quality=[r for k,r in qm.items() if k[:2]==(y,pid)]
            positions=range(3,10) if sel['position'] is None else [sel['position']]
            histories={str(p):history(people[pid],y,p,pid%5,refs) for p in positions}
            annual=[]
            for year in range(y-2,min(y+3,2025)+1):
                posrows=[]
                for p in range(2,10):
                    n=official[year,pid,p]
                    source=next((r for r in people[pid] if r['season']==year and r['position']==p),None)
                    if n==0 and source is None:continue
                    posrows.append(dict(position=p,official_outs=n,native=source,
                        observed_reference_rate=measured.get((year,p)) if year>y else None,
                        relative_observed_runs=None if source is None or not source['range_valid'] else
                            source['range_runs']-(measured[year,p]*source['native_outs']/1500 if p in (7,8,9) else 0)))
                annual.append(dict(season=year,positions=posrows))
            source_minor=[r for r in minor[pid] if y-2<=r['season']<=y]
            capture_paths={Path(r['capture_path']) for r in source_minor}
            records.append(dict(player_id=pid,origin=y,is_focal=pid==sel['player_id'],
                quality_predictions=quality,history_arithmetic=histories,annual_positions=annual,
                value_prediction=value,OF_value_channels=cs[rid] if rid else None,
                unchanged_other_channels=[c for c in oldcs[rid] if c['channel'] not in ('range_7','range_8','range_9')] if rid else None,
                position_exposure={o:{str(p):bm[rid][f'{o}_{p}'] for p in range(2,11)} for o in ('repair','actual')} if rid else None,
                origin_minor_source_counts=source_minor,source_hashes={str(p):sha256_file(p) for p in capture_paths}))
        groups.append(dict(selection=sel,records=records))
    write(PUBLIC/'player-walks.json.gz',dict(groups=groups,model_fits=0,player_walkthrough_status='pending',
        primary_quality_selection='2022 OF measured rows; largest squared-error gain/loss, false high/low, median absolute error.',
        peers='Origin-only stage/role age/exposure for value; same-position age/exposure for quality, including unknown future quality.',
        hashes={str(p):sha256_file(p) for p in [Path(__file__),counts_path,PUBLIC/'preflight.json.gz',PUBLIC/'report.json.gz',V25/'player-walks.json.gz']}))
    protections();print(f'{len(groups)} player groups and {sum(len(g["records"]) for g in groups)} full calculations saved; review pending.',flush=True)


if __name__=='__main__':main()
