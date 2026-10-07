"""Locked descriptive baseline scoring; no learned fit or exposure forecast."""
from collections import defaultdict
from pathlib import Path
import json
import polars as pl
from universal_baseball.arm_receiving_baseline import history, score, interval
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'reports/generated/arm-receiving-v6/official-scope'
OUT=ROOT/'reports/generated/arm-receiving-v6/talent'
PUBLIC=ROOT/'reports/model-evidence/arm-receiving-v6/talent'


def main():
    protections()
    assert not OUT.exists()
    support=json.loads((SOURCE/'talent-support-review.json').read_text())
    assert support['before_scoring'] and support['player_walkthrough_status']=='complete'
    for p,h in support['input_hashes'].items():assert sha256_file(Path(p))==h,p
    histories=defaultdict(list)
    for r in pl.read_parquet(SOURCE/'annual.parquet').to_dicts():histories[r['kind'],r['player_id']].append(r)
    rows=pl.read_parquet(SOURCE/'talent-labels.parquet').to_dicts()
    for r in rows:
        result=history(r['kind'],histories[r['kind'],r['player_id']],r['origin_year'])
        assert result['history_opportunities']==r['history_opportunities'] and result['history_runs']==r['history_runs']
        r.update(result);r['neutral']=0.
    hashes={str(p):sha256_file(p) for p in [Path(__file__),ROOT/'src/universal_baseball/arm_receiving_baseline.py',
        ROOT/'docs/arm-receiving-v6-talent-contract.md',SOURCE/'annual.parquet',SOURCE/'talent-labels.parquet',SOURCE/'talent-support-review.json']}
    OUT.mkdir(parents=True);PUBLIC.mkdir(parents=True,exist_ok=True)
    save(OUT/'comparison-preflight.json',dict(before_scoring=True,recipe_frozen=True,input_hashes=hashes,
        no_model_fit=True,no_2026_outcomes=True,primary_origin=2022))
    pl.DataFrame(rows,infer_schema_length=None).write_parquet(OUT/'predictions.parquet')
    reports=[]
    for kind in ('arm','receiving'):
        for y in sorted({r['origin_year'] for r in rows if r['kind']==kind}):
            allrows=[r for r in rows if r['kind']==kind and r['origin_year']==y]
            measured=[r for r in allrows if r['quality_rate'] is not None]
            if not measured:continue
            groups=[]
            for label,predicate in [('age<=24',lambda r:r['age'] is not None and r['age']<=24),
                ('age25-29',lambda r:r['age'] is not None and 24<r['age']<30),('age30+',lambda r:r['age'] is not None and r['age']>=30),
                ('tiny',lambda r:r['history_opportunities']<(50 if kind=='arm' else 100)),
                ('no_qualified_history',lambda r:not r['quality_evidence_observed'])]:
                rr=[r for r in measured if predicate(r)]
                if rr:groups.append(dict(group=label,neutral=score(rr,'neutral'),history=score(rr,'history')))
            reports.append(dict(kind=kind,origin=y,eligible=len(allrows),measured=len(measured),unknown=len(allrows)-len(measured),
                neutral=score(measured,'neutral'),history=score(measured,'history'),paired_interval=interval(measured),groups=groups))
    report=dict(reports=reports,no_model_fit=True,no_2026_outcomes=True,player_walkthrough_status='pending',
                disposition='provisional_until_player_review',deployment_allowed=False,input_hashes=hashes,
                output_hashes={str(OUT/'predictions.parquet'):sha256_file(OUT/'predictions.parquet')})
    save(OUT/'report.json',report);save(PUBLIC/'report.json',report)
    print(json.dumps([r for r in reports if r['origin']==2022],indent=2))


if __name__=='__main__':main()
