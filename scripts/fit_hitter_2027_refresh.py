"""Fixed year-refresh, all-head preflight before fitting, no new tuning."""
from pathlib import Path
import json
import hashlib
import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingClassifier,HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from universal_baseball.hitter_translation_reliability import reliable_translation
from universal_baseball.storage import sha256_file
from prepare_hitter_production_2026 import profile
from prepare_practical_hitter_v33 import safe_matrix
from fit_practical_hitter_v31 import weights
from assemble_hitter_2027_base import ROOT,OUT as SOURCE,PUBLIC
from capture_hitter_2027_origin_counts import write_once

OUT=ROOT/'reports/generated/hitter-2027-batting-refresh'
META=['row_id','player_id','origin_year','target_year','outer_fold','horizon','window_complete','stage','prior_debut','age',
      'elapsed','current_state','regular_window','quality_0','source_position','career_mlb_observed_pa','pa_0','minor_pa_0']
LABELS=['next_pa','next_value','next_active','next_batting_rate']


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assert not (PUBLIC/'batting-refresh-fit.json').exists()
    oldpre=json.loads((ROOT/'model_artifacts/hitter-selected-2026-production/preflight.json').read_text())
    names=oldpre['features'];settings=oldpre['histogram_settings']
    inputs=[Path(__file__),ROOT/'docs/hitter-2027-production-refresh.md']
    for name in ['base-input-player-review.json','availability-assembly.json','tracking-2026-final-review.json']:
        path=PUBLIC/name;r=json.loads(path.read_text());inputs.append(path)
        for p,h in r.get('output_hashes',{}).items():assert sha256_file(Path(p))==h,p
    def read(path):
        inputs.append(path);return pl.read_parquet(path)
    modern=read(ROOT/'reports/generated/hitter-preseason-readiness-v68/features.parquet')
    tracking=read(ROOT/'reports/generated/hitter-statcast-next-year/features.parquet')
    status=read(SOURCE/'availability.parquet')
    values=read(SOURCE/'values.parquet').filter(pl.col('season')==2026)
    rep=570*values['schedule_fraction'][0]/values['league_pa'][0]
    lab=values.select('player_id',pl.col('mlb_pa').alias('next_pa'),pl.col('component_war').alias('next_value')).with_columns(
        (600*(pl.col('next_value')-rep*pl.col('next_pa'))/pl.col('next_pa')).alias('next_batting_rate'),
        pl.lit(1).alias('next_active'))
    def frames(fold):
        old=pl.read_parquet(ROOT/f'reports/generated/hitter-translation-inputs-2025/forecast-inputs-{fold}.parquet')
        assert len(old)==4030 and old['player_id'].n_unique()==4030 and not any(c.startswith('next_') for c in old.columns)
        old=old.join(lab,on='player_id',how='left',validate='1:1').with_columns(pl.col(LABELS).fill_null(0))
        assert old['next_active'].sum()==655 and old['next_pa'].sum()==182453
        tr=modern.filter((pl.col('target_year')<=2025)&(pl.col('target_year')!=2020)&(pl.col('outer_fold')!=fold)&pl.col('window_complete'))
        active=tr.filter(pl.col('next_pa')>0)
        transit=pl.read_parquet(ROOT/f'reports/generated/hitter-talent-bridge-v74/features-{fold}.parquet')
        histories=dict(participation=tr,conditional_pa=active,rate_numeric=active,
            rate_tracking=tracking.filter(pl.col('row_id').is_in(active['row_id'])),
            rate_prospect=transit.filter(pl.col('row_id').is_in(active['row_id'])))
        result={}
        for head,cols in names.items():
            hist=histories[head];fresh=old.filter(pl.col('outer_fold')!=fold)
            if head!='participation':fresh=fresh.filter(pl.col('next_pa')>0)
            if head=='rate_prospect':hist=reliable_translation(hist);fresh=reliable_translation(fresh)
            use=list(dict.fromkeys(META+LABELS+cols))
            result[head]=pl.concat([hist.select(use),fresh.select(use)],how='vertical_relaxed').sort('row_id')
        q=pl.read_parquet(SOURCE/f'translation-{fold}.parquet').filter(pl.col('outer_fold')==fold).join(status.drop('player_id'),on='row_id',validate='1:1').sort('row_id')
        return result,q
    supports=[];cells=[]
    for fold in range(5):
        inputs.extend([ROOT/f'reports/generated/hitter-translation-inputs-2025/forecast-inputs-{fold}.parquet',
            ROOT/f'reports/generated/hitter-talent-bridge-v74/features-{fold}.parquet',SOURCE/f'translation-{fold}.parquet'])
        frames_by_head,q=frames(fold)
        for head,tr in frames_by_head.items():
            cols=names[head]
            assert tr['target_year'].max()==2026 and not (tr['target_year']==2020).any()
            assert (tr['target_year']==tr['origin_year']+1).all() and set(q['target_year'])=={2027}
            assert tr.unique('row_id').height==len(tr) and not set(tr['player_id'])&set(q['player_id'])
            assert tr['window_complete'].all() and (tr['outer_fold']!=fold).all()
            assert not any(c.startswith('next_') for c in cols) and not any(c.startswith('next_') for c in q.columns)
            assert np.isfinite(tr.select(cols).to_numpy().astype(float)).all() and np.isfinite(q.select(cols).to_numpy().astype(float)).all()
            assert np.isfinite(tr.select(LABELS).to_numpy().astype(float)).all()
            assert (tr['next_pa']>=0).all() and (tr.filter(pl.col('next_pa')==0)['next_value']==0).all()
            if head=='participation':assert set(tr['next_active'])=={0,1}
            else:assert tr['next_pa'].min()>0
            a,b=profile(tr),profile(q)
            groups=[['stage','prior_debut','career_band'],['stage','prior_debut','age_band','current_state','quality_band'],
                ['stage','prior_debut','age_band','current_state','regular_window','position_band']]
            notes=[]
            for i,keys in enumerate(groups):
                n=a.group_by(keys).agg(pl.col('player_id').n_unique().alias('training_people'))
                s=b.select('row_id',*keys).join(n,on=keys,how='left',validate='m:1').with_columns(
                    pl.col('training_people').fill_null(0),pl.lit(head).alias('head'),pl.lit(fold).alias('fold'),pl.lit(i).alias('profile_kind'))
                supports.append(s);notes.append(dict(profile=i,unseen=int((s['training_people']==0).sum()),sparse=int((s['training_people']<20).sum())))
            w=weights(tr)
            if head.startswith('rate'):w*=tr['next_pa'].to_numpy();w*=len(w)/w.sum()
            cells.append(dict(fold=fold,head=head,training_rows=len(tr),training_people=tr['player_id'].n_unique(),
                max_target_year=2026,forecast_rows=len(q),profile_support=notes,training_row_ids=tr['row_id'].to_list(),
                weight_sha256=hashlib.sha256(w.astype('<f8').tobytes()).hexdigest(),
                missing_current_scout_list=int((q['scout_list_available_0']==0).sum()),
                no_current_list_training_people=tr.filter(pl.col('scout_list_available_0')==0)['player_id'].n_unique() if 'scout_list_available_0' in tr.columns else None))
        print(f'2027 production preflight fold {fold}: all five heads checked.',flush=True)
    sp=OUT/'profile-support.parquet'
    prepath=OUT/'preflight.json'
    pre=dict(before_fitting=True,features=names,settings=settings,cells=cells,
        input_hashes={str(p):sha256_file(p) for p in inputs},predictive_improvement_claim=False,
        historical_model_recipe_unchanged_except_reviewed_reliability=True)
    if prepath.exists():assert json.loads(prepath.read_text())==pre
    else:
        assert not sp.exists();pl.concat(supports,how='diagonal_relaxed').write_parquet(sp);write_once(prepath,pre)
    receipts=[]
    with threadpool_limits(limits=2):
        for fold in range(5):
            receipt=OUT/f'fit-{fold}.json';forecastpath=OUT/f'forecast-{fold}.parquet'
            if receipt.exists():
                r=json.loads(receipt.read_text());assert r['preflight_sha256']==sha256_file(prepath)
                assert sha256_file(forecastpath)==r['forecast_sha256']
                for h in r['heads']:assert sha256_file(Path(h['path']))==h['sha256']
                receipts.append(r);continue
            frames_by_head,q=frames(fold);predictions={};heads=[]
            for head,tr in frames_by_head.items():
                cols=names[head];israte=head.startswith('rate');w=weights(tr)
                if israte:w*=tr['next_pa'].to_numpy();w*=len(w)/w.sum()
                note=next(c for c in cells if c['fold']==fold and c['head']==head)
                assert note['training_row_ids']==tr['row_id'].to_list()
                assert note['weight_sha256']==hashlib.sha256(w.astype('<f8').tobytes()).hexdigest()
                x=safe_matrix(tr,cols) if israte else tr.select(cols).to_numpy()
                tx=safe_matrix(q,cols) if israte else q.select(cols).to_numpy()
                model=Ridge(alpha=100) if israte else (HistGradientBoostingClassifier if head=='participation' else HistGradientBoostingRegressor)(**settings)
                target='next_batting_rate' if israte else 'next_active' if head=='participation' else 'next_pa'
                model.fit(x,tr[target].to_numpy(),sample_weight=w)
                prediction=model.predict_proba(tx)[:,1] if head=='participation' else model.predict(tx)
                mp=OUT/f'{head}-{fold}.joblib';assert not mp.exists();joblib.dump(model,mp,compress=3)
                replay=joblib.load(mp).predict_proba(tx)[:,1] if head=='participation' else joblib.load(mp).predict(tx)
                assert np.allclose(prediction,replay,rtol=0,atol=1e-12) and np.isfinite(prediction).all()
                predictions[head]=prediction;heads.append(dict(head=head,path=str(mp),sha256=sha256_file(mp),features=cols,target=target))
                print(f'2027 fold {fold}: {head} saved and replayed.',flush=True)
            unavailable=q['hard_unavailable'].to_numpy()|q['reported_retired'].to_numpy()
            p=np.where(unavailable,0,predictions['participation']);cond=np.clip(predictions['conditional_pa'],1,800);pa=p*cond
            prospect=q['prior_debut'].to_numpy()==0;tracked=q['sc_tracked'].to_numpy()
            rate=np.where(prospect,predictions['rate_prospect'],np.where(tracked,predictions['rate_tracking'],predictions['rate_numeric']))
            route=np.where(prospect,'translated_prospect',np.where(tracked,'measured_MLB','numeric_MLB'))
            # 2027 is a full-season projection; do not carry the one missed 2026
            # league game into the forecast schedule fraction.
            reference=570/183849
            q=q.with_columns(*[pl.Series('raw_'+h,v) for h,v in predictions.items()],
                pl.Series('participation_probability',p),pl.Series('conditional_pa',cond),pl.Series('expected_pa',pa),
                pl.Series('hitting_wins_per_600',rate),pl.Series('batting_contribution',pa*(rate/600+reference)),
                pl.Series('talent_route',route),pl.Series('participation_override',unavailable))
            assert not forecastpath.exists();q.write_parquet(forecastpath)
            r=dict(fold=fold,heads=heads,preflight_sha256=sha256_file(prepath),forecast_sha256=sha256_file(forecastpath))
            write_once(receipt,r);receipts.append(r)
    f=pl.concat([pl.read_parquet(OUT/f'forecast-{k}.parquet') for k in range(5)]).sort('row_id')
    assert len(f)==4851 and f['player_id'].n_unique()==4851
    path=OUT/'forecast.parquet';assert not path.exists();f.write_parquet(path)
    write_once(PUBLIC/'batting-refresh-fit.json',dict(forecast_year=2027,source_as_of='2026-10-09',players=len(f),heads_fitted=25,
        forecast_path=str(path),forecast_sha256=sha256_file(path),expected_PA=float(f['expected_pa'].sum()),
        expected_MLB_players=float(f['participation_probability'].sum()),batting_plus_replacement=float(f['batting_contribution'].sum()),
        head_replay_pass=True,player_forecast_walkthrough='pending',full_WAR=False,release_approved=False,
        preflight_sha256=sha256_file(prepath),fold_receipts=receipts))
    print(f'2027 batting/PA refresh complete for {len(f)} players; player review and full-value integration remain.',flush=True)


if __name__=='__main__':main()
