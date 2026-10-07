"""Fixed neutral-versus-shrunk history comparison, awaiting player review."""
from collections import defaultdict
import json
from pathlib import Path

import polars as pl

from source_catcher_throw_block_v5 import ROOT,OUT
from review_catcher_throw_block_source_v5 import PUBLIC
from audit_catcher_throw_block_talent_v5 import profile
from audit_defensive_talent_support import verify
from run_hitter_finite_return_baseline import protections,save
from universal_baseball import catcher_throw_block_baseline as baseline
from universal_baseball.storage import sha256_file


def main():
    protected=protections();pre=json.loads((OUT/'talent-support-review.json').read_text(encoding='utf8'));verify(pre['hashes'])
    assert pre['before_scoring'] and pre['player_walkthrough_status']=='complete' and pre['protections']==protected
    rows=pl.read_parquet(OUT/'talent-labels.parquet').to_dicts();annual=pl.read_parquet(OUT/'extension-annual.parquet').to_dicts()
    bypid=defaultdict(list)
    for s in annual:bypid[s['component'],s['player_id']].append(s)
    cells={(c['component'],c['origin'],c['fold']):c for c in pre['cells']}
    for r in rows:
        kind,pid,y=r['component'],r['player_id'],r['origin_year']
        h=baseline.history(kind,bypid[kind,pid],y)
        assert abs(h['history_opportunities']-r['history_opportunities'])<1e-8 and abs(h['history_runs']-r['history_runs'])<1e-8
        r.update(h);r['neutral']=0.;r['fold']=pid%5
        c=cells[kind,y,r['fold']];i=c['test_keys'].index([y,pid]);r['profile_people']=c['joint_profile_people'][i]
        r['sparse_profile']=r['profile_people']<20;r['training_people']=c['training_people']
    contracts=[ROOT/'docs/catcher-throw-block-v5-talent-contract.md',Path(__file__),ROOT/'src/universal_baseball/catcher_throw_block_baseline.py',OUT/'talent-support-review.json',OUT/'talent-labels.parquet']
    seal=OUT/'comparison-preflight.json';assert not seal.exists()
    save(seal,dict(before_scoring=True,no_learned_fit=True,protections=protected,hashes={str(p):sha256_file(p) for p in contracts},priors=baseline.PRIOR))
    scores=[];groups=[]
    for kind in ('throwing','blocking'):
        for year in sorted({r['origin_year'] for r in rows if r['component']==kind}):
            cohort=[r for r in rows if r['component']==kind and r['origin_year']==year];rr=[r for r in cohort if r['quality_rate'] is not None]
            if rr:scores.append(dict(component=kind,origin=year,eligible=len(cohort),neutral=baseline.score(rr,'neutral'),history=baseline.score(rr,'history'),interval=baseline.interval(rr)))
        rr=[r for r in rows if r['component']==kind and r['origin_year']==2022 and r['quality_rate'] is not None]
        for family,index in [('age',0),('exposure',1)]:
            for label in sorted({profile(r)[index] for r in rr}):
                group=[r for r in rr if profile(r)[index]==label]
                groups.append(dict(component=kind,family=family,group=label,neutral=baseline.score(group,'neutral'),history=baseline.score(group,'history'),interval=baseline.interval(group),
                        uncertainty='too few independent people for population inference' if len(group)<10 else 'development subset'))
    table=OUT/'talent-predictions.parquet';assert not table.exists();pl.DataFrame(rows,infer_schema_length=None).write_parquet(table)
    paths=[table,seal,*contracts]
    report=OUT/'talent-report.json';assert not report.exists()
    save(report,dict(player_walkthrough_status='pending',no_learned_fit=True,scores=scores,groups=groups,
        primary_sparse_profiles={k:sum(r['sparse_profile'] for r in rows if r['component']==k and r['origin_year']==2022 and r['quality_rate'] is not None) for k in baseline.PRIOR},
        protections=protected,no_2026_outcomes=True,deployment_approved=False,hashes={str(p):sha256_file(p) for p in paths}))
    for p in (seal,report):(PUBLIC/p.name).write_bytes(p.read_bytes())
    print(json.dumps(dict(primary=[s for s in scores if s['origin']==2022],groups=groups),indent=2))


if __name__=='__main__':main()
