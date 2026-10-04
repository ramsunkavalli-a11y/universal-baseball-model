"""Describe roster versus readiness errors; do not fit or adjust probabilities."""
import polars as pl

from prepare_hitter_available_season_history import ROOT, OUT, CURRENT, read, write
from prepare_hitter_extended_training import profile, verify
from review_hitter_extended_training import highest
from evaluate_hitter_available_season_history import probability
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.storage import sha256_file


def main():
    assert not (OUT/'roster-readiness-diagnostic.json').exists()
    pre = read(OUT/'preflight.json')
    verify(pre['input_hashes'])
    q = pl.read_parquet(OUT/'scored-predictions.parquet').filter(pl.col('prior_debut')==0)
    f = profile(pl.read_parquet(CURRENT/'features.parquet'))
    meta = f.select('row_id','scout_rank_score_0').with_columns(
        pl.Series('highest_origin_level',[highest(o) for o in f.iter_rows(named=True)]))
    meta = meta.rename({'scout_rank_score_0':'actual_scout_score'})
    q = q.join(meta,on='row_id',validate='1:1').with_columns(
        pl.when(pl.col('highest_origin_level')>=4).then(pl.lit('AA_AAA'))
        .when(pl.col('highest_origin_level')==3).then(pl.lit('Aplus'))
        .when(pl.col('highest_origin_level')==2).then(pl.lit('A'))
        .otherwise(pl.lit('short_rookie_DSL_or_none')).alias('readiness_level'),
        pl.when(pl.col('actual_scout_score')>=.81).then(pl.lit('top20'))
        .when(pl.col('actual_scout_score')>0).then(pl.lit('other_listed'))
        .otherwise(pl.lit('not_observed_listed')).alias('scout_group'))
    groups = []
    for keys in [['readiness_level','on_40man'],['readiness_level','on_40man','scout_group'],
                 ['origin_year','readiness_level','on_40man']]:
        for _,s in q.group_by(keys):
            first = s.row(0,named=True)
            groups.append(dict(group_keys=keys,profile={n:first[n] for n in keys},rows=len(s),people=s['player_id'].n_unique(),
                probability={a:probability(s,a) for a in ['preseason','available']},
                scores={a:score(s,a) for a in ['preseason','available']},actual_pa=int(s['next_pa'].sum())))
    write('roster-readiness-diagnostic.json',dict(postfit_mechanism_diagnostic=True,no_forecasts_changed=True,
        group_selection='Origin-known highest observed level, 40-man flag and fresh preseason list group; no outcome-based selection',
        interpretation='Descriptive calibration and errors. Roster protection is not proof of immediate MLB readiness. Not causal evidence, independent confirmation or a postfit routing rule.',
        groups=groups,hashes={str(p):sha256_file(p) for p in [CURRENT/'features.parquet',OUT/'scored-predictions.parquet',__file__ and ROOT/'scripts/diagnose_hitter_roster_readiness.py']}))
    for g in groups:
        if len(g['group_keys'])==2:
            print(g['profile'],g['rows'],g['people'],g['probability'],'PA',g['actual_pa'],
                [g['scores'][a]['pa_total'] for a in ['preseason','available']],flush=True)


if __name__=='__main__':
    main()
