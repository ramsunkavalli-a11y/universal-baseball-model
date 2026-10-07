"""Independent source replay; measurement certification is not talent validation."""
import json
import math

import polars as pl

from audit_defensive_talent_support import verify
from audit_catcher_native_opportunity_v3 import ROOT, OUT as PILOT
from extend_catcher_native_opportunity_v3 import OUT, PUBLIC
from source_defensive_positions_v2 import embedded
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file


def main():
    protected=protections()
    pilot=json.loads((PILOT/"source-review.json").read_text(encoding="utf8"))
    modern=json.loads((OUT/"source-review.json").read_text(encoding="utf8"))
    for r in (pilot,modern):
        verify(r["hashes"])
        assert r["player_walkthrough_status"]=="complete" and r["protections"]==protected
    frame=pl.read_parquet(OUT/"framing-annual.parquet")
    assert frame['season'].min()==2018 and frame['season'].max()==2025
    annual={(r['season'],r['player_id']):r for r in frame.iter_rows(named=True)}
    rebuilt=[]
    for y in range(2018,2026):
        txt=(OUT/f'framing-{y}.response').read_text(encoding='utf8')
        params=embedded(txt,'serverParams')
        assert int(params['seasonStart'])==int(params['seasonEnd'])==y and params['minPitches']==1
        data=embedded(txt,'data')
        assert len(data)==len({r['id'] for r in data})
        assert any(abs(r['rv_tot'])>1e-12 for r in data)
        for r in data:
            a=annual[y,r['id']]
            assert a['pitches']==r['pitches'] and a['shadow_pitches']==r['pitches_shadow']
            assert a['framing_runs']==r['rv_tot']
            assert math.isclose(a['rate_per_1000'],1000*r['rv_tot']/r['pitches'],abs_tol=1e-12)
            rebuilt.append((y,r['id']))
    assert len(rebuilt)==frame.height==878 and len(set(rebuilt))==frame.height
    old=pl.read_parquet(PILOT/'framing-pilot.parquet').filter(pl.col('season')==2016)
    assert old.height==104 and old['framing_runs'].null_count()==104 and old['rate_per_1000'].null_count()==104
    assert old['framing_measurement_valid'].sum()==0
    for y in (2016,2019,2025):
        qa=embedded((PILOT/f'framing-{y}.response').read_text(encoding='utf8'),'data')
        aa=embedded((PILOT/f'framing-{y}-all.response').read_text(encoding='utf8'),'data')
        q={r['id']:r for r in qa};a={r['id']:r for r in aa}
        assert set(q)<=set(a)
        for pid,r in q.items():
            assert r['pitches']==a[pid]['pitches'] and r['rv_tot']==a[pid]['rv_tot']
    walks=[json.loads((p/'player-walkthrough.json').read_text(encoding='utf8')) if p==PILOT else
           json.loads((p/'source-player-walkthrough.json').read_text(encoding='utf8')) for p in (PILOT,OUT)]
    assert all(w['player_walkthrough_status']=='complete' for w in walks)
    result=dict(source_replay='pass',modern_rows_replayed=frame.height,modern_people=frame['player_id'].n_unique(),
                pilot_source_cases=len(walks[0]['cases']),extension_source_cases=len(walks[1]['cases']),
                player_walkthrough_status='complete',qualification_setting_verified=True,
                original_qualified_anchors_unchanged=True,pre2018_placeholder_quarantine_verified=True,
                model_fit=False,predictive_improvement_established=False,deployment_approved=False,
                protections=protected,hashes={str(p):sha256_file(p) for p in (PILOT/'source-review.json',OUT/'source-review.json',
                                                                                  ROOT/'scripts/verify_catcher_native_opportunity_v3.py')})
    save(OUT/'verification.json',result)
    save(PUBLIC/'verification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('hashes','protections')},indent=2))


if __name__=='__main__':
    main()
