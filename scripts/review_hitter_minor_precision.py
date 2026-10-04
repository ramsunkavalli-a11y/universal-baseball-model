"""Review precise source-to-player mechanisms and preserve the completed evidence."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from universal_baseball.hitter_minor_precision import METRICS
from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.mlb_event_logit import EVENTS,VALUES
from prepare_practical_hitter_v33 import safe_matrix
from review_hitter_minor_statcast_next_year import scope,independent,META,distance
import prepare_hitter_minor_precision as prep


def main():
    out=prep.OUT;assert not (out/'final-review.json').exists(),'Preserve final review'
    pre=prep.read(out/'preflight.json');fit=prep.read(out/'fit-report.json');scores=prep.read(out/'scores.json')
    prep.old.verify_hashes(pre['input_hashes']);assert sha256_file(out/'predictions.parquet')==fit['predictions_sha256']
    assert sha256_file(prep.ROOT/'scripts/score_hitter_minor_precision.py')==scores['score_runner_sha256']
    q=pl.read_parquet(out/'scored-predictions.parquet').sort('row_id');anchor=pl.read_parquet(out/'anchor.parquet').sort('row_id')
    assert q.select([n for n in anchor.columns if n not in META]).equals(anchor.select([n for n in anchor.columns if n not in META]))
    assert len(q)==30506 and q['row_id'].n_unique()==30506 and q['target_year'].max()==2025
    counts=q.select(['count_'+e for e in EVENTS]).to_numpy();n=q['next_pa'].to_numpy();active=n>0
    assert np.array_equal(counts.sum(1),n)
    actual=np.zeros(len(q));index=counts@VALUES
    actual[active]=UNIT*(index[active]/n[active]-q.select(['target_env_'+e for e in EVENTS]).to_numpy()[active]@VALUES)
    assert np.allclose(actual,q['actual_future_relative_rate'],atol=1e-10,rtol=0)
    common=np.zeros(len(q));common[active]=UNIT*(index[active]/n[active]-q.select(['origin_env_'+e for e in EVENTS]).to_numpy()[active]@VALUES)
    assert np.allclose(n*(common/600+q['origin_replacement_rate'].to_numpy()),q['next_value'],atol=1e-10,rtol=0)
    for arm in pre['arms']:
        fallback=q.filter(~pl.col('msc_eligible'))
        for kind in ['rate','value']:assert fallback[arm+'_'+kind].equals(fallback['combined_'+kind])
        assert np.allclose(q[arm+'_value'],q['preseason_pa']*(q[arm+'_rate']/600+q['origin_replacement_rate']),atol=1e-12,rtol=0)
    verified=0
    for s in scores['scopes']:
        g=scope(q,s['scope']);assert len(g)==s['rows'] and g['next_pa'].sum()==s['actual_pa']
        assert np.isclose(g['preseason_pa'].sum(),s['predicted_pa']) and np.isclose(g['next_value'].sum(),s['actual_value'])
        for kind,key in [('rate','participant_rate'),('value','contribution')]:
            for arm,r in (s[key] or {}).items():
                assert np.allclose(independent(g,arm,kind),[r['mse'],r['mae'],r['bias']],atol=1e-12,rtol=0)
                if kind=='value':assert np.isclose(g[arm+'_value'].sum(),r['predicted_total'])
                verified+=1
    replays=0
    with threadpool_limits(limits=2):
        for k in range(5):
            f=pl.read_parquet(out/f'features-{k}.parquet')
            for c in [c for c in pre['cells'] if c['fold']==k]:
                tr,te,_=prep.routed(f,c);got=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                assert tr['target_year'].max()<=c['year'] and not set(tr['player_id'])&set(te['player_id'])
                base,_=prep.baseline(te,c);assert np.allclose(base,got['combined_rate'],atol=1e-10,rtol=0)
                for h in prep.read(out/f'fit-{c["year"]}-{k}.json')['heads']:
                    assert sha256_file(Path(h['path']))==h['sha256']
                    update=joblib.load(h['path']).predict(safe_matrix(te,h['features']))
                    assert np.allclose(update,got[h['arm']+'_raw_update'],atol=1e-12,rtol=0);replays+=1
    assert replays==20
    cases=prep.read(out/'cases.json');manual=prep.read(prep.ROOT/'config/hitter_minor_precision_review.json')
    assert {str(c['origin']['row_id']) for c in cases['cases']}==set(manual)
    assert len(cases['cases'])==18
    reasons={r for c in cases['cases'] for r in c['selection']}
    assert {'largest gain','largest harm','false high','false low','ordinary active'}<=reasons
    ledgers={y:pl.read_parquet(prep.old.SOURCE/f'launch-events-{y}.parquet') for y in range(2021,2025)}
    lines=['# Player walkthrough for minor tracking precision adjustments','',
        'Historical next-calendar-year MLB batting only. All rates are custom batting wins per 600 PA; contribution includes batting and replacement, not full WAR. Playing time is fixed.',
        '', 'Cases retain the prior sixteen origins and add the largest gain and ordinary active case. Outcome-selected cases diagnose mechanics; they are not independent confirmation.',
        '', 'Source information shares are before league support routing. Unsupported source groups receive no applied adjustment. Peer distances use origin-known age, actual weighted level PA, draft/rank evidence and MLB PA; not later success.', '']
    checked_bootstrap=0
    for c in cases['cases']:
        o=c['origin'];rid=str(o['row_id']);c['baseball_review']=manual[rid]
        c['information_share_status']='source precision before league support routing; unsupported blocks disabled in actual_inputs'
        assert len(manual[rid])>200 and len(c['peers'])==4
        assert all(s['season']<=o['origin_year'] for s in c['source_history']+c['noise_history'])
        for arm,tr in c['saved_traces'].items():
            expected=o['combined_rate'] if arm=='combined_benchmark' else o[arm+'_raw_update']
            assert np.isclose(tr['intercept']+sum(t['signed_term'] for t in tr['all_terms']),expected,atol=1e-10)
        pool=q.filter((pl.col('origin_year')==o['origin_year'])&(pl.col('prior_debut')==o['prior_debut'])&(pl.col('player_id')!=o['player_id']))
        selected=pool.with_columns(distance(o).alias('peer_distance')).sort('peer_distance','player_id').head(4)
        assert selected['row_id'].to_list()==[p['row_id'] for p in c['peers']]
        for r in c['references']:
            for stat in r['metrics'].values():
                from universal_baseball.post_arrival_history import player_fold
                assert all(player_fold(p)!=o['outer_fold'] for p in stat['reference_ids'])
        # Independent sort-based oracle, rather than partition-based bootstrap.
        for r in c['noise_history']:
            ev=ledgers[r['season']].filter((pl.col('player_id')==o['player_id'])&(pl.col('league_id')==r['league_id'])&pl.col('valid_ev'))['launch_speed'].to_numpy()
            assert len(ev)==r['ev_n']
            if len(ev)>=2:
                rng=np.random.default_rng((o['player_id']*17+r['season']*101+r['league_id'])%2**32)
                draw=np.sort(ev[rng.integers(0,len(ev),size=(128,len(ev)))],axis=1)[:,len(ev)-int(np.ceil(len(ev)/2)):].mean(axis=1)
                assert np.isclose(np.var(draw,ddof=1),r['bootstrap_best_half_variance'],atol=1e-12);checked_bootstrap+=1
        lines += [f'## {o["player_name"]} at the end of {o["origin_year"]}','',
            f'Selection: {", ".join(c["selection"])}. Minimum refined profile people: {o["minimum_profile_people"]}. Exact fallback: {c["exact_fallback"]}.', '',manual[rid],'',
            '| Forecast | Batting rate | Expected contribution |','| --- | ---: | ---: |']
        for arm in ['combined','old_joint','precision_coverage','precision_measurements']:
            lines.append(f'| {arm} | {o[arm+"_rate"]:+.4f} | {o[arm+"_value"]:+.4f} |')
        rate='Unobserved' if not o['next_pa'] else f'{o["actual_future_relative_rate"]:+.4f}'
        lines += [f'| Actual | {rate} | {o["next_value"]:+.4f} |','',
            f'Expected PA {o["preseason_pa"]:.1f}; actual PA {o["next_pa"]}. No zero-PA rate is fitted or scored.', '',
            '| Known season | Level | PA | HR | K | Unintentional BB |','| --- | --- | ---: | ---: | ---: | ---: |']
        for r in c['source_history']:
            lines.append(f'| {r["season"]} | {r["level_group"]} | {r["plate_appearances"]} | {r["home_runs"]} | {r["strike_outs"]} | {r["unintentional_walks"]} |')
        lines += ['', '| Origin selected peer | Age | Weighted recent AAA PA | Expected PA | Actual PA | Base rate | Adjusted rate |',
            '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
        for p in c['peers']:
            if p['next_pa']==0:assert p['actual_future_relative_rate'] is None
            assert all(x['season']<=o['origin_year'] for x in p['dated_production'])
            lines.append(f'| {p["player_name"]} | {p["age"]:.1f} | {p["pooled_AAA_pa"]:.1f} | {p["preseason_pa"]:.1f} | {p["next_pa"]} | {p["combined_rate"]:+.3f} | {p["precision_measurements_rate"]:+.3f} |')
        lines += ['', '| Largest fitted adjustment terms | Actual input | Coefficient | Signed term |','| --- | ---: | ---: | ---: |']
        for t in sorted(c['saved_traces'].get('precision_measurements',{}).get('all_terms',[]),key=lambda t:abs(t['signed_term']),reverse=True)[:6]:
            lines.append(f'| {t["feature"]} | {t["input"]:+.5f} | {t["coefficient"]:+.5f} | {t["signed_term"]:+.5f} |')
        lines += ['', 'All inputs, source/noise references, sample shares, fitted terms, actual next-year history and peer dated production are preserved in reviewed-cases.json. Signed terms are conditional model mechanics, not causal attribution.', '']
    dest=prep.ROOT/'reports/model-evidence/hitter-minor-statcast-precision';dest.mkdir(parents=True,exist_ok=True)
    walk=dest/'player-walkthrough.md';assert not walk.exists();walk.write_text('\n'.join(lines),encoding='utf8',newline='\n')
    cases['player_walkthrough_status']='complete';prep.write('reviewed-cases.json',cases)
    tests=subprocess.run([sys.executable,'-X','utf8','-m','pytest','-p','no:cacheprovider','tests/test_hitter_minor_precision.py',
        'tests/test_hitter_minor_precision_review.py','tests/test_hitter_minor_statcast_forecast.py','tests/test_hitter_minor_statcast_source.py',
        'tests/test_hitter_minor_statcast_review.py','tests/test_hitter_statcast_next_year.py','tests/test_hitter_statcast_measurement.py',
        'tests/test_hitter_statcast_history.py','tests/test_mlb_contact_history.py','-q'],cwd=prep.ROOT,check=True,capture_output=True,text=True)
    freeze=subprocess.run([sys.executable,'-X','utf8','scripts/verify_hitter_full_2026_freeze.py'],cwd=prep.ROOT,check=True,capture_output=True,text=True)
    doc=prep.ROOT/'docs/hitter-minor-statcast-precision-result.md';assert doc.exists()
    paths=[out/n for n in ['preflight.json','fit-report.json','scores.json','cases.json','reviewed-cases.json','scored-predictions.parquet',
        'annual-contact-noise.parquet','score-development-error.json']]+[doc,walk,Path(__file__),prep.ROOT/'config/hitter_minor_precision_review.json',
        prep.ROOT/'tests/test_hitter_minor_precision_review.py']
    prep.write('final-review.json',dict(execution_integrity=True,independently_reconstructed_rate_and_value_labels=True,
        endpoint_scores_independently_verified=verified,saved_adjustment_heads_replayed=replays,base_test_cells_replayed=35,
        playing_time_unchanged=True,forecasts=30506,eligible_forecasts=3116,exact_fallbacks=len(fallback),
        player_walkthrough_status='complete',case_origins=18,sort_oracle_bootstraps_verified=checked_bootstrap,
        precision_mechanism_repaired=True,incremental_measurement_gain_established=False,
        coherent_for_full_population=False,full_profile_validation=False,training_residuals_cross_fitted=False,
        reasonability='tiny-sample dominance removed; negative IL associations and base opportunity/talent misses remain',
        disposition='retain precision representation and evidence; do not promote fixed measurement adjustment',
        protected_outcomes_used=False,deployment_approved=False,provider_original_vintage_known=False,
        focused_tests=tests.stdout,protected_freeze=json.loads(freeze.stdout),
        artifact_hashes={str(p):sha256_file(p) for p in paths}))
    pack=[out/n for n in ['annual-contact-noise.parquet','scores.json','reviewed-cases.json','final-review.json','ranges.json','score-development-error.json','support.parquet']]
    pack+=list(out.glob('noise-reference-*.json'))+list(out.glob('*.joblib'))
    for p in pack:
        target=dest/p.name;assert not target.exists();shutil.copyfile(p,target)
    compact=[n for n in q.columns if n in ['row_id','player_id','player_name','origin_year','target_year','outer_fold','prior_debut','stage',
        'preseason_pa','next_pa','next_value','actual_future_relative_rate','msc_eligible','msc_own_ev_n','minimum_profile_people'] or
        n in [a+'_'+k for a in ['preseason','ridge_measurements','combined','old_joint','precision_coverage','precision_measurements'] for k in ['rate','value']]]
    p=dest/'scored-predictions-compact.parquet';assert not p.exists();q.select(compact).write_parquet(p)
    assert pl.read_parquet(p).equals(q.select(compact))
    # Existing committed identity sets plus these references reproduce the full preflight.
    summary={k:v for k,v in pre.items() if k!='cells'}
    summary['full_preflight_sha256']=sha256_file(out/'preflight.json');summary['full_preflight_local_path']=str(out/'preflight.json')
    summary['cells']=[{k:v for k,v in c.items() if k not in ['training_row_ids','test_row_ids']} |
        dict(identity_cell_reference=str(prep.old.OUT/'preflight.json'),training_rows=len(c['training_row_ids']),test_rows=len(c['test_row_ids'])) for c in pre['cells']]
    (dest/'preflight-compact.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8',newline='\n')
    manifest=dict(evidence_hashes={str(p):sha256_file(p) for p in dest.iterdir() if p.is_file()},
        full_feature_frames_retained_locally={str(out/f'features-{k}.parquet'):sha256_file(out/f'features-{k}.parquet') for k in range(5)},
        full_predictions_retained_locally={str(out/'scored-predictions.parquet'):sha256_file(out/'scored-predictions.parquet')})
    (dest/'evidence-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8',newline='\n')
    print('Review complete:',verified,'endpoint scores, 20 heads, 35 base cells,',checked_bootstrap,'independent bootstraps.',flush=True)
    print(tests.stdout,flush=True)


if __name__=='__main__':main()
