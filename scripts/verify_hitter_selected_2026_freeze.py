"""Read-only verification of the new, self-contained forecast replay package."""
from pathlib import Path
import json
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'model_artifacts/hitter-selected-2026-frozen-2026-10-05'
POOLED_PRIORS={'K':.23,'BB':.08,'HBP':.01,'HR':.03,'BABIP':.30,'2B':.05,'3B':.005}


def main():
    path=PACKAGE/'freeze-manifest.json'
    assert sha256_file(path)==(PACKAGE/'freeze-manifest.sha256').read_text().strip(),'Changed manifest'
    manifest=json.loads(path.read_text(encoding='utf8'))
    for f in manifest['files']:assert sha256_file(PACKAGE/f['path'])==f['sha256'],f['path']
    assert not manifest['protected_outcomes_used_before_freeze'] and manifest['population']==4030
    all_ids=[];replayed=0
    with threadpool_limits(limits=2):
        for fold in range(5):
            q=pl.read_parquet(PACKAGE/f'forecast-{fold}.parquet');all_ids.extend(q['player_id'].to_list())
            for h in [h for h in manifest['models'] if h['fold']==fold]:
                model=joblib.load(PACKAGE/h['path']);cols=[]
                for c in h['features']:
                    v=q[c].to_numpy().astype(float)
                    if h['head'].startswith('rate'):
                        if c=='career_mlb_observed_pa':v=v/6000
                        elif c.endswith('_pa'):v=v/600
                        elif c=='last_stat_gap':v=v/5
                        elif c.startswith('pooled_') and c.rsplit('_',1)[-1] in POOLED_PRIORS:v=(v-POOLED_PRIORS[c.rsplit('_',1)[-1]])/.1
                    cols.append(v)
                x=np.column_stack(cols)
                pred=model.predict_proba(x)[:,1] if h['head']=='participation' else model.predict(x)
                assert np.allclose(pred,q['raw_'+h['head']],atol=1e-10,rtol=0),h['head'];replayed+=1
            p=np.where(q['reported_retired'].to_numpy()|q['hard_unavailable'].to_numpy(),0.,q['raw_participation'].to_numpy())
            cond=np.clip(q['raw_conditional_pa'].to_numpy(),1,800);pa=p*cond
            rate=np.where(q['prior_debut'].to_numpy()==0,q['raw_rate_prospect'],np.where(q['sc_tracked'],q['raw_rate_tracking'],q['raw_rate_numeric']))
            value=pa*(rate/600+manifest['targets']['origin_replacement_reference'])
            for name,v in [('participation_probability',p),('conditional_pa',cond),('expected_pa',pa),('hitting_wins_per_600',rate),('batting_contribution',value)]:
                assert np.allclose(v,q[name],atol=1e-10,rtol=0),name
    assert len(all_ids)==len(set(all_ids))==4030 and replayed==25
    print(json.dumps(dict(status='verified',files=len(manifest['files']),players=4030,heads_replayed=25,
        manifest_sha256=sha256_file(path),protected_outcomes_read=False,predictive_accuracy_not_yet_evaluated=True)),flush=True)


if __name__=='__main__':main()
