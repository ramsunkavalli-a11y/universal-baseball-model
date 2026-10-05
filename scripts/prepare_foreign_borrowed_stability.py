"""Preflight all domestic/foreign cells and preserve a single bounded alternative."""
import argparse
import json
from pathlib import Path

import polars as pl

from prepare_foreign_component_translation import ROOT,INPUTS,DOMESTIC,sources,read,save,verify
from universal_baseball.foreign_component_translation import References,profile,training_pairs
from universal_baseball.foreign_component_translation_v2 import histories
from universal_baseball.foreign_borrowed_stability import domestic_pairs,fit
from universal_baseball.storage import sha256_file

OLD=ROOT/'reports/generated/foreign-component-translation-v2'
OUT=ROOT/'reports/generated/foreign-borrowed-stability'
CONTRACT=ROOT/'docs/hitter-foreign-borrowed-stability-contract.md'


class CachedReferences(References):
    def __init__(self,rows):
        super().__init__(rows);self.cache={}
    def get(self,l,y,excluded):
        key=l,y,tuple(sorted(set(excluded)))
        if key not in self.cache:self.cache[key]=super().get(l,y,excluded)
        return self.cache[key]


def data():
    rows=sources()
    frame=pl.read_parquet(DOMESTIC).filter((pl.col('season')<=2024)&(pl.col('bucket')=='MLB'))
    mapping=dict(pa='plate_appearances',so='strike_outs',bb='base_on_balls',ibb='intentional_walks',
        hbp='hit_by_pitch',hits='hits',doubles='doubles',triples='triples',hr='home_runs')
    domestic=[dict(player_id=r['player_id'],season=r['season'],league='MLB',position=r['position'],
        reported_age=r['reported_age'],**{k:r[v] for k,v in mapping.items()}) for r in frame.iter_rows(named=True)]
    return rows,domestic_pairs(domestic)


def prepare():
    assert not OUT.exists(),'Inspect previous preparation before restarting'
    last=read(OLD/'final-review.json');verify(last['source_hashes']);verify(last['artifact_hashes'])
    pre=read(OLD/'preflight.json');verify(pre['source_hashes'])
    rows,domestic=data();refs=CachedReferences(rows)
    pairs=read(INPUTS/'pair-role-evidence.json')['pairs'];checks=[]
    for cell in pre['cells']:
        y=cell['origin_year'];k=cell['excluded_folds']
        selected=[p for p in domestic if p['target_year']<=y and p['fold'] not in k]
        assert selected and all(p['source_year']<p['target_year']<=y and p['fold'] not in k for p in selected)
        assert all(s['season']<=p['source_year'] for p in selected for s in p['history'])
        for p in selected:
            refs.get('MLB',p['target_year'],k)
            for s in p['history']:refs.get('MLB',s['season'],k)
        movers=training_pairs(pairs,y,k)
        assert len(movers)==cell['pairs']
        checks.append(dict(**cell,domestic_calibration_pairs=len(selected),domestic_calibration_people=len({p['player_id'] for p in selected}),
            domestic_keys=[[p['player_id'],p['source_year']] for p in selected],maximum_domestic_target_year=max(p['target_year'] for p in selected)))
    save(OUT/'domestic-calibration.json',dict(pairs=domestic))
    paths=[CONTRACT,Path(__file__),ROOT/'src/universal_baseball/foreign_borrowed_stability.py',
        ROOT/'tests/test_foreign_borrowed_stability.py',OUT/'domestic-calibration.json',OLD/'preflight.json',OLD/'final-review.json',OLD/'profiles.json',OLD/'reviewed-cases.json']
    hashes={**pre['source_hashes'],**{str(p.relative_to(ROOT)):sha256_file(p) for p in paths}}
    save(OUT/'preflight.json',dict(cells=checks,source_hashes=hashes,all_checks_before_fits=True,
        domestic_pairs=len(domestic),domestic_people=len({p['player_id'] for p in domestic}),
        profile_membership_unchanged=True,source_origins=641,outer_profiles=3205,
        protected_outcomes_read=False,new_full_hitter_forecasts=0))
    print(json.dumps(dict(cells=len(checks),domestic_pairs=len(domestic),domestic_people=len({p['player_id'] for p in domestic}))),flush=True)


def run():
    pre=read(OUT/'preflight.json');verify(pre['source_hashes'])
    assert not (OUT/'fits.json').exists() and not (OUT/'fit-receipt.json').exists(),'Inspect actual execution before restarting'
    rows,domestic=data();assert domestic==read(OUT/'domestic-calibration.json')['pairs']
    refs=CachedReferences(rows);history=histories(rows);cache={}
    inputs={r['candidate_key']:r for r in read(INPUTS/'origin-inputs.json')['rows']}
    pairs=read(INPUTS/'pair-role-evidence.json')['pairs'];models=[];profiles=[]
    for i,c in enumerate(pre['cells']):
        y=c['origin_year'];k=c['excluded_folds'];m=fit(domestic,pairs,history,refs,y,k,cache)
        assert m['domestic_keys']==c['domestic_keys']
        key=f'{y}-'+'-'.join(map(str,k));models.append(dict(fit_key=key,**m))
        for member in c['members']:
            p=profile(inputs[member['candidate_key']],m,refs)
            for piece in p['leagues']:
                piece['domestic_coordinate_extrapolation']=[j for j,x in enumerate(piece['source_relative_clr']) if x<m['domestic_x_min'][j] or x>m['domestic_x_max'][j]]
            profiles.append(dict(**p,fit_key=key,outer_fold=member['outer_fold']))
        if (i+1)%20==0:print(json.dumps(dict(cells_fitted=i+1,total_cells=len(pre['cells']))),flush=True)
    assert len(profiles)==3205 and len({(p['candidate_key'],p['outer_fold']) for p in profiles})==3205
    save(OUT/'fits.json',dict(fits=models));save(OUT/'profiles.json',dict(profiles=profiles))
    save(OUT/'fit-receipt.json',dict(source_hashes=pre['source_hashes'],cells=len(models),domestic_component_fits=len(models)*8,
        foreign_offset_estimates=len(models)*16,profiles=len(profiles),missing_profiles=sum(p['missing_translation'] for p in profiles),
        source_only_profile_membership_unchanged=True,independent_review_status='pending',player_walkthrough_status='pending',
        full_hitter_forecasts_changed=False,
        artifact_hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [OUT/'preflight.json',OUT/'fits.json',OUT/'profiles.json']}))
    print(json.dumps(dict(profiles=len(profiles),review='pending')),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','fit']);args=parser.parse_args()
    prepare() if args.action=='prepare' else run()
