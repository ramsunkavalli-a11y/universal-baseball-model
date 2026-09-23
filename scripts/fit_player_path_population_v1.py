"""Frozen identity-balanced population ablation; current production stays unchanged."""
import argparse
import json
from pathlib import Path
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from audit_player_path_population_v1 import OUT, FOLDS, eligible, panel_data, ANCHORS
from fit_player_path_value_bridge_v1 import BASE, DEBUT, REFERENCE, training, references
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.player_path_distribution import forest_draws
from universal_baseball.player_path_population import fitted_weights, sample_weights, exact_summary, iid_summary
from universal_baseball.storage import sha256_file

PLAN = Path('docs/player-path-population-v1-plan.md')
RUNS = [(400,s) for s in (417,418,419,420,421)]+[(1600,417)]


def source_hashes():
    files = [PLAN,Path('docs/projection-anchored-path-next-checkpoint.md'),
        BASE/'panel.parquet',BASE/'targets.parquet',BASE/'manifest.json',DEBUT,REFERENCE,ANCHORS,
        OUT/'support-audit.json',Path(__file__),Path('scripts/audit_player_path_population_v1.py'),
        Path('scripts/score_player_path_population_v1.py'),Path('src/universal_baseball/player_path_population.py'),
        Path('src/universal_baseball/player_path_distribution.py'),Path('tests/test_player_path_population.py')]
    return {str(p):sha256_file(p) for p in files}


def main():
    parser = argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');args=parser.parse_args()
    manifest = OUT/'prefit-manifest.json'
    if args.freeze:
        if manifest.exists():
            raise ValueError('Pre-fit contract already frozen')
        save(manifest,{'source_hashes':source_hashes(),'folds':FOLDS,'runs':RUNS,
            'methods':['B0','F0','F1','A1'],'protected_outcomes_used':False})
        print('Pre-fit contract frozen');return
    contract = json.loads(manifest.read_text())
    assert contract['source_hashes']==source_hashes(), 'Changed pre-fit sources'
    panel = panel_data()
    features = json.loads((BASE/'manifest.json').read_text())['full_features']
    core = [c for c in features if c in ['age_centered','age_squared','age_missing','reorganization_era']
        or c.startswith(('level_','missing_lag','log_pa_lag','log_mlb_pa_lag'))]
    proof = OUT/'v1-reproduction.json'
    if not proof.exists():
        old = json.loads(Path('model_artifacts/player-path-value-bridge-v1-2026-09-23/fit-manifest.json').read_text())
        note = next(n for n in old['fits'] if n['origin']==2016 and n['horizon']==3 and n['method']=='F1' and not n['cold'])
        test = panel.filter(pl.col('origin_year')==2016).sort('player_id')
        train = training(panel,2016,3)
        draws,_ = forest_draws(train,test,features,3)
        saved = np.load(note['draw_path'])
        assert np.array_equal(draws,saved['donor_indices'])
        assert np.array_equal(train['player_id'].to_numpy(),saved['donor_player_id'])
        save(proof,{'origin':2016,'horizon':3,'method':'F1','exact_donor_matrix_match':True,
            'original_draw_sha256':sha256_file(Path(note['draw_path']))})
        print('Original F1 donor matrix reproduced exactly',flush=True)
    (OUT/'fits').mkdir(exist_ok=True)
    exact_frames, simulated_frames, notes = [],[],[]
    for year,h,cold in FOLDS:
        test = panel.filter(pl.col('origin_year')==year).sort('player_id')
        excluded = test['player_id'].to_list() if cold else ()
        latest = training(panel,year,h,excluded).with_columns(pl.lit(1.).alias('identity_weight'))
        all_rows = eligible(panel,year,h,excluded)
        base = test.select('origin_year','player_id','player_name','age','level','stage','prospect','recent_debut','mlb_pa_lag0').with_columns(
            pl.lit(h).alias('horizon'),pl.lit(cold).alias('cold'),pl.lit(year<2020<=year+h).alias('pandemic'))
        base = base.join(references(h),on=['origin_year','player_id'],how='left',validate='1:1',maintain_order='left')
        ay = None if year==2025 else test.select([f'war_h{i}' for i in range(1,h+1)]).to_numpy()
        ap = None if year==2025 else test.select([f'pa_h{i}' for i in range(1,h+1)]).to_numpy()
        for method in ('B0','F0','F1','A1'):
            prefix = OUT/'fits'/f'{year}-h{h}-cold{int(cold)}-{method}'
            exact_path = prefix.with_suffix('.exact.parquet')
            simulated_path = prefix.with_suffix('.simulated.parquet')
            note_path = prefix.with_suffix('.json')
            if note_path.exists():
                note=json.loads(note_path.read_text())
                assert sha256_file(exact_path)==note['exact_sha256']
                assert sha256_file(simulated_path)==note['simulated_sha256']
                exact_frames.append(pl.read_parquet(exact_path));simulated_frames.append(pl.read_parquet(simulated_path));notes.append(note)
                continue
            train = all_rows if method=='A1' else latest
            print(f'Fit {year} H{h} cold={cold} {method}: {train.height} snapshots',flush=True)
            weights,diagnostics = fitted_weights(train,test,core if method=='F0' else features,h,method)
            wy = train.select([f'war_h{i}' for i in range(1,h+1)]).to_numpy()
            py = train.select([f'pa_h{i}' for i in range(1,h+1)]).to_numpy()
            exact = base.with_columns(pl.lit(method).alias('method'),
                *[pl.Series(k,v) for k,v in exact_summary(weights,wy,py,ay,ap).items()])
            if ay is not None:
                exact=exact.with_columns(((pl.col('delivered_mean')-pl.col('actual_batting'))**2).alias('delivered_mse'))
            draws_frames=[];probe={}
            for n,seed in RUNS:
                draw=sample_weights(weights,n,seed)
                assert not (train['player_id'].to_numpy()[draw]==test['player_id'].to_numpy()[:,None]).any()
                result=base.with_columns(pl.lit(method).alias('method'),pl.lit(n).alias('draws'),pl.lit(seed).alias('seed'),
                    *[pl.Series(k,v) for k,v in iid_summary(wy[draw],py[draw],ay,ap).items()])
                if ay is not None:
                    result=result.with_columns(((pl.col('delivered_mean')-pl.col('actual_batting'))**2).alias('delivered_mse'))
                draws_frames.append(result);probe[f'n{n}s{seed}']=draw[:10]
            simulated=pl.concat(draws_frames,how='diagonal_relaxed')
            exact.write_parquet(exact_path);simulated.write_parquet(simulated_path)
            np.savez_compressed(prefix.with_suffix('.probe.npz'),**probe,
                donor_id=train['player_id'].to_numpy(),donor_origin=train['origin_year'].to_numpy(),
                row_weight=train['identity_weight'].to_numpy(),query_id=test['player_id'].to_numpy()[:10])
            note={'origin':year,'horizon':h,'cold':cold,'method':method,'rows':train.height,
                'identities':train['player_id'].n_unique(),'latest_training_outcome':int(train['origin_year'].max())+h,
                'diagnostics':diagnostics,'exact_sha256':sha256_file(exact_path),
                'simulated_sha256':sha256_file(simulated_path),'probe_sha256':sha256_file(prefix.with_suffix('.probe.npz'))}
            save(note_path,note);notes.append(note);exact_frames.append(exact);simulated_frames.append(simulated)
            del weights
            print(f'Ready {year} H{h} {method}',flush=True)
    pl.concat(exact_frames,how='diagonal_relaxed').write_parquet(OUT/'exact-predictions.parquet')
    pl.concat(simulated_frames,how='diagonal_relaxed').write_parquet(OUT/'simulated-predictions.parquet')
    assert contract['source_hashes']==source_hashes()
    save(OUT/'fit-manifest.json',{'prefit_sha256':sha256_file(manifest),'fits':notes,
        'protected_outcomes_used':False,'production_forecasts_changed':False})


if __name__=='__main__':
    with threadpool_limits(limits=4):
        main()
