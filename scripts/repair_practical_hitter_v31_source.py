"""Prefit correction: cumulative MLB PA, not just the primary season stint."""
from pathlib import Path
import polars as pl
import prepare_practical_hitter_v31 as r
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file

def main():
    note=r.read(r.OUT/'preflight.json');assert note['before_fitting']
    assert not (r.OUT/'preflight-ready.json').exists()
    for p,h in note['input_hashes'].items():assert sha256_file(Path(p))==h
    f=pl.read_parquet(r.OUT/'features.parquet')
    counts=pl.read_parquet(r.OUT/'counts.parquet').filter(pl.col('bucket')=='MLB').sort('player_id','season').with_columns(
        pl.col('plate_appearances').cum_sum().over('player_id').alias('true_career_mlb_observed_pa'))
    frames=[]
    for y in sorted(f['origin_year'].unique()):
        c=counts.filter(pl.col('season')<=y).sort('season',descending=True).unique('player_id',keep='first').select('player_id','true_career_mlb_observed_pa')
        frames.append(f.filter(pl.col('origin_year')==y).join(c,on='player_id',how='left',validate='1:1').with_columns(pl.col('true_career_mlb_observed_pa').fill_null(0)))
    g=pl.concat(frames).sort('row_id');changes=g.filter(pl.col('career_mlb_observed_pa')!=pl.col('true_career_mlb_observed_pa')).select('row_id','origin_year','player_id','player_name','career_mlb_observed_pa','true_career_mlb_observed_pa')
    changes.write_parquet(r.OUT/'career-source-changes.parquet')
    g=g.with_columns(pl.col('true_career_mlb_observed_pa').alias('career_mlb_observed_pa')).drop('true_career_mlb_observed_pa')
    g.write_parquet(r.OUT/'features-ready.parquet')
    cells=[];supports=[]
    for c in note['cells']:
        y,k=c['year'],c['fold'];tr=g.filter(pl.col('row_id').is_in(c['training_row_ids']));te=g.filter(pl.col('row_id').is_in(c['test_row_ids']))
        sup,pref=preflight(tr,te,cutoff=y,fold=k,features=note['detail_features'],expected_keys=te.select('row_id','horizon').iter_rows())
        supports.append(sup);cells.append(dict(year=y,fold=k,**pref,training_row_ids=c['training_row_ids'],test_row_ids=c['test_row_ids']))
    pl.concat(supports).write_parquet(r.OUT/'support-ready.parquet')
    note.update(cells=cells,ready_features=str(r.OUT/'features-ready.parquet'),source_correction_rows=len(changes),
        source_correction='Primary season stint omitted MLB work in split-level seasons. Recompute full cumulative MLB PA from every MLB count, cutoff-local; no fit or result informed correction.')
    for p in [r.OUT/'features-ready.parquet',r.OUT/'support-ready.parquet',r.OUT/'career-source-changes.parquet',Path(__file__),r.OUT/'preflight.json']:
        note['input_hashes'][str(p)]=sha256_file(p)
    r.write('preflight-ready.json',note)
    print(f'Prefit correction: {len(changes)} exposure rows; original source and manifest preserved; 35 cells rechecked.')

if __name__=='__main__':main()
