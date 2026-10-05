"""One fixed complete comparison, with all subsets checked before fitting."""
import sys
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.mlb_event_logit import VALUES
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights
from prepare_hitter_overseas_integration import OUT,ANCHOR,read,write,verify


def rate_weights(sub):
    years=sub['origin_year'].to_numpy();raw=np.minimum(sub['next_pa'].to_numpy(),300).astype(float)
    for y in np.unique(years):raw[years==y]/=raw[years==y].sum()
    return raw*len(sub)/len(np.unique(years))


def main():
    pre=read(OUT/'preflight.json');verify(pre['source_hashes'])
    assert pre['before_fitting'] and pre['checks_before_fits']==210
    seal={'runner_sha256':sha256_file(Path(__file__)),'preflight_sha256':sha256_file(OUT/'preflight.json')}
    if (OUT/'fit-seal.json').exists():assert read(OUT/'fit-seal.json')==seal
    else:write('fit-seal.json',seal)
    assert not (OUT/'fit-report.json').exists(),'Completed comparison is not rerun'
    anchor=pl.read_parquet(ANCHOR).select('row_id',pl.col('preseason_p').alias('current_p'),
        pl.col('preseason_conditional_pa').alias('current_conditional_pa'),pl.col('preseason_pa').alias('current_pa'),
        pl.col('combined_rate').alias('current_rate'),pl.col('combined_value').alias('current_value'))
    fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];pp=OUT/f'forecast-{y}-{k}.parquet'
            if pp.exists():
                note=read(OUT/f'fit-{y}-{k}.json');verify(note['hashes']);fits.append(note);continue
            f=pl.read_parquet(OUT/f'features-{y}-{k}.parquet')
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id');active=tr.filter(pl.col('next_pa')>0)
            q=te.select('row_id','player_id','player_name','origin_year','target_year','horizon','outer_fold','stage',
                'source_addition','age','pa_0','prior_debut',pl.col('integration_replacement_rate').alias('origin_replacement_rate'),'actual_relative_rate','actual_relative_value','next_pa','ctx_information_date',
                'status_hard_unavailable','status_retired').join(anchor,on='row_id',how='left',validate='1:1')
            heads=[];hashes={}
            for arm,features in pre['arms'].items():
                raw={}
                for head,sub in [('participation',tr),('conditional_pa',active),('rate',active)]:
                    if head=='rate':
                        m=make_pipeline(StandardScaler(),Ridge(alpha=pre['ridge_alpha']))
                        target='actual_relative_rate';sw=rate_weights(sub);kw={'ridge__sample_weight':sw}
                    else:
                        cls=HistGradientBoostingClassifier if head=='participation' else HistGradientBoostingRegressor
                        m=cls(**pre['settings']);target='next_active' if head=='participation' else 'next_pa';kw={'sample_weight':weights(sub)}
                    m.fit(sub.select(features).to_numpy(),sub[target].to_numpy(),**kw)
                    x=te.select(features).to_numpy();raw[head]=m.predict_proba(x)[:,1] if head=='participation' else m.predict(x)
                    assert np.isfinite(raw[head]).all()
                    path=OUT/f'{arm}-{head}-{y}-{k}.joblib';joblib.dump(m,path,compress=3);hashes[str(path)]=sha256_file(path)
                    heads.append(dict(arm=arm,head=head,path=str(path),sha256=hashes[str(path)],features=features,target=target,
                        training_rows=sub.height,training_players=sub['player_id'].n_unique(),maximum_target_year=int(sub['target_year'].max())))
                p=raw['participation'].copy();p[(te['status_hard_unavailable'].to_numpy()>0)|(te['status_retired'].to_numpy()>0)]=0
                cond=np.clip(raw['conditional_pa'],1,800)
                low=(VALUES.min()-te['origin_event_index'].to_numpy())*UNIT;high=(VALUES.max()-te['origin_event_index'].to_numpy())*UNIT
                rate=np.clip(raw['rate'],low,high);pa=p*cond;rep=te['integration_replacement_rate'].to_numpy()
                q=q.with_columns(pl.Series(arm+'_raw_p',raw['participation']),pl.Series(arm+'_p',p),
                    pl.Series(arm+'_raw_conditional_pa',raw['conditional_pa']),pl.Series(arm+'_conditional_pa',cond),
                    pl.Series(arm+'_raw_rate',raw['rate']),pl.Series(arm+'_rate',rate),pl.Series(arm+'_pa',pa),
                    pl.Series(arm+'_value',pa*(rate/600+rep)))
                q=q.with_columns((pl.col(arm+'_pa')*(pl.col('current_rate')/600+pl.col('origin_replacement_rate'))).alias(arm+'_workload_only_value'),
                    (pl.col('current_pa')*(pl.col(arm+'_rate')/600+pl.col('origin_replacement_rate'))).alias(arm+'_talent_only_value'))
                print(f'Saved heads {y}/{k}: {arm}.',flush=True)
            q.write_parquet(pp);hashes[str(pp)]=sha256_file(pp)
            note=dict(year=y,fold=k,heads=heads,hashes=hashes);write(f'fit-{y}-{k}.json',note);fits.append(note)
    q=pl.concat([pl.read_parquet(OUT/f'forecast-{c["year"]}-{c["fold"]}.parquet') for c in pre['cells']]).sort('row_id')
    assert q.height==pre['original_evaluation_rows']+pre['addition_evaluation_rows']
    assert q.filter(~pl.col('source_addition'))['row_id'].equals(anchor.sort('row_id')['row_id'])
    q.write_parquet(OUT/'predictions.parquet')
    write('fit-report.json',dict(cells=fits,new_heads=210,rows=q.height,output_sha256=sha256_file(OUT/'predictions.parquet'),
        player_walkthrough_status='pending',protected_outcomes_used=False,deployment_approved=False))


if __name__=='__main__':main()
