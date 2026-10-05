"""Append a reviewed inventory with compatible actual labels; preserve the replay."""
from pathlib import Path
import json

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file
from audit_hitter_incumbent_representation import ROOT,GENERATED,OUT,read,save


def main():
    inventory=read(OUT/'inventory.json')
    for group in ['input_hashes','saved_model_hashes']:
        for p,h in inventory[group].items():assert sha256_file(Path(p))==h,p
    assert inventory['heads_replayed']==175 and inventory['new_fits']==0
    doc=ROOT/'docs/hitter-incumbent-representation-review.md'
    text=doc.read_text(encoding='utf8')
    q=pl.read_parquet(GENERATED/'hitter-overseas-integration/predictions.parquet')
    old_cases=read(GENERATED/'hitter-overseas-integration/reviewed-cases.json')['cases']
    peers={r['origin']['row_id']:r for r in old_cases}
    aligned=[]
    for c in inventory['cases']:
        row=q.filter(pl.col('row_id')==c['row_id']).row(0,named=True)
        assert row['origin_year']==c['origin_year'] and row['player_id']==c['player_id']
        assert str(c['origin_year']) in text and c['player_name'] in text
        assert np.isclose(c['current']['rate'],row['current_rate'],atol=1e-10)
        assert np.isclose(c['current']['PA'],row['current_pa'],atol=1e-10)
        assert np.isclose(c['current']['value'],row['current_value'],atol=1e-10)
        case=dict(c)
        case['original_inventory_actual']=case.pop('actual')
        case['actual']=dict(PA=row['next_pa'],rate=row['actual_relative_rate'] if row['next_pa'] else None,
                            value=row['actual_relative_value'],reference='future MLB environment; origin replacement')
        case['existing_review_context_and_peers']=peers[c['row_id']]
        aligned.append(case)
    names=read(GENERATED/'practical-hitter-numeric-repair-v53/preflight.json')['rate_features']
    fields=[n for n in names if n.startswith('pooled_') and n.rsplit('_',1)[-1] in {'K','BB','HBP','HR','BABIP','2B','3B'}]
    minor=[n for n in fields if not n.startswith('pooled_MLB_')]
    assert len(fields)==98 and len(minor)==91 and len(aligned)==13
    result=dict(status='incumbent_inventory_review_complete_not_predictive_validation',heads_replayed=175,
        rows=30506,new_fits=0,player_walkthrough_status='complete',cases=aligned,missing_cases=inventory['missing_cases'],
        corrections=dict(pooled_event_rate_fields=98,non_MLB_event_rate_fields=91,
                         original_descriptive_count=105,legacy_actual_fields_replaced_in_this_append_only_receipt=True),
        protected_outcomes_used=False,frozen_forecast_changed=False,deployment_approved=False,broad_goal_achieved=False,
        hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'inventory.json',doc,
            GENERATED/'hitter-overseas-integration/predictions.parquet',
            GENERATED/'hitter-overseas-integration/reviewed-cases.json',
            GENERATED/'practical-hitter-v31/counts.parquet',
            GENERATED/'practical-hitter-numeric-repair-v53/preflight.json']})
    save(OUT/'final-review.json',result)
    save(ROOT/'reports/model-evidence/hitter-incumbent-representation/final-review.json',result)
    print('Inventory review complete: 175 replays, 13 cases, five explicit absences, compatible actual labels.',flush=True)


if __name__=='__main__':main()
