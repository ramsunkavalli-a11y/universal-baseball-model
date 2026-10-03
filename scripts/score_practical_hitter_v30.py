"""Recover reporting only: preserve all fitted models and saved predictions."""
import json
import polars as pl
import evaluate_practical_hitter_v30 as r
from universal_baseball.storage import sha256_file

def main():
    manifest=r.read(r.OUT/'preflight.json');r.check(manifest['input_hashes'])
    assert not (r.OUT/'report.json').exists()
    fits=r.read(r.OUT/'fits.json');assert len(fits)==210
    for fit in fits:assert sha256_file(r.Path(fit['artifact']))==fit['sha256']
    f=pl.read_parquet(r.OUT/'predictions.parquet').join(
        pl.read_parquet(r.OUT/'features.parquet').select('row_id','pa_1','pa_2'),on='row_id',validate='1:1')
    public=pl.read_parquet(r.PUBLIC).select('row_id','steamer_pa','steamer_value','zips_pa')
    alias=f.select('row_id','steamer_pa','steamer_value','zips_pa').join(public,on='row_id',validate='1:1')
    for col in ['steamer_pa','steamer_value','zips_pa']:assert alias[col].equals(alias[col+'_right'])
    scopes=[('all',f),('public_active',f.filter((pl.col('pa_0')>0)&pl.col('steamer_pa').is_not_null()&pl.col('zips_pa').is_not_null()))]
    scopes += [('origin_'+str(y),f.filter(pl.col('origin_year')==y)) for y in r.YEARS]
    scopes += [('current_zero',f.filter(pl.col('pa_0')==0)),('current_brief',f.filter(pl.col('pa_0').is_between(1,199))),
        ('current_partial',f.filter(pl.col('pa_0').is_between(200,399))),('current_regular',f.filter(pl.col('pa_0')>=400)),
        ('debut_brief',f.filter((pl.col('elapsed')==0)&pl.col('pa_0').is_between(1,199))),
        ('current600',f.filter(pl.col('pa_0')>=600)),('inactive_prior200',f.filter((pl.col('pa_0')==0)&(pl.col('pa_1')>=200)))]
    scores=[]
    for scope,g in scopes:
        if not len(g):continue
        prefixes=['v24','rules',*r.m.ARMS]+(['steamer'] if scope=='public_active' else [])
        scores.append(dict(scope=scope,rows=len(g),players=g['player_id'].n_unique(),actual_pa=float(g['next_pa'].sum()),
            actual_value=float(g['next_value'].sum()),scores={p:r.m.score(g,p) for p in prefixes}))
    r.write('report.json',dict(input_hashes=manifest['input_hashes'],scores=scores,player_walkthrough_status='pending',
        new_fits=len(fits),protected_2026_outcomes_used=False,frozen_forecast_changed=False,
        reporting_repair='Joined existing pa_1/pa_2 by row_id for cohort summaries only; no refits, feature changes or prediction changes.',
        value_warning='Fixed old expected-yield multiplication; workload diagnostic, not newly validated joint talent/value.',
        output_hashes={str(r.OUT/p):sha256_file(r.OUT/p) for p in ['predictions.parquet','fits.json']}))
    print(json.dumps(scores[:2],indent=2))

if __name__=='__main__':main()
