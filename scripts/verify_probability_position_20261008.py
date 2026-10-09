"""Independent scalar probability, source-pair and report arithmetic checks."""
from collections import defaultdict
from pathlib import Path
import gzip
import json
import math
import numpy as np
import polars as pl
from scipy.stats import betabinom, binom
from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/'reports/model-evidence/probability-position-2026-10-08'
OUT=ROOT/'reports/generated/probability-position-2026-10-08'


def read(path):
    with (gzip.open if path.suffix=='.gz' else open)(path,'rt',encoding='utf8') as f:return json.load(f)


def close(a,b,tol=1e-8):assert math.isclose(a,b,abs_tol=tol,rel_tol=0),(a,b)


def main():
    assert not (PUB/'independent-review.json.gz').exists()
    pre=read(PUB/'preflight.json.gz');seal=read(PUB/'execution-check.json.gz')
    for path,h in seal['hashes'].items():assert sha256_file(Path(path))==h,path
    for path,h in pre['hashes'].items():
        if '/scripts/' in path.replace('\\','/') or path.endswith('probability_position_diagnostics.py'):continue
        assert sha256_file(Path(path))==h,path
    for filename in ['numeric-execution-amendment.json.gz','resource-execution-amendment.json.gz']:
        assert read(PUB/filename)['scored_results_exposed'] is False
    f=pl.read_parquet(OUT/'workload-derived.parquet')
    audit=read(PUB/'workload-calibration.json.gz')
    old=pl.read_parquet(ROOT/'reports/generated/hitter-workload-risk/scored-predictions.parquet',
        columns=['row_id','preseason_p','preseason_conditional_pa','preseason_pa','preseason_value','next_pa','next_value']).sort('row_id')
    assert f.select(old.columns).equals(old)
    assert len(f)==30506 and f['row_id'].n_unique()==len(f)
    # Recompute the whole-population summaries from saved per-person quantities.
    allnote=next(s for s in audit['summaries'] if s['scope']=='all')
    for arm in ['risk','binomial']:
        for key in ['crps','pinball','width','coverage']:
            value=np.mean([sum(g[arm+'_'+key])/len(g) for g in f.partition_by('target_year')])
            close(value,allnote['arms'][arm][key])
        for j in range(10):
            value=np.mean([sum(g[arm+'_pit'+str(j)])/len(g) for g in f.partition_by('target_year')])
            close(value,allnote['arms'][arm]['pit_bins_equal_year'][j])
    close(float(f['preseason_p'].sum()),allnote['expected_appearances'])
    assert int((f['next_pa']>0).sum())==allnote['actual_appearances']
    risk=ROOT/'reports/generated/hitter-workload-risk'
    fits=read(risk/'fit-report.json')
    concentrations={(n['year'],n['fold']):n['concentration']['concentration'] for n in fits['cells']}
    selected=set()
    for g in f.partition_by(['origin_year','outer_fold']):
        for r in [g.sort('row_id').row(0,named=True),g.sort('preseason_p',descending=True).row(0,named=True),
                  g.sort((pl.col('preseason_pa')-pl.col('next_pa')).abs(),descending=True).row(0,named=True)]:selected.add(r['row_id'])
    cases=read(PUB/'workload-cases.json.gz')
    selected.update(c['row']['row_id'] for c in cases)
    checked=0
    for r in f.filter(pl.col('row_id').is_in(selected)).to_dicts():
        p,c,y=r['preseason_p'],r['preseason_conditional_pa'],r['next_pa']
        for arm in ['risk','binomial']:
            mu=(c-1)/799;k=concentrations[r['origin_year'],r['outer_fold']]
            law=betabinom(799,mu*k,(1-mu)*k) if arm=='risk' and 1<c<800 else binom(799,mu)
            for a in [.05,.1,.2,.3,.4,.5,.6,.7,.8,.9,.95]:
                q=0 if a<=1-p else int(1+law.ppf((a-(1-p))/p))
                assert q==r[arm+'_q'+str(int(a*100))]
                expected=p if q==0 else p*law.sf(q-1)
                close(expected,r[arm+'_exceed_expected'+str(int(a*100))],1e-7)
            close(p*law.sf(398),r[arm+'_p400'],1e-7)
            pmf=np.r_[1-p,p*law.pmf(np.arange(800))]
            pmf/=pmf.sum()
            # Alternative CRPS identity, without the scorer's CDF expression.
            cdf=np.cumsum(pmf);support=np.arange(801)
            pair_half=sum(cdf[:-1]*(1-cdf[:-1]))
            close(float(sum(pmf*np.abs(support-y))-pair_half),r[arm+'_crps'],1e-7)
            checked+=1
    assert len(cases)==14 and audit['player_walkthrough_status']=='complete'
    original_cases=read(risk/'cases.json')
    om={c['origin']['row_id']:c for c in original_cases}
    for c in cases:
        source=om[c['row']['row_id']]
        assert c['source_history']==source['source_history'] and c['actual_inputs']==source['actual_inputs']
        assert c['saved_point_paths']==source['saved_point_paths'] and c['peers']==source['peers']
    native=pl.read_parquet(ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet').to_dicts()
    nm={(r['season'],r['player_id'],r['position']):r for r in native}
    position=read(PUB/'position-comparison.json.gz');pairs=pl.read_parquet(OUT/'position-pairs.parquet')
    refs={}
    for a in position['annual_references']:
        r=[s for s in native if s['season']==a['season'] and s['position']==a['position'] and s['range_valid']]
        close(1500*sum(s['range_runs'] for s in r)/sum(s['native_outs'] for s in r),a['rate'])
        refs[a['season'],a['position']]=a['rate']
    official=pl.read_parquet(ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet').filter(
        pl.col('is_mlb')&pl.col('season').is_between(2016,2025)&pl.col('position_code').is_in(['7','8','9'])).group_by(
        'season','player_id','position_code').agg(pl.col('fielding_outs').sum())
    og=defaultdict(dict)
    for r in official.to_dicts():og[r['season'],r['player_id']][int(r['position_code'])]=r['fielding_outs']
    eligibility=set();official_missing=[]
    for (y,pid),m in og.items():
        if m.get(8,0)<450 or m.get(7,0)+m.get(9,0)<450:continue
        keys=[(y,pid,p) for p,n in m.items() if n>0]
        if any(key not in nm or not nm[key]['range_valid'] or not nm[key]['exposure_valid'] for key in keys):
            official_missing.append((y,pid));continue
        cf=nm[y,pid,8];corners=[nm[y,pid,p] for p in (7,9) if m.get(p,0)>0]
        if cf['native_outs']>=450 and sum(r['native_outs'] for r in corners)>=450:eligibility.add((y,pid))
    assert eligibility==set(zip(pairs['season'],pairs['player_id']))
    for r in pairs.to_dicts():
        y,pid=r['season'],r['player_id'];cf=nm[y,pid,8]
        corners=[nm[y,pid,p] for p in [7,9] if og[y,pid].get(p,0)>0]
        runs=sum(s['range_runs'] for s in corners);outs=sum(s['native_outs'] for s in corners)
        ref=sum(refs[y,s['position']]*s['native_outs'] for s in corners)/outs
        close(runs,r['corner_runs']);assert outs==r['corner_outs']
        raw=1500*cf['range_runs']/cf['native_outs']-1500*runs/outs
        relative=raw-refs[y,8]+ref
        close(raw,r['raw_difference']);close(relative,r['relative_difference'])
        close(relative+10*500/1458,r['relative_plus_schedule'])
        close(-relative*1458/500,r['equalization_gap_per1458'])
        close(r['raw_plus_schedule'],r['relative_plus_transferred_schedule'])
    for col,value in position['summaries']['all']['person_balanced'].items():
        means=pairs.group_by('player_id').agg(pl.col(col).mean())[col]
        close(float(means.mean()),value)
    pcases=read(PUB/'position-cases.json.gz')
    for c in pcases:
        r=c['row'];assert c['native_source_rows']==[s for s in native if s['season']==r['season'] and s['player_id']==r['player_id']]
        for peer in c['peers']:
            s=peer['row'];assert peer['native_source_rows']==[n for n in native if n['season']==s['season'] and n['player_id']==s['player_id']]
    result=dict(workload_rows_verified=len(f),independent_scalar_distributions=checked,
        quantile_checks=checked*11,position_pairs_rebuilt=len(pairs),position_people=pairs['player_id'].n_unique(),
        official_eligible_missing_measurement=len(official_missing),full_source_case_walks=len(pcases),
        workload_cases_and_old_traces_verified=len(cases),protected_files_unchanged=True,
        statistical_scope='Exposed historical diagnostics; no forecast improvement or deployment approval',
        hashes={str(p):sha256_file(p) for p in [Path(__file__),*PUB.glob('*.gz'),*OUT.glob('*.parquet')]})
    with gzip.open(PUB/'independent-review.json.gz','wt',encoding='utf8') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    print(json.dumps({k:v for k,v in result.items() if k!='hashes'},indent=2))


if __name__=='__main__':main()
