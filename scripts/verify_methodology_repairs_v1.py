"""Independent accounting checks on the three completed repair diagnostics."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file

ART=Path('model_artifacts')


def load(path):return json.loads(path.read_text())


def main():
    source=ART/'defensive-event-source-repair-v1-2026-09-25'
    report=load(source/'report.json');selection=load(source/'selection.json')
    assert len(selection['games'])==128 and selection['selected_before_events']
    assert all(g['season']<2026 for g in selection['games'])
    checks=load(source/'box-reconciliation.json')
    assert len(checks)==1024 and all(r['official']==r['ledger'] for r in checks)
    ledger=pl.DataFrame(load(source/'responsibility-candidate.json'))
    sums=ledger.group_by('game_pk','at_bat_index').agg(pl.col('share').sum())
    assert sums.height==2875
    np.testing.assert_array_equal(sums['share'].to_numpy(),np.ones(sums.height))
    assert not ledger['ex_ante_opportunity_certified'].any()
    assert report['battery_attribution_gate']=='not_certified'
    work=ART/'hitter-common-weight-v1-2026-09-25';score=load(work/'scores.json')
    for n,h in score['hashes'].items():assert sha256_file(work/n)==h
    replay=load(work/'replay.json')
    assert len(replay['checks'])==12 and all(r['max_difference']<=1e-9 for r in replay['checks'])
    w=pl.read_parquet(work/'predictions.parquet').sort('horizon','origin_year','player_id')
    old=pl.read_parquet(ART/'hitter-conditional-workload-v1-2026-09-23/predictions.parquet').sort('horizon','origin_year','player_id')
    for col in old.columns:assert w[col].equals(old[col]),col
    expected=np.where(w['prospect'],w['fixed_p']*w['W_conditional'],w['D_pa'])
    np.testing.assert_array_equal(expected,w['W_pa'])
    assert w['W_conditional'].is_between(1,750).all()
    assert (w['origin_year']+w['horizon']).max()<=2025
    wc=pl.read_parquet(work/'cumulative.parquet').filter(pl.col('prospect'))
    delta=wc.group_by('origin_year').agg((((pl.col('W_pa')-pl.col('actual_pa'))**2)-
        ((pl.col('D_pa')-pl.col('actual_pa'))**2)).mean().alias('d'))['d'].mean()
    np.testing.assert_allclose(delta,score['primary']['delta'],atol=1e-9)
    fact=ART/'hitter-batting-factorial-v1-2026-09-25';fr=load(fact/'report.json')
    for n,h in fr['hashes'].items():assert sha256_file(fact/n)==h
    f=pl.read_parquet(fact/'predictions.parquet')
    original=pl.read_parquet(ART/'hitter-integrated-opportunity-value-v1-2026-09-25/predictions.parquet')
    for col in original.columns:assert f.sort('horizon','origin_year','player_id')[col].equals(original.sort('horizon','origin_year','player_id')[col]),col
    for wname in ('E','H'):
        for r,field in [('anchor','performance_anchor'),('horizon','rate')]:
            prod=f[wname+'_pa'].to_numpy()*f[field].to_numpy()/600
            marginal=f['B_value'].to_numpy()+(f[wname+'_pa'].to_numpy()-f['B_pa'].to_numpy())*f[field].to_numpy()/600
            for name,pred in [(f'{wname}_{r}_product',prod),(f'{wname}_{r}_marginal',marginal)]:
                np.testing.assert_allclose(f[name],pred,atol=1e-12,rtol=0)
                np.testing.assert_allclose(f[name+'_expanded'],pred+f[wname+'_other_runs'].to_numpy()/10,atol=1e-12,rtol=0)
    for row in fr['residual_decomposition']:
        np.testing.assert_allclose(row['mse_change'],row['cross_term']+row['residual_square'],atol=1e-10)
    for row in fr['component_addition_decomposition']+fr['outfield_replacement_decomposition']:
        np.testing.assert_allclose(row['total_mse_change'],row['component_mse_change']+row['cross_error_term'],atol=1e-10)
    # Verify cumulative sums independently of the diagnostic builder.
    c=pl.read_parquet(fact/'cumulative.parquet')
    annual=f.group_by('origin_year','player_id').agg(pl.len().alias('n'),
        pl.col('H_anchor_product','E_anchor_product','actual_value').sum()).filter(pl.col('n')==3).sort('origin_year','player_id')
    assert c.height==12891
    for col in ('H_anchor_product','E_anchor_product','actual_value'):
        np.testing.assert_allclose(c[col],annual[col],atol=1e-12,rtol=0)
    delta=c.group_by('origin_year').agg((((pl.col('H_anchor_product')-pl.col('actual_value'))**2)-
        ((pl.col('E_anchor_product')-pl.col('actual_value'))**2)).mean().alias('d'))['d'].mean()
    np.testing.assert_allclose(delta,fr['primary']['delta'],atol=1e-12)
    print(json.dumps({'verified':True,'source_games':128,'box_checks':1024,'old_D_replays':12,
        'new_conditional_heads':12,'workload_rows':w.height,'factorial_rows':f.height,
        'cumulative_rows':c.height,'production_changed':False,'protected_outcomes_used':False}))


if __name__=='__main__':main()
