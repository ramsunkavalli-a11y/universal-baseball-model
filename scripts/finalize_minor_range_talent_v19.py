"""Seal the interpreted review separately from fitted/execution receipts."""
from collections import Counter
from pathlib import Path
import gzip
import json
import math

import numpy as np
import polars as pl

from verify_minor_range_talent_v19 import ROOT,OUT,PUBLIC,SOURCE,data,digest,near,score,same_scores
from run_hitter_finite_return_baseline import protections

NOTES={
 (2021,677951,6):'Witt has developing future range after a poor first MLB year; most change is penalty rather than counts. Arias measured; Downs cameo and Perez absent remain unknown. Two level-position training people cannot certify a rich individual grade.',
 (2021,665161,6):'Peña modest positive pooled quality is nearer baseline. AAA count signals erased; complex exposure is separate. Estevez and Davis lack SS labels; Fox cameo is not stable talent. Penalty causes most downgrade.',
 (2022,683011,6):'Volpe improves partly from favorable AA nonthrowing-error signal, partly penalty. AAA reliability zero. Rocchio measured; Mauricio and Tena insufficient SS quality, with Tena assist extrapolation. No certification from isolated Volpe gain.',
 (2021,682928,6):'Abrams count grade moves the wrong way despite persistent negative later SS range. Similar-age Rocchio develops positive range; Barreto absent and Groshans at 3B do not become zero SS talent.',
 (2022,678882,8):'Rafaela CF downgrade primarily weakens position baseline while count inputs have zero reliability. SS quality is negative and distinct, with assist extrapolation. Barrosa cameo, Mears and Doston unknown.',
 (2022,669364,4):'Edwards primary 2B label unknown because a positive 2024 exposure lacks valid native measurement. SS is separately measured and strongly negative. Westburg position-specific outcomes differ; Taylor cameo and Turang moved positions illustrate retention/selection.',
 (2022,687263,6):'Neto largest gain at equal penalties; unfavorable error signals help, but negative fitted assist coefficient is not an established baseball rule. Rafaela SS harmed; Rodriguez and Ozoria unknown. Count context and coefficient instability remain.',
 (2022,696285,8):'Jacob Young worst deterioration and false low: error-free counts erased; 97 percent of drop is changed baseline penalty. Positive future range in all three years; five level-position/one joint training person. Three nearest peers never yield MLB CF measurement.',
 (2022,669364,6):'Edwards SS largest false high; 71 AAA chances, three stage and zero joint training people. Turang mostly 2B, Wyatt Young and Hernandez absent. These outcomes do not validate a near-average SS prior.',
 (2022,686527,9):'Canzone ordinary median-error case worsens. Six complex chances receive 94.5 percent weight from unstable sparse reference moments, not MLB talent confidence. Fletcher just below cutoff, Leon cameo and Cedrola absent remain unknown.',
 (2022,641938,3):'Pabst complex 1B unsupported; matched baseline fallback preserves population but is uncertain borrowed prior, not receiving ability. Goldfarb, Schreiber and Melo lack later MLB labels.'}


def main():
    protections();assert not (OUT/'final-review.json.gz').exists()
    verified=data(OUT/'independent-review.json');walk=data(OUT/'player-walkthrough.json');diag=data(OUT/'recipe-diagnosis.json');report=data(OUT/'fit-report.json')
    for receipt in (verified,walk,diag):
        for p,h in receipt['hashes'].items():assert digest(Path(p))==h,p
    assert set(NOTES)=={tuple(s['key']) for s in walk['selection']}
    assert (walk['focal'],walk['peer_selections'],walk['unique_player_origins'],walk['position_walks'],walk['raw_reference_checks'])==(11,33,41,106,488)
    assert walk['missing_fixed'][0]['name']=='Bryce Eldridge' and len(walk['missing_fixed'])==1
    preds=pl.read_parquet(OUT/'predictions.parquet').to_dicts();key=lambda r:(r['origin_year'],r['player_id'],r['position'])
    wm={tuple(w['key']):w for w in walk['walks']};interpreted=[]
    for s in walk['selection']:
        k=tuple(s['key']);r=wm[k]['forecast']
        pool=[t for t in preds if t['origin_year']==r['origin_year'] and t['level']==r['level'] and t['position']==r['position'] and t['player_id']!=r['player_id']]
        chosen=sorted(pool,key=lambda t:(abs(t['age']-r['age']) if t['age'] is not None and r['age'] is not None else 999,
                                        abs(math.log1p(t['minor_outs'])-math.log1p(r['minor_outs'])),t['player_id']))[:3]
        assert [list(key(t)) for t in chosen]==s['peer_keys']
        assert all(wm[tuple(k)]['raw_reference_and_prediction_replayed'] for k in (s['key'],*s['peer_keys']))
        interpreted.append(dict(key=list(k),player_name=r['player_name'],main_review=NOTES[k],peer_keys=s['peer_keys']))
    for g in report['overall']:
        rs=[r for r in preds if r['origin_year']==g['origin']]
        for arm in ('baseline','candidate','neutral'):same_scores(score(rs,arm),g['scores'][arm])
    primary=next(g for g in report['overall'] if g['origin']==2022)
    improvement=primary['scores']['candidate']['rmse']<primary['scores']['baseline']['rmse'] and primary['scores']['candidate']['mae']<primary['scores']['baseline']['mae']
    uncertainty=primary['interval']['rmse_delta_interval'][1]<0
    harms=[g for g in report['groups'] if g['origin']==2022 and g['group'] in ('position','level','age_band') and g['scores']['baseline'] is not None
           and g['scores']['baseline']['people']>=10 and g['scores']['candidate']['rmse']>1.05*g['scores']['baseline']['rmse']]
    assert not improvement and not uncertainty and any(g['group']=='position' and g['value']==8 for g in harms)
    extreme=diag['supplemental_extreme_and_peers'][0]
    assert extreme['forecast']['player_name']=='Patrick Frick' and extreme['forecast']['support']['outside_feature_range'][19]
    assert extreme['forecast']['quality_rate'] is None and all(not p['native'] and not p['official'] for p in extreme['annual_paths'])
    # Check exact mirror bytes and seal every current numerical record. Canonical
    # .json references mean decompressed bytes; packed hashes remain explicit.
    mirrored={};canonical={}
    for p in sorted(PUBLIC.rglob('*')):
        if not p.is_file():continue
        local=OUT/p.relative_to(PUBLIC);assert local.exists() and p.read_bytes()==local.read_bytes(),p
        mirrored[str(p)]=digest(p)
        if p.name.endswith('.json.gz'):canonical[str(p)[:-3]]=digest(Path(str(p)[:-3]))
    paths=[Path(__file__),ROOT/'docs/defense-minor-range-v19-result.md',ROOT/'docs/defense-minor-range-repair-sequence.md',
           ROOT/'docs/defense-minor-range-v19-contract.md',ROOT/'docs/defense-minor-range-v19-storage-amendment.md',
           ROOT/'docs/defense-minor-range-v19-encoding-amendment.md',ROOT/'src/universal_baseball/minor_range_talent.py',
           ROOT/'tests/test_minor_range_talent.py',OUT/'predictions.parquet',OUT/'player-walkthrough.md',
           *[ROOT/'scripts'/n for n in ('run_minor_range_talent_v19.py','resume_minor_range_talent_v19.py','resume2_minor_range_talent_v19.py',
                                      'compress_minor_range_v19_evidence.ps1','verify_minor_range_talent_v19.py','review_minor_range_players_v19.py',
                                      'diagnose_minor_range_recipe_v19.py')]]
    final=dict(status='reviewed_count_recipe_not_promoted_reliability_repair_required',player_walkthrough_status='complete',
               predictive_screen=dict(primary_RMSE_and_MAE_improved=improvement,paired_RMSE_interval_below_zero=uncertainty,
                                      group_harms=harms,passed=False),
               execution_integrity='independent replay passed; not equivalent to predictive or deployment approval',
               training_support='sparse prospect joints; absent modern DSL/complex supervised levels; count extrapolation retained and flagged',
               reasonability='failed: changed baseline regularization drives most CF downgrades; unstable tiny-reference moments; extreme unsupported count grades',
               reviewed_cases=interpreted,supplemental_cases=[r['forecast']['player_name'] for r in diag['supplemental_extreme_and_peers']],
               selection_unchanged=True,source_reference_replay=walk['raw_reference_checks'],position_walks=106,unique_player_origins=41,
               no_global_count_rejection=True,diagnostics_not_new_candidate_selection=True,
               next_action='Contract and test source reliability/calibration first; then independently regularized count correction preserving baseline after walkthrough gate.',
               focused_tests=dict(count=28,command='.venv/Scripts/python.exe -X utf8 -m pytest tests/test_minor_range_talent.py tests/test_minor_fielding_counts.py -p no:cacheprovider -q',observed_exit_code=0),
               no_forecast_or_explorer_change=True,no_2026_outcome_access=True,goal_complete=False,
               previous_goal_turn='No defense progress: read-only Lovich explanation; revalidated sources and completed independent fits/reference/player review now.',
               unresolved=['Minor count recipe not safe as a practical grade; reliability and extrapolation require repair',
                           'Catcher historical minor-to-MLB quality support', 'Position-transfer quality and longer lower-minor trajectories',
                           'Delivered-value integration and full defense/WAR/control valuation', 'Separate Lovich batting defect remains open'],
               hashes={**canonical,**{str(p):digest(p) for p in paths}},packed_public_hashes=mirrored)
    payload=(json.dumps(final,indent=2,allow_nan=False)+'\n').encode()
    for folder in (OUT,PUBLIC):(folder/'final-review.json.gz').write_bytes(gzip.compress(payload,mtime=0))
    protections();print(json.dumps(dict(status=final['status'],player_walkthrough_status='complete',focal=11,peers=33,position_walks=106,
                                      supplemental=final['supplemental_cases'],mirrored_records=len(mirrored),goal_complete=False)),flush=True)


if __name__=='__main__':main()
