"""Seal and fit origin-local overseas component inputs; no forecast promotion."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

import polars as pl

from universal_baseball.foreign_component_translation import References, fit, profile, training_pairs
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/generated/foreign-component-translation'
INPUTS = ROOT / 'reports/generated/foreign-origin-inputs'
NPB = ROOT / 'reports/generated/npb-hitting-history/reviewed-batting.parquet'
KBO = ROOT / 'reports/generated/kbo-identity-overlay/reviewed-batting.parquet'
DOMESTIC = ROOT / 'reports/generated/practical-hitter-v31/dated-stints.parquet'
CONTRACT = ROOT / 'docs/hitter-foreign-component-integration-contract.md'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def save(path, obj):
    if path.exists():
        raise ValueError(f'Preserve existing artifact {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8', newline='\n')


def verify(mapping):
    for path, digest in mapping.items():
        if sha256_file(ROOT / path) != digest:
            raise ValueError(f'Source hash changed {path}')


def sources():
    rows = []
    for league, path in [('NPB', NPB), ('KBO', KBO)]:
        for r in pl.read_parquet(path).iter_rows(named=True):
            rows.append(dict(r, league=league))
    mapping = dict(pa='plate_appearances', hits='hits', doubles='doubles', triples='triples',
                   hr='home_runs', bb='base_on_balls', ibb='intentional_walks', hbp='hit_by_pitch', so='strike_outs')
    domestic = pl.read_parquet(DOMESTIC).filter((pl.col('season') <= 2024) & (pl.col('bucket') == 'MLB'))
    for r in domestic.iter_rows(named=True):
        rows.append(dict(player_id=r['player_id'], season=r['season'], league='MLB',
                         **{k: r[v] for k,v in mapping.items()}))
    return rows


def cells(inputs):
    grouped = defaultdict(list)
    for r in inputs:
        own = player_fold(r['player_id'])
        for outer in range(5):
            excluded = tuple(sorted({outer, own}))
            grouped[r['origin_year'], excluded].append(dict(candidate_key=r['candidate_key'], outer_fold=outer))
    return grouped


def prepare():
    if OUT.exists():
        raise ValueError('Inspect partial or completed preparation; do not restart')
    reviewed = read(INPUTS / 'independent-review.json')
    verify(reviewed['hashes'])
    paths = [CONTRACT, Path(__file__), ROOT / 'src/universal_baseball/foreign_component_translation.py',
             ROOT / 'tests/test_foreign_component_translation.py', ROOT / 'src/universal_baseball/post_arrival_history.py',
             NPB, KBO, DOMESTIC, INPUTS / 'independent-review.json', INPUTS / 'origin-inputs.json',
             INPUTS / 'pair-role-evidence.json', INPUTS / 'reviewed-cases.json']
    hashes = {str(p.relative_to(ROOT)): sha256_file(p) for p in paths}
    inputs = read(INPUTS / 'origin-inputs.json')['rows']
    pairs = read(INPUTS / 'pair-role-evidence.json')['pairs']
    if len(inputs) != 641 or len({r['candidate_key'] for r in inputs}) != 641:
        raise ValueError('Changed sealed input membership')
    refs = References(sources())
    checks = []
    for (year, excluded), members in sorted(cells(inputs).items()):
        pool = training_pairs(pairs, year, excluded)
        check = dict(origin_year=year, excluded_folds=list(excluded), members=members,
                     pairs=len(pool), people=len({p['player_id'] for p in pool}),
                     people_by_league={l: len({p['player_id'] for p in pool if p['a']==l}) for l in ['NPB','KBO']},
                     max_target_year=max((p['through_year'] for p in pool), default=None),
                     mover_keys=[[p['player_id'],p['a'],p['from_year'],p['through_year']] for p in pool])
        for r in [r for r in inputs if r['candidate_key'] in {m['candidate_key'] for m in members}]:
            if player_fold(r['player_id']) not in excluded or r['origin_year']!=year:
                raise ValueError('Generated input is not player-separated')
            refs.get('MLB',year,excluded)
            for l in ['NPB','KBO']:
                for lag in range(3):
                    s=r['foreign_history_counts'][f'{l}_{lag}']
                    if s['counts']['pa']>0:
                        refs.get(l,s['season'],excluded)
        checks.append(check)
    reference_summary = []
    for (league,year), totals in sorted(refs.totals.items()):
        if league in ['NPB','KBO']:
            reference_summary.append(dict(league=league,season=year,pa=float(totals.sum()),
                unmapped_pa=refs.unmapped[league,year], mapped_fraction=1-refs.unmapped[league,year]/totals.sum()))
    save(OUT / 'preflight.json', dict(source_hashes=hashes, cells=checks, input_origins=641,
         outer_fold_profiles=3205, original_source_origins=sum(r['original_source_origin'] for r in inputs),
         added_source_origins=sum(not r['original_source_origin'] for r in inputs),
         reference_summary=reference_summary, forecast_membership_changed=False,
         protected_outcomes_read=False, all_preflights_before_fits=True))
    print(json.dumps(dict(preflight_cells=len(checks),profiles=3205,heads_fitted=0)),flush=True)


def run():
    pre=read(OUT / 'preflight.json'); verify(pre['source_hashes'])
    if (OUT / 'fit-receipt.json').exists():
        raise ValueError('Completed component preparation exists')
    if (OUT / 'fits.json').exists() or (OUT / 'profiles.json').exists():
        raise ValueError('Inspect partial execution before restart')
    inputs=read(INPUTS / 'origin-inputs.json')['rows']; lut={r['candidate_key']:r for r in inputs}
    pairs=read(INPUTS / 'pair-role-evidence.json')['pairs']; refs=References(sources())
    fits=[]; profiles=[]
    for i,c in enumerate(pre['cells']):
        m=fit(pairs,refs,c['origin_year'],c['excluded_folds'])
        if m['people']!=c['people'] or m['people_by_league']!=c['people_by_league']:
            raise ValueError('Fit/preflight support mismatch')
        fit_key=f"{c['origin_year']}-" + '-'.join(map(str,c['excluded_folds']))
        fits.append(dict(fit_key=fit_key,**m))
        for member in c['members']:
            p=profile(lut[member['candidate_key']],m,refs)
            profiles.append(dict(**p,outer_fold=member['outer_fold'],fit_key=fit_key))
        if (i+1)%30==0:
            print(json.dumps(dict(fitted_cells=i+1,total_cells=len(pre['cells']))),flush=True)
    if len(profiles)!=3205 or len({(p['candidate_key'],p['outer_fold']) for p in profiles})!=3205:
        raise ValueError('Profile membership changed')
    save(OUT / 'fits.json',dict(fits=fits))
    save(OUT / 'profiles.json',dict(profiles=profiles))
    save(OUT / 'fit-receipt.json',dict(source_hashes=pre['source_hashes'],new_component_fits=len(fits)*8,
        origin_local_cells=len(fits),profiles=len(profiles),missing_profiles=sum(p['missing_translation'] for p in profiles),
        model_approved=False,full_hitter_forecasts_changed=False,independent_review_status='pending',
        player_walkthrough_status='pending',
        artifact_hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [OUT/'preflight.json',OUT/'fits.json',OUT/'profiles.json']}))
    print(json.dumps(dict(component_fits=len(fits)*8,profiles=len(profiles),missing=sum(p['missing_translation'] for p in profiles),review='pending')),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('action',choices=['prepare','fit'])
    args=parser.parse_args()
    prepare() if args.action=='prepare' else run()
