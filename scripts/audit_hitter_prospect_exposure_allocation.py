"""Diagnose unchanged forecasts; never fit, perturb or replace predictions."""
import json
from pathlib import Path
from types import SimpleNamespace

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.hitter_numeric_history import BUCKETS
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.prospect_exposure_diagnostic import exposure, pa_accounting
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/generated/hitter-prospect-exposure-allocation-audit-source-aligned'
CURRENT = ROOT/'reports/generated/hitter-preseason-readiness-v68'
BRIDGE = ROOT/'reports/generated/hitter-talent-bridge-v74'
FINAL = ROOT/'reports/generated/hitter-final-2026-evaluation'
FROZEN = ROOT/'model_artifacts/hitter-selected-2026-frozen-2026-10-05'
FIXED = [(701762,2024), (694671,2023), (677594,2021), (660670,2017),
         (624413,2018), (702616,2023), (682616,2023)]
FINAL_FIXED = [815908,815888,681198,805808]
CONTRACT = ROOT/'docs/hitter-prospect-exposure-allocation-audit-contract.md'


def read(p):
    return json.loads(p.read_text(encoding='utf8'))


def save(name, value):
    p = OUT/name
    assert not p.exists(), f'Preserve {p}'
    p.write_text(json.dumps(value,indent=2,allow_nan=False,ensure_ascii=False,default=str)+'\n',
                 encoding='utf8',newline='\n')


def tagged(q):
    return q.hstack(pl.DataFrame([exposure(r) for r in q.iter_rows(named=True)]))


def totals(q, vintage):
    p,c,y = ('preseason_p','preseason_conditional_pa','next_pa') if vintage=='history' else (
        'participation_probability','conditional_pa','actual_pa')
    pred,value = ('translated_ridge_value','next_value') if vintage=='history' else (
        'batting_contribution','actual_relative_value')
    return dict(people=q['player_id'].n_unique(),
        **pa_accounting(q[p],q[c],q[y]),
        predicted_batting_contribution=float(q[pred].sum()),
        actual_batting_contribution=float(q[value].sum()),
        batting_contribution_rmse=float(np.sqrt(np.mean((q[pred].to_numpy()-q[value].to_numpy())**2))))


def scopes(q, vintage):
    groups=[('all_never_debut',q)]
    for key in ['promotion_mismatch','highest_exposure_band','rank_band','origin_year']:
        groups += [(f'{key}={v}',q.filter(pl.col(key)==v)) for v in sorted(q[key].unique())]
    groups += [(f'exposure_rank={b}/{r}',g) for (b,r),g in q.partition_by(
        ['highest_exposure_band','rank_band'],as_dict=True).items()]
    # All predeclared experience groups by year, including zeros and bad years.
    groups += [(f'year_exposure={y}/{b}',g) for (y,b),g in q.partition_by(
        ['origin_year','highest_exposure_band'],as_dict=True).items()]
    return [dict(scope=n,**totals(g,vintage)) for n,g in groups if len(g)]


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assert not (OUT/'source-check.json').exists(), 'Preserve completed or interrupted audit'
    paths=[CONTRACT,ROOT/'docs/hitter-prospect-exposure-audit-execution-note.md',Path(__file__),ROOT/'src/universal_baseball/prospect_exposure_diagnostic.py',
        ROOT/'tests/test_prospect_exposure_diagnostic.py',CURRENT/'preflight.json',CURRENT/'features.parquet',
        BRIDGE/'predictions.parquet',FINAL/'scored-fixed-cohort.parquet',FINAL/'review-completion.json',
        ROOT/'reports/generated/practical-hitter-v31/counts.parquet',
        ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet',FROZEN/'freeze-manifest.json']
    before={str(p):sha256_file(p) for p in paths}
    pre=read(CURRENT/'preflight.json');names=pre['pa_features']
    assert len(names)==251
    source=pl.read_parquet(CURRENT/'features.parquet')
    hist=pl.read_parquet(BRIDGE/'predictions.parquet').sort('row_id')
    final=pl.read_parquet(FINAL/'scored-fixed-cohort.parquet').sort('row_id')
    counts=pl.read_parquet(paths[-3]);stints=pl.read_parquet(paths[-2])
    assert len(source)==63282 and len(hist)==30506 and len(final)==4030
    assert hist['row_id'].n_unique()==len(hist) and final['row_id'].n_unique()==len(final)
    assert np.array_equal(hist['preseason_pa'],hist['translated_ridge_pa'])
    assert counts.unique(['player_id','season','bucket']).height==len(counts)
    lut={(r['player_id'],r['season'],r['bucket']):r['plate_appearances'] for r in counts.iter_rows(named=True)}
    checks=[]
    for title,q in [('historical_source',source),('frozen_2026',final)]:
        for b in BUCKETS:
            for lag in range(3):
                expected=np.array([lut.get((pid,y-lag,b),0) for pid,y in q.select('player_id','origin_year').iter_rows()])
                actual=q[f'{b}_{lag}_pa'].to_numpy()
                bad=~np.isclose(expected,actual,atol=1e-10,rtol=0)
                checks.append(dict(source=title,field=f'{b}_{lag}_pa',rows=len(q),mismatches=int(bad.sum())))
    assert not any(c['mismatches'] for c in checks), 'Source-PA mismatch: stop before model interpretation'
    level_inputs=[f'{b}_{lag}_pa' for b in BUCKETS for lag in range(3)]
    assert set(level_inputs)<=set(names)
    assert not any(n in names for n in ['stage','snapshot_level','primary_level','highest_level'])
    paired_source=source.filter(pl.col('row_id').is_in(hist['row_id'].to_list())).sort('row_id')
    assert hist['row_id'].equals(paired_source['row_id'])
    shared=[n for n in names if n in hist.columns]
    inherited_differences=[]
    for n in shared:
        bad=~np.isclose(hist[n].to_numpy(),paired_source[n].to_numpy(),atol=1e-10,rtol=0)
        if bad.any():
            inherited_differences.append(dict(field=n,different_rows=int(bad.sum()),
                maximum_absolute_difference=float(abs(hist[n].to_numpy()-paired_source[n].to_numpy()).max())))
    # The export deliberately preserves older baseline fields. They are not
    # authoritative current inputs. Retain them under an explicit legacy label
    # in memory, then join the actual fitted input frame without changing scores.
    hist=hist.rename({n:'legacy_export_'+n for n in shared}).join(
        paired_source.select('row_id',*names),on='row_id',validate='1:1').sort('row_id')
    source,hist,final=map(tagged,[source,hist,final])
    save('source-check.json',dict(checks=checks,fields_compared=sum(c['rows'] for c in checks),
        source_pa_inputs_present=level_inputs,coarse_stage_is_not_model_input=True,
        inherited_export_fields_differing_from_actual_inputs=inherited_differences,
        inherited_export_fields_missing_actual_inputs=[n for n in names if n not in shared],
        diagnostic_groups_use_actual_fitted_inputs=True,
        no_promotion_dates_in_annual_stints=True,input_hashes=before,model_fits=0,
        protected_2026_outcomes_already_open=True,forecast_changes=False))
    never=hist.filter(pl.col('prior_debut')==0)
    now=final.filter(pl.col('prior_debut')==0)
    assert len(never)==24199 and len(now)==3116
    accounting=dict(historical=scopes(never,'history'),evaluated2026=scopes(now,'2026'),
        historical_value_ledger='Existing origin-relative batting plus replacement; translated prospect rate',
        final_value_ledger='Already evaluated future-season-relative batting plus replacement',
        interpretation='Descriptive exposed-data accounting, not causal effects, new forecasts or a validation of fixes')
    save('accounting.json',accounting)
    selected={};missing=[]
    for pid,year in FIXED:
        g=never.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==year))
        if len(g):selected[('history',g['row_id'][0])]='fixed historical case'
        else:missing.append(dict(player_id=pid,origin_year=year,reason='Not eligible for fixed never-debut historical diagnosis'))
    cameo=never.filter(pl.col('promotion_mismatch')&(pl.col('highest_pa')<200)).with_columns(
        (pl.col('preseason_pa')-pl.col('next_pa')).alias('pa_error'))
    for purpose,sub in [('largest cameo overestimate',cameo.sort('pa_error','row_id',descending=[True,False])),
        ('largest cameo underestimate',cameo.sort('pa_error','row_id')),
        ('ordinary cameo',cameo.filter(pl.col('preseason_pa')>=5).with_columns(pl.col('pa_error').abs().alias('absolute_error')).sort('absolute_error','row_id'))]:
        if len(sub):selected[('history',sub['row_id'][0])]=purpose
    for pid in FINAL_FIXED:
        g=now.filter(pl.col('player_id')==pid)
        if len(g):selected[('2026',g['row_id'][0])]='Fixed exposed 2026 explanatory case only'
    save('selection.json',dict(cases=[dict(vintage=v,row_id=rid,purpose=purpose) for (v,rid),purpose in selected.items()],
        missing_fixed_cases=missing,peer_rule='Same origin, rank band, age within two, age-known status, primary and highest affiliated level; outcomes unused',
        no_new_candidate=True))
    manifest=read(FROZEN/'freeze-manifest.json');frozen_pre=read(FROZEN/'preflight.json')
    models={};walks=[]
    def walk(vintage,r,reason,peers=False):
        frame=source if vintage=='history' else final
        trainframe=source
        if vintage=='history':
            cell=next(c for c in pre['cells'] if c['year']==r['origin_year'] and c['fold']==r['outer_fold'])
            note=read(CURRENT/f"fit-{r['origin_year']}-{r['outer_fold']}.json")
            heads=[dict(h,features=names) for h in note['heads']]
            train_ids=cell['training_row_ids']
            train=trainframe.filter(pl.col('row_id').is_in(train_ids))
            result_names=['preseason_p','preseason_conditional_pa','preseason_pa','translated_ridge_rate',
                          'translated_ridge_value','next_pa','next_value']
        else:
            cell=next(c for c in frozen_pre['cells'] if c['fold']==r['outer_fold'])
            heads=[dict(h,path=str(FROZEN/h['path'])) for h in manifest['models']
                   if h['fold']==r['outer_fold'] and h['head'] in ['participation','conditional_pa']]
            train=trainframe.filter(pl.col('row_id').is_in(cell['training_row_ids']))
            result_names=['participation_probability','conditional_pa','expected_pa','hitting_wins_per_600',
                          'batting_contribution','actual_pa','actual_relative_value']
        assert not (train['player_id']==r['player_id']).any()
        assert train['target_year'].max()<=r['origin_year']
        group=( (pl.col('prior_debut')==0)&(pl.col('rank_band')==r['rank_band'])&
            (pl.col('primary_level')==r['primary_level'])&(pl.col('highest_level')==r['highest_level'])&
            (pl.col('age_unknown')==r['age_unknown'])&(abs(pl.col('age')-r['age'])<=2) )
        matching=train.filter(group)
        support=dict(full_training_people=matching['player_id'].n_unique(),
            active_training_people=matching.filter(pl.col('next_pa')>0)['player_id'].n_unique(),
            profile_warning='Matching profile is descriptive, not proof of adequate model support')
        output={k:r[k] for k in result_names};traces={}
        for h in heads:
            p=Path(h['path']);assert sha256_file(p)==h['sha256']
            before[str(p)]=h['sha256']
            if str(p) not in models:models[str(p)]=joblib.load(p)
            model=models[str(p)]
            actual_inputs=(source.filter(pl.col('row_id')==r['row_id']).row(0,named=True)
                           if vintage=='history' else r)
            # Historical prediction exports omit some game-input columns.
            # Replay the actual saved model input, never fabricate absent inputs.
            for n in h['features']:
                if n in r:
                    assert np.isclose(r[n],actual_inputs[n],atol=1e-10,rtol=0), n
            x=np.array([actual_inputs[n] for n in h['features']],dtype=float)
            if h['head']=='participation':
                proxy=SimpleNamespace(_baseline_prediction=model._baseline_prediction,
                    _predictors=model._predictors,predict=model.decision_function)
                t=trace(proxy,x,h['features']);prob=float(1/(1+np.exp(-t['raw_prediction'])))
                assert np.isclose(prob,model.predict_proba(x[None,:])[0,1],atol=1e-10,rtol=0)
                t['linked_probability']=prob
                expected=r['preseason_raw_p' if vintage=='history' else 'raw_participation']
                assert np.isclose(prob,expected,atol=1e-10,rtol=0)
            else:
                t=trace(model,x,h['features'])
                expected=r['preseason_raw_conditional_pa' if vintage=='history' else 'raw_conditional_pa']
                assert np.isclose(t['raw_prediction'],expected,atol=1e-8,rtol=0)
            traces[h['head']]=dict(model_path=str(p),model_sha256=h['sha256'],
                                  actual_inputs={n:actual_inputs[n] for n in h['features']},**t)
        candidates=frame.filter(group&(pl.col('origin_year')==r['origin_year'])&(pl.col('player_id')!=r['player_id']))
        candidates=candidates.with_columns((abs(pl.col('age')-r['age'])/2+
            abs(pl.col('affiliated_pa')-r['affiliated_pa'])/300+
            abs(pl.col('highest_pa')-r['highest_pa'])/200+
            abs(pl.col('scout_rank_score_0')-r['scout_rank_score_0'])+
            pl.when(pl.col('source_position')!=r['source_position']).then(.5).otherwise(0)).alias('peer_distance'))
        nearest=candidates.sort('peer_distance','player_id').head(3)
        known=['player_id','player_name','origin_year','age','age_unknown','source_position','snapshot_level','stage',
            'primary_level','highest_level','highest_pa','highest_exposure_band','primary_share','rank_band',
            'scout_listed_0','scout_rank_score_0','on_40man',*level_inputs]
        result=dict(vintage=vintage,reason=reason,origin={k:r[k] for k in known},forecasts_and_actuals=output,
            source_counts=counts.filter((pl.col('player_id')==r['player_id'])&
                pl.col('season').is_between(r['origin_year']-2,r['origin_year'])).sort('season','bucket').to_dicts(),
            annual_team_stints=stints.filter((pl.col('player_id')==r['player_id'])&
                pl.col('season').is_between(r['origin_year']-2,r['origin_year'])).sort('season','team_id').to_dicts(),
            actual_training_support=support,pa_head_replays=traces)
        if not peers:
            lookup=hist if vintage=='history' else final
            # Source frame lacks saved predictions; attach them only after peer selection.
            result['peers']=[walk(vintage,lookup.filter(pl.col('row_id')==p['row_id']).row(0,named=True),
                'Outcome-blind matching peer',True) for p in nearest.iter_rows(named=True)]
            result['eligible_peer_people']=candidates['player_id'].n_unique()
            result['missing_peer_warning']=len(nearest)==0
        return result
    with threadpool_limits(limits=2):
        for (v,rid),purpose in selected.items():
            q=hist if v=='history' else final;r=q.filter(pl.col('row_id')==rid).row(0,named=True)
            walks.append(walk(v,r,purpose))
            print(f"Replayed {v} {r['player_id']}/{r['origin_year']} and outcome-blind peers",flush=True)
    save('player-walks.json',dict(cases=walks,focal_cases=len(walks),
        total_replayed_cases=sum(1+len(w.get('peers',[])) for w in walks),
        mechanical_replay_status='complete',interpretive_review_status='pending',models_refitted=0))
    assert all(sha256_file(Path(p))==h for p,h in before.items())
    save('verification.json',dict(all_inputs_and_models_unchanged=True,input_hashes=before,
        output_hashes={str(p):sha256_file(p) for p in OUT.iterdir() if p.suffix=='.json'},
        new_fits=0,changed_forecasts=0,disposition='Interpretive review pending',
        final2026_is_explanatory_not_validation_of_any_repair=True))
    print(json.dumps([accounting['historical'][0],accounting['evaluated2026'][0]],indent=2),flush=True)


if __name__=='__main__':
    main()
