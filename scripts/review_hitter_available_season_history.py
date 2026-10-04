"""Actual source inputs, saved paths, fixed heads and outcome-blind peers."""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from prepare_hitter_available_season_history import ROOT, OUT, CURRENT, read, write
from prepare_hitter_extended_training import profile, verify, BUCKETS
from review_hitter_extended_training import highest, distance, linear
from evaluate_hitter_readiness_v49 import logit_trace
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file


def prepare_review(selection_name='selected-cases.json',case_name='cases.json',receipt_name='review-preparation.json'):
    assert not (OUT/case_name).exists(), 'Preserve case evidence'
    pre = read(OUT/'preflight.json')
    verify(pre['input_hashes'])
    check = read(OUT/'verification.json')
    verify(check['hashes'])
    base = profile(pl.read_parquet(CURRENT/'features.parquet'))
    base = base.with_columns(pl.Series('highest_level',[highest(s) for s in base.iter_rows(named=True)]))
    available = pl.read_parquet(OUT/'features.parquet')
    dates = pl.read_parquet(OUT/'source-years.parquet')
    q = pl.read_parquet(OUT/'scored-predictions.parquet')
    counts_path = ROOT/'reports/generated/practical-hitter-v31/counts.parquet'
    games_path = ROOT/'reports/generated/practical-hitter-v38/game-counts.parquet'
    counts,games = pl.read_parquet(counts_path),pl.read_parquet(games_path)
    support = pl.read_parquet(OUT/'profile-support.parquet')
    numeric = ROOT/'reports/generated/practical-hitter-numeric-repair-v53'
    rate_features = read(numeric/'preflight.json')['rate_features']
    cases,models = [],{}
    def load(head):
        verify({head['path']:head['sha256']})
        if head['path'] not in models:
            models[head['path']]=joblib.load(head['path'])
        return models[head['path']]
    with threadpool_limits(limits=2):
        for selected in read(OUT/selection_name):
            rid = selected['row_id']
            f = base.filter(pl.col('row_id')==rid)
            a = available.filter(pl.col('row_id')==rid)
            o,v,result = f.row(0,named=True),a.row(0,named=True),q.filter(pl.col('row_id')==rid).row(0,named=True)
            y,k = o['origin_year'],o['outer_fold']
            cell = next(c for c in pre['cells'] if c['year']==y and c['fold']==k)
            note = read(OUT/f'fit-{y}-{k}.json')
            control = load(cell['control'])
            model = load(note['head'])
            x,z = f.select(pre['features']).to_numpy()[0],a.select(pre['features']).to_numpy()[0]
            old_path,new_path = logit_trace(control,x,pre['features']),logit_trace(model,z,pre['features'])
            np.testing.assert_allclose([old_path['linked_probability'],new_path['linked_probability']],
                [result['preseason_raw_p'],result['available_raw_p']],atol=1e-10,rtol=0)
            current = read(CURRENT/f'fit-{y}-{k}.json')
            ch = next(h for h in current['heads'] if h['head']=='conditional_pa')
            conditional_path = trace(load(ch),x,pre['features'])
            assert abs(conditional_path['raw_prediction']-result['preseason_raw_conditional_pa'])<1e-8
            rate_head = next(h for h in read(numeric/f'fit-{y}-{k}.json')['heads'] if h['head']=='rate')
            rate_path = linear(load(rate_head),f,rate_features)
            assert abs(rate_path['prediction']-result['baseline_rate'])<1e-8
            changed = {n:dict(calendar=o[n],available=v[n]) for n in pre['features'] if abs(o[n]-v[n])>1e-12}
            # Both mixed-input probes are diagnostic only. They decompose an
            # input change from a refit without declaring either a forecast.
            probes = dict(control_on_available_inputs=float(control.predict_proba(z[None,:])[0,1]),
                candidate_on_calendar_inputs=float(model.predict_proba(x[None,:])[0,1]),
                interpretation='Fixed-model mechanics, potentially unsupported mixed combinations; not causal or selectable forecasts')
            pool = base.filter((pl.col('origin_year')==y)&(pl.col('prior_debut')==o['prior_debut'])&
                (pl.col('dominant_level')==o['dominant_level'])&(pl.col('highest_level')==o['highest_level'])&
                (pl.col('age_unknown')==o['age_unknown'])&(abs(pl.col('age')-o['age'])<=2)&(pl.col('player_id')!=o['player_id']))
            peers = pool.with_columns(distance(pool,o).alias('distance')).sort('distance','player_id').head(4)
            origin_cols = ['row_id','player_id','player_name','origin_year','age','prior_debut','stage','source_position',
                'dominant_level','highest_level','minor_pa_0','pa_0','scout_rank_score_0','draft_known','draft_rank',
                *[b+'_0_pa' for b in BUCKETS]]
            if o['dominant_level'] in BUCKETS:
                origin_cols += ['pooled_'+o['dominant_level']+'_'+e for e in ['HR','BB','K']]
            peer_rows=[]
            for peer in peers.iter_rows(named=True):
                p = q.filter(pl.col('row_id')==peer['row_id']).row(0,named=True)
                peer_rows.append(dict(origin={n:peer[n] for n in origin_cols},distance=peer['distance'],
                    forecasts={n:p[n] for n in ['preseason_pa','available_pa','preseason_p','available_p','baseline_rate','next_pa','next_value']}))
            history_years = [dates.filter(pl.col('row_id')==rid)['affiliated_source_year_'+str(j)][0] for j in range(3)]
            hist = counts.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(min(y-2,min(history_years)),y)).sort('season','bucket')
            ghist = games.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(min(y-2,min(history_years)),y)).sort('season','bucket')
            cases.append(dict(selection=selected,information_date=cell['information_date'],origin={n:o[n] for n in origin_cols},
                source_counts=hist.to_dicts(),source_games=ghist.to_dicts(),calendar_source_years=[y-j for j in range(3)],
                available_affiliated_source_years=history_years,true_calendar_gaps=[y-j for j in history_years],
                calendar_inputs={n:o[n] for n in pre['features']},available_inputs={n:v[n] for n in pre['features']},
                changed_model_inputs=changed,saved_model_accounting=dict(calendar=old_path,available=new_path,
                    fixed_conditional_pa=conditional_path,fixed_batting_rate=rate_path),diagnostic_probes=probes,
                forecasts={arm:{n:result[arm+'_'+n] for n in ['p','pa','value']} for arm in ['preseason','available']},
                fixed_heads=dict(raw_conditional_pa=result['preseason_raw_conditional_pa'],conditional_pa=result['preseason_conditional_pa'],
                    batting_rate=result['baseline_rate'],translated_rate=result['translated_ridge_rate'],replacement_per_pa=result['origin_replacement_rate']),
                reality=dict(next_pa=result['next_pa'],next_value=result['next_value'],
                    target_season_batting_rate=result['realized_season_rate'] if result['next_pa']>0 else None),
                actual_fold_support=support.filter(pl.col('row_id')==rid).to_dicts(),peers=peer_rows,
                peer_rule='Same origin/debut/dominant and highest level/known age status, age within two; PA, position, rank, draft and HR/BB/K distance; no future outcomes',
                model_receipts=[cell['control'],note['head'],ch,rate_head]))
    write(case_name,cases)
    write(receipt_name,dict(player_walkthrough_status='pending',case_count=len(cases),
        hashes={str(OUT/n):sha256_file(OUT/n) for n in ['preflight.json','source-approval.json','verification.json','scores.json','intervals.json',selection_name,case_name]},
        source_hashes={str(p):sha256_file(p) for p in [counts_path,games_path]}))
    show(case_name)


def show(case_name='cases.json'):
    for c in read(OUT/case_name):
        print(json.dumps(dict(selection=c['selection'],forecasts=c['forecasts'],fixed=c['fixed_heads'],reality=c['reality'],
            changed_input_count=len(c['changed_model_inputs']),probe=c['diagnostic_probes'],
            effects={a:c['saved_model_accounting'][a]['feature_effects'][:7] for a in ['calendar','available']},
            support=[(s['arm'],s['subset'],s['kind'],s['profile_people']) for s in c['actual_fold_support']],
            peers=[(p['origin']['player_name'],p['forecasts']['next_pa']) for p in c['peers']]),ensure_ascii=False),flush=True)


def supplement():
    assert not (OUT/'selected-supplement.json').exists()
    q = pl.read_parquet(OUT/'scored-predictions.parquet').filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))
    high = q.filter(pl.col('next_pa')==0).sort(['available_pa','row_id'],descending=[True,False]).head(1)
    low = q.filter(pl.col('next_pa')>0).with_columns((pl.col('next_pa')-pl.col('available_pa')).abs().alias('error')).sort(['error','row_id'],descending=[True,False]).head(1)
    selected = []
    for frame,reason in [(high,'Postfit stage coverage supplement: largest lower-minor nonarrival false high'),
                          (low,'Postfit stage coverage supplement: largest lower-minor active PA miss')]:
        o = frame.row(0,named=True)
        selected.append(dict(row_id=o['row_id'],player_id=o['player_id'],origin_year=o['origin_year'],name=o['player_name'],reasons=[reason]))
    write('selected-supplement.json',selected)
    prepare_review('selected-supplement.json','cases-supplement.json','review-supplement-preparation.json')


def finish():
    receipt = read(OUT/'review-preparation.json')
    verify(receipt['hashes'])
    verify(receipt['source_hashes'])
    extra = read(OUT/'review-supplement-preparation.json')
    verify(extra['hashes'])
    verify(extra['source_hashes'])
    cases = read(OUT/'cases.json')+read(OUT/'cases-supplement.json')
    reviews_path = ROOT/'config/hitter_available_season_model_review.json'
    reviews = read(reviews_path)
    assert reviews['player_walkthrough_status']=='complete'
    assert {r['row_id'] for r in reviews['cases']}=={c['selection']['row_id'] for c in cases}
    assert all(r['assessment'] for r in reviews['cases'])
    diagnostic = OUT/'roster-readiness-diagnostic-separate-mexico.json'
    verify(read(diagnostic)['hashes'])
    import xml.etree.ElementTree as ET
    tests_path = OUT/'unit-tests.xml'
    suite = ET.parse(tests_path).getroot().find('testsuite')
    assert int(suite.attrib['tests'])==9 and int(suite.attrib['failures'])==0 and int(suite.attrib['errors'])==0
    for c in cases:
        for h in c['model_receipts']:
            verify({h['path']:h['sha256']})
    pre = read(OUT/'preflight.json')
    support = pl.read_parquet(OUT/'profile-support.parquet')
    prospect_ids = pl.read_parquet(OUT/'scored-predictions.parquet').filter(pl.col('prior_debut')==0)['row_id'].to_list()
    warnings = support.filter(pl.col('row_id').is_in(prospect_ids)).group_by('arm','kind','subset').agg(
        pl.len().alias('forecasts'),(pl.col('profile_people')==0).sum().alias('empty'),
        (pl.col('profile_people')<20).sum().alias('sparse')).sort('arm','kind','subset').to_dicts()
    write('preflight-summary.json',dict(checks_before_fits=70,controls_replayed=35,
        source_rows=pre['source_rows'],evaluation_rows=pre['evaluation_rows'],features=pre['features'],settings=pre['settings'],
        cells=[{n:c[n] for n in ['year','fold','information_date','checks','identical_matrices']} for c in pre['cells']],
        support_warnings=warnings,source_hashes=pre['input_hashes'],
        stored_preflight_sha256=sha256_file(OUT/'preflight.json'),protected_outcomes_used=False))
    write('final-report.json',dict(execution_integrity=True,player_walkthrough_status='complete',reviewed_cases=len(cases),
        disposition=reviews['disposition'],assessments=reviews['cases'],checks_before_fits=70,
        new_classifiers=20,classifiers_replayed=35,controls_replayed_before_fits=35,
        fixed_conditional_and_hitting=True,established_unchanged=True,protected_outcomes_used=False,
        frozen_forecast_changed=False,explorer_changed=False,deployment_approved=False,full_goal_complete=False,
        unit_tests_passed=9,
        hashes={**receipt['hashes'],**receipt['source_hashes'],**extra['hashes'],str(reviews_path):sha256_file(reviews_path),
                str(diagnostic):sha256_file(diagnostic),str(tests_path):sha256_file(tests_path),
                str(OUT/'preflight-summary.json'):sha256_file(OUT/'preflight-summary.json'),
                str(ROOT/'docs/hitter-available-season-history-result.md'):sha256_file(ROOT/'docs/hitter-available-season-history-result.md'),
                str(__file__):sha256_file(Path(__file__))}))
    # Compact receipts go to version control; local fitted models/raw source
    # exports remain local and are explicitly not a self-contained clean clone.
    import shutil
    evidence = ROOT/'reports/model-evidence/hitter-available-season-history'
    evidence.mkdir(parents=True,exist_ok=True)
    for n in ['source-review.json','source-approval.json','scores.json','intervals.json','selected-cases.json',
              'cases.json','selected-supplement.json','cases-supplement.json','scoring-repair.json','preflight-summary.json',
              'roster-readiness-diagnostic-separate-mexico.json','verification.json','final-report.json']:
        shutil.copyfile(OUT/n,evidence/n)
        assert sha256_file(OUT/n)==sha256_file(evidence/n)
    print('Actual source and model walks complete; final disposition recorded.',flush=True)


if __name__=='__main__':
    {'prepare':prepare_review,'show':show,'supplement':supplement,'finish':finish}[sys.argv[1]]()
