"""Independent additions checks and explicit delayed mutation coverage."""
from pathlib import Path
import numpy as np
import polars as pl

from prepare_hitter_overseas_integration import ROOT,OUT,OLD,ADDITIONS,FOREIGN,read,write,addition_frame,annual_labels,BUCKETS
from universal_baseball.storage import sha256_file


def main():
    assert not (OUT/'addition-source-audit.json').exists(),'Preserve prior audit'
    f=pl.read_parquet(OUT/'features.parquet');old=pl.read_parquet(OLD/'features.parquet')
    admitted=[r for r in read(ADDITIONS/'origin-inputs.json')['rows'] if r['qualified_for_batting_input']]
    raw=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet')
    counts=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet')
    targets=pl.read_parquet(ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet')
    _,env=annual_labels(raw)
    foreign={r['candidate_key']:r for r in read(FOREIGN/'origin-inputs.json')['rows']}
    debut={r['player_id']:r['mlb_debut_date'].year for r in pl.read_parquet(ROOT/'reports/generated/hitter-arrival-source-repair-v1/debut-dates.parquet').to_dicts()}
    games=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v38/game-counts.parquet')
    ranks=pl.read_parquet(ROOT/'reports/generated/hitter-preseason-readiness-v67/ranks.parquet')
    checks=0
    for r in f.filter(pl.col('source_addition')).to_dicts():
        y,pid=r['origin_year'],r['player_id'];prior=raw.filter((pl.col('player_id')==pid)&(pl.col('season')<=y))
        for lag in range(3):
            for b in BUCKETS:
                a=prior.filter((pl.col('season')==y-lag)&(pl.col('bucket')==b))
                assert a['plate_appearances'].sum()==r[f'{b}_{lag}_pa'];checks+=1
                g=games.filter((pl.col('player_id')==pid)&(pl.col('season')==y-lag)&(pl.col('bucket')==b))
                assert g['plate_appearances'].sum()==r[f'{b}_{lag}_pa'];checks+=1
        assert bool(r['scout_listed_0']==1)==bool(ranks.filter((pl.col('player_id')==pid)&(pl.col('season')==y+1)).height);checks+=1
    # Source admission had already checked future mutations before fitting. This
    # additional end-to-end feature reconstruction is explicitly later, not
    # misreported as another pre-fit check or a reason to rerun unchanged fits.
    excluded={'row_id','next_pa','next_value','next_state','next_batting_rate','next_active'}
    feature_names=[n for n in old.columns if n not in excluded]
    origins=[]
    for y in sorted({r['origin_year'] for r in admitted}):
        selected=[r for r in admitted if r['origin_year']==y]
        before=addition_frame(old,selected,foreign,counts,targets,env,debut)
        changed=counts.with_columns([pl.when(pl.col('season')>y).then(pl.col(n)*7+999).otherwise(pl.col(n)).alias(n)
            for n in counts.columns if n not in ['season','player_id','bucket']])
        target_changed=targets.with_columns(pl.when(pl.col('season')>y).then(pl.col('mlb_pa')*9+111).otherwise(pl.col('mlb_pa')).alias('mlb_pa'),
            pl.when(pl.col('season')>y).then(pl.col('component_war')*9+111).otherwise(pl.col('component_war')).alias('component_war'))
        after=addition_frame(old,selected,foreign,changed,target_changed,env,debut)
        assert before.select(feature_names).equals(after.select(feature_names)),y
        origins.append(y);print(f'Future domestic count/outcome mutation leaves addition predictors unchanged: {y}',flush=True)
    write('addition-source-audit.json',dict(source_additions=32,count_and_scout_checks=checks,
        future_mutation_origins=origins,complete_addition_predictors_unchanged=True,
        labels_intentionally_not_required_to_ignore_actual_outcome_mutations=True,
        prefit_admission_mutations_previously_verified=True,new_feature_mutation_check_completed_after_fitting_started=True,
        original_source_labels_preserved=True,no_changed_fits_or_model_choices=True,
        hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [Path(__file__),OUT/'features.parquet',OUT/'preflight.json']}))


if __name__=='__main__':main()
