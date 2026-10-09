"""No-fit error attribution and origin-selected prospect player walks."""
import gzip
import json
import math
from collections import defaultdict
import polars as pl
from check_hitter_2027_historical_full_value import BASE, OUT, PUBLIC, decode, loss
from capture_hitter_2027_origin_counts import write_once
from universal_baseball.storage import sha256_file


def main():
    rows = pl.read_parquet(OUT/'predictions-reviewed.parquet').to_dicts()
    stints = pl.read_parquet(BASE/'stints.parquet').to_dicts()
    histories = defaultdict(list)
    for r in stints: histories[r['player_id']].append(r)
    observed = {}
    checks = []
    fields = ['Batting','BaseRunning','Fielding','Positional','Replacement','wLeague']
    for y in (2023,2024,2025):
        source, _ = decode(gzip.decompress((OUT/f'fg-batting-{y}.html.gz').read_bytes()).decode(),y)
        discrepancy = max(abs(math.fsum(r.get(k) or 0 for k in fields)-r['RAR']) for r in source)
        assert discrepancy < 1e-8
        checks.append(dict(year=y,rows=len(source),max_RAR_reconciliation_error=discrepancy,
                           framing_already_in_Fielding=True))
        for r in source: observed[y,int(r['xMLBAMID'])] = {k:r.get(k) for k in ['PA','WAR','RAR',*fields]}
    for r in rows:
        origin_history = [s for s in histories[r['player_id']] if s['season']<=r['origin_year']]
        r['prior_MLB_PA'] = sum(s['plate_appearances'] for s in origin_history if s['level_group']=='MLB')
        r['actual_components'] = observed.get((r['target_year'],r['player_id']), dict.fromkeys(['PA','WAR','RAR',*fields],0.))
    def aggregate(rr):
        return dict(rows=len(rr),expected_PA=sum(r['expected_PA'] for r in rr),actual_PA=sum(r['actual_PA'] for r in rr),
            WAR=sum(r['combined'] for r in rr),actual_WAR=sum(r['actual_WAR'] for r in rr),
            forecast_runs={k:sum(r[k] for r in rr) for k in rows[0] if k.endswith('_runs')},
            realized_runs={k:sum(r['actual_components'][k] or 0 for r in rr) for k in fields},
            scores={a:loss(rr,a) for a in ['combined','batting_anchor','simple_history']})
    groups={}
    for stage in sorted({r['stage'] for r in rows}):
        cohort=[r for r in rows if r['stage']==stage]
        groups[stage]=aggregate(cohort)
        for y in (2023,2024,2025): groups[f'{stage}_{y}']=aggregate([r for r in cohort if r['target_year']==y])
        if stage!='Current MLB':
            for status,predicate in [('no_prior_MLB',lambda r:r['prior_MLB_PA']==0),('MLB_returnee',lambda r:r['prior_MLB_PA']>0),
                                     ('future_nonparticipant',lambda r:r['actual_PA']==0),('future_participant',lambda r:r['actual_PA']>0)]:
                rr=[r for r in cohort if predicate(r)]
                if rr:groups[f'{stage}_{status}']=aggregate(rr)
    upper=[r for r in rows if r['stage']=='Upper minors']
    chosen={}
    def choose(r,why):chosen.setdefault(r['row_id'],[]).append(why)
    choose(max(upper,key=lambda r:r['combined']-r['actual_WAR']),'largest upper-minors false high')
    choose(min(upper,key=lambda r:r['combined']-r['actual_WAR']),'largest upper-minors false low')
    for pid,year in [(702616,2024),(701762,2025),(691723,2024),(686948,2025),(665487,2023)]:
        for r in rows:
            if (r['player_id'],r['target_year'])==(pid,year):choose(r,'diagnostic from initial cohort inspection')
    choose(min([r for r in upper if r['actual_PA']>=100],key=lambda r:abs(r['combined']-r['actual_WAR'])),'ordinary upper-minors arrival')
    bat={r['row_id']:r for r in pl.read_parquet(BASE.parent/'hitter-2027-translation-repair/predictions.parquet').to_dicts()}
    roles={r['row_id']:r for r in pl.read_parquet(BASE/'role-fallback-repair/role-budget-historical.parquet').to_dicts()}
    def case(r):
        source=[s for s in histories[r['player_id']] if r['origin_year']-2<=s['season']<=r['origin_year']]
        return dict(forecast=r,origin_stints=source,batting_input=bat[r['row_id']],role_input=roles[r['row_id']])
    walks=[]
    for rid,reasons in chosen.items():
        r=next(s for s in rows if s['row_id']==rid)
        peers=sorted([s for s in rows if s['origin_year']==r['origin_year'] and s['stage']==r['stage']
            and s['position']==r['position'] and bool(s['prior_MLB_PA'])==bool(r['prior_MLB_PA']) and s['player_id']!=r['player_id']],
            key=lambda s:(abs(s['origin_PA']-r['origin_PA']),abs((s['age'] or 27)-(r['age'] or 27)),s['player_id']))[:3]
        walks.append(dict(reasons=reasons,primary=case(r),peers=[case(s) for s in peers]))
    path=PUBLIC/'historical-full-value-cohort-walks.json.gz';assert not path.exists()
    path.write_bytes(gzip.compress(json.dumps(walks,default=str,allow_nan=False).encode(),mtime=0))
    write_once(PUBLIC/'historical-full-value-cohort-diagnosis.json',dict(groups=groups,actual_component_reconciliation=checks,
        no_model_change=True,actual_opportunity_conditioning_diagnostic_only=True,
        peer_rule='same origin, stage, position, previous MLB experience; nearest origin PA then age/ID',
        walkthrough_status='pending_written_review',walk_sha256=sha256_file(path)))
    print(json.dumps({k:v for k,v in groups.items() if k.startswith('Upper minors')},indent=2))
    for w in walks:
        r=w['primary']['forecast'];print(r['player_name'],r['target_year'],r['expected_PA'],r['actual_PA'],r['combined'],r['actual_WAR'],flush=True)


if __name__=='__main__':main()
