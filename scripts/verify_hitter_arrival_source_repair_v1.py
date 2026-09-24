"""Independent artifact, source chronology and matched-population verification."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from fit_hitter_arrival_source_repair_v1 import OUT,SOURCE,FOLDS,hashes,arm_panel
from universal_baseball.hitter_arrival_source_repair import COHORTS,FEATURES,corrected_cohorts,attach_leagues,attach_roster
from universal_baseball.hitter_detail_arrival import eligible,target_values,TARGETS
from universal_baseball.storage import sha256_file
from score_hitter_detail_arrival_v1 import metrics

PACKAGE=Path('model_artifacts/hitter-arrival-source-repair-v1-2026-09-23')


def main():
    pre=json.loads((OUT/'prefit-manifest.json').read_text());assert pre['hashes']==hashes()
    fit=json.loads((OUT/'fit-manifest.json').read_text())
    assert fit['prediction_sha256']==sha256_file(OUT/'predictions.parquet')
    assert fit['prefit_sha256']==sha256_file(OUT/'prefit-manifest.json')
    audit=json.loads((OUT/'source-audit.json').read_text())
    for path,h in audit['source_hashes'].items(): assert sha256_file(Path(path))==h,path
    assert [x['season'] for x in audit['debut']['censuses']]==list(range(1960,2026))
    assert all(x['teams']==30 for x in audit['roster_counts'])
    assert all(x['unmatched_stints']==0 and x['unknown_league_stints']==0 for x in audit['leagues'])
    old=pl.read_parquet(SOURCE/'input-panel.parquet');new=pl.read_parquet(OUT/'repaired-panel.parquet')
    d=pl.read_parquet(OUT/'debut-dates.parquet');a=pl.read_parquet(OUT/'league-context.parquet');r=pl.read_parquet(OUT/'year-end-rosters.parquet')
    rebuilt=attach_roster(attach_leagues(corrected_cohorts(old,d),a),r)
    assert new.equals(rebuilt)
    assert new.height==old.height and new['player_id'].equals(old['player_id'])
    for c in old.columns:
        if c not in COHORTS+['on_40man']:assert old[c].equals(new[c]),c
    for k in range(3):
        assert new[FEATURES[k*2]].drop_nulls().is_between(0,1).all()
        assert new[FEATURES[k*2+1]].is_between(0,1).all()
    assert not new.filter(pl.col('player_id').is_in([121252,425854])&pl.col('prospect')).height
    assert new.filter((pl.col('origin_year')==2021)&pl.col('player_id').is_in([665161,677649]))['on_40man'].sum()==2
    f=pl.read_parquet(OUT/'predictions.parquet')
    assert not f.select('origin_year','player_id','arm','target').is_duplicated().any()
    assert f['probability'].is_finite().all() and f['probability'].is_between(1e-6,1-1e-6).all()
    assert len(fit['fits'])==30 and len(fit['mutations'])==2 and fit['original_replay_exact']
    assert all(x['max_difference']==0 for x in fit['mutations'])
    for note in fit['fits']:
        p=arm_panel(old,new,note['arm']);t=eligible(p,note['year'],note['target'])
        assert note['training_rows']==t.height
        assert note['latest_label']==max(t['origin_year'])+TARGETS[note['target']]<=note['year']
        assert not t.filter((pl.col('origin_year')<2020)&(pl.col('origin_year')+TARGETS[note['target']]>=2020)).height
        np.testing.assert_allclose(t.group_by('player_id').agg(pl.col('identity_weight').sum())['identity_weight'],1.)
        used=set(note['used_features'])|set(note['dropped_constant_or_unobserved'])
        assert used==set(pre['base_columns']+(FEATURES if note['arm'] in ('C','F') else []))
    score=json.loads((OUT/'score-report.json').read_text())
    for year,target in FOLDS:
        q=new.filter(pl.col('origin_year')==year)
        for arm in ('R','C','T','F'):
            g=f.filter((pl.col('origin_year')==year)&(pl.col('target')==target)&(pl.col('arm')==arm))
            np.testing.assert_array_equal(g['player_id'],q['player_id'])
            np.testing.assert_array_equal(g['actual'],target_values(q,target))
            for c in COHORTS:assert g[c].equals(q[c])
            m=metrics(g.filter(pl.col('prospect')))
            saved=score['targets'][target]['annual'][str(year)][arm]
            for k in ('rows','observed','expected','brier','log_loss'):np.testing.assert_allclose(m[k],saved[k],rtol=1e-12,atol=1e-12)
    if (PACKAGE/'manifest.json').exists():
        archive=json.loads((PACKAGE/'manifest.json').read_text())
        for n,h in archive['files'].items():assert sha256_file(PACKAGE/n)==h
        for n,h in archive['code'].items():assert sha256_file(Path(n))==h
    print(json.dumps({'verified':True,'new_fits':30,'mutation_replays':2,'original_replays':1,
        'rows':f.height,'protected_outcomes_used':False,'production_forecasts_changed':False}))


if __name__=='__main__':main()
