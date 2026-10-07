"""Independent reference, eligibility, rates, value, scores and player arithmetic."""
from collections import defaultdict,Counter
from pathlib import Path
import gzip
import json
import math
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
from verify_double_play_support_v22 import write
from run_hitter_finite_return_baseline import protections

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/defense-reference-history-v26'
PUBLIC=ROOT/'reports/model-evidence/defense-reference-history-v26'
NATIVE=ROOT/'reports/generated/defense-native-range-v3'
V12=ROOT/'reports/generated/defense-value-v12'
ARMS=('legacy','centered','neutral')


def read(p):
    with (gzip.open(p,'rt',encoding='utf8') if p.suffix=='.gz' else p.open(encoding='utf8')) as f:return json.load(f)


def eq(a,b):
    assert (a is None and b is None) or (a is not None and b is not None and abs(float(a)-float(b))<1e-8),(a,b)


def check_scores(rows,report,target,fields):
    origins=sorted({r['origin_year'] for r in rows});computed=[]
    for y in origins:
        rs=[r for r in rows if r['origin_year']==y and r[target] is not None]
        if not rs:continue
        actual=np.array([r[target] for r in rs])
        for a in fields:
            predicted=np.array([r[a] for r in rs]);error=predicted-actual
            c=dict(origin=y,arm=a,rows=len(rs),rmse=np.sqrt(np.mean(error**2)),mae=np.mean(abs(error)),bias=np.mean(error),actual_total=sum(actual),predicted_total=sum(predicted))
            old=next(s for s in report['per_origin'] if s['origin']==y and s['arm']==a)
            for k,v in c.items():
                if isinstance(v,str):assert v==old[k]
                else:eq(v,old[k])
            computed.append(c)
    for s in report['equal_origin']:
        parts=[c for c in computed if c['arm']==s['arm']]
        for k in ('rmse','mae','bias'):eq(s['mean_origin_'+k],np.mean([c[k] for c in parts]))
    for s in report.get('intervals',[]):
        valid=[r for r in rows if r[target] is not None];ids=sorted({r['player_id'] for r in valid});ys=sorted({r['origin_year'] for r in valid})
        ix={p:i for i,p in enumerate(ids)};yi={y:i for i,y in enumerate(ys)}
        counts=np.zeros((len(ids),len(ys)));loss=np.zeros((len(ids),len(ys),2))
        for r in valid:
            i,j=ix[r['player_id']],yi[r['origin_year']];assert counts[i,j]==0;counts[i,j]=1
            loss[i,j]=[(r[s[k]]-r[target])**2 for k in ('left','right')]
        rng=np.random.default_rng(s['seed']);draws=[]
        base=np.sqrt(loss.sum(axis=0)/counts.sum(axis=0)[:,None]).mean(axis=0)
        for _ in range(s['draws']):
            pick=rng.integers(len(ids),size=len(ids));root=np.sqrt(loss[pick].sum(axis=0)/counts[pick].sum(axis=0)[:,None]).mean(axis=0)
            draws.append(root[0]-root[1])
        eq(s['mean_origin_RMSE_difference'],base[0]-base[1])
        for a,b in zip(s['interval_95'],np.quantile(draws,[.025,.975])):eq(a,b)


def check_quality(rows,report):
    valid=[r for r in rows if r['quality_rate'] is not None]
    if not valid:assert report is None;return
    g=defaultdict(list)
    for r in valid:g[r['player_id']].append(r)
    for score in report['scores']:
        a=score['arm'];mse=[];mae=[];bias=[]
        for rs in g.values():
            error=np.array([r[a]-r['quality_rate'] for r in rs]);mse.append(np.mean(error**2));mae.append(np.mean(abs(error)));bias.append(np.mean(error))
        eq(score['rmse'],np.sqrt(np.mean(mse)));eq(score['mae'],np.mean(mae));eq(score['bias'],np.mean(bias))
        assert score['people']==len(g) and score['rows']==len(valid)
    for s in report['intervals']:
        losses=np.array([[np.mean([(r[a]-r['quality_rate'])**2 for r in rs]) for a in (s['left'],s['right'])] for rs in g.values()])
        rng=np.random.default_rng(s['seed']);changes=[]
        for _ in range(s['draws']):
            sample=losses[rng.integers(len(losses),size=len(losses))];roots=np.sqrt(sample.mean(axis=0));changes.append(roots[0]-roots[1])
        eq(s['difference'],np.sqrt(losses.mean(axis=0))[0]-np.sqrt(losses.mean(axis=0))[1])
        for a,b in zip(s['interval_95'],np.quantile(changes,[.025,.975])):eq(a,b)


def main():
    protections();assert not (PUBLIC/'independent-review.json.gz').exists()
    pre=read(PUBLIC/'preflight.json.gz');report=read(PUBLIC/'report.json.gz');walks=read(PUBLIC/'player-walks.json.gz')
    for note in (pre,report,walks):
        for p,h in {**note['hashes'],**note.get('output_hashes',{})}.items():assert sha256_file(Path(p))==h,p
    native=pl.read_parquet(NATIVE/'component-ledger.parquet').to_dicts();people=defaultdict(list)
    for r in native:people[r['player_id']].append(r)
    ref={};real={}
    for y in range(2016,2026):
        for p in (7,8,9):
            rows=[r for r in native if r['season']==y and r['position']==p and r['range_valid']]
            real[y,p]=1500*sum(r['range_runs'] for r in rows)/sum(r['native_outs'] for r in rows)
            for fold in range(5):
                subset=[r for r in rows if r['player_id']%5!=fold]
                n=sum(r['native_outs'] for r in subset);v=sum(r['range_runs'] for r in subset)
                ref[y,p,fold]=(v,n,1500*v/n,len({r['player_id'] for r in subset}))
    for c in pre['annual_held_references']:
        v,n,rate,count=ref[c['season'],c['position'],c['fold']]
        eq(c['runs'],v);eq(c['outs'],n);eq(c['rate'],rate);assert c['people']==count
    for c in pre['realized_target_references']:eq(c['rate'],real[c['season'],c['position']])
    official=defaultdict(int)
    for r in pl.read_parquet(ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet').to_dicts():
        if r['is_mlb'] and r['position_code'].isdigit():official[r['season'],r['player_id'],int(r['position_code'])]+=r['fielding_outs']
    def hist(pid,y,p):
        rows=[r for r in people[pid] if y-2<=r['season']<=y and r['position']==p and r['range_valid']]
        n=sum(r['native_outs']/2**(y-r['season']) for r in rows)
        raw=sum(r['range_runs']/2**(y-r['season']) for r in rows)
        centered=sum((r['range_runs']-(ref[r['season'],p,pid%5][2]*r['native_outs']/1500 if p in (7,8,9) else 0))/2**(y-r['season']) for r in rows)
        valid_refs=[(year,ref[year,p,pid%5]) for year in range(y-2,y+1) if (year,p,pid%5) in ref] if p in (7,8,9) else []
        center=1500*sum(v[0]/2**(y-year) for year,v in valid_refs)/sum(v[1]/2**(y-year) for year,v in valid_refs) if valid_refs else 0.
        return n,raw,centered,center,rows
    q=pl.read_parquet(OUT/'quality-predictions.parquet').to_dicts();oldq=pl.read_parquet(NATIVE/'predictions.parquet').to_dicts()
    assert [(r['origin_year'],r['player_id'],r['position']) for r in q]==[(r['origin_year'],r['player_id'],r['position']) for r in oldq]
    for r,old in zip(q,oldq):
        y,pid,p=r['origin_year'],r['player_id'],r['position'];n,raw,centered,center,rows=hist(pid,y,p)
        eq(n,r['history_outs']);eq(raw,r['history_raw_runs']);eq(centered,r['history_relative_runs']);eq(center,r['origin_reference'])
        eq(r['legacy'],1500*raw/(n+3000)-center);eq(r['centered'],1500*centered/(n+3000));eq(r['centered_intrinsic'],r['centered']+center)
        eq(r['reliability'],n/(n+3000));assert r['talent_known']==(n>0) and sum(s['native_outs'] for s in rows)>=25
        future=[s for s in people[pid] if y<s['season']<=min(y+3,2025) and s['position']==p and s['range_valid']]
        fn=sum(s['native_outs'] for s in future);fv=sum(s['range_runs'] for s in future)
        missing=sum(official[year,pid,p] for year in range(y+1,min(y+3,2025)+1) if not any(s['season']==year for s in future))
        is_valid=y+3<=2025 and fn>=1500 and len(future)>=2 and missing==0
        eq(fn,r['future_outs']);eq(fv,r['future_raw_runs']);eq(missing,r['future_missing_outs'])
        target_runs=sum(s['range_runs']-(real[s['season'],p]*s['native_outs']/1500 if p in (7,8,9) else 0) for s in future)
        eq(target_runs,r['future_relative_runs']);eq(r['quality_rate'],1500*target_runs/fn if is_valid else None)
        assert is_valid==(old['quality_rate'] is not None) and old['quality_status']==r['quality_status']
    for c in pre['mature_profile_support']:
        tr=[r for r in q if r['quality_rate'] is not None and r['window_end']<=c['origin'] and r['player_id']%5!=c['fold'] and
            (r['position'],r['age_band'],r['sample_band'])==(c['position'],c['age'],c['sample'])]
        te=[r for r in q if r['origin_year']==c['origin'] and r['fold']==c['fold'] and (r['position'],r['age_band'],r['sample_band'])==(c['position'],c['age'],c['sample'])]
        assert c['mature_training_people']==len({r['player_id'] for r in tr}) and c['eligible_test_people']==len({r['player_id'] for r in te})
    for cell in pre['coverage']:
        rs=[r for r in q if tuple(r[k] for k in ('origin_year','position','age_band','sample_band','quality_status'))==tuple(cell[k] for k in ('origin_year','position','age_band','sample_band','quality_status'))]
        assert len(rs)==cell['rows'] and len({r['player_id'] for r in rs})==cell['people']
    f=pl.read_parquet(OUT/'value-predictions.parquet').to_dicts();oldf={r['row_id']:r for r in pl.read_parquet(V12/'predictions.parquet').to_dicts()}
    bridge={r['row_id']:r for r in pl.read_parquet(ROOT/'reports/generated/defense-transition-v10/predictions.parquet').to_dicts()}
    oldcells=defaultdict(list)
    for c in pl.read_parquet(V12/'channel-predictions.parquet').to_dicts():oldcells[c['row_id']].append(c)
    newcells=defaultdict(list)
    for c in pl.read_parquet(OUT/'OF-predictions.parquet').to_dicts():newcells[c['row_id']].append(c)
    assert {r['row_id'] for r in f}==set(oldf) and len(f)==12432
    for r in f:
        old=oldf[r['row_id']];b=bridge[r['row_id']];cs=newcells[r['row_id']];y=r['origin_year'];pid=r['player_id']
        outside=sum(c['repair_history'] for c in oldcells[r['row_id']] if c['channel'] not in ('range_7','range_8','range_9'))
        eq(outside,r['non_OF_history_runs']);eq(old['batting_forecast'],r['batting_forecast']);eq(old['repair_position_runs'],r['position_runs'])
        eq(old['actual_position_runs'],r['actual_position_runs']);eq(old['actual_batting'],r['actual_batting']);eq(b['preseason_pa'],r['expected_PA'])
        for c in cs:
            p=c['position'];n,raw,centered,center,past=hist(pid,y,p);den=b[f'repair_{p}']
            eq(c['history_outs'],n);eq(c['history_raw_runs'],raw);eq(c['history_relative_runs'],centered)
            eq(c['legacy_rate'],1500*raw/(n+3000)-center);eq(c['centered_rate'],1500*centered/(n+3000));eq(c['origin_reference'],center)
            eq(c['projected_outs'],den);eq(c['legacy_runs'],den*c['legacy_rate']/1500);eq(c['centered_runs'],den*c['centered_rate']/1500)
            assert c['talent_known']==(n>0)
            oc=next(s for s in oldcells[r['row_id']] if s['channel']=='range_'+str(p));eq(c['actual_raw_runs'],oc['actual_runs'])
            s=next((s for s in people[pid] if s['season']==y+1 and s['position']==p),None)
            aoff=0. if oc['actual_official_exposure']==0 else None if oc['actual_runs'] is None else real[y+1,p]*s['native_outs']/1500
            eq(aoff,c['actual_reference_offset']);eq(c['actual_relative_runs'],None if aoff is None else oc['actual_runs']-aoff)
        for a in ARMS:
            defense=outside+sum(c[a+'_runs'] for c in cs);eq(defense,r[a+'_defense']);eq(r['batting_forecast']+(defense+r['position_runs'])/10,r[a+'_expanded'])
        offsets=[c['actual_reference_offset'] for c in cs]
        target=None if old['actual_defense'] is None else old['actual_defense']-sum(offsets)
        eq(target,r['actual_defense']);eq(None if target is None else r['actual_batting']+(target+r['actual_position_runs'])/10,r['actual_expanded'])
    for c in report['quality']:
        rows=[r for r in q if r['origin_year']==c['origin']]
        if c['family']=='OF':rows=[r for r in rows if r['position'] in (7,8,9)]
        elif c['family']!='all_positions':rows=[r for r in rows if r['position'] in (7,8,9) and r[c['family']]==c['group']]
        check_quality(rows,c['result'])
    for target in ('defense','expanded'):check_scores(f,report['value'][target],'actual_'+target,[a+'_'+target for a in ARMS])
    for group in report['stage_groups']:
        rows=[r for r in f if r['stage']==group['stage']]
        for target in ('defense','expanded'):check_scores(rows,group[target],'actual_'+target,[a+'_'+target for a in ARMS])
    check_scores([r for r in f if r['actual_fielding_outs']>0],report['actual_defenders']['defense'],'actual_defense',[a+'_defense' for a in ARMS])
    qm={(r['origin_year'],r['player_id'],r['position']):r for r in q};fm={(r['origin_year'],r['player_id']):r for r in f}
    for group in walks['groups']:
        selection=group['selection'];y=selection['origin'];focal=selection['player_id'];assert [r['player_id'] for r in group['records']]==[focal,*selection['peer_ids']]
        if selection['kind']=='quality':
            p=selection['position'];r=qm[y,focal,p]
            pool=[s for s in q if s['origin_year']==y and s['position']==p and s['player_id']!=focal]
            pool.sort(key=lambda s:(s['age'] is None or r['age'] is None,abs(s['age']-r['age']) if s['age'] is not None and r['age'] is not None else 0,abs(s['history_outs']-r['history_outs']),s['player_id']))
            assert selection['peer_ids']==[s['player_id'] for s in pool[:3]]
        elif selection['kind']=='value':
            b=bridge[fm[y,focal]['row_id']]
            pool=[s for s in bridge.values() if s['origin_year']==y and s['stage']==b['stage'] and s['repertoire_primary_role']==b['repertoire_primary_role'] and s['player_id']!=focal]
            pool.sort(key=lambda s:(abs((s['age'] if s['age'] is not None else 27)-(b['age'] if b['age'] is not None else 27)),abs(s['role_defensive_sample']-b['role_defensive_sample']),s['row_id']))
            assert selection['peer_ids']==[s['player_id'] for s in pool[:3]]
        else:
            oldwalk=read(ROOT/'reports/model-evidence/defense-reference-v25/fold-repair/player-walks.json.gz')
            source=next(s for s in oldwalk['cases'] if s['focal_player_id']==focal)
            assert selection['peer_ids']==[r['forecast']['player_id'] for r in source['records'][1:]]
        for rec in group['records']:
            pid=rec['player_id'];assert rec['value_prediction']==fm.get((y,pid))
            for r in rec['quality_predictions']:assert r==qm[y,pid,r['position']]
            for ps,h in rec['history_arithmetic'].items():
                p=int(ps);n,raw,centered,center,past=hist(pid,y,p)
                eq(h['history_outs'],n);eq(h['weighted_raw_runs'],raw);eq(h['weighted_relative_runs'],centered)
                eq(h['centered'],1500*centered/(n+3000));assert h['talent_known']==(n>0)
                assert len(h['history_sources'])==len(past)
                for s in h['history_sources']:
                    rawrow=next(r for r in past if r['season']==s['season']);eq(s['raw_runs'],rawrow['range_runs']);eq(s['native_outs'],rawrow['native_outs'])
                    sr=ref[s['season'],p,pid%5][2] if p in (7,8,9) else 0.;eq(sr,s['reference_rate']);eq(s['relative_runs'],s['raw_runs']-sr*s['native_outs']/1500)
            for year in rec['annual_positions']:
                for s in year['positions']:assert s['official_outs']==official[year['season'],pid,s['position']]
            for p,h in rec['source_hashes'].items():assert sha256_file(Path(p))==h,p
    # Independently reselect all declared outcome diagnostics; fixed peers above.
    primary=[r for r in q if r['origin_year']==2022 and r['position'] in (7,8,9) and r['quality_rate'] is not None]
    delta=lambda r:((r['centered']-r['quality_rate'])**2-(r['legacy']-r['quality_rate'])**2,r['player_id'],r['position'])
    picks={'quality_largest_gain':min(primary,key=delta),'quality_largest_loss':max(primary,key=delta),
        'quality_false_high':max(primary,key=lambda r:(r['centered']-r['quality_rate'],-r['player_id'],-r['position'])),
        'quality_false_low':min(primary,key=lambda r:(r['centered']-r['quality_rate'],r['player_id'],r['position']))}
    median=np.median([abs(r['centered']-r['quality_rate']) for r in primary]);picks['quality_ordinary']=min(primary,key=lambda r:(abs(abs(r['centered']-r['quality_rate'])-median),r['player_id'],r['position']))
    for cat,r in picks.items():assert any(cat in g['selection']['categories'] and (g['selection']['origin'],g['selection']['player_id'],g['selection']['position'])==(r['origin_year'],r['player_id'],r['position']) for g in walks['groups'])
    complete=[r for r in f if r['actual_defense'] is not None]
    for metric in ('defense','expanded'):
        delta=lambda r:((r['centered_'+metric]-r['actual_'+metric])**2-(r['legacy_'+metric]-r['actual_'+metric])**2,r['row_id'])
        for cat,r in [('gain',min(complete,key=delta)),('loss',max(complete,key=delta))]:
            assert any(metric+'_largest_'+cat in g['selection']['categories'] and (g['selection']['origin'],g['selection']['player_id'])==(r['origin_year'],r['player_id']) for g in walks['groups'])
    paths=[Path(__file__),PUBLIC/'preflight.json.gz',PUBLIC/'report.json.gz',PUBLIC/'player-walks.json.gz']
    write(PUBLIC/'independent-review.json.gz',dict(model_fits=0,execution_integrity_pass=True,
        quality_predictions_replayed=len(q),value_predictions_replayed=len(f),OF_channels_replayed=sum(map(len,newcells.values())),
        all_reference_means_replayed=True,mature_support_and_coverage_replayed=True,all_scores_and_intervals_replayed=True,
        player_groups_replayed=len(walks['groups']),player_records_replayed=sum(len(g['records']) for g in walks['groups']),
        selections_and_origin_only_peers_replayed=True,main_baseball_review_pending=True,
        hashes={str(p):sha256_file(p) for p in paths}))
    protections();print('All reference/history/eligibility/value/score/bootstrap and selected-player arithmetic replayed.',flush=True)


if __name__=='__main__':main()
