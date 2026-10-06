"""Seal reviewed decision; never changes forecasts or fitted parameters."""
from pathlib import Path
import polars as pl
from run_minor_infield_play_share import ROOT, OUT, PUBLIC, read, verify, hashes
from run_hitter_finite_return_baseline import protections, save


def main():
    protections()
    fit=read(OUT/'fit-report.json'); verify(fit['hashes'])
    walks=read(OUT/'player-traces.json'); verify(walks['hashes'])
    assert len(walks['fit_replays'])==150
    assert all(r['max_error']<1e-12 for r in walks['fit_replays'])
    assert len(walks['cases'])==13 and all(c['status']=='walked' for c in walks['cases'])
    assert walks['annual_pooling_verified'] and walks['scores_independently_recomputed']
    assert all(len(c['origin_known_peers'])==3 for c in walks['cases'])
    needed=['fixed diagnostic','largest squared-loss improvement','largest squared-loss deterioration','largest false high','largest false low','ordinary active well-predicted','non-arrival largest absolute quality forecast']
    reasons={r for c in walks['cases'] for r in c['selection']}
    assert set(needed)<=reasons
    p=pl.read_parquet(OUT/'predictions.parquet')
    assert p.height==8172 and p['target_year'].max()==2025
    assert p.filter(pl.col('origin_year')>=2022).height==4852
    assert p.filter((pl.col('future_official_outs').fill_null(0)==0)&pl.col('quality').is_not_null()).is_empty()
    assert p.filter((pl.col('future_official_outs')>0)&pl.col('delivered').is_null()).height==3
    assert p.filter((pl.col('origin_year')>=2022)&(pl.col('future_official_outs')>0)&pl.col('delivered').is_null()).height==2
    intervals=fit['paired_recent_MSE_difference_complete_minus_benchmark']['interval95']
    assert intervals[0]<0<intervals[1]
    assert fit['recent_quality']['arms']['complete']['weighted_mse']>fit['recent_quality']['arms']['benchmark']['weighted_mse']
    docs=[ROOT/'docs/minor-infield-play-share-result.md',ROOT/'docs/minor-infield-play-share-player-walkthrough.md',ROOT/'docs/nonbatting-hitter-component-review.md',ROOT/'docs/nonbatting-hitter-milestone-plan.md']
    for path in docs:
        assert path.exists()
    result={'status':'bounded_comparison_and_component_review_complete','player_walkthrough_status':'complete',
        'decision':'do_not_promote_or_tune_this_recipe','execution_integrity':'passed',
        'training_support':'global fitting sufficient; conditional profiles sparse, lower-level talent untested',
        'predictive_promotion':'failed; negligible uncertain delivered gain, conditional error worsens',
        'baseball_review':'complete; role changes, unsupported conditional extrapolation and benchmark compression documented',
        'full_nonbatting_model_complete':False,'broader_app_goal_complete':False,'deployment_approved':False,
        'production_changed':False,'new_2026_outcomes_used':False,'saved_fit_replays':150,'player_origins_walked':13,
        'hashes':hashes([OUT/'fit-report.json',OUT/'player-traces.json',Path(__file__).resolve(),ROOT/'scripts/review_minor_infield_play_share.py',ROOT/'tests/test_minor_infield_play_share_support.py',*docs]),
        'next_gate':'Scale frozen catcher event/exposure extraction on a predeclared historical population; audit failures before skill fitting.'}
    save(OUT/'final-review.json',result); save(PUBLIC/'final-review.json',result)
    print(result['status'])


if __name__=='__main__':
    main()
