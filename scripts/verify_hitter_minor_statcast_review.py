"""Independent final source, support, peer-context and protection receipt."""
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
import finalize_hitter_minor_statcast_source as final

ROOT,OUT,SOURCE=final.ROOT,final.OUT,final.SOURCE


def read(p):return json.loads(Path(p).read_text(encoding='utf8'))


def main():
    assert not (OUT/'final-review.json').exists(),'Preserve final review'
    report=read(OUT/'source-report.json');base=read(SOURCE/'source-report.json');walk=read(OUT/'player-source-walkthrough.json')
    checked={}
    for r in [report,base,walk]:
        for group in ['input_hashes','output_hashes']:
            for p,h in r.get(group,{}).items():
                assert sha256_file(Path(p))==h,p;checked[p]=h
    annual=pl.read_parquet(OUT/'annual-launch-features.parquet');assert len(annual)==4255
    for y in range(2021,2025):
        q=pl.read_parquet(OUT/f'launch-events-{y}.parquet');a=annual.filter(pl.col('season')==y)
        assert q.unique(['game_pk','player_id','at_bat_number','pitch_number']).height==len(q)
        assert not q['venue_id'].null_count() and not q['league_id'].null_count()
        known=read(OUT/f'missing-physical-contacts-{y}.json')['cases'];assert len(known)=={2021:3,2022:2,2023:1,2024:1}[y]
        for r in a.iter_rows(named=True):
            player=q.filter((pl.col('player_id')==r['player_id'])&(pl.col('league_id')==r['league_id']))
            joint=player.filter(pl.col('complete_pair'));n=len(joint)
            air=joint.filter((pl.col('launch_speed')>=95)&pl.col('launch_angle').is_between(8,50)).height
            sweet=joint.filter((pl.col('launch_speed')>=95)&pl.col('launch_angle').is_between(8,32)).height
            assert n==r['measured_pair_contacts'] and air==r['hard_air_contacts'] and sweet==r['hard_sweet_spot_contacts']
            expected_missing=sum(k['player_id']==r['player_id'] and k['league_id']==r['league_id'] for k in known)
            assert r['official_nonbunt_contact_opportunities']==len(player)+expected_missing
            assert np.isclose(r['pair_coverage'],n/r['official_nonbunt_contact_opportunities'],atol=1e-12)
            assert (r['hard_air_fraction'] is None and n==0) or np.isclose(r['hard_air_fraction'],air/n,atol=1e-12)
        paired=pl.read_parquet(OUT/f'contact-boundary-reconciliation-{y}.parquet')
        assert paired.select((pl.col('source_contacts')+pl.col('known_missing_contacts')==pl.col('expected_contact_count')-pl.col('noncontact_AB')).all()).item()
    assert annual['measured_pair_contacts'].sum()==361530
    # Original peer identities are retained; expand their actual level exposure
    # so a late one-PA promotion cannot masquerade as a full AAA comparison.
    dated=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet')
    features=pl.read_parquet(ROOT/'reports/generated/hitter-preseason-readiness-v68/features.parquet')
    peers=[]
    for c in walk['cases']:
        o=c['origin'];assert not c['forecast_changed']
        assert np.isclose(c['current_rate_trace']['replayed_rate'],o['preseason_rate'],atol=1e-10)
        if o['next_pa']==0:assert o['actual_future_relative_rate'] is None
        for p in c['peers']:
            stats=dated.filter((pl.col('player_id')==p['player_id'])&pl.col('season').is_between(o['origin_year']-2,o['origin_year']))
            f=features.filter(pl.col('row_id')==p['row_id']);assert len(f)==1
            peers.append(dict(focal_player_id=o['player_id'],origin_year=o['origin_year'],peer=p,
                actual_dated_production=stats.to_dicts(),known_context=f.select('snapshot_level','age','draft_known','draft_rank',
                    'pooled_AAA_pa','pooled_AA_pa','pooled_Aplus_pa','pooled_A_pa','scout_listed_0','scout_rank_score_0').to_dicts()[0],
                peer_matching_is_a_diagnostic_not_certified_baseball_equivalence=True))
    final.write('peer-context-review.json',dict(cases=peers,original_identities_retained=True,
        concrete_limit='Langford original peers have only 1–5 AAA PA; AAA label alone is not relevant profile support.',
        no_model_or_peer_distance_tuned=True))
    doc=ROOT/'docs/hitter-minor-statcast-source-result.md';assert doc.exists()
    support=read(OUT/'training-support-review.json');assert support['independently_rechecked_folds']==35
    freeze=subprocess.run([sys.executable,'-X','utf8','scripts/verify_hitter_full_2026_freeze.py'],cwd=ROOT,
        check=True,capture_output=True,text=True)
    tests=subprocess.run([sys.executable,'-X','utf8','-m','pytest','-p','no:cacheprovider','-q',
        'tests/test_hitter_minor_statcast_source.py','tests/test_hitter_minor_statcast_review.py',
        'tests/test_hitter_statcast_measurement.py','tests/test_hitter_statcast_history.py',
        'tests/test_hitter_statcast_next_year.py','tests/test_mlb_contact_history.py'],cwd=ROOT,check=True,capture_output=True,text=True)
    final.write('final-review.json',dict(source_execution_integrity=True,all_player_game_boundaries_reconciled=True,
        all_launch_venues_resolved=True,annual_summaries=4255,complete_pairs=361530,all_joint_counts_independently_verified=True,
        player_walkthrough_status='complete',reviewed_player_origins=11,distinct_players=9,current_rate_heads_replayed=11,
        peer_context_expanded=True,chronological_support_folds_rechecked=35,full_profile_support=False,
        qualified_source_approved_for_bounded_experiment=True,predictive_fits=0,predictive_improvement_claimed=False,
        provider_original_vintage_known=False,camera_only_data_claimed=False,deployment_approved=False,
        protected_freeze=json.loads(freeze.stdout),focused_tests=tests.stdout,verified_input_and_output_files=len(checked),
        walkthrough_path=str(doc),walkthrough_sha256=sha256_file(doc),reviewer_sha256=sha256_file(Path(__file__)),
        artifact_hashes={str(p):sha256_file(p) for p in [OUT/'source-report.json',OUT/'player-source-walkthrough.json',
            OUT/'peer-context-review.json',OUT/'training-support-review.json',OUT/'annual-launch-features.parquet']}))
    print('Qualified source approved; 11 player walks, 35 support checks; no new forecasts.',tests.stdout.strip())


if __name__=='__main__':main()
