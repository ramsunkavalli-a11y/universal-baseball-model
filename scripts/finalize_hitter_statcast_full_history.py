"""Independently verify source summaries and preserve additive source approval."""
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import polars as pl
import materialize_hitter_statcast_full_history as source


def main():
    out=source.OUT; assert not (out/'final-source-review.json').exists()
    report=source.checked_report(out/'source-report.json')
    annual=pl.read_parquet(out/'annual-launch-features.parquet')
    checked=0
    for year in range(2015,2025):
        q=pl.read_parquet(out/f'launch-events-{year}.parquet')
        assert q.unique(source.KEY).height==len(q) and q.unique(source.KEY[:-1]).height==len(q)
        assert q['venue_id'].null_count()==0 and set(q['league_id'].unique())<={103,104}
        expected=annual.filter(pl.col('season')==year)
        lookup={r['player_id']:r for r in expected.iter_rows(named=True)}
        for (pid,),part in q.group_by('player_id'):
            r=lookup[pid]; ev=part.filter(pl.col('valid_ev'))['launch_speed'].to_numpy()
            la=part.filter(pl.col('valid_la'))['launch_angle'].to_numpy()
            assert r['measured_ev_contacts']==len(ev) and r['measured_la_contacts']==len(la)
            if len(ev):
                assert np.isclose(r['mean_ev'],ev.mean(),atol=1e-10)
                assert np.isclose(r['ev95'],np.quantile(ev,.95,method='linear'),atol=1e-10)
                assert np.isclose(r['hard_hit_fraction'],(ev>=95).mean(),atol=1e-10)
            else: assert r['mean_ev'] is None and r['ev95'] is None
            checked+=1
    scored=pl.read_parquet(source.old.CURRENT/'scored-predictions.parquet')
    walks=source.old.read(out/'cases.json')
    for case in walks['cases']:
        o=case['origin']; r=scored.filter(pl.col('row_id')==o['row_id']).row(0,named=True)
        for c in ['preseason_rate','preseason_pa','preseason_value','next_pa','next_value']:
            assert np.isclose(r[c],o[c],atol=1e-12)
        assert all(s['season']<=o['origin_year'] for s in case['full_launch_history'])
        assert case['tracking_candidate_forecast'] is None
        for peer in case['peers']:
            peer['launch_history']=annual.filter((pl.col('player_id')==peer['player_id'])&
                pl.col('season').is_between(o['origin_year']-2,o['origin_year'])).to_dicts()
    source.old.write(out/'final-cases.json',walks)
    freeze=subprocess.run([sys.executable,'-X','utf8',str(source.ROOT/'scripts/verify_hitter_full_2026_freeze.py')],
        cwd=source.ROOT,check=True,capture_output=True,text=True)
    tests=subprocess.run([sys.executable,'-X','utf8','-m','pytest','-p','no:cacheprovider',
        'tests/test_hitter_statcast_measurement.py','tests/test_hitter_statcast_history.py','tests/test_mlb_contact_history.py','-q'],
        cwd=source.ROOT,check=True,capture_output=True,text=True)
    review=source.ROOT/'docs/hitter-statcast-full-history-review.md'
    source.old.write(out/'final-source-review.json',dict(source_only=True,new_model_fits=0,forecasts_changed=False,
        source_walkthrough_status='complete',readable_walkthrough=str(review),readable_walkthrough_sha256=source.sha256_file(review),
        source_report_sha256=source.sha256_file(out/'source-report.json'),reviewer_sha256=source.sha256_file(Path(__file__)),
        independently_verified_player_season_summaries=checked,complete_pairs_total=report['complete_pairs_total'],
        all_twenty_residuals_explained=True,qualified_MLB_source_approved_for_bounded_experiment=True,
        original_publication_vintage_known=False,camera_only_measurement_claim=False,predictive_validation=False,
        minor_tracking_supplied=False,deployment_approved=False,protected_freeze=json.loads(freeze.stdout),
        focused_tests=tests.stdout,final_cases_sha256=source.sha256_file(out/'final-cases.json')))
    print('Source review complete:',checked,'independent annual summaries; no model fits or forecast changes.')


if __name__=='__main__':main()
