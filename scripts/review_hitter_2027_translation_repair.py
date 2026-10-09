"""Source-to-coefficient case review and unchanged-production sensitivity."""
from pathlib import Path
import gzip
import json

import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits

from universal_baseball.hitter_talent_bridge import PROFILE_FEATURES
from universal_baseball.hitter_translation_reliability import reliable_translation
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
from fit_practical_hitter_v31 import weights
from test_hitter_2027_translation_repair import ROOT, OLD, OUT, PUBLIC, read, profile
from capture_hitter_2027_origin_counts import write_once


def trace(model,row,names):
    x=safe_matrix(row,names)[0];contributions=x*model.coef_
    result=float(model.intercept_+contributions.sum())
    assert np.isclose(result,model.predict(x[None,:])[0],rtol=0,atol=1e-10)
    translated=[i for i,c in enumerate(names) if c in PROFILE_FEATURES[:8]]
    ordered=np.argsort(-np.abs(contributions))[:12]
    return dict(prediction=result,intercept=float(model.intercept_),
        translated_event_contribution=float(contributions[translated].sum()),
        other_feature_contribution=float(contributions.sum()-contributions[translated].sum()),
        translated_features=[dict(feature=names[i],input=float(x[i]),coefficient=float(model.coef_[i]),contribution=float(contributions[i])) for i in translated],
        largest_terms=[dict(feature=names[i],input=float(x[i]),coefficient=float(model.coef_[i]),contribution=float(contributions[i])) for i in ordered])


def production_probe(names):
    frozen=ROOT/'model_artifacts/hitter-selected-2026-frozen-2026-10-05'
    manifest=read(frozen/'freeze-manifest.json')
    for entry in manifest['files']:
        assert sha256_file(frozen/entry['path'])==entry['sha256']
    pre=read(frozen/'preflight.json');receipt=[];cases=[]
    for k in range(5):
        cell=next(c for c in pre['cells'] if c['fold']==k)
        f=pl.read_parquet(OLD/f'features-{k}.parquet')
        tr=f.filter(pl.col('row_id').is_in(cell['active_training_row_ids'])).sort('row_id')
        assert tr['row_id'].to_list()==sorted(cell['active_training_row_ids'])
        q=pl.read_parquet(frozen/f'inputs-{k}.parquet').sort('row_id')
        old=joblib.load(frozen/f'rate_prospect-{k}.joblib')
        frozen_q=pl.read_parquet(frozen/f'forecast-{k}.parquet').sort('row_id')
        assert np.allclose(old.predict(safe_matrix(q,names)),frozen_q['raw_rate_prospect'],rtol=0,atol=1e-10)
        assert tr['target_year'].max()<=2025 and not set(tr['player_id'])&set(q['player_id'])
        transformed=reliable_translation(tr);newq=reliable_translation(q)
        w=weights(tr)*tr['next_pa'].to_numpy();w*=len(w)/w.sum()
        new=Ridge(alpha=100).fit(safe_matrix(transformed,names),tr['next_batting_rate'].to_numpy(),sample_weight=w)
        path=OUT/f'production-probe-{k}.joblib';assert not path.exists();joblib.dump(new,path,compress=3)
        receipt.append(dict(fold=k,training_rows=len(tr),training_people=tr['player_id'].n_unique(),
            model_path=str(path),sha256=sha256_file(path),max_training_target_year=int(tr['target_year'].max()),
            no_2026_outcomes_used=True))
        for pid in [804944,805811,808393,592450,701762]:
            row=q.filter(pl.col('player_id')==pid)
            if row.is_empty():continue
            if row['prior_debut'][0]:
                cases.append(dict(player_id=pid,player_name=row['player_name'][0],prior_debut=True,
                                  interpretation='Not a prospect-route deployment change; retained current selected rate.'))
                continue
            cases.append(dict(player_id=pid,player_name=row['player_name'][0],prior_debut=False,
                origin_year=2025,supported_pa=row['translation_supported_pa'][0],
                reliability=row['translated_reliability'][0],
                baseline=trace(old,row,names),candidate=trace(new,newq.filter(pl.col('player_id')==pid),names)))
    # This only explains the known failure on old inputs; not a replacement for
    # the frozen forecast and not a new untouched 2026 evaluation.
    return dict(kind='nondeployed_2025_input_sensitivity',heads=receipt,cases=cases,
                frozen_forecast_sha256=sha256_file(frozen/'forecast.parquet'))


def main():
    report=PUBLIC/'translation-repair-player-walkthrough.json.gz'
    if report.exists():raise ValueError('Preserve completed cases')
    pre=read(OUT/'preflight.json');names=pre['features']
    q=pl.read_parquet(OUT/'predictions.parquet');fits=read(OUT/'fits.json')
    assert sha256_file(OUT/'predictions.parquet')==fits['predictions_sha256']
    never=q.filter(pl.col('prior_debut')==0).with_columns(
        ((pl.col('baseline_value')-pl.col('next_value'))**2-(pl.col('candidate_value')-pl.col('next_value'))**2).alias('gain'),
        (pl.col('candidate_value')-pl.col('next_value')).alias('error'))
    chosen={}
    def choose(rows,reason):
        if rows.is_empty():raise ValueError('Missing case category')
        rid=rows['row_id'][0];chosen.setdefault(rid,[]).append(reason)
    for pid,y in [(701762,2024),(694671,2023),(670867,2017),(702616,2023)]:
        choose(never.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed_before_fit')
    for reason,rows in [('largest_gain',never.sort('gain',descending=True)),('largest_harm',never.sort('gain')),
                        ('false_high',never.sort('error',descending=True)),('false_low',never.sort('error')),
                        ('ordinary_active',never.filter(pl.col('next_pa').is_between(100,600)).sort(pl.col('error').abs()))]:
        choose(rows,reason)
    source_path=ROOT/'reports/generated/practical-hitter-v31/counts.parquet'
    counts=pl.read_parquet(source_path);support=pl.read_parquet(OUT/'support.parquet');cases=[]
    with threadpool_limits(limits=2):
        for k in range(5):
            f=pl.read_parquet(OLD/f'features-{k}.parquet')
            selected=q.filter((pl.col('outer_fold')==k)&pl.col('row_id').is_in(list(chosen)))
            for r in selected.to_dicts():
                y,rid=r['origin_year'],r['row_id'];row=f.filter(pl.col('row_id')==rid)
                candidates=f.filter((pl.col('origin_year')==y)&(pl.col('outer_fold')==k)&
                    (pl.col('prior_debut')==0)&(pl.col('stage')==r['stage'])&(pl.col('player_id')!=r['player_id']))
                peers=candidates.with_columns((((pl.col('age')-r['age'])/3)**2+
                    ((pl.col('translation_supported_pa')-r['translation_supported_pa'])/500)**2+
                    (pl.col('source_position')!=row['source_position'][0]).cast(pl.Int64)).alias('distance')).sort('distance','player_id').head(3)
                oldhead=next(h for h in read(OLD/f'fit-{y}-{k}.json')['heads'] if h['arm']=='translated_ridge')
                assert sha256_file(Path(oldhead['path']))==oldhead['sha256']
                old=joblib.load(oldhead['path']);new=joblib.load(OUT/f'ridge-{y}-{k}.joblib')
                origins=pl.concat([row,peers.drop('distance')],how='vertical_relaxed')
                traces=[]
                for origin in origins.iter_rows(named=True):
                    single=origins.filter(pl.col('row_id')==origin['row_id']);pid=origin['player_id']
                    observed=q.filter(pl.col('row_id')==origin['row_id']).row(0,named=True)
                    a,b=trace(old,single,names),trace(new,reliable_translation(single),names)
                    assert np.isclose(a['prediction'],observed['baseline_rate'],atol=1e-10,rtol=0)
                    assert np.isclose(b['prediction'],observed['candidate_rate'],atol=1e-10,rtol=0)
                    traces.append(dict(player_id=pid,player_name=origin['player_name'],age=origin['age'],
                        source_history=counts.filter((pl.col('player_id')==pid)&pl.col('season').is_between(y-2,y)).to_dicts(),
                        original_features=single.select(names).to_dicts()[0],
                        supported_pa=origin['translation_supported_pa'],reliability=origin['translated_reliability'],
                        baseline=a,candidate=b,observed_and_opportunity=observed,
                        profile_support=support.filter(pl.col('row_id')==origin['row_id']).to_dicts()))
                graph=next(g for g in read(OLD/f'translation-{k}.json')['graphs'] if g['cutoff']==y)
                cases.append(dict(player_id=r['player_id'],origin_year=y,fold=k,reasons=chosen[rid],
                    peer_rule='same origin, held fold, stage and never-debut; nearest age, exposure and position without target outcomes',
                    peers=peers.select('player_id','player_name','distance').to_dicts(),
                    graph_mlb_reference=graph['mlb_reference'],graph_offsets=graph['offsets'],traces=traces))
        probe=production_probe(names)
    data=dict(status='calculations_complete_baseball_interpretation_pending',cases=cases,production_probe=probe,
        source_counts_sha256=sha256_file(source_path),predictions_sha256=fits['predictions_sha256'],
        player_walkthrough_status='pending_written_interpretation',forecast_changed=False)
    report.write_bytes(gzip.compress(json.dumps(data,allow_nan=False,ensure_ascii=False,default=str).encode('utf8'),mtime=0))
    write_once(PUBLIC/'translation-repair-walkthrough-receipt.json',dict(path=str(report),sha256=sha256_file(report),
        historical_cases=len(cases),peer_count=sum(len(c['peers']) for c in cases),
        player_walkthrough_status='pending_written_interpretation',production_probe_heads=5))
    for case in cases:
        t=case['traces'][0];r=t['observed_and_opportunity']
        print(f"{t['player_name']} {case['origin_year']}: {r['baseline_rate']:.3f} -> {r['candidate_rate']:.3f}, actual relative {r['actual_relative_rate']:.3f}, actual PA {r['next_pa']}, reasons {case['reasons']}",flush=True)
    for c in probe['cases']:
        if not c['prior_debut']:
            print(f"Production probe {c['player_name']}: {c['baseline']['prediction']:.4f} -> {c['candidate']['prediction']:.4f}; event contribution {c['baseline']['translated_event_contribution']:.4f} -> {c['candidate']['translated_event_contribution']:.4f}",flush=True)


if __name__=='__main__':main()
