"""One fixed DP history versus neutral talent comparison; no fitted weights."""
from collections import defaultdict
from pathlib import Path
import json

import polars as pl
from universal_baseball.defense_double_play import history, profile, score, interval
from universal_baseball.storage import sha256_file
from verify_double_play_support_v22 import ROOT, read, write
from run_hitter_finite_return_baseline import protections

PUBLIC = ROOT/'reports/model-evidence/defense-double-play-talent-v23'
V22 = ROOT/'reports/model-evidence/defense-double-play-source-v22'


def main():
    protections()
    assert read(V22/'final-review.json.gz')['player_walkthrough_status'] == 'complete'
    PUBLIC.mkdir(parents=True, exist_ok=True)
    native_path = ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet'
    paths = [Path(__file__), ROOT/'src/universal_baseball/defense_double_play.py', ROOT/'tests/test_defense_double_play.py',
        ROOT/'docs/defense-double-play-talent-v23-contract.md', ROOT/'docs/defense-double-play-source-v22-count-correction.md',
        V22/'final-review.json.gz', V22/'labels.json.gz', native_path]
    write(PUBLIC/'preflight.json.gz', dict(before_forecast_generation=True, model_fits=0, learned_parameters=0,
        prior_outs=3000, recency=[1,.5,.25], no_2026_selection=True, traffic_limit_explicitly_accepted=True,
        hashes={str(p):sha256_file(p) for p in paths}))
    native = defaultdict(list)
    for r in pl.read_parquet(native_path).to_dicts():
        assert 2016 <= r['season'] <= 2025
        native[r['player_id']].append(r)
    all_rows = []
    for r in read(V22/'labels.json.gz'):
        if r['population'] == 'MLB_history':
            all_rows.append(dict(r, **history(native[r['player_id']], r['origin_year'], r['position'])))
    folds = []; predictions = []
    for year in (2021, 2022):
        current = [r for r in all_rows if r['origin_year'] == year]
        for fold in range(5):
            train = [r for r in all_rows if r['quality_rate'] is not None and r['window_end'] <= year and r['player_id']%5 != fold]
            test = [r for r in current if r['player_id']%5 == fold]
            assert {r['player_id'] for r in train}.isdisjoint(r['player_id'] for r in test)
            neighborhoods = defaultdict(set)
            for r in train:
                neighborhoods[profile(r)].add(r['player_id'])
            folds.append(dict(origin=year, held_fold=fold, training_people=len({r['player_id'] for r in train}),
                training_origins=sorted({r['origin_year'] for r in train}), test_rows=len(test), model_fits=0,
                training_windows_with_2020=sum(r['origin_year'] < 2020 <= r['window_end'] for r in train),
                training_keys=[[r['origin_year'],r['player_id'],r['position']] for r in train],
                profile_counts=[dict(identity=[year,r['player_id'],r['position']], profile=list(profile(r)),
                    distinct_training_people=len(neighborhoods[profile(r)])) for r in test]))
            for r in test:
                predictions.append(dict(r, fold=fold, distinct_profile_training_people=len(neighborhoods[profile(r)]),
                    sparse_profile=len(neighborhoods[profile(r)]) < 10))
    write(PUBLIC/'support.json.gz', folds)
    write(PUBLIC/'predictions.json.gz', predictions)
    results = []
    for year in (2021,2022):
        measured = [r for r in predictions if r['origin_year'] == year and r['quality_rate'] is not None]
        groups = []
        for kind in ('position','age','history_exposure'):
            keys = {'position':0,'age':1,'history_exposure':2}
            for group in sorted({profile(r)[keys[kind]] for r in measured}, key=str):
                subset = [r for r in measured if profile(r)[keys[kind]] == group]
                groups.append(dict(kind=kind, group=group, neutral=score(subset,'neutral'), candidate=score(subset,'candidate')))
        base = score(measured,'neutral'); candidate = score(measured,'candidate'); ci = interval(measured,23023 if year==2022 else 23022)
        failures = []
        if ci['interval_95'][1] >= 0: failures.append('no_supported_RMSE_gain')
        if candidate['mae'] > base['mae']: failures.append('MAE_worsens')
        if abs(candidate['bias']) > max(.15,abs(base['bias'])+.05): failures.append('bias_limit')
        for g in groups:
            if g['kind']=='position' and g['neutral']['people']>=10 and g['candidate']['rmse']>1.05*g['neutral']['rmse']:
                failures.append(f"position_{g['group']}_RMSE_harm")
        results.append(dict(origin=year, neutral=base, candidate=candidate, paired_RMSE=ci, groups=groups,
            quality_screen_failures=failures, eligible_rows=sum(r['origin_year']==year for r in predictions),
            fallback_rows=sum(r['origin_year']==year and r['fallback'] for r in predictions),
            sparse_rows=sum(r['origin_year']==year and r['sparse_profile'] for r in predictions),
            unknown_quality_rows=sum(r['origin_year']==year and r['quality_rate'] is None for r in predictions)))
    write(PUBLIC/'report.json.gz', dict(results=results, model_fits=0, learned_parameters=0,
        player_walkthrough_status='pending', predictive_claim='provisional_development', deployment_approved=False,
        hashes={str(p):sha256_file(p) for p in (PUBLIC/'preflight.json.gz',PUBLIC/'support.json.gz',PUBLIC/'predictions.json.gz')}))
    print(json.dumps(results,indent=2),flush=True)
    protections()


if __name__=='__main__':
    main()
