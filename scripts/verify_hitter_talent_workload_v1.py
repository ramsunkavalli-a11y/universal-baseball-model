"""Verify nested chronology, source joins, frozen comparators and scoring."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from fit_hitter_talent_workload_v1 import OUT,PACKAGE,PANEL,PREVIOUS,hashes
from score_hitter_talent_workload_v1 import ARMS,summary,cumulative,decision
from universal_baseball.hitter_conditional_workload import active_training
from universal_baseball.hitter_talent_workload import TALENT,PEDIGREE,pedigree_features,talent_training
from universal_baseball.storage import sha256_file


def main():
    pre=json.loads((OUT/'prefit-manifest.json').read_text());assert hashes()==pre['hashes']
    fit=json.loads((OUT/'fit-manifest.json').read_text());score=json.loads((OUT/'score-report.json').read_text())
    assert fit['prefit_sha256']==sha256_file(OUT/'prefit-manifest.json')
    assert fit['prediction_sha256']==sha256_file(OUT/'predictions.parquet')
    assert fit['nested_sha256']==sha256_file(OUT/'nested-talent.parquet')
    assert pre['draft_sha256']==sha256_file(OUT/'draft-evidence.parquet')
    p=pl.read_parquet(PANEL).filter(pl.col('origin_year')<=2022).sort('origin_year','player_id')
    draft=pl.read_parquet(OUT/'draft-evidence.parquet');assert draft['draft_year'].max()<=2022
    assert draft.columns==['draft_year','player_id','pick_number','school_class']
    assert not draft.select('draft_year','player_id','pick_number').is_duplicated().any()
    p=pedigree_features(p,draft)
    for year in sorted(p['origin_year'].unique()):
        base=p.filter(pl.col('origin_year')==year).drop(PEDIGREE)
        # Truncating future draft evidence cannot affect any prior snapshot.
        a=pedigree_features(base,draft).select(PEDIGREE)
        b=pedigree_features(base,draft.filter(pl.col('draft_year')<=year)).select(PEDIGREE)
        assert a.equals(b)
    nested=pl.read_parquet(OUT/'nested-talent.parquet')
    assert nested.select('origin_year','player_id').equals(p.select('origin_year','player_id'))
    assert len(fit['inner_fits'])==2*p['origin_year'].n_unique()
    for n in fit['inner_fits']:
        t=talent_training(p,n['year'],n['horizon'])
        assert t.height==n['training_rows'] and t['player_id'].n_unique()==n['training_players']
        assert n['training_origins']==sorted(t['origin_year'].unique().to_list())
        assert n['latest_label'] is None or n['latest_label']<=n['year']
        assert n['supported']==(t.height>=200 and t['origin_year'].n_unique()>=2)
        q=nested.filter(pl.col('origin_year')==n['year'])
        assert (q[f"talent_supported_h{n['horizon']}"]==int(n['supported'])).all()
        pred=q[f"talent_rate_h{n['horizon']}"]
        if n['supported']:
            assert pred.is_finite().all() and pred.is_between(-5,10).all()
            assert set(n['used_features']).issubset(pre['columns'])
        else:assert pred.is_nan().all()
    p=p.join(nested,on=['origin_year','player_id'],validate='1:1',maintain_order='left')
    f=pl.read_parquet(OUT/'predictions.parquet');refs=pl.read_parquet(PREVIOUS/'predictions.parquet')
    assert not f.select('origin_year','player_id','horizon').is_duplicated().any()
    assert f.select(refs.columns).equals(refs)
    assert len(fit['workload_fits'])==36 and len(fit['mutations'])==4
    assert fit['prior_D_replay']['maximum_difference']==0
    assert all(n['maximum_difference']==0 for n in fit['mutations'])
    for n in fit['workload_fits']:
        t=active_training(p,n['year'],n['horizon'])
        assert n['training_rows']==t.height and n['training_players']==t['player_id'].n_unique()
        assert n['latest_label']<=n['year']
        np.testing.assert_allclose(t.group_by('player_id').agg(pl.col('identity_weight').sum())['identity_weight'],1.)
        extras={'T':TALENT,'P':PEDIGREE,'TP':TALENT+PEDIGREE}[n['arm']]
        assert set(n['used_features'])|set(n['dropped_features'])==set(pre['columns']+extras)
    for year,h in pre['folds']:
        g=f.filter((pl.col('origin_year')==year)&(pl.col('horizon')==h))
        q=p.filter(pl.col('origin_year')==year)
        assert g.select('player_id',*TALENT,*PEDIGREE).equals(q.select('player_id',*TALENT,*PEDIGREE))
        np.testing.assert_array_equal(g['actual_pa'],q[f'pa_h{h}'])
        for arm in ('T','P','TP'):
            assert g[arm+'_conditional'].is_finite().all() and g[arm+'_conditional'].is_between(1,750).all()
            prospect=g.filter(pl.col('prospect'))
            np.testing.assert_array_equal(prospect[arm+'_pa'],prospect['fixed_p']*prospect[arm+'_conditional'])
            np.testing.assert_array_equal(g.filter(~pl.col('prospect'))[arm+'_pa'],g.filter(~pl.col('prospect'))['B_pa'])
    c=cumulative(f);assert c.equals(pl.read_parquet(OUT/'cumulative-predictions.parquet'))
    assert set(c['origin_year'])=={2016,2021,2022}
    for h,q in [(str(h),f.filter(pl.col('horizon')==h)) for h in (1,2,3)]+[('cumulative',c)]:
        actual=summary(q.filter(pl.col('prospect')))
        saved=(score['cumulative'] if h=='cumulative' else score['annual'][h])['groups']['prospects']
        for a in ARMS:
            for k in ('rmse','mae','bias','aggregate_absolute_error'):
                np.testing.assert_allclose(actual['arms'][a][k],saved['arms'][a][k],rtol=1e-12,atol=1e-12)
    assert decision(score)==score['decision']
    for n,h in score['hashes'].items():assert sha256_file(OUT/n)==h
    if (PACKAGE/'manifest.json').exists():
        m=json.loads((PACKAGE/'manifest.json').read_text())
        for n,h in m['files'].items():assert sha256_file(PACKAGE/n)==h
        for n,h in m['code'].items():assert sha256_file(Path(n))==h
    print(json.dumps({'verified':True,'workload_heads':36,'nested_supported_heads':sum(n['supported'] for n in fit['inner_fits']),
        'prediction_rows':f.height,'future_mutations':4,'protected_outcomes_used':False,'production_forecasts_changed':False}))


if __name__=='__main__':main()
