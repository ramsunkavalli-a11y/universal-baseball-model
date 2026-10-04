"""Corrected roster/readiness diagnostic with Mexico explicitly separate."""
from pathlib import Path
import polars as pl

from prepare_hitter_available_season_history import ROOT, OUT, CURRENT, read, write
from prepare_hitter_extended_training import verify
from evaluate_hitter_available_season_history import probability
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.storage import sha256_file


def main():
    name = 'roster-readiness-diagnostic-separate-mexico.json'
    assert not (OUT/name).exists()
    verify(read(OUT/'preflight.json')['input_hashes'])
    f = pl.read_parquet(CURRENT/'features.parquet')
    meta = f.select('row_id',pl.col('scout_rank_score_0').alias('actual_scout_score'),
        pl.when(pl.sum_horizontal('AA_0_pa','AAA_0_pa')>0).then(pl.lit('AA_AAA'))
        .when(pl.col('Aplus_0_pa')>0).then(pl.lit('Aplus'))
        .when(pl.col('A_0_pa')>0).then(pl.lit('A'))
        .when(pl.col('MEX_0_pa')>0).then(pl.lit('Mexico_without_A_or_higher_affiliated'))
        .otherwise(pl.lit('short_rookie_DSL_or_none')).alias('readiness_level'))
    q = pl.read_parquet(OUT/'scored-predictions.parquet').filter(pl.col('prior_debut')==0).join(meta,on='row_id',validate='1:1')
    q = q.with_columns(pl.when(pl.col('actual_scout_score')>=.81).then(pl.lit('top20'))
        .when(pl.col('actual_scout_score')>0).then(pl.lit('other_listed'))
        .otherwise(pl.lit('not_observed_listed')).alias('scout_group'))
    groups=[]
    for keys in [['readiness_level','on_40man'],['readiness_level','on_40man','scout_group'],
                 ['origin_year','readiness_level','on_40man']]:
        for _,s in q.group_by(keys):
            first=s.row(0,named=True)
            groups.append(dict(group_keys=keys,profile={n:first[n] for n in keys},rows=len(s),people=s['player_id'].n_unique(),
                probability={a:probability(s,a) for a in ['preseason','available']},
                scores={a:score(s,a) for a in ['preseason','available']},actual_pa=int(s['next_pa'].sum())))
    write(name,dict(postfit_mechanism_diagnostic=True,no_forecasts_changed=True,
        supersedes='roster-readiness-diagnostic.json, whose highest-level helper pooled Mexico with AA',
        group_selection='Actual origin-known affiliated exposure, separate Mexico fallback, 40-man flag and fresh list group; no outcome selection',
        interpretation='Descriptive errors, not a causal team decision model or selectable postfit routing. Roster protection need not imply readiness; the observed group totals decide whether a blanket correction is warranted.',
        groups=groups,hashes={str(p):sha256_file(p) for p in [CURRENT/'features.parquet',OUT/'scored-predictions.parquet',Path(__file__)]}))
    for g in groups:
        if len(g['group_keys'])==2:
            print(g['profile'],g['rows'],g['people'],g['probability'],'PA',g['actual_pa'],[g['scores'][a]['pa_total'] for a in ['preseason','available']],flush=True)


if __name__=='__main__':
    main()
