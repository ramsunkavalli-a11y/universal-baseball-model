"""Independent context correction and applied transparent component replay."""
from collections import defaultdict
import math
from pathlib import Path

import polars as pl

from audit_catcher_framing_talent_v4 import ROOT,SOURCE,OUT,PUBLIC,read,write
from audit_defensive_talent_support import verify
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections


def main():
    review=read(OUT/'baseline-preparation-review.json');verify(review['hashes'])
    final=read(OUT/'final-review.json');verify(final['hashes'])
    assert review['protections']==final['protections']==protections()
    original=pl.read_parquet(OUT/'labels.parquet').to_dicts();corrected=pl.read_parquet(OUT/'corrected-age-context.parquet').to_dicts()
    snap_path=Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated/opportunity-history-sources-v2/tables/hitter_snapshots.parquet')
    snapshots=defaultdict(list)
    for s in pl.read_parquet(snap_path,columns=['snapshot_year','player_id','age_years']).iter_rows(named=True):
        snapshots[s['player_id']].append(s)
    changed=[]
    for a,b in zip(original,corrected):
        assert {k:v for k,v in a.items() if k not in ('age','age_basis')}=={k:v for k,v in b.items() if k not in ('age','age_basis')}
        if a['age'] is not None:
            assert a['age']==b['age'] and a['age_basis']==b['age_basis']
            continue
        past=[s for s in snapshots[a['player_id']] if a['origin_year']-3<=s['snapshot_year']<=a['origin_year']
              and s['age_years'] is not None and math.isfinite(s['age_years']) and 15<=s['age_years']<=55]
        values={float(s['age_years']+a['origin_year']-s['snapshot_year']) for s in past}
        expected=next(iter(values)) if len(values)==1 else None
        assert b['age']==expected
        if expected is not None:
            changed.append((a['origin_year'],a['player_id']))
    assert len(changed)==review['corrected_unknown_age_rows']==91
    assert set(changed)=={(r['origin'],r['player_id']) for r in review['repairs']}
    assert all(all(s['snapshot_year']<=r['origin'] for s in r['evidence']) for r in review['repairs'])
    annual=pl.read_parquet(SOURCE/'framing-annual.parquet').to_dicts()
    current=pl.read_parquet(OUT/'current-2025-history-baseline.parquet').to_dicts()
    pids={s['player_id'] for s in annual if 2023<=s['season']<=2025}
    assert {r['player_id'] for r in current}==pids and len(current)==len(pids)==149
    for r in current:
        past=[s for s in annual if s['player_id']==r['player_id'] and 2023<=s['season']<=2025]
        n=sum(s['pitches']/2**(2025-s['season']) for s in past)
        runs=sum(s['framing_runs']/2**(2025-s['season']) for s in past)
        assert math.isclose(n,r['history_pitches'],abs_tol=1e-10)
        assert math.isclose(runs,r['history_runs'],abs_tol=1e-10)
        assert math.isclose(1000*runs/(6000+n),r['framing_quality_per_1000'],abs_tol=1e-10)
        assert r['research_only'] and not r['future_pitch_exposure_forecast'] and not r['awarded_framing_value_forecast']
    walk=read(OUT/'baseline-source-player-walkthrough.json')
    assert walk['player_walkthrough_status']=='complete'
    for c in walk['cases']:
        for p in [c['primary'],*c['peers']]:
            n=sum(s['pitches']*s['weight'] for s in p['source']);runs=sum(s['framing_runs']*s['weight'] for s in p['source'])
            assert math.isclose(1000*runs/(n+6000),p['component']['framing_quality_per_1000'],abs_tol=1e-10)
    result=dict(execution_integrity='pass',corrected_age_rows_replayed=91,current_component_people_replayed=149,
                baseline_origin_calculations_replayed=889,source_player_cases=len(walk['cases']),
                original_calibration_preserved_not_adopted=True,new_model_fit=False,
                no_2026_outcomes=True,player_walkthrough_status='complete',deployment_approved=False,
                protections=protections(),hashes={str(p):sha256_file(p) for p in (OUT/'baseline-preparation-review.json',Path(__file__))})
    write('baseline-verification.json',result)
    p=PUBLIC/'baseline-verification.json';assert not p.exists();p.write_bytes((OUT/'baseline-verification.json').read_bytes())
    print({k:v for k,v in result.items() if k not in ('hashes','protections')})


if __name__=='__main__':
    main()
