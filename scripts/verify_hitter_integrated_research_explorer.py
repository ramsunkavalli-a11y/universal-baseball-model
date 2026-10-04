"""Check all rows, exact displayed inputs, labels and matched cohort losses."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import polars as pl
from universal_baseball.hitter_research_export import ARMS, branch
from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.mlb_event_logit import EVENTS, VALUES
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
import build_hitter_integrated_research_explorer as b
from review_hitter_minor_statcast_next_year import scope, independent


def main():
    assert not (b.OUT/'verification.json').exists(),'Preserve prior verification'
    receipt=b.prep.read(b.OUT/'build-report.json')
    b.prep.old.verify_hashes(receipt['source_hashes'])
    for p,h in receipt['output_hashes'].items():assert sha256_file(b.DIST/p)==h,p
    meta=b.prep.read(b.DIST/'metadata.json');heads=b.prep.read(b.DIST/'heads.json')
    q=pl.read_parquet(b.prep.OUT/'scored-predictions.parquet').sort('row_id')
    expected={r['row_id']:r for r in q.iter_rows(named=True)};exported={};histories={};launch={}
    for year in meta['target_years']:
        z=b.prep.read(b.DIST/f'years/{year}.json')
        for r in z['rows']:
            assert r['row_id'] not in exported and r['target_year']==year==r['origin_year']+1<=2025
            source=expected[r['row_id']]
            assert r['branch']==branch(source)
            for key,col in [('pa','preseason_pa'),('p','preseason_p'),('conditional_pa','preseason_conditional_pa'),
                ('next_pa','next_pa'),('next_value','next_value'),('raw_p','preseason_raw_p'),
                ('raw_conditional_pa','preseason_raw_conditional_pa')]:assert r[key]==source[col]
            for arm in ARMS:
                assert r['rates'][arm]==source[arm+'_rate'] and r['values'][arm]==source[arm+'_value']
            assert r['next_rate']==(source['actual_future_relative_rate'] if source['next_pa']>0 else None)
            assert r['public_match']==bool(source['pa_0']>0 and source['steamer_index'] is not None and source['zips_index'] is not None)
            own=z['history'][str(r['player_id'])];own_launch=z['launch'][str(r['player_id'])]
            assert all(year-3<=h[0]<year for h in own)
            assert all(year-3<=h['season']<year for h in own_launch)
            exported[r['row_id']]=r;histories[r['row_id']]=own;launch[r['row_id']]=own_launch
    assert set(exported)==set(expected) and len(exported)==30506
    counts=q.select(['count_'+e for e in EVENTS]).to_numpy();n=q['next_pa'].to_numpy();active=n>0
    assert np.array_equal(counts.sum(1),n)
    index=counts@VALUES
    future=UNIT*(index[active]/n[active]-q.select(['target_env_'+e for e in EVENTS]).to_numpy()[active]@VALUES)
    assert np.allclose(future,q.filter(pl.col('next_pa')>0)['actual_future_relative_rate'],atol=1e-10,rtol=0)
    common=np.zeros(len(q));common[active]=UNIT*(index[active]/n[active]-q.select(['origin_env_'+e for e in EVENTS]).to_numpy()[active]@VALUES)
    assert np.allclose(n*(common/600+q['origin_replacement_rate'].to_numpy()),q['next_value'],atol=1e-10,rtol=0)
    pre=b.prep.read(b.prep.OUT/'preflight.json');pf=b.previous.e.old.context();exact_inputs=0;derived_predictions=0
    for fold in range(5):
        f=pl.read_parquet(b.prep.OUT/f'features-{fold}.parquet')
        for c in [c for c in pre['cells'] if c['fold']==fold]:
            _,te,_=b.prep.routed(f,c);key=f'{c["year"]}-{fold}'
            detail=b.prep.read(b.DIST/f'cells/{key}.json')['rows'];h=heads[key]
            assert set(map(int,detail))==set(te['row_id'])
            px=pf.filter(pl.col('row_id').is_in(te['row_id'].to_list())).sort('row_id').select(meta['opportunity_features']).to_numpy()
            xs={name:safe_matrix(te,head['features']) for name,head in h['rate'].items()}
            ax={name:safe_matrix(te,head['features']) for name,head in h['adjustments'].items()}
            for i,r in enumerate(te.iter_rows(named=True)):
                rid=r['row_id'];z=detail[str(rid)];o=exported[rid];head=h['rate'][o['branch']]
                assert np.array_equal(z['rate_inputs'],xs[o['branch']][i])
                assert np.array_equal(z['opportunity_inputs'],px[i])
                predicted=head['intercept']+np.dot(z['rate_inputs'],head['coefficients'])
                assert np.isclose(predicted,o['rates']['combined'],atol=1e-10,rtol=0)
                for arm,x in ax.items():
                    ah=h['adjustments'][arm];inputs=z['adjustment_inputs'][arm]
                    assert np.array_equal(inputs,x[i])
                    update=ah['intercept']+np.dot(inputs,ah['coefficients']) if o['minor_comparison_enabled'] else 0.
                    assert np.isclose(predicted+update,o['rates'][arm],atol=1e-10,rtol=0)
                exact_inputs+=1;derived_predictions+=1+len(ax)
    scores=b.prep.read(b.prep.OUT/'scores.json');checked=0
    for s in scores['scopes']:
        g=scope(q,s['scope'])
        for kind,key in [('rate','participant_rate'),('value','contribution')]:
            for arm in ARMS:
                r=(s[key] or {}).get(arm)
                if r is not None:
                    assert np.allclose(independent(g,arm,kind),[r['mse'],r['mae'],r['bias']],atol=1e-12,rtol=0)
                    checked+=1
    # Representative display walks span every selected branch and an unseen future rate.
    selected=[('Aaron Judge',2024),('Nick Kurtz',2024),('Brandon Belt',2023),('Bo Bichette',2024),
              ('Junior Caminero',2024),('Steven Kwan',2021),('Juneiker Caceres',2024),('Eric Thames',2016)]
    walks=[]
    for name,origin in selected:
        found=q.filter((pl.col('player_name')==name)&(pl.col('origin_year')==origin))
        assert len(found)==1,(name,origin)
        rid=found['row_id'][0];o=exported[rid]
        walks.append(dict(row=o,origin_source_history=histories[rid],origin_launch_history=launch[rid],
            exact_inputs_and_selected_fit_verified=True,review_path=f'reviews/{rid}.json' if o['reviewed'] else None))
    b.write(b.OUT/'display-player-walks.json',dict(cases=walks,selection='Fixed origin cases covering MLB, debut prospect, non-arrival, precision defect and breakout miss; not new validation.'))
    freeze=subprocess.run([sys.executable,'-X','utf8','scripts/verify_hitter_full_2026_freeze.py'],cwd=b.ROOT,check=True,capture_output=True,text=True)
    test=subprocess.run([sys.executable,'-X','utf8','-m','pytest','-p','no:cacheprovider','tests/test_hitter_research_export.py','-q'],cwd=b.ROOT,check=True,capture_output=True,text=True)
    b.write(b.OUT/'verification.json',dict(export_verification_status='complete',all_exported_rows_checked=30506,
        exact_rate_and_opportunity_inputs_checked=exact_inputs,displayed_linear_predictions_checked=derived_predictions,
        independent_endpoint_components=checked,outcome_labels_reconstructed=True,nonarrival_rates_null=True,
        fixed_player_display_walks=len(walks),new_models_fitted=0,protected_freeze=json.loads(freeze.stdout),
        tests=test.stdout,browser_verification_status='pending',deployment_approved=False,full_goal_complete=False,
        source_hashes={str(b.OUT/'build-report.json'):sha256_file(b.OUT/'build-report.json'),str(Path(__file__)):sha256_file(Path(__file__))},
        player_walks_sha256=sha256_file(b.OUT/'display-player-walks.json')))
    print('Verified all exported rows, exact inputs, reconstructed labels and',checked,'endpoint components.',flush=True)


if __name__=='__main__':main()
