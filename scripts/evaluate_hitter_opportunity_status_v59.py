"""Bounded dated-context addition to the corrected hitter opportunity heads."""
from collections import defaultdict
from datetime import date
from pathlib import Path
import json
import sys
import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights
import evaluate_hitter_numeric_repair_v53 as base
import evaluate_availability_context_v29b as historical

ROOT=base.ROOT
OUT=ROOT/'reports/generated/practical-hitter-opportunity-status-v59'
FEATURES=['status_capture_scope','status_medical_scope','status_acquired',
    'status_minor_contract','status_ordinary_departure','status_log_absence730',
    'status_open_medical','status_medical_full_absence','status_offseason_activation',
    'status_nonmedical_unresolved']


def read(p):
    return json.loads(Path(p).read_text(encoding='utf8'))


def write(name,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(obj,indent=2,default=str,allow_nan=False)+'\n',encoding='utf8')


def context(row,records,calendars):
    h=historical.repaired.row_features(row,records,calendars)
    captured=float(h['context_capture_scope'])
    observed=float(h['il_scope'])
    x=dict(zip(FEATURES,[captured,observed,captured*h['context_acquired'],
        captured*h['context_minor_contract'],
        captured*h['context_scope_exit']*(1-h['context_nonmedical_unresolved']),
        observed*h['il_log_days730'],observed*h['il_open'],
        observed*h['context_medical_absence'],observed*h['il_offseason_activation'],
        captured*h['context_nonmedical_unresolved']]))
    return x,h


def profiles(g):
    return g.with_columns((pl.col('age')//5).alias('age_group'),
        pl.when(pl.col('pa_0')==0).then(pl.lit('none')).when(pl.col('pa_0')<200)
        .then(pl.lit('brief')).when(pl.col('pa_0')<600).then(pl.lit('partial_regular'))
        .otherwise(pl.lit('large_regular')).alias('current_workload'),
        (pl.col('status_medical_full_absence')>0).alias('medical_absence_profile'))


def prepare():
    assert read(base.OUT/'report.json')['player_walkthrough_status']=='complete'
    assert not (OUT/'preflight.json').exists(),'Preserve completed preflight'
    OUT.mkdir(parents=True,exist_ok=True)
    historical.configure()
    lookup,calendars,paths,audit=historical.runner.sources()
    source=pl.read_parquet(base.OUT/'features.parquet')
    rows=[];details=[];future_checks=0
    for row in source.iter_rows(named=True):
        x,h=context(row,lookup[row['player_id']],calendars)
        rows.append(dict(row_id=row['row_id'],**x))
        details.append(h)
        if (row['player_id'],row['origin_year']) in [(592450,2022),(680574,2024),
            (666158,2023),(665487,2022),(677551,2023),(645801,2023),(694671,2023)]:
            cutoff=date(row['origin_year'],12,31)
            extra=dict(transaction_id=-999999,player_id=row['player_id'],
                available_date=date(cutoff.year+1,1,1),event_date=date(cutoff.year,1,1),
                kind='deceased',description='future mutation',il_kind=None,
                category='unspecified',surgery=False)
            assert context(row,lookup[row['player_id']]+[extra],calendars)==(x,h)
            future_checks+=1
    enriched=source.join(pl.DataFrame(rows),on='row_id',validate='1:1')
    assert enriched.select(source.columns).equals(source)
    enriched.write_parquet(OUT/'features.parquet')
    pl.DataFrame(details,infer_schema_length=None).write_parquet(OUT/'context.parquet')
    write('records.json',{str(pid):rs for pid,rs in lookup.items() if pid in set(source['player_id'])})
    previous=read(base.OUT/'preflight.json');cells=[];supports=[];flags=[]
    keys=['stage','prior_debut','age_group','current_workload','medical_absence_profile']
    for cell in previous['cells']:
        tr=enriched.filter(pl.col('row_id').is_in(cell['training_row_ids'])).sort('row_id')
        te=enriched.filter(pl.col('row_id').is_in(cell['test_row_ids'])).sort('player_id')
        checks={};enabled={};feature_support={}
        for head,sub in [('participation',tr),('conditional_pa',tr.filter(pl.col('next_pa')>0))]:
            support={}
            for feature in FEATURES:
                g=sub.filter(pl.col(feature)>0)
                support[feature]=dict(players=g['player_id'].n_unique(),
                    origins=g['origin_year'].n_unique(),
                    positive_players=g.filter(pl.col('next_pa')>0)['player_id'].n_unique(),
                    zero_players=g.filter(pl.col('next_pa')==0)['player_id'].n_unique())
            names=previous['pa_features']+[n for n in FEATURES if n in FEATURES[:2] or support[n]['players']>=20]
            sp,note=preflight(sub,te,cutoff=cell['year'],fold=cell['fold'],
                features=names,expected_keys=te.select('row_id','horizon').iter_rows())
            supports.append(sp.with_columns(pl.lit(head).alias('head')))
            count=profiles(sub).group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_players'))
            flags.append(profiles(te).select('row_id',*keys).join(count,on=keys,how='left',validate='m:1')
                .with_columns(pl.col('profile_players').fill_null(0),pl.lit(head).alias('head')))
            checks[head]=note;enabled[head]=names;feature_support[head]=support
        cells.append(dict(**cell,checks=checks,features=enabled,feature_support=feature_support))
    pl.concat(supports).write_parquet(OUT/'support.parquet')
    pl.concat(flags).write_parquet(OUT/'profile-support.parquet')
    paths.extend([Path(__file__),ROOT/'docs/practical-hitter-opportunity-status-v59-contract.md',
        base.OUT/'features.parquet',base.OUT/'scored-predictions.parquet',base.OUT/'preflight.json',
        OUT/'features.parquet',OUT/'context.parquet',OUT/'records.json',
        ROOT/'src/universal_baseball/injury_detail_v26.py',
        ROOT/'src/universal_baseball/hitter_health_budget.py'])
    write('preflight.json',dict(before_fitting=True,cells=cells,settings=previous['settings'],
        added_features=FEATURES,source_rows=len(source),source_audit=audit,future_mutation_checks=future_checks,
        source_publication_vintages_verified=False,all_level_medical_coverage=False,
        input_hashes={str(p):sha256_file(p) for p in paths},protected_outcomes_used=False))
    print('Source and all 70 actual head/subset preflights saved.',flush=True)
    for pid,y in [(592450,2022),(680574,2024),(666158,2023),(665487,2022),(677551,2023)]:
        print(enriched.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y))
            .select('player_name','origin_year',*FEATURES).to_dicts(),flush=True)


def fit():
    pre=read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    source=pl.read_parquet(OUT/'features.parquet')
    anchor=pl.read_parquet(base.OUT/'scored-predictions.parquet');fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];path=OUT/f'forecast-{y}-{k}.parquet'
            if path.exists():
                note=read(OUT/f'fit-{y}-{k}.json')
                assert sha256_file(path)==note['prediction_sha256']
                for h in note['heads']:assert sha256_file(Path(h['path']))==h['sha256']
                fits.append(note);continue
            tr=source.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q=anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            assert q['row_id'].equals(te['row_id'])
            heads=[];outputs={}
            for head,sub,model in [
                ('participation',tr,HistGradientBoostingClassifier(**pre['settings'])),
                ('conditional_pa',tr.filter(pl.col('next_pa')>0),HistGradientBoostingRegressor(**pre['settings']))]:
                names=c['features'][head];x=sub.select(names).to_numpy();tx=te.select(names).to_numpy()
                model.fit(x,sub['next_active' if head=='participation' else 'next_pa'].to_numpy(),sample_weight=weights(sub))
                outputs[head]=model.predict_proba(tx)[:,1] if head=='participation' else model.predict(tx)
                assert np.isfinite(outputs[head]).all()
                mp=OUT/f'{head}-{y}-{k}.joblib';joblib.dump(model,mp,compress=3)
                heads.append(dict(head=head,path=str(mp),sha256=sha256_file(mp),features=names,
                    training_rows=len(sub),training_players=sub['player_id'].n_unique()))
            p=outputs['participation'].copy()
            p[q['hard_unavailable'].to_numpy()|q['reported_retired'].to_numpy()]=0
            cond=np.clip(outputs['conditional_pa'],1,800)
            q=q.with_columns(pl.Series('status_raw_p',outputs['participation']),pl.Series('status_p',p),
                pl.Series('status_raw_conditional_pa',outputs['conditional_pa']),
                pl.Series('status_conditional_pa',cond),pl.Series('status_pa',p*cond),
                pl.col('repaired_rate').alias('status_rate'))
            q=q.with_columns((pl.col('status_pa')*(pl.col('status_rate')/600+pl.col('origin_replacement_rate'))).alias('status_value'))
            q.write_parquet(path)
            note=dict(year=y,fold=k,heads=heads,prediction_sha256=sha256_file(path))
            write(f'fit-{y}-{k}.json',note);fits.append(note)
            print(f'Status opportunity {y}/{k}: saved two heads.',flush=True)
    q=pl.concat([pl.read_parquet(OUT/f"forecast-{c['year']}-{c['fold']}.parquet") for c in pre['cells']]).sort('row_id')
    assert len(q)==30506 and q.select(anchor.columns).equals(anchor.sort('row_id'))
    assert q['status_rate'].equals(q['repaired_rate'])
    q.write_parquet(OUT/'predictions.parquet');write('fits.json',fits)
    write('fit-report.json',dict(heads=70,baseline_columns_exact=True,batting_rate_exact=True,
        player_walkthrough_status='pending',protected_outcomes_used=False,frozen_forecast_changed=False))


if __name__=='__main__':
    {'prepare':prepare,'fit':fit}[sys.argv[1]]()
