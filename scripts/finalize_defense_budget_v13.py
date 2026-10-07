"""Verify source walks, record limits and seal the completed source milestone."""

from pathlib import Path
import json
import math
import polars as pl
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/defense-budget-v13'
PUBLIC=ROOT/'reports/model-evidence/defense-budget-v13'


def read(p): return json.loads(p.read_text(encoding='utf8'))


def main():
    protections(); source=read(OUT/'source-review.json'); v=read(OUT/'independent-verification.json'); w=read(OUT/'player-walkthrough.json')
    assert v['source_integrity']=='pass' and w['player_walkthrough_status']=='complete'
    for receipt in (source,v,w):
        for p,h in {**receipt.get('hashes',{}),**receipt.get('output_hashes',{})}.items(): assert sha256_file(Path(p))==h,p
    q=pl.read_parquet(ROOT/'reports/generated/defense-transition-v10/predictions.parquet').to_dicts()
    f={r['row_id']:r for r in pl.read_parquet(ROOT/'reports/generated/defense-repertoire-v9/features.parquet').iter_rows(named=True)}
    raw=pl.read_parquet(ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet')
    checked=0
    for case in w['cases']:
        a=case['primary']; origin=a['origin']; pid=a['player_id']; role=a['primary_role']
        choices=[r for r in q if r['origin_year']==origin and r['player_id']!=pid and r['stage']==a['stage'] and f[r['row_id']]['repertoire_primary_role']==role]
        def distance(r):
            age=abs(r['age']-a['age']) if r['age'] is not None and a['age'] is not None else 100.
            return age+abs(math.log1p(r['pa_0'])-math.log1p(a['current_MLB_PA'])),r['player_id']
        assert case['eligible_origin_role_stage_peers']==len(choices)
        assert [p['player_id'] for p in case['peers']]==[r['player_id'] for r in sorted(choices,key=distance)[:3]]
        for p in [a,*case['peers']]:
            r=next(r for r in q if r['player_id']==p['player_id'] and r['origin_year']==origin)
            assert math.isclose(p['saved_own_DH']+p['saved_prior_DH'],r['repair_10'],abs_tol=1e-9)
            assert p['expected_PA']==r['preseason_pa'] and p['actual_PA']==r['next_pa']
            for yr in p['source_history']:
                s=raw.filter((pl.col('season')==yr['season'])&(pl.col('normalized_level')==yr['level'])&(pl.col('player_id')==p['player_id']))
                assert s.height==yr['source_rows']
                for pos in yr['positions']:
                    z=s.filter(pl.col('position_code')==pos['position_code'])
                    assert z['fielding_outs'].sum()==pos['fielding_outs'] and z['games_started'].sum()==pos['games_started']
            assert math.isclose(p['source_only_forecast_position_run_delta'],-17.5*p['source_only_own_DH_delta']/162.,abs_tol=1e-12)
            assert math.isclose(p['reviewed_actual_position_runs'],p['original_actual_position_runs']+p['actual_position_source_delta'],abs_tol=1e-12)
            checked+=1
    assert checked==28 and len(w['negative_controls'])==2
    paths=[Path(__file__),ROOT/'docs/defense-budget-v13-result.md',ROOT/'docs/defense-budget-v13-source-contract.md',
           ROOT/'docs/defense-budget-v13-rule-source-amendment.md',ROOT/'docs/defense-budget-v13-execution-amendment.md',
           ROOT/'scripts/audit_defense_budget_v13.py',ROOT/'scripts/verify_defense_budget_v13.py',
           ROOT/'scripts/review_defense_budget_v13.py',ROOT/'src/universal_baseball/defense_budget_source.py',
           ROOT/'tests/test_defense_budget_source.py',OUT/'source-review.json',OUT/'source-summary.json',
           OUT/'reviewed-DH-starts.parquet',OUT/'independent-verification.json',OUT/'player-walkthrough.json']
    result=dict(status='source_milestone_complete_not_forecast_promotion',player_walkthrough_status='complete',
        reviewed_player_records=checked,negative_controls=2,source_integrity='pass',new_fits=0,
        data_correction='65 certified dual P/DH starts in 2022/2023/2025; additive source view only.',
        disposition='Use reviewed DH measurements in the next contracted matched budget comparison.',
        unresolved=['Propagate corrected source to training and forecast inputs under the next contract.',
            'Mixed-rule pooled DH priors do not explicitly transport opportunity into the universal-DH environment.',
            'Known pure DH versus unknown repertoire; tiny old OF fallback is not a current role.',
            'Role changes, cohort remainder and scarce SS jobs require a coherent individual allocation, not blanket scaling.',
            'Coarse highest-level/primary-role labels do not certify comparable minor development or defensive quality.',
            'Sparse/minor talent transfer and longer-horizon defense remain unfinished.',
            'Lovich batting defect remains a separate open repair.'],
        protected_outcomes_used=False,forecast_or_explorer_changed=False,active_defense_goal_complete=False,
        hashes={str(p):sha256_file(p) for p in paths})
    for d in (OUT,PUBLIC): save(d/'final-review.json',result)
    protections(); print('Source milestone sealed, all 28 source walks checked; defense goal remains active.',flush=True)


if __name__=='__main__': main()
