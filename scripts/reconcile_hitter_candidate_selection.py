"""Verify compatibility of completed candidates; no refits or new selection tuning."""
import json
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from universal_baseball.mlb_event_logit import VALUES,EVENTS
from universal_baseball.hitter_compatible_value import UNIT
from prepare_practical_hitter_v33 import safe_matrix
import evaluate_hitter_talent_bridge_v74 as bridge
import test_hitter_positive_workload_capacity as capacity

ROOT=bridge.ROOT;OUT=ROOT/'reports/model-evidence/hitter-candidate-selection'


def main():
    sources=[capacity.OUT/'final-report.json',bridge.OUT/'report.json']
    receipts=[json.loads(path.read_text(encoding='utf8')) for path in sources]
    assert all(r['player_walkthrough_status']=='complete' for r in receipts)
    verified=0
    for report in receipts:
        for key in ['input_hashes','output_hashes','evidence_hashes','local_fit_hashes']:
            for path,expected in report.get(key,{}).items():
                assert sha256_file(Path(path))==expected,path;verified+=1
    current=pl.read_parquet(bridge.previous.OUT/'scored-predictions.parquet').sort('row_id')
    source=pl.read_parquet(bridge.previous.OUT/'features.parquet').sort('row_id')
    old=pl.read_parquet(bridge.OUT/'scored-predictions.parquet').sort('row_id')
    assert len(current)==len(old)==30506 and old.select(current.columns).equals(current)
    # The inherited baseline_pa/value still name the older pre-ranking model.
    # Only baseline_rate was deliberately unchanged when opportunity was updated.
    assert old['baseline_rate'].equals(current['preseason_rate'])
    assert old['next_value'].equals(current['next_value'])
    pre=json.loads((bridge.OUT/'preflight.json').read_text(encoding='utf8'));replays=0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            f=pl.read_parquet(bridge.OUT/f"features-{c['fold']}.parquet")
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            q=old.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert te['row_id'].equals(q['row_id'])
            model=joblib.load(bridge.OUT/f"translated_ridge-{c['year']}-{c['fold']}.joblib")
            raw=model.predict(safe_matrix(te,pre['features']['translated_ridge']))
            assert np.allclose(raw,q['translated_ridge_all_rate'],atol=1e-10,rtol=0)
            primary=np.where(q['prior_debut'].to_numpy()==0,raw,q['baseline_rate'].to_numpy())
            assert np.allclose(primary,q['translated_ridge_rate'],atol=1e-10,rtol=0);replays+=1
    established=old.filter(pl.col('prior_debut')==1)
    assert established['translated_ridge_rate'].equals(established['baseline_rate'])
    pa=old['preseason_pa'].to_numpy();rate=old['translated_ridge_rate'].to_numpy()
    value=pa*(rate/600+old['origin_replacement_rate'].to_numpy())
    assert np.allclose(value,old['translated_ridge_value'],atol=1e-10,rtol=0)
    assert old['translated_ridge_pa'].equals(current['preseason_pa'])
    joined=old.select('row_id','next_pa',*['count_'+e for e in EVENTS],*['target_env_'+e for e in EVENTS]).join(
        source.select('row_id',pl.col('next_batting_rate').alias('contract_rate')),on='row_id',validate='1:1').sort('row_id')
    counts=joined.select(['count_'+e for e in EVENTS]).to_numpy();n=joined['next_pa'].to_numpy();active=n>0
    actual=np.zeros(len(n));env=joined.select(['target_env_'+e for e in EVENTS]).to_numpy()@VALUES
    actual[active]=UNIT*(counts[active]@VALUES/n[active]-env[active])
    assert np.array_equal(counts.sum(1),n) and np.allclose(actual,joined['contract_rate'],atol=1e-10,rtol=0)
    scores=json.loads((bridge.OUT/'scores-contract.json').read_text(encoding='utf8'))
    focal=[]
    for pid,year in [(701762,2024),(694671,2023),(624413,2018),(677594,2021),(702616,2023),(592450,2024)]:
        q=old.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==year));assert len(q)==1
        row=q.row(0,named=True);label=joined.filter(pl.col('row_id')==row['row_id'])['contract_rate'][0]
        focal.append({k:row[k] for k in ['row_id','player_name','origin_year','target_year','preseason_pa','next_pa','preseason_rate','translated_ridge_rate','preseason_value','translated_ridge_value','next_value']}
            |dict(actual_target_relative_rate=float(label) if row['next_pa'] else None))
    paths=sources+[Path(__file__),bridge.OUT/'scores-contract.json',bridge.OUT/'preflight.json',bridge.OUT/'scored-predictions.parquet',
        bridge.previous.OUT/'features.parquet',bridge.previous.OUT/'scored-predictions.parquet',
        ROOT/'docs/hitter-talent-bridge-v74-result.md',ROOT/'reports/model-evidence/hitter-talent-bridge-v74/player-walkthrough.md']
    paths.extend([ROOT/'src/universal_baseball/hitter_compatible_value.py',ROOT/'src/universal_baseball/mlb_event_logit.py',
        ROOT/'scripts/prepare_practical_hitter_v33.py'])
    report=dict(new_fits=0,new_experiments=0,verified_prior_hashes=verified,existing_translated_heads_replayed=replays,
        evaluation_rows=len(old),current_columns_exact=True,opportunity_exact=True,established_hitting_exact=True,
        corrected_rate_labels_independently_reconstructed=True,prior_player_reviews_complete=True,
        shortlist='Current coherent baseline; existing translated linear prospect alternative retained as a component candidate, not a deployed whole-model winner.',
        field_mapping=dict(current_workload='preseason_pa',current_rate='preseason_rate',current_value='preseason_value',
            legacy_baseline_PA_and_value='Older V53/V63 opportunity, not the current V68 anchor; do not compare against these inherited columns.'),
        blocked_repeats=['team_record','closed_conditional_workload_capacity'],cases=focal,
        inherited_corrected_scores=[s for s in scores if s['scope'] in ['all','never_debut','public']],
        current_candidate_changed=False,protected_outcomes_used=False,deployment_approved=False,
        source_hashes={str(p):sha256_file(p) for p in paths})
    OUT.mkdir(parents=True,exist_ok=True);target=OUT/'compatibility.json';assert not target.exists()
    target.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')
    print('No new fits; completed talent alternative matches current identities, labels, workload and established forecasts.',flush=True)
    print('Verified prior hashes:',verified,'replayed translated heads:',replays,flush=True)
    for case in focal:print(case,flush=True)


if __name__=='__main__':main()
