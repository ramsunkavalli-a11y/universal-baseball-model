"""Independent label checks and completed human source/player interpretation."""
import json
import shutil
from pathlib import Path
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
import audit_hitter_followup_support as audit

NOTES={
    600524:'Nunez arrives only in Years 5-6 with tiny samples; neither next-year nonarrival nor those rates measures his latent talent.',
    600869:'Candelario similarly arrives late; 14 PA and 142 PA give quite different noisy observed rates. Most origin peers do not arrive inside six years.',
    624641:'Sosa has only 13 PA within six years. A complete calendar window need not cover the useful portion of a player career.',
    642423:'Sierra arrives but batting production remains poor/variable. Peer Siri arrives in Year 8, beyond the window; zero window PA is not failed career.',
    646240:'Devers enters in Year 3, then has a worse second observed season before improvement. 2020 Year 6 is short, not missing.',
    660670:'Acuna enters Year 3 with strong performance. Only two exact-group peers exist; the source must not manufacture a larger comparable set.',
    670867:'Maitan never bats in the six years; his sole exact-group peer Vientos enters in Year 5. Future nonarrival is not an observed zero rate.',
    624413:'Alonso already has immediate upper-level support. Six-year labels do not fix the 215-versus-693 next-year workload miss by themselves.',
    592450:'Judge has extensive immediate support, but broad age/exposure peers do not match superstar talent. All outcomes after 2025 stay null.',
    701762:'Kurtz gains coarse later-arrival analogues but still zero elite-entry refined support. Never justify his miss by weaker unranked thin-sample peers.',
    821181:'Caceres has later-arrival support, not immediate ability validation. Actual no-PA next year leaves batting talent unobserved; later years remain censored.',
}


def main():
    out=audit.OUT; report=audit.read(out/'report.json');cases=audit.read(out/'cases.json')
    assert not (out/'final-report.json').exists(),'Preserve completed review'
    for path,digest in report['input_and_output_hashes'].items(): assert sha256_file(Path(path))==digest,path
    target=pl.read_parquet(audit.ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet')
    values={(s['season'],s['player_id']):s for s in target.iter_rows(named=True)}
    env={s['season']:s for s in target.unique('season').iter_rows(named=True)}
    reviewed=[];observations=0
    assert {c['origin']['player_id'] for c in cases}==set(NOTES)
    for c in cases:
        origin=c['origin'];assert all(s['season']<=origin['origin_year'] for s in c['dated_stats'])
        later=[]
        for p in c['annual_paths']:
            for row in p['annual_outcomes']:
                y=row['season'];pid=p['player_id'];assert y==origin['origin_year']+row['followup_year']
                if y>2025:
                    assert not row['observed'] and row['mlb_pa'] is None and row['batting_rate'] is None and row['component_value'] is None
                    continue
                actual=values.get((y,pid));pa=actual['mlb_pa'] if actual else 0
                assert row['mlb_pa']==pa and row['observed']
                if pa:
                    e=env[y];rate=600*(actual['component_war']/pa-570*e['schedule_fraction']/e['league_pa'])
                    assert abs(rate-row['batting_rate'])<1e-10
                else: assert row['batting_rate'] is None and row['component_value']==0
                observations+=1
            history=target.filter((pl.col('player_id')==p['player_id'])&(pl.col('season')>origin['origin_year'])&(pl.col('mlb_pa')>0))
            first=int(history['season'].min()) if len(history) else None
            later.append(dict(player_id=p['player_id'],player_name=p['player_name'],
                first_observed_post_origin_MLB_year=first,
                first_observed_post_origin_horizon=first-origin['origin_year'] if first else None,
                observation_ends=2025,not_career_failure_if_absent=True))
        if origin['player_id']==642423:
            siri=next(p for p in later if p['player_id']==642350)
            assert siri['first_observed_post_origin_horizon']==8
        reviewed.append(dict(row_id=origin['row_id'],player_id=origin['player_id'],name=origin['player_name'],
            assessment=NOTES[origin['player_id']],beyond_window_source_context=later,review_status='complete'))
    audit.write('reviewed-cases.json',reviewed)
    paths=[out/'report.json',out/'cases.json',out/'reviewed-cases.json',Path(__file__),
        audit.ROOT/'docs/hitter-followup-support-result.md',audit.ROOT/'tests/test_hitter_followup.py']
    audit.write('final-report.json',dict(no_new_fits=True,current_forecasts_changed=False,
        player_walkthrough_status='complete',reviewed_cases=len(reviewed),independently_checked_observed_case_and_peer_years=observations,
        disposition='Use mature annual horizon-specific labels for a bounded sharing comparison, not cumulative windows or immediate DSL talent certification',
        protected_outcomes_used=False,frozen_forecast_changed=False,deployment_approved=False,full_goal_complete=False,
        source_and_execution_hashes=report['input_and_output_hashes'],review_hashes={str(p):sha256_file(p) for p in paths}))
    evidence=audit.ROOT/'reports/model-evidence/hitter-followup-support';evidence.mkdir(parents=True,exist_ok=True)
    for name in ['report.json','cases.json','reviewed-cases.json','final-report.json']:
        shutil.copyfile(out/name,evidence/name)
        assert sha256_file(out/name)==sha256_file(evidence/name)
    print('Eleven actual player walks complete; observed labels independently checked:',observations)


if __name__=='__main__': main()
