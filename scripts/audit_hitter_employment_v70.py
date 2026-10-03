"""Cutoff transaction employment states and existing-model baseball diagnosis."""
from datetime import date
from pathlib import Path
import json
import sys
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file
from universal_baseball.practical_hitter_v30 import score
from evaluate_hitter_readiness_v49 import logit_trace
from score_hitter_readiness_v49 import probability_score
import evaluate_hitter_preseason_readiness_v68 as prior

ROOT=prior.ROOT;OUT=ROOT/'reports/generated/hitter-employment-v70'
FIXED=[(664056,2023),(547180,2018),(502110,2017),(446308,2016),(598265,2022),(474832,2022),(474832,2023),(475582,2021),(518626,2023)]


def write(n,o):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/n).write_text(json.dumps(o,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n',encoding='utf8')


def event(r):
    desc=r.get('description','').lower();kind=r.get('typeDesc','').lower()
    if kind=='declared free agency' or ' elected free agency' in desc or ' became a free agent' in desc:
        status='free_agent'
    elif kind in ['signed as free agent','trade','traded','claimed off waivers','assigned']:
        status='attached'
    else:return None
    dates=[date.fromisoformat(r[n][:10]) for n in ['date','effectiveDate','resolutionDate'] if r.get(n)]
    if not dates:raise ValueError('Employment record lacks a date')
    return dict(transaction_id=r['id'],player_id=r['person']['id'],available_date=max(dates).isoformat(),
        recorded_date=r.get('date'),effective_date=r.get('effectiveDate'),resolution_date=r.get('resolutionDate'),
        status=status,type_code=r.get('typeCode'),type_description=r.get('typeDesc'),description=r.get('description'))


def state(records,year):
    valid=[r for r in records if r['available_date']<=f'{year}-12-31']
    if not valid:return dict(recorded_open_fa=-1,latest_employment_date=None,latest_events=[])
    latest=max(r['available_date'] for r in valid);last=[r for r in valid if r['available_date']==latest]
    statuses={r['status'] for r in last}
    return dict(recorded_open_fa=(1 if statuses=={'free_agent'} else 0 if statuses=={'attached'} else -1),latest_employment_date=latest,latest_events=last)


def main():
    assert not (OUT/'audit.json').exists(),'Preserve source audit'
    OUT.mkdir(parents=True,exist_ok=True)
    assert prior.read(ROOT/'reports/generated/hitter-graduation-v69/report.json')['player_walkthrough_status']=='complete'
    frame=pl.read_parquet(prior.OUT/'features.parquet');q=pl.read_parquet(prior.OUT/'scored-predictions.parquet');pre=prior.read(prior.OUT/'preflight.json')
    paths=[];lookup={};capture_counts={}
    for year in range(2015,2025):
        folder='source-2015' if year==2015 else 'source';path=ROOT/f'reports/generated/hitter-injury-history-v2/{folder}/captures/transactions-{year}.json'
        paths.append(path);raw=prior.read(path)['transactions'];capture_counts[year]=len(raw)
        for r in raw:
            if not r.get('person',{}).get('id'):continue
            e=event(r)
            if e:lookup.setdefault(e['player_id'],{})[e['transaction_id']]=e
    lookup={pid:list(rs.values()) for pid,rs in lookup.items()};rows=[];details={}
    for r in frame.select('row_id','player_id','origin_year','on_40man').iter_rows(named=True):
        s=state(lookup.get(r['player_id'],[]),r['origin_year']) if r['origin_year']>=2015 else dict(recorded_open_fa=-1,latest_employment_date=None,latest_events=[])
        rows.append(dict(row_id=r['row_id'],employment_capture_scope=int(r['origin_year']>=2015),recorded_open_fa=s['recorded_open_fa'],
            fa_roster_conflict=int(s['recorded_open_fa']==1 and r['on_40man']==1)))
        if (r['player_id'],r['origin_year']) in FIXED:
            details[r['row_id']]=s|dict(all_known_employment_events=sorted([e for e in lookup.get(r['player_id'],[]) if e['available_date']<=f"{r['origin_year']}-12-31"],key=lambda e:e['available_date']))
            future=dict(transaction_id=-1,player_id=r['player_id'],available_date=f"{r['origin_year']+1}-01-01",status='attached')
            assert state(lookup.get(r['player_id'],[])+[future],r['origin_year'])==s
    statuses=pl.DataFrame(rows);f=frame.join(statuses,on='row_id',validate='1:1');q=q.join(statuses,on='row_id',validate='1:1')
    assert f.select(frame.columns).equals(frame) and len(q)==30506
    f.write_parquet(OUT/'features.parquet');q.write_parquet(OUT/'diagnostic-forecasts.parquet');support=[]
    for c in pre['cells']:
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']))
        exposed=tr.filter((pl.col('recorded_open_fa')==1)&(pl.col('on_40man')==0)&(pl.col('pa_0')>0))
        support.append(dict(year=c['year'],fold=c['fold'],participation_people=exposed['player_id'].n_unique(),
            active_people=exposed.filter(pl.col('next_pa')>0)['player_id'].n_unique(),zero_people=exposed.filter(pl.col('next_pa')==0)['player_id'].n_unique(),
            source_origins=sorted(exposed['origin_year'].unique().to_list())))
    current=q.filter(pl.col('pa_0')>0)
    groups=[('current_MLB',current),('documented_FA_unlisted',current.filter((pl.col('on_40man')==0)&(pl.col('recorded_open_fa')==1))),
        ('other_current_unlisted',current.filter((pl.col('on_40man')==0)&(pl.col('recorded_open_fa')!=1))),('current_listed',current.filter(pl.col('on_40man')==1))]
    fa=groups[1][1]
    groups += [('FA_origin_'+str(y),fa.filter(pl.col('origin_year')==y)) for y in sorted(fa['origin_year'].unique())]
    groups += [('FA_PA_'+label,fa.filter(expr)) for label,expr in [('1_199',pl.col('pa_0')<200),('200_399',pl.col('pa_0').is_between(200,399)),('400_plus',pl.col('pa_0')>=400)]]
    scores=[dict(scope=n,rows=len(g),people=g['player_id'].n_unique(),actual_pa=int(g['next_pa'].sum()),actual_offense=float(g['next_value'].sum()),
        existing=score(g,'preseason'),probability=probability_score(g,'preseason')) for n,g in groups if len(g)]
    counts=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet');cases=[]
    with threadpool_limits(limits=2):
        for pid,y in FIXED:
            r=q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)).row(0,named=True);row=f.filter(pl.col('row_id')==r['row_id']);note=prior.read(prior.OUT/f"fit-{y}-{r['outer_fold']}.json");traces={}
            for h in note['heads']:
                assert sha256_file(Path(h['path']))==h['sha256'];m=joblib.load(h['path']);x=row.select(pre['pa_features']).to_numpy()[0]
                traces[h['head']]=logit_trace(m,x,pre['pa_features']) if h['head']=='participation' else trace(m,x,pre['pa_features'])
                pred=traces[h['head']].get('linked_probability',traces[h['head']]['raw_prediction'])
                assert np.isclose(pred,r['preseason_raw_p' if h['head']=='participation' else 'preseason_raw_conditional_pa'],atol=1e-10)
            peers=current.filter((pl.col('origin_year')==y)&(pl.col('on_40man')==0)&(pl.col('player_id')!=pid)).with_columns(
                (((pl.col('age')-r['age'])/3)**2+((pl.col('pa_0')-r['pa_0'])/250)**2).alias('distance')).sort('distance','player_id').head(4)
            cases.append(dict(origin=r,source_state=details[r['row_id']],actual_inputs={n:row[n][0] for n in pre['pa_features']},
                source_history=counts.filter((pl.col('player_id')==pid)&pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts(),
                saved_paths={head:dict(reference=t['reference'],raw_prediction=t['raw_prediction'],linked_probability=t.get('linked_probability'),
                    terms=t['feature_effects'][:8],roster_terms=[x for x in t['feature_effects'] if x['feature']=='on_40man']) for head,t in traces.items()},
                actual_training_exposure=next(s for s in support if s['year']==y and s['fold']==r['outer_fold']),
                peers=peers.select('player_id','player_name','age','pa_0','recorded_open_fa','preseason_p','preseason_conditional_pa','preseason_pa','preseason_value','next_pa','next_value').to_dicts()))
    write('scores.json',scores);write('support.json',support);write('cases.json',cases)
    paths += [prior.OUT/'features.parquet',prior.OUT/'scored-predictions.parquet',prior.OUT/'preflight.json',ROOT/'reports/generated/hitter-arrival-source-repair-v1/year-end-rosters.parquet',
        Path(__file__),ROOT/'docs/hitter-employment-v70-contract.md']
    write('audit.json',dict(source_hashes={str(p):sha256_file(p) for p in paths},capture_counts=capture_counts,rows=len(f),eval_rows=len(q),
        fixed_model_replays=18,future_event_checks=9,source_publication_vintages_verified=False,roster_conflicts=int(f['fa_roster_conflict'].sum()),
        player_walkthrough_status='pending',new_models_fitted=0,forecasts_changed=False,protected_outcomes_used=False))
    for s in scores[:4]:print(s['scope'],s['rows'],s['actual_pa'],s['existing']['pa_total'],s['probability']['actual_participants'],s['probability']['expected_participants'],flush=True)


if __name__=='__main__':main()
