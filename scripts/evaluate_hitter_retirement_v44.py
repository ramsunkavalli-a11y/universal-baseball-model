"""Fixed source/status repair of reviewed means; no fitting or altered eligibility."""
from collections import defaultdict
from datetime import date
from pathlib import Path
import json
import numpy as np
import polars as pl
from universal_baseball.retirement_availability import events,state
from universal_baseball.storage import sha256_file
from universal_baseball.practical_hitter_v30 import score
from score_practical_hitter_v31 import paired

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/practical-hitter-retirement-v44'
ARMS=['safe_ridge','cohort','games']


def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(n,o):(OUT/n).write_text(json.dumps(o,indent=2,default=str,allow_nan=False),encoding='utf8')


def sources():
    captures=[]
    for y in range(2015,2025):
        p=ROOT/'reports/generated/hitter-injury-history-v2'/('source-2015' if y==2015 else 'source')/'captures'/f'transactions-{y}.json'
        captures.append((y,p,read(p)))
    return captures


def main():
    assert read(ROOT/'reports/generated/practical-hitter-joint-forest-v43/report.json')['player_walkthrough_status']=='complete'
    assert not (OUT/'source-manifest.json').exists();OUT.mkdir(parents=True,exist_ok=True)
    captures=sources();records=events(captures,date(2024,12,31));by=defaultdict(list)
    for r in records:by[r['player_id']].append(r)
    src=ROOT/'reports/generated/practical-hitter-v38/predictions.parquet';original=pl.read_parquet(src)
    states=[state(by[o['player_id']],date(o['origin_year'],12,31)) for o in original.iter_rows(named=True)]
    flags=np.array([s['reported_retired'] for s in states]);q=original.with_columns(pl.Series('reported_retired',flags))
    bridge=pl.read_parquet(ROOT/'reports/generated/practical-hitter-joint-forest-v43/origin-evidence-bridge.parquet')
    q=q.join(bridge.select('row_id','origin_evidence_bridge'),on='row_id',how='left',validate='1:1');assert q['origin_evidence_bridge'].null_count()==0
    hashes={str(p):sha256_file(p) for _,p,_ in captures}
    for p in [src,ROOT/'docs/practical-hitter-retirement-v44-contract.md',Path(__file__),
        ROOT/'src/universal_baseball/retirement_availability.py',ROOT/'reports/generated/practical-hitter-joint-forest-v43/report.json']:
        hashes[str(p)]=sha256_file(p)
    write('source-manifest.json',dict(before_scoring=True,input_hashes=hashes,retirement_statuses=int(flags.sum()),
        fitting=False,eligibility_unchanged=True,publication_vintages_verified=False,all_level_coverage_certified=False,
        primary_crosschecks=[dict(player_id=120074,known_public_date='2016-11-16',source='https://www.mlb.com/news/david-ortiz-officially-retires-from-baseball-c208949106'),
            dict(player_id=457763,known_public_date='2021-11-04',source='https://www.mlb.com/giants/video/buster-posey-announces-retirement')]))
    for a in ARMS:
        q=q.with_columns(*[pl.when(pl.col('reported_retired')).then(pl.lit(0.)).otherwise(pl.col(a+'_'+m)).alias('retired_'+a+'_'+m) for m in ['pa','value']])
        assert q.filter(~pl.col('reported_retired'))[a+'_pa'].equals(q.filter(~pl.col('reported_retired'))['retired_'+a+'_pa'])
        assert q[a+'_rate'].equals(original[a+'_rate'])
    assert q.select(original.columns).equals(original) and len(q)==30506 and q['target_year'].max()==2025
    q.write_parquet(OUT/'predictions.parquet');public=q.filter(pl.col('v24_pa').is_not_null()&(pl.col('pa_0')>0)&pl.col('steamer_pa').is_not_null()&pl.col('zips_rate').is_not_null());assert len(public)==1789
    scopes=[('all',q),('public_active',public),('reported_retired',q.filter(pl.col('reported_retired'))),('unchanged',q.filter(~pl.col('reported_retired'))),
        ('source_supported_diagnostic',q.filter(pl.col('origin_evidence_bridge'))),('roster_only_unverified',q.filter(~pl.col('origin_evidence_bridge')))]
    scopes.extend(('origin_'+str(y),q.filter(pl.col('origin_year')==y)) for y in sorted(q['origin_year'].unique()))
    scopes.extend(('stage_'+s,q.filter(pl.col('stage')==s)) for s in sorted(q['stage'].unique()))
    scores=[];intervals=[]
    for label,g in scopes:
        scores.append(dict(scope=label,rows=len(g),actual_pa=int(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
            scores={a:score(g,a) for a in [*ARMS,*['retired_'+a for a in ARMS]]+(['steamer'] if label=='public_active' else [])}))
        if label in ['all','public_active']:
            for a in ARMS:
                for m in ['pa','value']:intervals.append(dict(scope=label,**paired(g,'retired_'+a,a,m)))
    write('scores.json',scores);write('intervals.json',intervals)
    changed=q.filter(pl.col('reported_retired'));selected=set(changed['row_id'])
    for pid,y in [(405395,2021),(592450,2024),(701762,2024)]:
        cell=q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y));assert len(cell)==1;selected.add(cell['row_id'][0])
    counts=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet');keys=read(ROOT/'reports/generated/practical-hitter-v34/preflight.json')['features'];cases=[]
    for o,s in zip(q.iter_rows(named=True),states):
        if o['row_id'] not in selected:continue
        peers=q.filter((pl.col('origin_year')==o['origin_year'])&(pl.col('stage')==o['stage'])&(pl.col('player_id')!=o['player_id'])).with_columns(
            ((pl.col('age')-o['age'])**2+((pl.col('pa_0')-o['pa_0'])/100)**2+((pl.col('quality_0')-o['quality_0']))**2).alias('distance')).sort('distance','player_id').head(3)
        cases.append(dict(origin=o,status=s,selection='all reported-retired states' if s['reported_retired'] else 'fixed unchanged counterexample',
            actual_inputs={k:o[k] for k in keys},source_history=counts.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(o['origin_year']-2,o['origin_year'])).sort('season','bucket').to_dicts(),
            context_records=[x for x in by[o['player_id']] if x['known_date']<=date(o['origin_year'],12,31)],
            peers=peers.select('player_id','player_name','age','pa_0','reported_retired','safe_ridge_pa','retired_safe_ridge_pa','next_pa','next_value').to_dicts()))
    write('cases.json',cases);write('events.json',records)
    # Source-only counterexample: opted out in 2020 but reinstated before origin end.
    posey=state(by[457763],date(2020,12,31));assert not posey['reported_retired']
    write('verification.json',dict(player_walkthrough_status='pending',rows=len(q),retirement_rows=len(changed),
        positive_future_pa_retirement_rows=int(changed.filter(pl.col('next_pa')>0).height),
        all_old_columns_exact=True,batting_rate_unchanged=True,unchanged_rows_bit_exact=True,
        source_eligibility_qualified=True,posey_2020_not_retired=posey,protected_outcomes_used=False,frozen_forecast_changed=False))
    print('Retirement rows',len(changed),'review cases',len(cases),'actual retirement-row next PA',changed['next_pa'].sum(),flush=True)
    for s in scores[:3]:print(s['scope'],{a:(round(v['pa_rmse'],3),round(v['pa_mae'],3),round(v['value_rmse'],5)) for a,v in s['scores'].items()},flush=True)


if __name__=='__main__':main()
