"""Apply a locked positive-rank fallback; no refits or outcome-based gates."""
import json
from pathlib import Path
import polars as pl
from universal_baseball.storage import sha256_file
import evaluate_hitter_scouting_v47 as old

ROOT=old.ROOT
OUT=ROOT/'reports/generated/practical-hitter-scouting-v48'


def write(name,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False,ensure_ascii=False)+'\n',encoding='utf8')


def prepare():
    assert old.r.read(old.OUT/'report.json')['player_walkthrough_status']=='complete'
    verified=old.r.read(old.OUT/'verification.json');assert verified['replayed_heads']==35 and verified['player_walkthrough_status']=='complete'
    f=pl.read_parquet(old.OUT/'predictions.parquet');source=pl.read_parquet(old.OUT/'features.parquet')
    f=f.join(source.select('row_id','scout_listed_0','scout_rank_score_0'),on='row_id',validate='1:1')
    assert len(f)==30506 and f['row_id'].n_unique()==30506 and f['origin_year'].max()==2024 and f['target_year'].max()==2025
    f=f.with_columns((pl.col('scout_listed_0')==1).alias('positive_rank_gate'))
    paths=[old.OUT/'predictions.parquet',old.OUT/'features.parquet',old.OUT/'verification.json',old.OUT/'report.json',old.OUT/'cases.json',
        ROOT/'docs/practical-hitter-scouting-v48-fallback-contract.md',Path(__file__)]
    # Persist identity selection before loss calculation, retaining the original training provenance.
    write('preflight.json',dict(before_scoring=True,input_hashes={str(p):sha256_file(p) for p in paths},rows=len(f),positive_rank_rows=int(f['positive_rank_gate'].sum()),
        gate_row_ids=f.filter(pl.col('positive_rank_gate'))['row_id'].to_list(),prior_training_heads=35,refitted_heads=0,
        selection_uses_outcomes=False,prior_review_complete=True,post_review_development_design=True,protected_outcomes_used=False))
    f.select('row_id','origin_year','player_id','positive_rank_gate').write_parquet(OUT/'gate-identities.parquet')
    f=f.with_columns(pl.when('positive_rank_gate').then('scout_pa').otherwise('retired_games_pa').alias('fallback_pa'),pl.col('cohort_rate').alias('fallback_rate'))
    f=f.with_columns((pl.col('fallback_pa')*(pl.col('fallback_rate')/600+pl.col('origin_replacement_rate'))).alias('fallback_value'))
    f.write_parquet(OUT/'predictions.parquet')
    print('Saved outcome-blind positive-rank gate:',int(f['positive_rank_gate'].sum()),'of',len(f),'forecasts; no new fits.',flush=True)


if __name__=='__main__':prepare()
