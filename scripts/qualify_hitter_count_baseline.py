"""Production-matched origin-only peers and independent score equations; no fits."""
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
from run_hitter_count_baseline import OUT,ROOT,FEATURES,read,save,verify


def main():
    assert not (OUT/'review-qualification.json').exists()
    receipt=read(OUT/'review-receipt.json');verify(receipt['hashes'])
    refs=read(OUT/'reference-review.json');verify(refs['hashes'])
    pre=read(OUT/'preflight.json');walks=read(OUT/'player-walks.json')['cases'];frames={k:pl.read_parquet(OUT/f'features-{k}.parquet') for k in range(5)}
    q=pl.read_parquet(OUT/'predictions.parquet');g=q.filter(~pl.col('source_addition'));scores=read(OUT/'scores.json')
    allscore=next(s for s in scores['scopes'] if s['scope']=='all');checks=0
    # Independent per-origin equations, not imported score functions.
    for arm in ['current','count']:
        rmse=[];mae=[];bias=[];rate=[]
        for y in sorted(g['origin_year'].unique()):
            h=g.filter(pl.col('origin_year')==y);d=(h[arm+'_value']-h['actual_relative_value']).to_numpy()
            rmse.append(np.mean(d*d));mae.append(np.mean(abs(d)));bias.append(np.mean(d))
            active=h.filter(pl.col('next_pa')>0);d=(active[arm+'_rate']-active['actual_relative_rate']).to_numpy()
            rate.append(np.sum(active['next_pa'].to_numpy()*d*d)/active['next_pa'].sum())
        a=allscore['scores'][arm]
        for key,v in [('value_rmse',np.sqrt(np.mean(rmse))),('value_mae',np.mean(mae)),('value_bias',np.mean(bias)),('rate_rmse',np.sqrt(np.mean(rate)))]:
            assert np.isclose(a[key],v,atol=1e-12);checks+=1
    supplement=[]
    for c in walks:
        rid=c['row_id'];o=c['forecast'];y,k=o['origin_year'],o['outer_fold'];f=frames[k];one=f.filter(pl.col('row_id')==rid).row(0,named=True)
        cell=next(a for a in pre['cells'] if a['year']==y and a['fold']==k);tr=f.filter(pl.col('row_id').is_in(cell['training_row_ids']))
        pool=tr.filter((pl.col('prior_debut')==one['prior_debut'])&(pl.col('stage')==one['stage']))
        if one['count_NPB_share']+one['count_KBO_share']>0:
            pool=pool.filter(((pl.col('count_NPB_share')>0)==(one['count_NPB_share']>0))&((pl.col('count_KBO_share')>0)==(one['count_KBO_share']>0)))
        diff=pl.sum_horizontal([(pl.col(n)-one[n])**2 for n in FEATURES[:8]]).sqrt()
        pool=pool.with_columns((diff+(pl.col('age')-one['age']).abs()/5+(pl.col('pa_0')-one['pa_0']).abs()/600+
            (pl.col('draft_rank')-one['draft_rank']).abs()+(pl.col('scout_rank_score_0')-one['scout_rank_score_0']).abs()).alias('origin_production_distance'))
        peers=pool.sort('origin_production_distance','player_id','origin_year').unique('player_id',maintain_order=True).head(3)
        names=['row_id','player_id','player_name','origin_year','age','pa_0','minor_pa_0','next_pa','actual_relative_rate','origin_production_distance',*FEATURES]
        learner=[]
        for league in ['NPB','KBO']:
            h=tr.filter(pl.col(f'count_{league}_share')>0);a=h.filter(pl.col('next_pa')>0)
            learner.append(dict(league=league,full_people=h['player_id'].n_unique(),active_people=a['player_id'].n_unique(),active_rows=a.height,
                active_future_PA=int(a['next_pa'].sum()),never_debut_active_people=a.filter(pl.col('prior_debut')==0)['player_id'].n_unique()))
        # CLR baseline coordinates include a fixed unit offset plus learned calibration.
        names_model=pre['arms'][c['branch']]
        import joblib
        m=joblib.load(OUT/f'{c["branch"]}-rate-{y}-{k}.joblib');beta=m['beta']
        profile_logit=np.asarray([t['effects'] for t in c['feature_logit_terms'] if t['feature'] in FEATURES[:8]]).sum(0)
        supplement.append(dict(row_id=rid,player_name=o['player_name'],origin_year=y,
            origin_production_selected_comparisons=peers.select(names).to_dicts(),foreign_learner_support=learner,
            profile_calibration_logit=profile_logit.tolist(),
            HR_vs_other_profile_slope=float(1+beta[names_model.index('count_past_HR')+1,7]-beta[names_model.index('count_past_HR')+1,0]),
            clarification='The fixed past offset is also present; coefficients alone omit it. Production peers are selected before inspecting outcomes. Same-stage demographic peers in the original walk are not talent matches.'))
    save('review-qualification.json',dict(independent_all_score_checks=checks,
        foreign_references_independently_reconstructed=refs['past_foreign_references_reconstructed'],cases=supplement,
        hashes={str(p):sha256_file(p) for p in [__import__('pathlib').Path(__file__),OUT/'review-receipt.json',OUT/'reference-review.json']},
        deployment_approved=False,protected_outcomes_used=False))
    print(f'{checks} independent primary score equations checked; production-matched peers and actual foreign learner support saved.')


if __name__=='__main__':main()
