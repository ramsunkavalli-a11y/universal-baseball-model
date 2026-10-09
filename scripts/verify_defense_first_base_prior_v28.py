"""Independent arithmetic and score replay, without the candidate functions."""
from collections import defaultdict
from pathlib import Path
import gzip
import json
import math
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
from source_defensive_positions_v2 import embedded
from audit_defense_component_bias_v27 import protected
from reconstruct_defense_value_v26 import reconstruct

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'reports/model-evidence/defense-first-base-prior-v28'


def read(n):
    with gzip.open(PUBLIC/(n+'.json.gz'),'rt',encoding='utf8') as f:return json.load(f)


def eq(a,b):
    if isinstance(a,dict):
        for k,v in a.items():eq(v,b[k])
    elif isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b):eq(x,y)
    elif isinstance(a,(int,float)) and not isinstance(a,bool):
        assert b is not None and math.isclose(a,b,abs_tol=1e-8,rel_tol=1e-10),(a,b)
    else:assert a==b,(a,b)


def quality(rows):
    rs=[r for r in rows if r['quality_rate'] is not None]
    if not rs:return None
    people={}
    for r in rs:people.setdefault(r['player_id'],[]).append(r)
    arms=['zero','history','calibrated','candidate'];loss=[];scores=[]
    for a in arms:
        errors=[[r[a]-r['quality_rate'] for r in g] for g in people.values()]
        scores.append(dict(arm=a,people=len(people),rows=len(rs),rmse=math.sqrt(sum(sum(x*x for x in e)/len(e) for e in errors)/len(errors)),
            mae=sum(sum(abs(x) for x in e)/len(e) for e in errors)/len(errors),bias=sum(sum(e)/len(e) for e in errors)/len(errors)))
        loss.append([sum(x*x for x in e)/len(e) for e in errors])
    matrix=np.array(loss).T;rng=np.random.default_rng(728028);differences=[]
    for _ in range(2000):
        counts=np.bincount(rng.integers(len(people),size=len(people)),minlength=len(people))
        roots=np.sqrt(counts@matrix/len(people));differences.append(roots[3]-roots[:3])
    return dict(scores=scores,intervals=[dict(left='candidate',right=a,difference=scores[3]['rmse']-scores[i]['rmse'],
        interval_95=np.quantile(np.array(differences)[:,i],[.025,.975]).tolist(),draws=2000,seed=728028) for i,a in enumerate(arms[:3])])


def delivery(rows,fields,target):
    result=[]
    for y in sorted({r['origin_year'] for r in rows}):
        rs=[r for r in rows if r['origin_year']==y and r[target] is not None]
        if not rs:continue
        for f in fields:
            e=np.array([r[f]-r[target] for r in rs])
            result.append(dict(origin=y,arm=f,rows=len(rs),rmse=float(np.sqrt((e*e).mean())),mae=float(abs(e).mean()),bias=float(e.mean()),
                actual_total=sum(r[target] for r in rs),predicted_total=sum(r[f] for r in rs)))
    equal=[]
    for f in fields:
        rs=[r for r in result if r['arm']==f]
        if rs:equal.append(dict(arm=f,origins=len(rs),mean_origin_rmse=np.mean([r['rmse'] for r in rs]),
            mean_origin_mae=np.mean([r['mae'] for r in rs]),mean_origin_bias=np.mean([r['bias'] for r in rs])))
    return dict(per_origin=result,equal_origin=equal)


def interval(rows,left,right,target):
    rs=[r for r in rows if r[target] is not None]
    ids=sorted({r['player_id'] for r in rs});years=sorted({r['origin_year'] for r in rs})
    pi={p:i for i,p in enumerate(ids)};yi={y:i for i,y in enumerate(years)}
    sums=np.zeros((len(ids),len(years),2));n=np.zeros((len(ids),len(years)))
    for r in rs:
        i,j=pi[r['player_id']],yi[r['origin_year']];assert n[i,j]==0;n[i,j]=1
        sums[i,j]=[(r[left]-r[target])**2,(r[right]-r[target])**2]
    rng=np.random.default_rng(728028);ds=[]
    for _ in range(2000):
        counts=np.bincount(rng.integers(len(ids),size=len(ids)),minlength=len(ids))
        roots=np.sqrt(np.einsum('i,ijk->jk',counts,sums)/(counts@n)[:,None]).mean(axis=0)
        ds.append(float(roots[0]-roots[1]))
    roots=np.sqrt(sums.sum(axis=0)/n.sum(axis=0)[:,None]).mean(axis=0)
    return dict(mean_origin_RMSE_difference=float(roots[0]-roots[1]),interval_95=np.quantile(ds,[.025,.975]).tolist())


def main():
    assert not (PUBLIC/'independent-review.json.gz').exists();pre=read('preflight');eq(protected(),pre['protected_hashes'])
    for p,h in pre['hashes'].items():assert sha256_file(Path(p))==h,p
    native=pl.read_parquet(ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet').filter(pl.col('position')==3).to_dicts()
    rawhash={};rawcount=0
    for y in range(2016,2026):
        path=ROOT/f'reports/generated/defensive-talent-position-v2/position-{y}.response'
        raw={(r['id'],r['pos_id']):r for r in embedded(path.read_text(encoding='utf8'),'data')}
        rawhash[str(path)]=sha256_file(path)
        for r in native:
            if r['season']==y:
                s=raw[r['player_id'],3];eq(s['range_runs'],r['range_runs']);eq(s['outs_total'],r['native_outs']);rawcount+=1
    refs={}
    for r in pre['references']:
        y,f=r['origin'],r['excluded_fold'];ss=[s for s in native if s['range_valid'] and y-2<=s['season']<=y and s['player_id']%5!=f]
        people=len({s['player_id'] for s in ss});seasons=len({s['season'] for s in ss})
        n=sum(s['native_outs']/(2**(y-s['season'])) for s in ss);v=sum(s['range_runs']/(2**(y-s['season'])) for s in ss)
        supported=people>=20 and seasons>=2 and n>0
        eq(dict(people=people,seasons=seasons,outs=n,runs=v,supported=supported,fallback=not supported,rate=1500*v/n if supported else 0),r)
        refs[y,f]=r['rate']
    official=defaultdict(int)
    for r in pl.read_parquet(ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet',columns=['is_mlb','position_code','season','player_id','fielding_outs']).iter_rows(named=True):
        if r['is_mlb'] and r['position_code']=='3':official[r['season'],r['player_id']]+=r['fielding_outs']
    by=defaultdict(list)
    for r in native:by[r['player_id']].append(r)
    source=pl.read_parquet(ROOT/'reports/generated/defense-native-range-v3/predictions.parquet').filter(pl.col('position')==3).to_dicts()
    q=read('quality-predictions')['rows'];assert len(q)==len(source)
    for r,s in zip(q,source):
        eq(s,r);y,p=r['origin_year'],r['player_id']
        hist=[s for s in by[p] if y-2<=s['season']<=y and s['range_valid']]
        n=sum(s['native_outs']*2**(s['season']-y) for s in hist);v=sum(s['range_runs']*2**(s['season']-y) for s in hist)
        eq((1500*v+3000*refs[y,p%5])/(n+3000),r['candidate']);eq(1500*v/(n+3000),r['history'])
        future=[s for s in by[p] if y<s['season']<=min(y+3,2025) and s['range_valid']]
        fn=sum(s['native_outs'] for s in future);fr=sum(s['range_runs'] for s in future)
        missing=sum(official[z,p] for z in range(y+1,min(y+3,2025)+1) if z not in {s['season'] for s in future})
        valid=y+3<=2025 and fn>=1500 and len(future)>=2 and missing==0
        eq(1500*fr/fn if valid else None,r['quality_rate'])
    baseline,recovery=reconstruct();eq(recovery,pre['reconstruction'])
    values=read('value-predictions')['rows'];assert len(values)==len(baseline)==12432
    columns=['row_id','player_id','origin_year','history_rate','history_opportunities','repair_predicted_opportunities','repair_history','actual_runs','actual_official_exposure','actual_native_opportunities']
    channels=pl.read_parquet(ROOT/'reports/generated/defense-value-v12/channel-predictions.parquet',columns=['channel',*columns]).filter(pl.col('channel')=='range_3').to_dicts()
    cb={r['row_id']:r for r in channels}
    for r,s in zip(values,baseline):
        eq(s,r);c=cb[r['row_id']];y,p=c['origin_year'],c['player_id']
        hist=[s for s in by[p] if y-2<=s['season']<=y and s['range_valid']]
        n=sum(s['native_outs']*2**(s['season']-y) for s in hist);v=sum(s['range_runs']*2**(s['season']-y) for s in hist)
        rate=(1500*v+3000*refs[y,p%5])/(n+3000);runs=rate*c['repair_predicted_opportunities']/1500
        eq(runs,r['candidate_1b']);eq(c['repair_history'],r['history_1b']);eq(c['actual_runs'],r['actual_1b'])
        delta=runs-c['repair_history'];eq(s['centered_defense']+delta,r['candidate_defense']);eq(s['centered_expanded']+delta/10,r['candidate_expanded'])
        eq(r['candidate_expanded'],r['batting_forecast']+(r['position_runs']+r['candidate_defense'])/10)
        actual_n=0 if c['actual_official_exposure']==0 else c['actual_native_opportunities']
        eq(None if actual_n is None else actual_n*rate/1500,r['candidate_1b_oracle'])
    report=read('report');eq(quality([r for r in q if r['origin_year']==2022]),report['primary'])
    for g in report['quality_groups']:
        rs=[r for r in q if r['origin_year']==g['origin']]
        if g['scope']!='all':rs=[r for r in rs if r[g['scope']]==g['group']]
        eq(quality(rs),g['result'])
    for target,left,right,truth in [('first_base','candidate_1b','history_1b','actual_1b'),('defense','candidate_defense','centered_defense','actual_defense'),('expanded','candidate_expanded','centered_expanded','actual_expanded')]:
        eq(delivery(values,[right,left],truth),report['value'][target]);eq(interval(values,left,right,truth),report['value'][target]['interval'])
    for g in report['stage']:
        rs=[r for r in values if r['stage']==g['stage']]
        eq(delivery(rs,['centered_defense','candidate_defense'],'actual_defense'),g['defense'])
        eq(delivery(rs,['centered_expanded','candidate_expanded'],'actual_expanded'),g['expanded'])
    defenders=[r for r in values if r['actual_1b_official']>0]
    eq(delivery(defenders,['history_1b','candidate_1b','history_1b_oracle','candidate_1b_oracle'],'actual_1b'),report['first_base_defenders'])
    walks=read('player-walks')['groups'];vb={r['row_id']:r for r in values};qby={(r['origin_year'],r['player_id']):r for r in q}
    bs=pl.read_parquet(ROOT/'reports/generated/defense-transition-v10/predictions.parquet',columns=['row_id','player_id','origin_year','stage','age','repertoire_primary_role','role_defensive_sample']).to_dicts()
    bby={(r['origin_year'],r['player_id']):r for r in bs}
    for g in walks:
        s=g['selection'];b=bby[s['origin'],s['player_id']]
        pool=[r for r in bs if r['origin_year']==b['origin_year'] and r['stage']==b['stage'] and r['repertoire_primary_role']==b['repertoire_primary_role'] and r['player_id']!=b['player_id']]
        peers=sorted(pool,key=lambda r:(abs((r['age'] if r['age'] is not None else 27)-(b['age'] if b['age'] is not None else 27)),abs(r['role_defensive_sample']-b['role_defensive_sample']),r['row_id']))[:3]
        assert [r['player_id'] for r in g['records']]==[r['player_id'] for r in [b,*peers]]
        for w in g['records']:
            y,p=w['origin'],w['player_id'];bb=bby[y,p];c=cb[bb['row_id']]
            eq(vb[bb['row_id']],w['value']);eq(qby.get((y,p)),w['quality'])
            eq([s for s in by[p] if y-2<=s['season']<=y],w['history'])
            eq([s for s in by[p] if y<s['season']<=min(y+3,2025)],w['future_measurements'])
            eq(refs[y,p%5],w['empirical_prior']['rate']);eq(c,w['first_base'])
            eq(w['value']['candidate_1b'],w['first_base']['candidate_runs'])
            eq(w['first_base']['candidate_rate']*c['repair_predicted_opportunities']/1500,w['value']['candidate_1b'])
    # Replay deterministic outcome-based selections as diagnostics, not confirmation.
    rs=[r for r in q if r['origin_year']==2022 and r['quality_rate'] is not None]
    gain=lambda r:(r['candidate']-r['quality_rate'])**2-(r['history']-r['quality_rate'])**2
    selected=dict(largest_gain=min(rs,key=gain),largest_deterioration=max(rs,key=gain),
                  false_high=max(rs,key=lambda r:r['candidate']-r['quality_rate']),false_low=min(rs,key=lambda r:r['candidate']-r['quality_rate']),
                  median_error=sorted(rs,key=lambda r:(abs(r['candidate']-r['quality_rate']),r['player_id']))[len(rs)//2])
    for g in walks:
        if g['selection']['kind'] in selected:assert g['selection']['player_id']==selected[g['selection']['kind']]['player_id']
    eq(protected(),pre['protected_hashes'])
    paths=[Path(__file__),*[PUBLIC/(x+'.json.gz') for x in ('preflight','report','quality-predictions','value-predictions','player-walks')]]
    note=dict(execution_integrity_pass=True,quality_rows_replayed=len(q),value_rows_replayed=len(values),raw_native_rows_replayed=rawcount,
        references_replayed=len(refs),all_scores_intervals_and_selections_replayed=True,player_records_replayed=sum(len(g['records']) for g in walks),
        origin_only_peers_replayed=True,forecast_explorer_unchanged=True,no_2026_access=True,
        hashes={str(p):sha256_file(p) for p in paths},raw_source_hashes=rawhash)
    with gzip.open(PUBLIC/'independent-review.json.gz','wt',encoding='utf8') as f:json.dump(note,f,allow_nan=False,separators=(',',':'))
    print({k:v for k,v in note.items() if 'hash' not in k})


if __name__=='__main__':main()
